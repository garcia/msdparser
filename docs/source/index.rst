msdparser
=========

A robust & lightning fast MSD parser for Python.
MSD is the underlying file format
for the SM and SSC simfile formats used by StepMania,
as well as a few older formats like DWI.


Quickstart
----------

:func:`.parse_msd` takes a **named** `file` or `string` argument
and yields :class:`.MSDParameter` instances:

.. doctest::

    >>> msd_data = """
    ... #VERSION:0.83;
    ... #TITLE:Springtime;
    ... #SUBTITLE:;
    ... #ARTIST:Kommisar;
    ... """
    >>> from msdparser import parse_msd
    >>> for param in parse_msd(string=msd_data):
    ...         print(
    ...             "key=" + repr(param.key),
    ...             "value=" + repr(param.value),
    ...         )
    ...
    key='VERSION' value='0.83'
    key='TITLE' value='Springtime'
    key='SUBTITLE' value=''
    key='ARTIST' value='Kommisar'

:class:`.MSDParameter` instances stringify back to MSD.
They can be created from a sequence of strings,
typically the key and value:

.. code-block:: python

    >>> from msdparser import MSDParameter
    >>> pairs = [('TITLE', 'Springtime'), ('ARTIST', 'Kommisar')]
    >>> for key, value in pairs:
    ...     print(str(MSDParameter([key, value])))
    ...
    #TITLE:Springtime;
    #ARTIST:Kommisar;

Prefer to use :class:`.MSDParameter`
over interpolating the key/value pairs between ``#:;`` characters yourself.
The ``str()`` implementation inserts escape sequences where required,
preventing generation of invalid MSD.


Further reading
---------------

.. toctree::
    :maxdepth: 1

    format
    lexer
    changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
