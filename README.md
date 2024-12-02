# msdparser

A comprehensive, pure-Python, speed-optimized MSD parser.
MSD is the underlying file format
for the SM and SSC simfile formats used by StepMania,
as well as a few older formats like DWI.

Full documentation can be found on **[Read the Docs](https://msdparser.readthedocs.io/en/latest/)**.

## Features

- MSD lexer and parser
- Optional escape sequences (on by default)
- Optional strict parsing (off by default)
- Bidirectionally-lossless parsing & serialization (in most cases)

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

Parameters can be stringified exactly how they were parsed
by calling `serialize` or `stringify` with `exact=True`:

```python
>>> import codecs
>>> import filecmp
>>> from msdparser import MSDParameter, parse_msd
>>> with codecs.open("tests/testdata/backup.ssc", encoding="utf-8") as infile:
...     params = list(parse_msd(file=infile))
...
>>> with codecs.open("output.ssc", "w", encoding="utf-8") as outfile:
...     for param in params:
...         param.serialize(outfile, exact=True)
...
>>> filecmp.compare("tests/testdata/backup.ssc", "output.ssc")
True
```

## Developing

**msdparser** uses [uv](https://docs.astral.sh/uv/) for package management.
Install it using `pipx install uv` or `pip install uv`,
or see the [installation docs](https://docs.astral.sh/uv/getting-started/installation/) for more options.

Create the virtual environment for **msdparser**:

```sh
uv sync
```

Activate the virtual environment:

```sh
# Windows
.venv\Scripts\activate
# Linux / Mac
source .venv/bin/activate
```

Run the unit tests:

```sh
uv run -m unittest
# Or, if you've activated your virtual environment:
python -m unittest
```

Build the documentation:

```sh
docs/make html
```
