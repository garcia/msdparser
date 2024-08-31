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
    strict: bool = False,
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

    # Any text before the first parameter.
    # After the first parameter, this is set to None and never used again.
    preamble: Optional[StringIO] = StringIO()

    # A partial MSD parameter
    components: List[StringIO] = []

    # Whether we are inside a parameter (`#...;`)
    inside_parameter: bool = False

    # Line number inside parameter (starting from the opening `#`)
    line_inside_parameter: int = 0

    # Mapping of line numbers to comments (there can only be one per line)
    comments: dict[int, str] = {}

    # Any text after a parameter and before the next parameter
    suffix = StringIO()

    # The last parameter we've seen (useful for debugging stray text)
    last_key: Optional[str] = None

    def push_text(text: str) -> None:
        """
        Push plain text to the current component, preamble, or suffix.

        Also checks for stray text during strict parsing.
        """
        nonlocal components, line_inside_parameter, last_key

        if inside_parameter:
            components[-1].write(text)
            # TODO: decide how / whether to handle '\r'
            line_inside_parameter += value.count("\n")
        else:
            # Check for stray text during strict parsing
            if text and strict and not text.isspace() and text != "\ufeff":
                char = text.lstrip()[0]
                if last_key is None:
                    at_location = "at start of document"
                else:
                    at_location = f"after {repr(last_key)} parameter"
                raise MSDParserError(f"stray {repr(char)} encountered {at_location}")

            if preamble and len(components) == 0:
                preamble.write(text)
            else:
                suffix.write(text)

    def next_component() -> None:
        """Append an empty component string"""
        nonlocal inside_parameter
        inside_parameter = True
        components.append(StringIO())

    def assemble_parameter(reset: bool = False) -> Iterator[MSDParameter]:
        """
        Yield an MSDParameter from the current parser state.

        If `reset` is True, reset the parser state afterward.
        """
        nonlocal preamble, components, inside_parameter, line_inside_parameter, suffix, comments, last_key

        if len(components) == 0:
            return

        yield MSDParameter(
            components=tuple(component.getvalue() for component in components),
            preamble=preamble and preamble.getvalue(),
            comments=comments.copy(),
            suffix=suffix.getvalue(),
        )

        if reset:
            if preamble:
                preamble = None
            components = []
            inside_parameter = True
            line_inside_parameter = 0
            comments = {}
            suffix = StringIO()

    if tokens is None:
        tokens = lex_msd(
            file=file,
            string=string,
            escapes=escapes,
        )

    for token, value in tokens:
        if token is MSDToken.TEXT:
            try:
                push_text(value)
            except MSDParserError:
                if components:
                    yield from assemble_parameter()
                raise

        elif token is MSDToken.START_PARAMETER:
            assert not inside_parameter
            if len(components) > 0:
                yield from assemble_parameter(reset=True)
            next_component()

        elif token is MSDToken.END_PARAMETER:
            assert inside_parameter
            inside_parameter = False
            last_key = components[0].getvalue()
            suffix.write(value)

            if value != ";" and strict:
                raise MSDParserError(
                    f"Missing semicolon detected after {repr(last_key)} parameter"
                )

        elif token is MSDToken.NEXT_COMPONENT:
            assert inside_parameter
            next_component()

        elif token is MSDToken.ESCAPE:
            try:
                push_text(value[1])
            except MSDParserError:
                if components:
                    yield from assemble_parameter()
                raise

        elif token is MSDToken.COMMENT:
            if inside_parameter:
                comments[line_inside_parameter] = value
            else:
                if preamble and len(components) == 0:
                    preamble.write(value)
                else:
                    suffix.write(value)
        else:
            assert False, f"unexpected token {token}"

    # Remember to output the last parameter
    yield from assemble_parameter()
