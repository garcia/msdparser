Changelog
=========

2.1.0
-----

* Stringifying an :class:`.MSDParameter` with escapes enabled
  will now escape any `#` characters inside a component.
  While this is not required by the inferred spec,
  StepMania has difficulties dealing with a `#`
  as the very first character of a component,
  and simply escaping it resolves the issue.

2.0.0
-----

.. warning::

    Per semantic versioning,
    msdparser version 2 includes one **breaking change**
    that will require updated client code:
    
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
