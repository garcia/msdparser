msdparser
=========

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

Usage
-----

:func:`.parse_msd` takes a named `file` or `string` argument and yields parameters as (key, value) pairs of strings:

.. doctest::

    >>> from msdparser import parse_msd
    >>> with open('simfile.sm', 'r', encoding='utf-8') as simfile:
    ...     for (key, value) in parse_msd(file=simfile):
    ...         if key == 'NOTES':
    ...             break
    ...         print(key, '=', repr(value))

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

Changelog
---------

2.0.0-beta.1
~~~~~~~~~~~~

* The :code:`MSDParser` class has been converted into the more suitable :func:`.parse_msd` function.
* Semicolons between parameters are now correctly handled as stray text.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
