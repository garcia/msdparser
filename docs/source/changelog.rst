Changelog
---------

2.0.0-beta.4
~~~~~~~~~~~~

* **Enhancement:** :attr:`.MSDParameter.key`'s type has been narrowed from ``Optional[str]``
  to ``str``.

2.0.0-beta.3
~~~~~~~~~~~~

* **Feature:** Added :func:`.lex_msd`, a lexer for MSD data which produces (token, string)
  tuples. This lexer is now used by :func:`.parse_msd` under the hood, which also serves as a
  reference implementation for consuming the output of the lexer.
* **Enhancement:** :func:`.parse_msd` is now up to 10 times faster than version 1.0!
* **Enhancement:** :class:`.MSDParserError` now provides the last parameter's key prior to
  encountering stray text for ease of debugging.

2.0.0-beta.2
~~~~~~~~~~~~

This release significantly changes how multi-value parameters are handled. Unescaped colons
(``:``) after the key are no longer treated as literal text: now a colon _always_ separates
components, and the key and value are defined as the first and second components. This
brings **msdparser** into parity with StepMania when unexpected colons appear after a
parameter's key.

**API change:** :class:`.MSDParameter` is no longer a subclass of ``NamedTuple``. Instead,
it's a dataclass with :attr:`~.key` and :attr:`~.value` properties that index into a sequence
of :attr:`~.components`.

2.0.0-beta.1
~~~~~~~~~~~~

**Bugfix/feature:** Escape sequences are now handled by default. While the
absence of this feature was technically a bug in the spec (escapes have been
supported since the SM format!), this is still a breaking change, hence the
major version bump.

Backslash escapes can be disabled by passing :code:`escapes=False` to :func:`.parse_msd`,
restoring the 1.0.0 behavior and preserving spec-compliant parsing of older
formats like DWI.

**Feature:** The return type of :func:`.parse_msd` has been changed from 
:code:`Tuple[str, str]` to :class:`.MSDParameter`, which is a :code:`NamedTuple` of two strings, 
`key` and `value`. Stringifying an :class:`.MSDParameter` interpolates the key/value 
pair into the MSD :code:`#KEY:VALUE;` format, escaping special characters by default.

Existing :func:`.parse_msd` client code that expects :code:`(key, value)` tuples should 
still operate fine, but you can now also access the key/value pair as `key` / 
`value` properties on the yielded objects.

**Enhancement:** :func:`.parse_msd` has been optimized for most MSD documents,
particularly those containing large blocks of note data.

1.0.0
~~~~~

Initial stable release.

1.0.0-beta.1
~~~~~~~~~~~~

* The :code:`MSDParser` class has been converted into the more suitable :func:`.parse_msd` function.
* Semicolons between parameters are now correctly handled as stray text.