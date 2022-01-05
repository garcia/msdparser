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

In version 2.0, the aforementioned tuples are :class:`.MSDParameter` instances, a ``NamedTuple`` subclass:

.. doctest::

    >>> from msdparser import MSDParameter
    >>> param = MSDParameter('TITLE', 'Springtime')
    >>> str(param)
    '#TITLE:Springtime;'

This interface is compatible with plain tuple usage, but also allows access through :code:`.key` and :code:`.value` attributes.

When serializing MSD data, prefer to use this method over interpolating the key/value pairs between ``#:;`` characters yourself. The ``str()`` implementation inserts escape sequences where required, preventing generation of invalid MSD.

.. note::

    If your use case requires no escaping (for example, when serializing DWI data), use the alternate method ``param.serialize(escapes=False)`` instead, which will never escape special characters and will raise :code:`ValueError` if the parameter cannot be serialized without escapes (for example, if a value contains a ``;`` or a ``//``).

API
---

.. automodule:: msdparser
    :members:


Further reading
---------------

.. toctree::
    :maxdepth: 1

    format
    changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
