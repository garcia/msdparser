from dataclasses import dataclass
from functools import reduce
from io import StringIO
import re
from typing import Mapping, Optional, Sequence, TextIO


__all__ = ["MSDParameter"]


def match_next_n_lines(n: int) -> re.Pattern:
    return re.compile(
        r"^(?:[^\r\n]*(?:\r?\n)){NNN}[^\r\n]*".replace("NNN", str(n)), re.MULTILINE
    )


UNTIL_NEWLINE = re.compile(r"([^\r\n]*)(\r?\n)", re.MULTILINE)


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
    def value(self) -> str:
        """
        The second MSD component, separated from the key by a ``:``.

        If there *is* no second MSD component (i.e. the parameter has no
        ``:`` separator), returns an empty string *(new in 3.0)*. This
        rarely happens in practice and is typically treated the same as a
        blank value anyway.
        """
        try:
            return self.components[1]
        except IndexError:
            return ""

    @staticmethod
    def _serialize_component_without_comments(
        component: str, *, escapes: bool = True
    ) -> str:
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

    def _serialize_components_with_comments(
        self,
        file: TextIO,
        *,
        escapes: bool = True,
    ):
        assert self.comments

        last_component = len(self.components) - 1
        lines_with_comments = sorted(self.comments.keys())
        line = 0

        for c, component in enumerate(self.components):
            while component and lines_with_comments:
                line_with_comment = lines_with_comments[0]
                assert line <= line_with_comment, f"{line} > {line_with_comment}"
                if line == line_with_comment:
                    match = re.match(UNTIL_NEWLINE, component)
                    if not match:
                        # No newline in the rest of this component;
                        # write it and move on to the next component
                        file.write(
                            self._serialize_component_without_comments(
                                component, escapes=escapes
                            )
                        )
                        component = ""
                        break
                    # Insert comment before the newline
                    component = component[len(match.group(0)) :]
                    fragment: str = match.group(1)
                    newline: str = match.group(2)
                    file.write(
                        self._serialize_component_without_comments(
                            fragment, escapes=escapes
                        )
                    )
                    file.write(self.comments[line])
                    file.write(newline)
                    lines_with_comments.pop(0)
                    line += 1

                else:
                    # Get lines up to the comment
                    lines_to_skip = line_with_comment - line
                    assert lines_to_skip >= 1, f"{lines_to_skip} < 1"

                    next_n_lines = match_next_n_lines(lines_to_skip)
                    match = re.match(next_n_lines, component)
                    if not match:
                        file.write(
                            self._serialize_component_without_comments(
                                component, escapes=escapes
                            )
                        )
                        line += component.count("\n")
                        break

                    assert (
                        match.group(0).count("\n") == lines_to_skip
                    ), rf'{repr(match.group(0))}.count("\n") != {lines_to_skip}'

                    component = component[len(match.group(0)) :]
                    file.write(match.group(0))
                    line += lines_to_skip

            if c != last_component:
                file.write(":")

        # We should have hit all the lines with comments by the end
        assert len(lines_with_comments) == 0, lines_with_comments

        # Handle any leftover component
        if component:
            file.write(
                self._serialize_component_without_comments(component, escapes=escapes)
            )

    def serialize(
        self,
        file: TextIO,
        *,
        escapes: bool = True,
        exact: bool = False,
    ):
        """
        Serialize the key/value pair to MSD, including the surrounding
        ``#:;`` characters.

        By default, backslashes (``\\``) and special substrings (``:``,
        ``;``, and ``//``) are escaped. Setting `escapes` to False will
        interpolate the components unchanged, unless any contain a special
        substring, in which case a ``ValueError`` will be raised instead.
        """
        if exact and self.preamble:
            file.write(self.preamble)
        file.write("#")
        if exact and self.comments:
            self._serialize_components_with_comments(file, escapes=escapes)
        else:
            last_component = len(self.components) - 1
            for c, component in enumerate(self.components):
                file.write(
                    MSDParameter._serialize_component_without_comments(
                        component, escapes=escapes
                    )
                )
                if c != last_component:
                    file.write(":")
        if exact:
            file.write(self.suffix)
        else:
            file.write(";")

    def __str__(self) -> str:
        return self.stringify()

    def stringify(self, *, escapes: bool = True, exact: bool = False):
        output = StringIO()
        self.serialize(output, escapes=escapes, exact=exact)
        return output.getvalue()
