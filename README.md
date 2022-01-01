# msdparser

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

## Installing

`msdparser` is available on PyPI. During the current beta phase, make sure to pass `--pre` to `pip`:

    pip install --pre msdparser

## Parsing

`parse_msd` takes a named `file` or `string` argument and yields parameters as named (key, value) tuples:

```python
>>> from msdparser import parse_msd
>>> with open('simfile.sm', 'r', encoding='utf-8') as simfile:
>>>     for (key, value) in parse_msd(file=simfile):
>>>         if key == 'NOTES':
>>>             break
>>>         print(key, '=', repr(value))
```

## Serializing (v1.1+)

The aforementioned tuples are actually instances of `MSDParameter`, a `NamedTuple` subclass that stringifies to valid MSD:

```python
>>> from msdparser import MSDParameter
>>> param = MSDParameter('TITLE', 'Springtime')
>>> str(param)
'#TITLE:Springtime;'
```

These strings (along with any desired whitespace or comments) can be written to a file to produce a valid MSD document.

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
