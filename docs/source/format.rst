The MSD format
--------------

MSD is a key-value store, similar in function to INI files. `Here is an example <https://github.com/stepmania/stepmania/blob/5_1-new/Songs/StepMania%205/Springtime/Springtime.ssc>`_ of an SSC file, a file format based on MSD.

In general, MSD key-value pairs look like ``#KEY:VALUE;`` - the ``#`` starts a parameter, the first ``:`` separates the key from the value, and the ``;`` terminates the value. Keys don't have to be unique - for example, each chart in an SM file uses the same ``NOTES`` key.

Comments start with ``//`` and persist until the end of the line. They can appear anywhere, including inside values (or even keys).

Escape sequences
~~~~~~~~~~~~~~~~

Modern applications of MSD have *escape sequences*: any special character (``:``, ``;``, ``\``) or comment initializer (``//``) can be treated as literal text by prefixing it with a ``\``. This behavior is enabled by default.

Older applications treat backslashes as regular text, and thus do not permit a literal ``;`` in keys or values, nor ``:`` in keys. This behavior can be replicated by passing ``escapes=False`` to :func:`.parse_msd` or :meth:`.MSDParameter.serialize`.

Refer to the table below to decide whether escapes should be left enabled or explicitly disabled:

======== ============
Format   Has escapes?
-------- ------------
SM       ✓
SMA      ✓
SSC      ✓
TXT [1]_ ✓
CRS
DWI
KSF
======== ============

.. [1] Refers to the file ``Data/RandomAttacks.txt`` that comes bundled with StepMania.

Edge cases
~~~~~~~~~~

Keys and values can be blank. The ``:`` separator can even be omitted, which has the same result as a blank value.

StepMania recovers from a missing ``;`` if it finds a ``#`` marker at the start of a line, so this parser does too.

Multi-value parameters
~~~~~~~~~~~~~~~~~~~~~~

Some keys (such as the SM format's ``NOTES``) are expected to have multiple ``:``-separated values. For simplicity, this parser always treats ``:`` in a value literally, leaving any multi-value semantics up to client code to implement. (In other words, the value of ``#KEY:A:B;`` deserializes to ``'A:B'``, rather than ``['A', 'B']`` or similar.)
