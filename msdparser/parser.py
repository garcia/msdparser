from io import StringIO
from typing import Iterable, Iterator, List, Optional, TextIO, Tuple

from .lexer import lex_msd, MSDToken
from .parameter import MSDParameter


__all__ = ["MSDParserError", "parse_msd"]


class MSDParserError(Exception):
    """
    Raised when non-whitespace text is encountered between parameters.

    The byte order mark (U+FEFF) is special-cased as whitespace to
    simplify handling UTF-8 files with a leading BOM.
    """


def parse_msd(
    *,
    file: Optional[TextIO] = None,
    string: Optional[str] = None,
    tokens: Optional[Iterable[Tuple[MSDToken, str]]] = None,
    escapes: bool = True,
    ignore_stray_text: bool = False,
) -> Iterator[MSDParameter]:
    """
    Parse MSD data into a stream of :class:`.MSDParameter` objects.

    Input is specified using exactly one of these named parameters:

    * `file`:   any file-like object
    * `string`: string containing MSD data
    * `tokens`: iterable of (:class:`.MSDToken`, str) tuples;
      see :func:`.lex_msd` for details

    Most modern applications of MSD (like the SM and SSC formats) treat
    backslashes as escape characters, but some older ones (like DWI) don't.
    Set `escapes` to False to treat backslashes as regular text.

    Raises :class:`MSDParserError` if non-whitespace text is
    encountered between parameters, unless `ignore_stray_text` is True, in
    which case the stray text is simply discarded.
    """
    if sum(param is None for param in (file, string, tokens)) != 2:
        raise TypeError(
            "Must provide exactly one of `file`, `string`, or `tokens` "
            "as a named argument"
        )

    # A partial MSD parameter
    components: List[StringIO] = []

    # Whether we are inside a parameter (`#...;`)
    inside_parameter: bool = False

    # The last parameter we've seen (useful for debugging stray text)
    last_key: Optional[str] = None

    def push_text(text: str) -> None:
        """Append to the last component if inside a parameter, or handle stray text"""
        if inside_parameter:
            components[-1].write(text)
        elif not ignore_stray_text:
            if text and not text.isspace() and text != "\ufeff":
                char = text.lstrip()[0]
                if last_key is None:
                    at_location = "at start of document"
                else:
                    at_location = f"after {repr(last_key)} parameter"
                raise MSDParserError(f"stray {repr(char)} encountered {at_location}")

    def next_component() -> None:
        """Append an empty component string"""
        nonlocal inside_parameter
        inside_parameter = True
        components.append(StringIO())

    def complete_parameter() -> MSDParameter:
        """Form the components into an MSDParameter and reset the state"""
        nonlocal last_key, components, inside_parameter

        parameter = MSDParameter(
            tuple(component.getvalue() for component in components)
        )

        last_key = parameter.key
        components = []
        inside_parameter = False

        return parameter

    if tokens is None:
        tokens = lex_msd(
            file=file,
            string=string,
            escapes=escapes,
        )

    for token, value in tokens:
        if token is MSDToken.TEXT:
            push_text(value)

        elif token is MSDToken.START_PARAMETER:
            if inside_parameter:
                # The lexer only allows this condition at the start of the line
                # (otherwise the '#' will be emitted as text).
                yield complete_parameter()
            next_component()

        elif token is MSDToken.END_PARAMETER:
            if inside_parameter:
                yield complete_parameter()

        elif token is MSDToken.NEXT_COMPONENT:
            if inside_parameter:
                next_component()

        elif token is MSDToken.ESCAPE:
            push_text(value[1])

        elif token is MSDToken.COMMENT:
            pass

        else:
            assert False, f"unexpected token {token}"

    # Handle missing ';' at the end of the input
    if inside_parameter:
        yield complete_parameter()
