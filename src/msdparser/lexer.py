from dataclasses import dataclass
import enum
from io import StringIO
import re
from typing import Iterator, List, Optional, TextIO, Tuple, cast


__all__ = ["MSDToken", "lex_msd"]


class MSDToken(enum.Enum):
    """
    Enumeration of the lexical tokens produced by :func:`lex_msd`.
    """

    TEXT = enum.auto()
    """A literal text fragment. This matches anything not matched below."""
    START_PARAMETER = enum.auto()
    """A ``#`` indicating the start of a parameter."""
    NEXT_COMPONENT = enum.auto()
    """A ``:`` inside a parameter separating its components."""
    END_PARAMETER = enum.auto()
    """
    A ``;`` indicating the end of a parameter, or a string containing
    a line break & any surrounding whitespace if we recovered from a
    missing semicolon.
    """
    ESCAPE = enum.auto()
    """A ``\\`` followed by (and including) the escaped character."""
    COMMENT = enum.auto()
    """
    A ``//`` followed by (and including) the comment text. Doesn't include
    the terminating newline.
    """


class LexerMatch(enum.Enum):
    ESCAPED_TEXT = re.compile(r"[^\\\/:;#]+")
    UNESCAPED_TEXT = re.compile(r"[^\/:;#]+")
    POUND = re.compile(r"#")
    COLON = re.compile(r":")
    SEMICOLON = re.compile(r";")
    ESCAPE = re.compile(r"(?s)\\.")
    COMMENT = re.compile(r"//[^\r\n]*")
    SLASH = re.compile(r"/")


@dataclass
class LexerPattern:
    match: LexerMatch
    token_outside_param: MSDToken
    token_inside_param: MSDToken
    escapes: Optional[bool] = None


LEXER_PATTERNS = [
    LexerPattern(
        match=LexerMatch.ESCAPED_TEXT,
        token_outside_param=MSDToken.TEXT,
        token_inside_param=MSDToken.TEXT,
        escapes=True,
    ),
    LexerPattern(
        match=LexerMatch.UNESCAPED_TEXT,
        token_outside_param=MSDToken.TEXT,
        token_inside_param=MSDToken.TEXT,
        escapes=False,
    ),
    LexerPattern(
        match=LexerMatch.POUND,
        token_outside_param=MSDToken.START_PARAMETER,
        token_inside_param=MSDToken.TEXT,
    ),
    LexerPattern(
        match=LexerMatch.COLON,
        token_outside_param=MSDToken.TEXT,
        token_inside_param=MSDToken.NEXT_COMPONENT,
    ),
    LexerPattern(
        match=LexerMatch.SEMICOLON,
        token_outside_param=MSDToken.TEXT,
        token_inside_param=MSDToken.END_PARAMETER,
    ),
    LexerPattern(
        match=LexerMatch.ESCAPE,
        token_outside_param=MSDToken.TEXT,
        token_inside_param=MSDToken.ESCAPE,
        escapes=True,
    ),
    LexerPattern(
        match=LexerMatch.COMMENT,
        token_outside_param=MSDToken.COMMENT,
        token_inside_param=MSDToken.COMMENT,
    ),
    LexerPattern(
        match=LexerMatch.SLASH,
        token_outside_param=MSDToken.TEXT,
        token_inside_param=MSDToken.TEXT,
    ),
]


SPACE_OR_TAB = re.compile(r"[ \t]*")


def lex_msd(
    *,
    file: Optional[TextIO] = None,
    string: Optional[str] = None,
    escapes: bool = True,
) -> Iterator[Tuple[MSDToken, str]]:
    """
    Tokenize MSD data into a stream of (:class:`.MSDToken`, str) tuples.

    Expects either a `file` (any file-like object) or a `string`
    containing MSD data, but not both.

    Most modern applications of MSD (like the SM and SSC formats) treat
    backslashes as escape characters, but some older ones (like DWI) don't.
    Set `escapes` to False to treat backslashes as regular text.

    Tokens will always follow these constraints:

    * :data:`~MSDToken.START_PARAMETER`, :data:`~MSDToken.NEXT_COMPONENT`,
      and :data:`~MSDToken.END_PARAMETER` tokens all represent
      *semantically meaningful* instances of their corresponding
      metacharacters (``#:;``), never escaped or out-of-context instances.
    * _(New in 3.0)_ Occurrences of :data:`~MSDToken.START_PARAMETER` and
      :data:`~MSDToken.END_PARAMETER` always perfectly alternate. In the
      case of a missing semicolon, :data:`~MSDToken.END_PARAMETER` may
      contain a line break.
    * Concatenating all of the tokenized strings together produces the
      original input.

    Keep in mind that MSD components (particularly values) are often
    separated into multiple :data:`~MSDToken.TEXT` fragments, possibly with
    :data:`~MSDToken.ESCAPE` and :data:`~.COMMENT` tokens interspersed.
    """
    file_or_string = file or string
    if file_or_string is None:
        raise ValueError("must provide either a file or a string")
    if file is not None and string is not None:
        raise ValueError("must provide either a file or a string, not both")

    textio = file if file else StringIO(string)

    # Part of the MSD document that has been read but not consumed
    msd_buffer = ""

    # Whether we are inside a parameter (between the '#' and its following ';')
    inside_parameter = False

    # Whether we are done reading from the input file or string
    done_reading = False

    # Only the lexer patterns that match the escapes flag
    # Pull out the regex pattern to reduce property accesses in the tight loop
    lexer_patterns = cast(
        List[Tuple[LexerPattern, re.Pattern]],
        [
            (pattern, pattern.match.value)
            for pattern in LEXER_PATTERNS
            if pattern.escapes in (None, escapes)
        ],
    )

    while not done_reading:
        chunk = textio.read(4096)
        if not chunk:
            done_reading = True
        msd_buffer += chunk

        # Reading chunks is faster than reading lines, but MSD relies on
        # lines to determine where comments end & when to recover from a
        # missing semicolon. This condition enforces that the MSD buffer
        # always either contains a newline *or* the rest of the input, so
        # that comments, escapes, etc. don't get split in half.
        while (
            # Measurably faster than `any(c in msd_buffer for c in '\r\n')`
            "\n" in msd_buffer
            or "\r" in msd_buffer
            or (done_reading and msd_buffer)
        ):
            for pattern, regex in lexer_patterns:
                match = regex.match(msd_buffer)
                if match:
                    msd_buffer = msd_buffer[match.end() :]
                    matched_text = match[0]
                    token = (
                        pattern.token_inside_param
                        if inside_parameter
                        else pattern.token_outside_param
                    )

                    # Recover from missing ';' at the end of a line
                    if (
                        # If we stopped at a '#' while parsing text inside a parameter,
                        msd_buffer[:1] == "#"
                        and inside_parameter
                        and token is MSDToken.TEXT
                        # And our text contains a newline (find the last one),
                        and (
                            last_nl := max(
                                matched_text.rfind("\r"), matched_text.rfind("\n")
                            )
                        )
                        != -1
                        # And everything after that newline is ' ' or '\t'...
                        and re.fullmatch(SPACE_OR_TAB, matched_text[last_nl + 1 :])
                    ):
                        # Stop the text at the trailing whitespace
                        matched_text_before_ws = matched_text.rstrip("\r\n\t ")
                        if matched_text_before_ws:
                            yield (token, matched_text_before_ws)
                        # Treat the trailing whitespace as an `END_PARAMETER` token
                        token = MSDToken.END_PARAMETER
                        matched_text = matched_text[len(matched_text_before_ws) :]

                    if token is MSDToken.START_PARAMETER:
                        inside_parameter = True
                    elif token is MSDToken.END_PARAMETER:
                        inside_parameter = False

                    yield (token, matched_text)
                    break

            else:
                # Didn't break from the pattern iterator
                assert False, f"no regex matches {repr(msd_buffer)}"
