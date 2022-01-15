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
    _ESCAPED_TEXT = r'[^\\\/\r\n:;#]+'
    _UNESCAPED_TEXT = r'[^\/\r\n:;#]+'
    TEXT = r'.' # This regex is never actually used
    COMMENT = r'//[^\r\n]*'
    POUND = r'#'
    COLON = r':'
    SEMICOLON = r';'
    WHITESPACE = r'\s'
    _ESCAPE = r'\\.'
    _SLASH = r'/'

    @classmethod
    def _literal_members(cls, *, escapes: bool) -> Sequence['MSDToken']:
        literal_members = (
            cls._ESCAPED_TEXT,
            cls._UNESCAPED_TEXT,
            cls._SLASH,
            cls.POUND,
            cls.WHITESPACE,
        )
        if escapes:
            return literal_members
        else:
            return (*literal_members, cls._ESCAPE)
    
    @classmethod
    def _exclude_members(cls, *, escapes: bool):
        if escapes:
            return (cls.TEXT, cls._UNESCAPED_TEXT)
        else:
            return (cls.TEXT, cls._ESCAPED_TEXT, cls._ESCAPE)



COMPILED_TOKENS: List[Pattern[str]] = [re.compile(token.value) for token in MSDToken]
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
        ignore_stray_text=ignore_stray_text,
    ):
        # Handle missing ';' outside of the loop
        if parameter_state.writing and token is MSDToken.POUND:
            yield parameter_state.complete()

        # Read normal characters at the start of the loop for speed
        if char not in ALL_METACHARACTERS or escaping:
            ps.write(char)
            if escaping:
                escaping = False

        elif char == '#':
            # Start of the next parameter
            if not ps.writing:
                ps.next_component()
            # Treat '#' normally elsewhere
            else:
                ps.write(char)

        elif char == '/':
            # Skip the rest of the line for comments
            if col+1 < len(line) and line[col+1] == '/':
                # Preserve the newline
                ps.write(trailing_newline(line))
                break
            # Write the '/' if it's not part of a comment
            ps.write(char)

        elif char == ';':
            # End of the parameter
            if ps.writing:
                yield ps.complete()
            # Otherwise this is a stray character
            else:
                ps.write(char)
        
        elif char == ':':
            # Key/values separator
            if ps.writing:
                ps.next_component()
            # Treat ':' normally elsewhere
            else:
                ps.write(char)
        
        elif char == '\\':
            if escapes:
                # Unconditionally write the next character
                escaping = True
            else:
                # Treat '\' normally if escapes are disabled
                ps.write(char)
        
        else:
            assert False, 'this branch should never be reached'

    # Handle missing ';' at the end of the input
    if ps.writing:
        yield ps.complete()

def lex_msd(
    *,
    file: Optional[Union[TextIO, Iterator[str]]] = None,
    string: Optional[str] = None,
    escapes: bool = True,
    ignore_stray_text: bool = False,
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
    
    partial_text: Optional[StringIO] = None
    exclude_members = MSDToken._exclude_members(escapes=escapes)
    literal_members = MSDToken._literal_members(escapes=escapes)

    def finish_text(text: Optional[StringIO]):
        if text:
            yield (MSDToken.TEXT, text.getvalue())
    
    for line in line_iterator:
        remaining_contents = line
        while remaining_contents:
            for token, compiled_token in zip(MSDToken, COMPILED_TOKENS):
                if token in exclude_members:
                    continue

                match = compiled_token.match(remaining_contents)
                if match:
                    line_start = remaining_contents is line
                    remaining_contents = remaining_contents[match.end():]
                    matched_text = match[0]
                    
                    if token is MSDToken.POUND and line_start and partial_text:
                        yield (MSDToken.TEXT, partial_text.getvalue())
                        partial_text = None
                    
                    if partial_text is not None:
                        if token in literal_members:
                            partial_text.write(matched_text)
                            break
                        elif token is MSDToken._ESCAPE:
                            # Write only the character after the backslash
                            partial_text.write(matched_text[1])
                            break
                        else:
                            yield (MSDToken.TEXT, partial_text.getvalue())
                            if token is MSDToken.SEMICOLON:
                                partial_text = None
                            else:
                                partial_text = StringIO()
                    
                    elif token is MSDToken.POUND:
                        partial_text = StringIO()

                    elif token not in (MSDToken.WHITESPACE, MSDToken.COMMENT):
                        if not ignore_stray_text:
                            raise MSDParserError(f'stray {token} encountered')
                        
                    
                    yield (token, matched_text)
                    break

            else: # didn't break
                assert False, f'no regex matches {repr(remaining_contents)}'
    
    if partial_text:
        yield (MSDToken.TEXT, partial_text.getvalue())