__version__ = '2.0.0-beta.1'

import enum
from functools import reduce
from io import StringIO
import re
from typing import Iterable, Iterator, NamedTuple, Optional, Sequence, TextIO, Tuple, Union


__all__ = ['parse_msd', 'MSDParserError', 'MSDParameter']


def trailing_newline(line: str):
    end_of_line = len(line.rstrip('\r\n'))
    return line[end_of_line:]


class State(enum.Enum):
    """
    Encapsulates the high-level state of the MSD parser.
    """
    SEEK = enum.auto() # Discard until a '#' is reached
    KEY = enum.auto() # Read the key until a ':' or ';' is reached
    VALUE = enum.auto() # Read the value until a ';' is reached


class MSDParserError(Exception):
    """
    Raised when non-whitespace text is encountered between parameters.

    The byte order mark (U+FEFF) is special-cased as whitespace to
    simplify handling UTF-8 files with a leading BOM.
    """


class MSDParameter(NamedTuple):
    """
    A key/value tuple.

    Stringifying an ``MSDParameter`` converts it back into MSD, escaping
    any backslashes ``\\`` or special substrings.
    """
    key: str
    '''The first MSD component. Any special substrings are unescaped.'''
    value: str
    '''The second MSD component. Any special substrings are unescaped.'''

    @classmethod
    def _serialize_component(
        cls,
        *,
        component_name: str,
        component: str,
        must_escape: Tuple[str, ...],
        escapes: bool,
    ) -> str:
        if escapes:
            return reduce(
                lambda key, esc: key.replace(esc, f'\\{esc}'),
                ('\\',) + must_escape, # sequence
                component,   # initial value
            )
        elif any(esc in component for esc in must_escape):
            raise ValueError(
                f'{repr(component)}: invalid MSD {component_name} without escapes'
            )
        else:
            return component

    def serialize_key(self, *, escapes: bool = True) -> str:
        """
        Serialize the key.

        By default, backslashes ``\\`` and special substrings for keys
        (``:``, ``;`` and ``//``) are escaped. When ``escapes`` is set to
        False and the key contains a special substring, this method throws
        ``ValueError`` to avoid producing invalid MSD.
        """
        return MSDParameter._serialize_component(
            component_name='key',
            component=self.key,
            must_escape=('//', ':', ';'),
            escapes=escapes,
        )

    def serialize_value(self, *, escapes: bool = True) -> str:
        """
        Serialize the value.
        
        By default, backslashes ``\\`` and special substrings for values
        (``;`` and ``//``) are escaped. When ``escapes`` is set to False
        and the key contains a special substring, this method throws
        ``ValueError`` to avoid producing invalid MSD.
        """
        return MSDParameter._serialize_component(
            component_name='value',
            component=self.value,
            must_escape=('//', ';'),
            escapes=escapes,
        )

    def serialize(self, *, escapes: bool = True) -> str:
        """
        Serialize the key/value pair to MSD, including the surrounding
        ``#:;`` characters.

        By default, backslashes ``\\`` and special substrings are escaped.
        When `escapes` is set to False and the key or value contains a
        special substring, this method throws ``ValueError`` to avoid
        producing invalid MSD. See :meth:`serialize_key` and
        :meth:`serialize_value` for more details.
        """
        return (
            f'#{self.serialize_key(escapes=escapes)}'
            f':{self.serialize_value(escapes=escapes)};'
        )
    
    def __str__(self) -> str:
        return self.serialize()


class ParameterState(object):
    """
    Encapsulates the complete state of the MSD parser, including the partial
    key/value pair.
    """
    __slots__ = ['key', 'value', 'state', 'ignore_stray_text']

    def __init__(self, ignore_stray_text):
        self.ignore_stray_text = ignore_stray_text
        self._reset()
    
    def _reset(self) -> None:
        """
        Clear the key & value and set the state to SEEK.
        """
        self.key = StringIO()
        self.value = StringIO()
        self.state = State.SEEK
    
    def write(self, text) -> None:
        """
        Write to the key or value, or handle stray text if seeking.
        """
        if self.state is State.KEY:
            self.key.write(text)
        elif self.state is State.VALUE:
            self.value.write(text)
        elif not self.ignore_stray_text:
            if text and not text.isspace() and text != '\ufeff':
                raise MSDParserError(f"stray {repr(text)} encountered")
    
    def complete(self) -> MSDParameter:
        """
        Return the parameter as a (key, value) tuple and reset to the initial
        key / value / state.
        """
        parameter = MSDParameter(self.key.getvalue(), self.value.getvalue())
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
) -> Iterator[Tuple[str, str]]:
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
        line_iterator = file_or_string.splitlines(True)
    else:
        line_iterator = file_or_string

    ps = ParameterState(ignore_stray_text=ignore_stray_text)
    escaping = False

    for line in line_iterator:

        # Handle missing ';' outside of the loop
        if ps.state is not State.SEEK and line.startswith('#'):
            yield ps.complete()
        
        # Note data constitutes the vast majority of most MSD files, and
        # metacharacters are very sparse in this context. Checking this
        # up-front and writing the whole line rather than each character
        # yields a ~50% speed boost:
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
                if ps.state is State.SEEK:
                    ps.state = State.KEY
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
                if ps.state is not State.SEEK:
                    yield ps.complete()
                # Otherwise this is a stray character
                else:
                    ps.write(char)
            
            elif char == ':':
                # Key-value separator
                if ps.state is State.KEY:
                    ps.state = State.VALUE
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
    if ps.state is not State.SEEK:
        yield ps.complete()
