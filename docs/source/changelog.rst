Changelog
=========

3.0.0a2
-------

Bugfixes
~~~~~~~~

* Parameters containing comments now handle escapes correctly.
* Parameters that have components with newlines
  followed by components with comments
  no longer serialize comments on the wrong lines.
* Parameter suffixes are now serialized correctly with ``exact=True``.

3.0.0a1
-------

Breaking changes
~~~~~~~~~~~~~~~~

.. warning::

    **msdparser** 3.0 introduces some breaking changes
    that you may need to update your code to handle:

    **Strict parsing is now opt-in**
      
      :func:`.parse_msd`'s `ignore_stray_text` argument has been removed
      and replaced with a `strict` argument that defaults to `False`.
      Strict parsing throws an :class:`.MSDParserError`
      if stray text is encountered *or* a missing semicolon is detected.

      If your code passes :code:`ignore_stray_text=True` to :func:`.parse_msd`,
      simply remove it to restore the expected behavior.
      If your code omits `ignore_stray_text` or sets it to `False`,
      consider adding :code:`strict=True` to restore the old default behavior
      (along with errors for missing semicolons).

    **Values are now always strings**
      
      :attr:`.MSDParameter.value` no longer returns `None`
      in the edge case where a parameter ends without any ``:`` separator.
      Now it returns an empty string instead.
      
      Your code no longer needs to guard against `None` when accessing the value.
      If you want to handle the missing ``:`` case,
      check if the :attr:`~.components` array has a length of 1.

New features
~~~~~~~~~~~~

:class:`.MSDParameter` has three new attributes:
:attr:`~.preamble`, :attr:`~.comments`, and :attr:`~.suffix`.

  These attributes cover all of the asemantic text
  that would otherwise be discarded.

:class:`.MSDParameter` has a new method: :meth:`~.stringify`.

  These are all equivalent::

    str(param)
    param.__str__()
    param.stringify()
  
  The new :meth:`~.stringify` method
  takes the same named arguments as :meth:`~.serialize`,
  including both `escapes` and a new `mirror_input` argument (described below).

:class:`.MSDParameter`'s :meth:`.serialize` and :meth:`.stringify` methods
now accept an optional, named `mirror_input` argument.

  Passing :code:`mirror_input=True` will reincorporate the asemantic text
  (:attr:`~.preamble`, :attr:`~.comments`, and :attr:`~.suffix`)
  into the output, exactly mirroring the input in most cases.
  (One counterexample is that unnecessary escape sequences won't be preserved).

Bugfixes
~~~~~~~~

:class:`.MSDParameter`'s :meth:`.serialize` and :meth:`.stringify` methods
now escape literal ``#`` characters by default.
This change prevents StepMania from rejecting certain seemingly-valid input,
such as a song title that begins with ``#``.
Passing ``escapes=False`` disables this behavior,
along with all other escaping.

Missing semicolon detection now behaves the same as StepMania.
Specifically, the new line containing a ``#`` may now have leading whitespace,
and all whitespace before the ``#`` is trimmed from the preceding parameter.  
This is implemented in :func:`.lex_msd`
by emitting the whitespace as an :attr:`~.END_PARAMETER` token.
:func:`.parse_msd` includes the whitespace
in the preceding parameter's :attr:`.suffix`.

2.0.0
-----

Breaking changes
~~~~~~~~~~~~~~~~

.. warning::

    **msdparser** 2.0 introduces some breaking changes
    that you may need to update your code to handle:
    
    * The return type of :func:`.parse_msd` has been changed
      from :code:`Tuple[str, str]` to :class:`.MSDParameter`,
      a dataclass with :attr:`~.key` and :attr:`~.value` properties
      that index into a sequence of :attr:`~.components`.
      This means you can no longer iterate over :func:`.parse_msd`'s output
      using :code:`for key, value in parse_msd(...)`.
      Instead, you'll want to write :code:`for param in parse_msd(...)`
      and use the :data:`.key`, and :data:`.value` properties.
    
    This change is motivated by two deviations from the spec
    that have been corrected in this version:

    * Escape sequences are now handled by default.
      While the absence of this feature was technically a bug in version 1,
      fixing it changes how certain MSD documents are parsed.
      Backslash escapes can be disabled by passing :code:`escapes=False` to :func:`.parse_msd`,
      restoring the behavior from version 1
      and preserving spec-compliant parsing of older formats like DWI.
    * Unescaped colons (``:``) after the key are no longer treated as literal text:
      now a colon *always* separates components,
      and the key and value are defined as the first and second components.
      This brings the parser into parity with StepMania
      when unexpected colons appear after a parameter's key.


New features
~~~~~~~~~~~~

* The newly introduced :class:`.MSDParameter` class
  stringifies to valid MSD,
  escaping special characters by default.
  Client code that performs ad-hoc serialization
  is encouraged to adopt this usage pattern
  to avoid generation of invalid MSD.
* A new :mod:`.lexer` module provides the function :func:`.lex_msd`,
  a lexer for MSD data which produces (token, string) tuples.
  This lexer is now used by :func:`.parse_msd` under the hood,
  which also serves as a reference implementation
  for consuming the output of the lexer.
* :func:`.parse_msd` can now take a third input argument, `tokens`,
  to allow the output of :func:`.lex_msd`
  to be processed before parsing.

Enhancements
~~~~~~~~~~~~

* :func:`.parse_msd` has been optimized for most MSD documents,
  particularly those containing large blocks of note data.
  The function is now up to 10 times faster than version 1!
* :class:`.MSDParserError` now provides the last parameter's key
  prior to encountering stray text
  for ease of debugging.

1.0.0
-----

Initial stable release.
