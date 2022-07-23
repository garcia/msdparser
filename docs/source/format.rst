The MSD format
--------------

An MSD document is a sequence of **parameters**, each of which has at least one **component**. These are defined as follows:

* ``#`` starts a new parameter.

  * Inside of a parameter,
    ``#`` is treated as literal text,
    unless it occurs at the start of a line.

* ``:`` inside a parameter separates components.
* ``;`` ends a parameter.
* ``//`` starts a line-based comment.
* ``\`` inside a parameter escapes the following character,
  forcing it to be treated as literal text.

  * This feature is an extension to the original format;
    see the "Escape sequences" section below for details.

Parameters are typically comprised of two components,
a **key** and a **value**,
but the exact semantics are up to the application.
Keys don't have to be unique.
Parameters can contain additional components past the first value,
although this feature is seldom used;
see the "Multi-value parameters" section below for details.

MSD documents **should** have no text between parameters
other than whitespace (spaces, newlines, tabs) and comments.
By default, :func:`.parse_msd` throws an exception
if it encounters stray text between parameters,
but this can be changed using the `ignore_stray_text` argument.

Escape sequences
~~~~~~~~~~~~~~~~

Modern applications of MSD have *escape sequences*:
any special token can be treated as literal text
by prefixing it with a ``\``.
:func:`.parse_msd` unescapes any escaped characters by default,
and :class:`.MSDParameter`'s components are always stored unescaped.

Older applications treat backslashes as regular text,
and consequently do not support literal ``:``, ``;``, or ``//`` tokens.
This behavior can be replicated
by setting `escapes` to ``False`` in
:func:`.parse_msd`,
:func:`.lex_msd`, or
:meth:`.MSDParameter.serialize`.

Refer to the table below to decide
whether escapes should be left enabled
or explicitly disabled:

======== ============
Format   Has escapes?
-------- ------------
SM       ✓ [1]_
SMA      ✓
SSC      ✓
TXT [2]_ ✓
CRS
DWI
KSF
======== ============

.. [1] Only in StepMania versions 4 and 5 (and their forks).
   Older versions like 3.9 and forks like OpenITG / NotITG
   do not support escapes.
.. [2] Refers to the file ``Data/RandomAttacks.txt``
   that comes bundled with StepMania.

Multi-value parameters
~~~~~~~~~~~~~~~~~~~~~~

MSD parameters can have multiple values separated by colons,
like ``#KEY:VALUE1:VALUE2:...;``.
While this feature is seldom used,
it's an important detail for understanding
how StepMania treats unescaped colons in a value.
For example, specifying a song title as ``#TITLE:rE:Voltagers;``
will cause StepMania to display the title as ``rE``,
discarding everything after the unescaped colon.
In other words, StepMania is generally only concerned
with the *first value* in a given property.

For simplicity, :attr:`.MSDParameter.value`
always corresponds to the first value.
If there are multiple values,
they can be found in the array :attr:`MSDParameter.components`
after the first two elements
(the key and the first value).

These are the properties
where StepMania expects to find multi-value parameters:

========== ====== ======
Property   SM     SSC
---------- ------ ------
DISPLAYBPM ✓      ✓
ATTACKS    ✓      ✓
NOTES      ✓
========== ====== ======

.. note::

    The `simfile <https://simfile.readthedocs.io/en/latest/>`_ library
    handles these specific properties
    by joining the value components together
    with ``:`` separators.
    All other properties discard any values past the first.


Edge cases
~~~~~~~~~~

Keys and values can be blank.
A parameter can even lack any ``:`` separator,
which deserializes to an :class:`.MSDParameter`
with a value of ``None``.

StepMania recovers from a missing ``;``
if it finds a ``#`` marker
at the start of a line,
so this library does too.
