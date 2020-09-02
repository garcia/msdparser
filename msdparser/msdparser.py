import codecs
import enum
from io import StringIO


__all__ = ['MSDParser']


class State(enum.Enum):
    """
    Encapsulates the high-level state of the MSD parser.
    """
    SEEK = enum.auto() # Discard until a '#' is reached
    KEY = enum.auto() # Read the key until a ':' or ';' is reached
    VALUE = enum.auto() # Read the value until a ';' is reached


class ParameterState(object):
    """
    Encapsulates the complete state of the MSD parser, including the partial
    key/value pair.
    """
    __slots__ = ['key', 'value', 'state']

    def __init__(self):
        self._reset()
    
    def _reset(self):
        """
        Clear the key & value and set the state to SEEK.
        """
        self.key = StringIO()
        self.value = StringIO()
        self.state = State.SEEK
    
    def write(self, text):
        """
        Write to the key or value, or ignore if seeking.
        """
        if self.state is State.KEY:
            self.key.write(text)
        elif self.state is State.VALUE:
            self.value.write(text)
    
    def complete(self):
        """
        Return the parameter as a (key, value) tuple and reset to the initial
        key / value / state.
        """
        parameter = (self.key.getvalue(), self.value.getvalue())
        self._reset()
        return parameter


class MSDParser(object):
    """
    Simple parser for MSD files. All parameters are treated as key-value pairs.
    """
    def __init__(self, *, file=None, string=None):
        if file is None and string is None:
            raise ValueError("must provide either a file or a string")
        if file is not None and string is not None:
            raise ValueError("must provide either a file or a string, not both")
        self.file = file
        self.string = string

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.file:
            self.file.close()
    
    def _line_iterator(self):
        if self.file is not None:
            return self.file
        elif self.string is not None:
            return self.string.splitlines(True)
        else:
            assert False

    def __iter__(self):
        ps = ParameterState()
        
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
                        break
                    # Write the '/' otherwise
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
        if ps.state is State.VALUE:
            yield ps.complete()
