__version__ = '2.0.0-beta.2'

from dataclasses import dataclass
import enum
from functools import reduce
from io import StringIO
import re
from typing import Iterator, List, Optional, Pattern, Sequence, TextIO, Tuple


__all__ = ['MSDParserError', 'MSDParameter', 'MSDToken', 'parse_msd', 'lex_msd']


def trailing_newline(line: str):
    end_of_line = len(line.rstrip('\r\n'))
    return line[end_of_line:]


class MSDParserError(Exception):
    """
    Raised when non-whitespace text is encountered between parameters.

    The byte order mark (U+FEFF) is special-cased as whitespace to
    simplify handling UTF-8 files with a leading BOM.
    """


@dataclass
class MSDParameter:
    '''
    An MSD parameter, comprised of a key and some values (usually one).

    Stringifying an ``MSDParameter`` converts it back into MSD, escaping
    any backslashes ``\\`` or special substrings.
    '''
    MUST_ESCAPE = ('//', ':', ';')
    
    components: Sequence[str]
    '''The raw MSD components. Any special substrings are unescaped.'''

    @property
    def key(self) -> Optional[str]:
        '''The first MSD component.'''
        try:
            return self.components[0]
        except IndexError:
            return None

    @property
    def value(self) -> Optional[str]:
        '''
        The second MSD component, after the key.
        '''
        try:
            return self.components[1]
        except IndexError:
            return None

    @staticmethod
    def serialize_component(component: str, *, escapes: bool = True) -> str:
        """
        Serialize an MSD component (key or value).

        By default, backslashes (``\\``) and special substrings (``:``,
        ``;``, and ``//``) are escaped. When `escapes` is set to False, if
        the component contains a special substring, this method throws
        ``ValueError`` to avoid producing invalid MSD.
        """
        if escapes:
            # Backslashes must be escaped first to avoid double-escaping
            return reduce(
                lambda key, esc: key.replace(esc, f'\\{esc}'),
                ('\\',) + MSDParameter.MUST_ESCAPE,
                component,
            )
        elif any(esc in component for esc in MSDParameter.MUST_ESCAPE):
            raise ValueError(
                f"{repr(component)} can't be serialized without escapes"
            )
        else:
            return component

    def serialize(self, file: TextIO, *, escapes: bool = True):
        """
        Serialize the key/value pair to MSD, including the surrounding
        ``#:;`` characters.

        By default, backslashes (``\\``) and special substrings (``//``,
        ``:``, and ``;``) are escaped. When `escapes` is set to False, if
        any component contains a special substring, this method throws
        ``ValueError`` to avoid producing invalid MSD.
        """
        last_component = len(self.components) - 1
        file.write('#')
        for c, component in enumerate(self.components):
            file.write(MSDParameter.serialize_component(component, escapes=escapes))
            if c != last_component:
                file.write(':')
        file.write(';')
    
    def __str__(self, *, escapes: bool = True) -> str:
        output = StringIO()
        self.serialize(output, escapes=escapes)
        return output.getvalue()


class ParameterState:
    """
    Encapsulates the complete state of the MSD parser, including the partial
    key/value pair.
    """
    __slots__ = ['writing', 'components', 'state', 'ignore_stray_text']

    def __init__(self, ignore_stray_text):
        self.ignore_stray_text = ignore_stray_text
        self.reset()
    
    def reset(self) -> None:
        """
        Clear the components & turn off writing.
        """
        self.components: List[StringIO] = []
        self.writing = False
    
    def write(self, text: str) -> None:
        """
        Write to the key or value, or handle stray text if seeking.
        """
        if self.writing:
            self.components[-1].write(text)
        elif not self.ignore_stray_text:
            if text and not text.isspace() and text != '\ufeff':
                raise MSDParserError(f"stray {repr(text)} encountered")
    
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


class MSDToken(enum.Enum):
    '''
    Enumeration of the lexical tokens produced by :func:`lex_msd`.
    '''
    TEXT = enum.auto()
    '''Literal text fragment, including any text between parameters.'''
    START_PARAMETER = enum.auto()
    '''A ``#`` indicating the start of a parameter.'''
    NEXT_COMPONENT = enum.auto()
    '''A ``:`` inside a parameter separating its components.'''
    END_PARAMETER = enum.auto()
    '''A ``;`` indicating the end of a parameter.'''
    ESCAPE = enum.auto()
    '''A ``\\`` followed by the escaped character.'''
    COMMENT = enum.auto()
    '''A ``//`` followed by the comment text, not including the newline.'''


def parse_msd(
    *,
    file: Optional[TextIO] = None,
    string: Optional[str] = None,
    escapes: bool = True,
    ignore_stray_text: bool = False
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
            assert False, f'unexpected token {token}'

    # Handle missing ';' at the end of the input
    if parameter_state.writing:
        yield parameter_state.complete()


class LexerPattern(enum.Enum):
    ESCAPED_TEXT = r'[^\\\/:;#]+'
    UNESCAPED_TEXT = r'[^\/:;#]+'
    POUND = r'#'
    COLON = r':'
    SEMICOLON = r';'
    ESCAPE = r'(?s)\\.'
    COMMENT = r'//[^\r\n]*'
    SLASH = r'/'

class LexerPatterns:
    TOKEN_MAPPINGS = {
        LexerPattern.ESCAPED_TEXT: [MSDToken.TEXT, MSDToken.TEXT],
        LexerPattern.UNESCAPED_TEXT: [MSDToken.TEXT, MSDToken.TEXT],
        LexerPattern.POUND: [MSDToken.START_PARAMETER, MSDToken.TEXT],
        LexerPattern.COLON: [MSDToken.TEXT, MSDToken.NEXT_COMPONENT],
        LexerPattern.SEMICOLON: [MSDToken.TEXT, MSDToken.END_PARAMETER],
        LexerPattern.ESCAPE: [MSDToken.TEXT, MSDToken.ESCAPE],
        LexerPattern.COMMENT: [MSDToken.COMMENT, MSDToken.COMMENT],
        LexerPattern.SLASH: [MSDToken.TEXT, MSDToken.TEXT],
    }

    IGNORE_PER_ESCAPES = {
        False: (LexerPattern.ESCAPED_TEXT, LexerPattern.ESCAPE),
        True: (LexerPattern.UNESCAPED_TEXT,),
    }
    
    @staticmethod
    def patterns(*, escapes: bool):
        return [
            t for t in LexerPattern
            if t not in LexerPatterns.IGNORE_PER_ESCAPES[escapes]
        ]


COMPILED_PATTERNS: List[Pattern[str]] = [
    re.compile(token.value) for token in LexerPattern
]


class TextBuffer(str):
    buffer: StringIO

    def __init__(self):
        self._reset()
    
    def _reset(self):
        self.buffer = StringIO()
    
    def write(self, value: str):
        self.buffer.write(value)
    
    def ends_with_newline(self) -> bool:
        value = self.buffer.getvalue()
        return any(value.endswith(c) for c in '\r\n')
    
    def complete(self) -> Iterator[Tuple[MSDToken, str]]:
        '''
        Yield a Text token for the buffered text & clear the buffer.
        
        Returns True if the buffered text ends with a newline.
        '''
        if self.buffer:
            value = self.buffer.getvalue()
            if value:
                yield (MSDToken.TEXT, value)
        self._reset()


def lex_msd(
    *,
    file: Optional[TextIO] = None,
    string: Optional[str] = None,
    escapes: bool = True,
) -> Iterator[Tuple[MSDToken, str]]:
    """
    Tokenize MSD data into a stream of (:class:`.MSDToken`, str) tuples.

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
        raise ValueError('must provide either a file or a string')
    if file is not None and string is not None:
        raise ValueError('must provide either a file or a string, not both')
    
    textio = file if file else StringIO(string)
    
    # This buffer stores literal text so that it can be yielded as
    # a single TEXT token, rather than multiple consecutive tokens.
    text_buffer = TextBuffer()

    # Part of the MSD document that has been read but not consumed
    msd_buffer = ''

    # Whether we are inside a parameter (between the '#' and its following ';')
    inside_parameter = False

    # Whether we are done reading from the input file or string
    done_reading = False

    # Try matching each MSD segment against each of these patterns.
    # This 3-tuple of (LexerPattern, Pattern[str], List[MSDToken]) is an
    # optimization that performs measurably better than indexing into the
    # token mapping on each innermost loop.
    pattern_iterator = [
        (pattern, compiled, LexerPatterns.TOKEN_MAPPINGS[pattern])
        for (pattern, compiled) in zip(LexerPattern, COMPILED_PATTERNS)
        if pattern in LexerPatterns.patterns(escapes=escapes)
    ]
    
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
            '\n' in msd_buffer
            or '\r' in msd_buffer
            or (done_reading and msd_buffer)
        ):
            for pattern, compiled_pattern, tokens in pattern_iterator:

                match = compiled_pattern.match(msd_buffer)
                if match:
                    msd_buffer = msd_buffer[match.end():]
                    matched_text = match[0]
                    token = tokens[inside_parameter]

                    # Recover from missing ';' at the end of a line
                    if (
                        pattern is LexerPattern.POUND
                        and token is MSDToken.TEXT
                        and text_buffer.ends_with_newline()
                    ):
                        token = MSDToken.START_PARAMETER

                    # Buffer text until non-text is reached
                    if token is MSDToken.TEXT:
                        text_buffer.write(matched_text)
                        break
                    
                    # Non-text matched, so yield & discard any buffered text
                    yield from text_buffer.complete()
                    
                    if token is MSDToken.START_PARAMETER:
                        inside_parameter = True
                    elif token is MSDToken.END_PARAMETER:
                        inside_parameter = False
                    
                    yield (token, matched_text)
                    break

            else: # didn't break from the pattern iterator
                assert False, f'no regex matches {repr(msd_buffer)}'
    
    yield from text_buffer.complete()