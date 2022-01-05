# msdparser

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

## Installing

`msdparser` is available on PyPI. During the current 2.0 beta phase, make sure to pass `--pre` to `pip`:

```sh
pip install --pre msdparser
```

## Parsing

`parse_msd` takes a named `file` or `string` argument and yields parameters as named (key, value) tuples:

```python
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
```

## Serializing (v2.0+)

To serialize key/value pairs back into MSD, construct an `MSDParameter` for each pair and stringify it:

```python
>>> from msdparser import MSDParameter
>>> pairs = [('TITLE', 'Springtime'), ('ARTIST', 'Kommisar')]
>>> for key, value in pairs:
...     print(str(MSDParameter(key=key, value=value)))
...
#TITLE:Springtime;
#ARTIST:Kommisar;
```

`parse_msd` yields `MSDParameter` instances, so you could read & write MSD in a single loop:

```python
>>> from msdparser import parse_msd, MSDParameter
>>> with open('testdata/Springtime.ssc', 'r') as simfile, open('output.ssc', 'w') as output:
...     for param in parse_msd(file=simfile):
...         if param.key == 'SUBTITLE':
...             param = param._replace(value=param.value + ' (edited)')
...         output.write(str(param))
...         output.write('\n')
```

Prefer to use `MSDParameter` over interpolating the key/value pairs between `#:;` characters yourself. The `str()` implementation inserts escape sequences where required, preventing generation of invalid MSD.

## Documentation

https://msdparser.readthedocs.io/en/latest/

## The MSD format

In general, MSD key-value pairs look like `#KEY:VALUE;` - the `#` starts a parameter, the first `:` separates the key from the value, and the `;` terminates the value. Keys are not expected to be unique.

Comments start with `//` and persist until the end of the line. They can appear anywhere, including inside values (or even keys).

Keys and values can be blank. The `:` separator can even be omitted, which has the same result as a blank value.

StepMania recovers from a missing `;` if it finds a `#` marker at the start of a line, so this parser does too.

### Escape sequences

Modern applications of MSD (such as the SM and SSC formats) have escape sequences: any special character (`:`, `;`, `\`) or comment initializer (`//`) can be treated as literal text by prefixing it with a `\`. This behavior is enabled by default.

Older applications like DWI treat backslashes as regular text, and thus do not permit a literal `;` in keys or values, nor `:` in keys. This behavior can be replicated by passing `escapes=False` to `parse_msd` or `MSDParameter.serialize`.

### Multi-value parameters

Some keys (such as the SM format's `STEPS`) are expected to have multiple `:`-separated values. For simplicity, this parser always treats `:` in a value literally, leaving any multi-value semantics up to client code to implement. (In other words, `#KEY:A:B;` deserializes to `('KEY', 'A:B')`, rather than `('KEY', ['A', 'B'])` or similar.)
