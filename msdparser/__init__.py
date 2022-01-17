__version__ = '2.0.0-beta.2'

from ast import Str
from dataclasses import dataclass
import enum
from functools import reduce
from io import StringIO
import re
from typing import Iterable, Iterator, List, NamedTuple, Optional, Pattern, Sequence, TextIO, Tuple, Union


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
    Enumeration of MSD tokens and their corresponding regex.

    Members with a leading underscore are only used internally, and tokens
    representing metacharacters are guaranteed to be semantically
    meaningful (i.e. not literal text) as long as stray text is disabled
    from :meth:`lex_msd`.
    '''
    TEXT = enum.auto()
    START_PARAMETER = enum.auto()
    NEXT_COMPONENT = enum.auto()
    END_PARAMETER = enum.auto()
    ESCAPE = enum.auto()
    COMMENT = enum.auto()


ALL_METACHARACTERS = ':;/#\\'
HAS_METACHARACTERS = re.compile(f'[{re.escape(ALL_METACHARACTERS)}]')


def parse_msd(
    *,
    file: Optional[Union[TextIO, Iterator[str]]] = None,
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

    def token(
        self: 'LexerPattern',
        *,
        inside_parameter: bool,
        line_start: bool,
    ):
        if inside_parameter:
            if self in {
                LexerPattern.ESCAPED_TEXT,
                LexerPattern.UNESCAPED_TEXT,
                LexerPattern.SLASH,
            }:
                return MSDToken.TEXT
            elif self is LexerPattern.POUND:
                return MSDToken.START_PARAMETER if line_start else MSDToken.TEXT
            elif self is LexerPattern.COLON:
                return MSDToken.NEXT_COMPONENT
            elif self is LexerPattern.SEMICOLON:
                return MSDToken.END_PARAMETER
            elif self is LexerPattern.ESCAPE:
                return MSDToken.ESCAPE
        else:
            if self in {
                LexerPattern.ESCAPED_TEXT,
                LexerPattern.UNESCAPED_TEXT,
                LexerPattern.COLON,
                LexerPattern.SEMICOLON,
                LexerPattern.ESCAPE,
                LexerPattern.SLASH,
            }:
                return MSDToken.TEXT
            elif self is LexerPattern.POUND:
                return MSDToken.START_PARAMETER
        
        if self is LexerPattern.COMMENT:
            return MSDToken.COMMENT
        
        assert False, f'No matching MSDToken for {self}'


COMPILED_PATTERNS: List[Pattern[str]] = [
    re.compile(token.value) for token in LexerPattern
]


class PatternGroups:
    LITERALS = (
        LexerPattern.ESCAPED_TEXT,
        LexerPattern.UNESCAPED_TEXT,
        LexerPattern.SLASH,
        LexerPattern.POUND,
    )
    
    EXCLUDE_WITH_ESCAPES = (LexerPattern.UNESCAPED_TEXT,)
    EXCLUDE_WITHOUT_ESCAPES = (LexerPattern.ESCAPED_TEXT, LexerPattern.ESCAPE)


class TextBuffer(str):
    buffer: StringIO

    def __init__(self):
        self._reset()
    
    def _reset(self):
        self.buffer = StringIO()
    
    def write(self, value):
        self.buffer.write(value)
    
    def complete(self) -> Iterator[Tuple[MSDToken, str]]:
        if self.buffer:
            value = self.buffer.getvalue()
            if value:
                yield (MSDToken.TEXT, value)
        self._reset()


def lex_msd(
    *,
    file: Optional[Union[TextIO, Iterator[str]]] = None,
    string: Optional[str] = None,
    escapes: bool = True,
) -> Iterator[Tuple[MSDToken, str]]:
    file_or_string = file or string
    if file_or_string is None:
        raise ValueError('must provide either a file or a string')
    if file is not None and string is not None:
        raise ValueError('must provide either a file or a string, not both')
    
    # We've proven that `file_or_string` is not None because mypy can't prove
    # "either `file` or `string` is not None", hence the awkwardness here.
    # IMO this tradeoff is worth it for the explicitness of separate, named
    # parameters; otherwise users might try to pass filenames as input strings.
    line_iterator: Iterable[str]
    if isinstance(file_or_string, str):
        line_iterator = file_or_string.splitlines(True) # keep line endings
    else:
        line_iterator = file_or_string
    
    # This buffer stores literal text so that it can be yielded as
    # a single TEXT token, rather than multiple consecutive tokens.
    text_buffer = TextBuffer()
    inside_parameter = False
    exclude_patterns = PatternGroups.EXCLUDE_WITH_ESCAPES if escapes else PatternGroups.EXCLUDE_WITHOUT_ESCAPES
    
    for line in line_iterator:
        remaining_contents = line
        while remaining_contents:
            for pattern, compiled_pattern in zip(LexerPattern, COMPILED_PATTERNS):
                if pattern in exclude_patterns:
                    continue

                match = compiled_pattern.match(remaining_contents)
                if match:
                    line_start = remaining_contents is line
                    remaining_contents = remaining_contents[match.end():]
                    matched_text = match[0]
                    token = pattern.token(
                        inside_parameter=inside_parameter,
                        line_start=line_start,
                    )

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

            else: # didn't break
                assert False, f'no regex matches {repr(remaining_contents)}'
    
    yield from text_buffer.complete()