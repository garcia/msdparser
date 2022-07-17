from io import StringIO
from typing import Iterator, List, Optional, TextIO

from .lexer import lex_msd, MSDToken
from .parameter import MSDParameter


__all__ = ["MSDParserError", "MSDParameter", "parse_msd"]


class MSDParserError(Exception):
    """
    Raised when non-whitespace text is encountered between parameters.

    The byte order mark (U+FEFF) is special-cased as whitespace to
    simplify handling UTF-8 files with a leading BOM.
    """


class ParameterState:
    """
    Encapsulates the complete state of the MSD parser, including the partial
    key/value pair.
    """

    __slots__ = ["writing", "components", "state", "ignore_stray_text", "last_key"]

    def __init__(self, ignore_stray_text):
        self.ignore_stray_text = ignore_stray_text
        self.components: List[StringIO] = []
        self.writing = False
        self.last_key: Optional[str] = None

    def reset(self) -> None:
        """
        Clear the components & turn off writing.
        """
        self.last_key = self.components[0].getvalue() if self.components else ""
        self.components = []
        self.writing = False

    def write(self, text: str) -> None:
        """
        Write to the key or value, or handle stray text if seeking.
        """
        if self.writing:
            self.components[-1].write(text)
        elif not self.ignore_stray_text:
            if text and not text.isspace() and text != "\ufeff":
                char = text.lstrip()[0]
                if self.last_key is None:
                    at_location = "at start of document"
                else:
                    at_location = f"after {repr(self.last_key)} parameter"
                raise MSDParserError(f"stray {repr(char)} encountered {at_location}")

    def next_component(self) -> None:
        self.writing = True
        self.components.append(StringIO())

    def complete(self) -> MSDParameter:
        """
        Return the completed :class:`MSDParameter` and reset to the initial
        state.
        """
        parameter = MSDParameter(
            tuple(component.getvalue() for component in self.components)
        )
        self.reset()
        return parameter


def parse_msd(
    *,
    file: Optional[TextIO] = None,
    string: Optional[str] = None,
    escapes: bool = True,
    ignore_stray_text: bool = False,
) -> Iterator[MSDParameter]:
    """
    Parse MSD data into a stream of :class:`MSDParameter` objects.

    Expects either a `file` (any file-like object) or a `string`
    containing MSD data, but not both.

    Most modern applications of MSD (like the SM and SSC formats) treat
    backslashes as escape characters, but some older ones (like DWI) don't.
    Set `escapes` to False to treat backslashes as regular text.

    Raises :class:`MSDParserError` if non-whitespace text is
    encountered between parameters, unless `ignore_stray_text` is True, in
    which case the stray text is simply discarded.
    """
    parameter_state = ParameterState(ignore_stray_text)

    for token, value in lex_msd(
        file=file,
        string=string,
        escapes=escapes,
    ):
        if token is MSDToken.TEXT:
            parameter_state.write(value)

        elif token is MSDToken.START_PARAMETER:
            if parameter_state.writing:
                # The lexer only allows this condition at the start of the line
                # (otherwise the '#' will be emitted as text).
                yield parameter_state.complete()
            parameter_state.next_component()

        elif token is MSDToken.END_PARAMETER:
            if parameter_state.writing:
                yield parameter_state.complete()

        elif token is MSDToken.NEXT_COMPONENT:
            if parameter_state.writing:
                parameter_state.next_component()

        elif token is MSDToken.ESCAPE:
            parameter_state.write(value[1])

        elif token is MSDToken.COMMENT:
            pass

        else:
            assert False, f"unexpected token {token}"

    # Handle missing ';' at the end of the input
    if parameter_state.writing:
        yield parameter_state.complete()
