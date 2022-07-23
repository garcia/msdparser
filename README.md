# msdparser

A robust & lightning fast MSD parser for Python.
MSD is the underlying file format
for the SM and SSC simfile formats used by StepMania,
as well as a few older formats like DWI.

Full documentation can be found on **[Read the Docs](https://msdparser.readthedocs.io/en/latest/)**.

## Features

- Speed-optimized lexer & low-overhead parser
- Support for escape sequences by default
- Strict & lenient parse modes

## Installation

`msdparser` is available on PyPI:

```sh
pip install msdparser
```

## Quickstart

`parse_msd` takes a **named** _file_ or _string_ argument and yields `MSDParameter` instances:

```python
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
```

`MSDParameter` instances stringify back to MSD.
They can be created from a sequence of strings,
typically the key and value:

```python
>>> from msdparser import MSDParameter
>>> pairs = [('TITLE', 'Springtime'), ('ARTIST', 'Kommisar')]
>>> for key, value in pairs:
...     print(str(MSDParameter([key, value])))
...
#TITLE:Springtime;
#ARTIST:Kommisar;
```

Prefer to use `MSDParameter`
over interpolating the key/value pairs
between `#:;` characters yourself.
The `str()` implementation inserts escape sequences where required,
preventing generation of invalid MSD.

## Developing

**msdparser** uses Pipenv for dependency management. Activate the environment:

    pipenv shell

To run the unit tests:

    py -m unittest

To build the documentation:

    docs/make html
