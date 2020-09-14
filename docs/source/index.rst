msdparser
=========

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

Usage
-----

`MSDParser` takes a named `file` or `string` argument. It supports context management and iteration. Parameters are yielded as (key, value) pairs of strings::

    from msdparser import MSDParser

    with open('simfile.sm', 'r', encoding='utf-8') as simfile:
        with MSDParser(file=simfile) as parser:
            for (key, value) in parser:
                if key == 'NOTES':
                    break
                print(key, '=', repr(value))

API
---

.. automodule:: msdparser.msdparser
    :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
