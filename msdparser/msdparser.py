import codecs
import enum
from io import StringIO, TextIOBase
from typing import Iterator, List, Optional, TextIO, Tuple, Union


__all__ = ['MSDParser', 'MSDParserError']


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
    Raised when a non-whitespace character is found outside parameters.

    The byte order mark (BOM, U+FEFF) is special-cased as whitespace.
    """


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
    
    def complete(self) -> Tuple[str, str]:
        """
        Return the parameter as a (key, value) tuple and reset to the initial
        key / value / state.
        """
        parameter = (self.key.getvalue(), self.value.getvalue())
        self._reset()
        return parameter


class MSDParser(object):
    """
    Simple parser for MSD files.

    :param Optional[Union[TextIO,Iterator[str]]] file:
        file or file-like object to read (mutually excludes `string`)
    :param Optional[str] string:
        string to read (mutually excludes `file`)
    :param bool ignore_stray_text:
        whether to suppress :class:`MSDParserError` when stray
        non-whitespace text is found outside parameters
    """
    def __init__(self, *,
                 file: Optional[Union[TextIO, Iterator[str]]] = None,
                 string: Optional[str] = None,
                 ignore_stray_text: bool = False):
        if file is None and string is None:
            raise ValueError('must provide either a file or a string')
        if file is not None and string is not None:
            raise ValueError('must provide either a file or a string, not both')
        self.file = file
        self.string = string
        self.ignore_stray_text = ignore_stray_text

    def __enter__(self) -> 'MSDParser':
        return self

    def __exit__(self, type, value, traceback) -> None:
        if isinstance(self.file, TextIOBase):
            self.file.close()
    
    def _line_iterator(self) -> Union[TextIO, Iterator[str], List[str]]:
        if self.file is not None:
            return self.file
        elif self.string is not None:
            return self.string.splitlines(True)
        else:
            assert False

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        ps = ParameterState(ignore_stray_text=self.ignore_stray_text)
        
        for line in self._line_iterator():

            # Handle missing ';' outside of the loop
            if ps.state is not State.SEEK and line.startswith('#'):
                yield ps.complete()

            for col, char in enumerate(line):

                # Read normal characters at the start of the loop for speed
                if char not in ':;/#':
                    ps.write(char)
                
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
                
                elif char == ':':
                    # Key-value separator
                    if ps.state is State.KEY:
                        ps.state = State.VALUE
                    # Treat ':' normally elsewhere
                    else:
                        ps.write(char)
        
        # Handle missing ';' at the end of the input
        if ps.state is not State.SEEK:
            yield ps.complete()
