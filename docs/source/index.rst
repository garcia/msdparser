msdparser
=========

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

Parsing
-------

:func:`.parse_msd` takes a named `file` or `string` argument and yields parameters as (key, value) tuples:

.. doctest::

    >>> from msdparser import parse_msd
    >>> with open('simfile.sm', 'r', encoding='utf-8') as simfile:
    ...     for (key, value) in parse_msd(file=simfile):
    ...         if key == 'NOTES':
    ...             break
    ...         print(key, '=', repr(value))

Serializing (v2.0+)
-------------------

In version 2.0, the aforementioned tuples are :class:`MSDParameter` instances, a :code:`NamedTuple` subclass:

.. doctest::

    >>> from msdparser import MSDParameter
    >>> param = MSDParameter('TITLE', 'Springtime')
    >>> str(param)
    '#TITLE:Springtime;'

This interface is compatible with plain tuple usage, but also allows access through :code:`.key` and :code:`.value` attributes.

When serializing MSD data, prefer to use this method over interpolating the key/value pairs between :code:`#:;` characters yourself. The :code:`str()` implementation inserts escape sequences where required, preventing generation of invalid MSD.

.. note::

    If your use case requires no escaping (for example, when serializing DWI data), use the alternate method `param.serialize(escapes=False)` instead, which will never escape special characters and will raise :code:`ValueError` if the parameter cannot be serialized without escapes (for example, if a value contains a `;` or a `//`).

The MSD format
--------------

In general, MSD key-value pairs look like :code:`#KEY:VALUE;` - the :code:`#` starts a parameter, the first :code:`:` separates the key from the value, and the :code:`;` terminates the value. Keys are not expected to be unique. There are no escape sequences.

Comments start with :code:`//` and persist until the end of the line.

Keys can contain any text except for :code:`:`, :code:`//`, and a newline followed by a :code:`#` (see below). Values are the same, except :code:`:` is allowed.

Keys and values can be blank. The :code:`:` separator can even be omitted, which has the same result as a blank value.

StepMania recovers from a missing :code:`;` if it finds a :code:`#` marker at the start of a line, so this parser does too.

API
---

.. automodule:: msdparser
    :members:


Further reading
---------------

.. toctree::
    :maxdepth: 1

    changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
