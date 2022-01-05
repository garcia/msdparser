msdparser
=========

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

Parsing
-------

:func:`.parse_msd` takes a named `file` or `string` argument and yields parameters that can be unpacked as (key, value) tuples:

.. doctest::

    >>> from msdparser import parse_msd
    >>> with open('testdata/Springtime.ssc', 'r', encoding='utf-8') as simfile:
    ...     for (key, value) in parse_msd(file=simfile):
    ...         if key == 'NOTEDATA': break     # stop at the first chart
    ...         if not value: continue          # hide empty values
    ...         print(key, '=', repr(value))
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

Serializing (v2.0+)
-------------------

To serialize key/value pairs back into MSD, construct an :class:`.MSDParameter` for each pair and stringify it:

.. code-block:: python

    >>> from msdparser import MSDParameter
    >>> pairs = [('TITLE', 'Springtime'), ('ARTIST', 'Kommisar')]
    >>> for key, value in pairs:
    ...     print(str(MSDParameter(key=key, value=value)))
    ...
    #TITLE:Springtime;
    #ARTIST:Kommisar;

:func:`parse_msd` yields :class:`.MSDParameter` instances, so you could read & write MSD in a single loop:

.. code-block:: python

    >>> from msdparser import parse_msd, MSDParameter
    >>> with open('testdata/Springtime.ssc', 'r') as simfile, open('output.ssc', 'w') as output:
    ...     for param in parse_msd(file=simfile):
    ...         if param.key == 'SUBTITLE':
    ...             param = param._replace(value=param.value + ' (edited)')
    ...         output.write(str(param))
    ...         output.write('\n')

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
