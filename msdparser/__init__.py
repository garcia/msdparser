__version__ = '2.0.0-beta.1'

from dataclasses import dataclass
from functools import reduce
from io import StringIO
import re
from typing import Iterable, Iterator, List, NamedTuple, Optional, Sequence, TextIO, Tuple, Union


__all__ = ['parse_msd', 'MSDParserError', 'MSDParameter']


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
        self._reset()
    
    def _reset(self) -> None:
        """
        Clear the key & value and set the state to SEEK.
        """
        self.components: List[StringIO] = []
        self.writing = False
    
    def write(self, text) -> None:
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
        self._reset()
        return parameter


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

    ps = ParameterState(ignore_stray_text=ignore_stray_text)
    escaping = False

    for line in line_iterator:

        # Handle missing ';' outside of the loop
        if ps.writing and line.startswith('#'):
            yield ps.complete()
        
        # Note data constitutes the vast majority of most MSD files, and
        # metacharacters are very sparse in this context. Checking this
        # up-front and writing the whole line rather than each character
        # yields a significant speed boost:
        if not HAS_METACHARACTERS.search(line):
            ps.write(line)
            continue

        for col, char in enumerate(line):

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
