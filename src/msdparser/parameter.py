from dataclasses import dataclass
from functools import reduce
from io import StringIO
from typing import Mapping, Optional, Sequence, TextIO


@dataclass
class MSDParameter:
    """
    An MSD parameter, comprised of a key and some values (usually one).

    Stringifying an ``MSDParameter`` converts it back into MSD, escaping
    any backslashes ``\\`` or special substrings.
    """

    _MUST_ESCAPE = ("//", ":", ";")
    _SHOULD_ESCAPE = ("\\", "#")

    components: Sequence[str]
    """The raw MSD components. Any special substrings are unescaped."""

    preamble: Optional[str] = None
    """
    Any text before the first parameter, for example, a comment at the top
    of the file.

    This attribute is always a string (possibly empty) for the first
    parameter and always None otherwise.
    """

    comments: Optional[Mapping[int, str]] = None
    """
    Mapping of line numbers to comments.
    
    Line numbers are relative to the ``#`` delimiter and start at 0.
    The comment string includes its ``//`` delimiter
    but does not include the trailing newline.
    """

    suffix: str = ""
    """
    Any text from the end of this parameter (including the ``;``)
    to the start of the next parameter (excluding the ``#``) or EOF.
    This will typically be a ``;`` followed by a line break.

    If we recovered from a missing ``;``, this string will *only* contain
    whitespace, at least a line break.
    """

    @property
    def key(self) -> str:
        """
        The first MSD component, the part immediately after the ``#`` sign.

        Raises ``IndexError`` if :attr:`~.components` is an empty sequence
        (:func:`.parse_msd` will never produce such a parameter).
        """
        return self.components[0]

    @property
    def value(self) -> Optional[str]:
        """
        The second MSD component, separated from the key by a ``:``.

        Returns None if the parameter ends after the key with no ``:``.
        This rarely happens in practice and is typically treated the same
        as a blank value.
        """
        try:
            return self.components[1]
        except IndexError:
            return None

    @staticmethod
    def serialize_component(component: str, *, escapes: bool = True) -> str:
        """
        Serialize an MSD component (key or value).

        By default, backslashes (``\\``) and special substrings (``:``,
        ``;``, and ``//``) are escaped. Setting `escapes` to False will
        return the component unchanged, unless it contains a special
        substring, in which case a ``ValueError`` will be raised instead.
        """
        if escapes:
            # Backslashes must be escaped first to avoid double-escaping
            return reduce(
                lambda key, esc: key.replace(esc, f"\\{esc}"),
                MSDParameter._SHOULD_ESCAPE + MSDParameter._MUST_ESCAPE,
                component,
            )
        elif any(esc in component for esc in MSDParameter._MUST_ESCAPE):
            raise ValueError(f"{repr(component)} can't be serialized without escapes")
        else:
            return component

    def serialize(self, file: TextIO, *, escapes: bool = True):
        """
        Serialize the key/value pair to MSD, including the surrounding
        ``#:;`` characters.

        By default, backslashes (``\\``) and special substrings (``:``,
        ``;``, and ``//``) are escaped. Setting `escapes` to False will
        interpolate the components unchanged, unless any contain a special
        substring, in which case a ``ValueError`` will be raised instead.
        """
        last_component = len(self.components) - 1
        file.write("#")
        for c, component in enumerate(self.components):
            file.write(MSDParameter.serialize_component(component, escapes=escapes))
            if c != last_component:
                file.write(":")
        file.write(";")

    def __str__(self, *, escapes: bool = True) -> str:
        output = StringIO()
        self.serialize(output, escapes=escapes)
        return output.getvalue()
