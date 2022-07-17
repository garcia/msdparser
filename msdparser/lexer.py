from dataclasses import dataclass
import enum
from io import StringIO
import re
from typing import Iterator, List, Optional, Pattern, TextIO, Tuple, cast


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
    """A ``;`` indicating the end of a parameter."""
    ESCAPE = enum.auto()
    """A ``\\`` followed by (and including) the escaped character."""
    COMMENT = enum.auto()
    """
    A ``//`` followed by (and including) the comment text. Doesn't include
    the trailing newline.
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
    * :data:`~MSDToken.TEXT` will always be as long as possible. (You
      should never find multiple consecutive text tokens.)
    * Concatenating all of the tokenized strings together will produce the
      original input.

    Keep in mind that MSD components (particularly values) are often
    separated into multiple :data:`~MSDToken.TEXT` fragments due to
    :data:`~MSDToken.ESCAPE` and :data:`~.COMMENT` tokens. Refer to the
    source code for :func:`parse_msd` to understand how to consume the
    output of this function.
    """
    file_or_string = file or string
    if file_or_string is None:
        raise ValueError("must provide either a file or a string")
    if file is not None and string is not None:
        raise ValueError("must provide either a file or a string, not both")

    textio = file if file else StringIO(string)

    # This buffer stores literal text so that it can be yielded as
    # a single TEXT token, rather than multiple consecutive tokens.
    text_buffer = StringIO()

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

    def ends_with_newline(text) -> bool:
        return text and text[-1] in "\r\n"

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
                        pattern.match is LexerMatch.POUND
                        and token is MSDToken.TEXT
                        and ends_with_newline(text_buffer.getvalue())
                    ):
                        token = MSDToken.START_PARAMETER

                    # Buffer text until non-text is reached
                    if token is MSDToken.TEXT:
                        text_buffer.write(matched_text)
                        break

                    # Non-text matched, so yield & discard any buffered text
                    text = text_buffer.getvalue()
                    if text:
                        yield (MSDToken.TEXT, text)
                        text_buffer = StringIO()

                    if token is MSDToken.START_PARAMETER:
                        inside_parameter = True
                    elif token is MSDToken.END_PARAMETER:
                        inside_parameter = False

                    yield (token, matched_text)
                    break

            else:
                # Didn't break from the pattern iterator
                assert False, f"no regex matches {repr(msd_buffer)}"

    # Yield any remaining text
    text = text_buffer.getvalue()
    if text:
        yield (MSDToken.TEXT, text)
