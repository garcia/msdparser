msdparser
=========

Simple MSD parser for Python. MSD is the underlying file format for a few rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

Parsing
-------

:func:`.parse_msd` takes a named `file` or `string` argument and yields :class:`MSDParameter` instances:

.. doctest::

    >>> from msdparser import parse_msd
    >>> with open('testdata/Springtime.ssc', 'r', encoding='utf-8') as simfile:
    ...     for param in parse_msd(file=simfile):
    ...         if param.key == 'NOTEDATA': break   # stop at the first chart
    ...         if not param.value: continue        # hide empty values
    ...         print(param.key, '=', repr(param.value))
    ...
    VERSION = '0.83'
    TITLE = 'Springtime'
    ARTIST = 'Kommisar'
    BANNER = 'springbn.png'
    BACKGROUND = 'spring.png'
    MUSIC = 'Kommisar - Springtime.mp3'
    OFFSET = '-0.090'
    SAMPLESTART = '105.760'
    SAMPLELENGTH = '15'
    SELECTABLE = 'YES'
    DISPLAYBPM = '182'
    BPMS = '0=181.685'
    TIMESIGNATURES = '0=4=4'
    TICKCOUNTS = '0=2'
    COMBOS = '0=1'
    SPEEDS = '0=1=0=0'
    SCROLLS = '0=1'
    LABELS = '0=Song Start'

Serializing
-----------

:class:`.MSDParameter` instances stringify back to MSD. They can be created from a sequence of strings:

.. code-block:: python

    >>> from msdparser import MSDParameter
    >>> pairs = [('TITLE', 'Springtime'), ('ARTIST', 'Kommisar')]
    >>> for key, value in pairs:
    ...     print(str(MSDParameter([key, value])))
    ...
    #TITLE:Springtime;
    #ARTIST:Kommisar;

Prefer to use :class:`.MSDParameter` over interpolating the key/value pairs between ``#:;`` characters yourself. The ``str()`` implementation inserts escape sequences where required, preventing generation of invalid MSD.

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
