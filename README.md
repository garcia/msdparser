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
>>> with open('simfile.sm', 'r', encoding='utf-8') as simfile:
...     for (key, value) in parse_msd(file=simfile):
...         if key == 'NOTES':
...             break
...         print(key, '=', repr(value))
```

## Serializing (v2.0+)

In version 2.0, the aforementioned tuples are instances of `MSDParameter`, a `NamedTuple` subclass that stringifies to valid MSD:

```python
>>> from msdparser import MSDParameter
>>> param = MSDParameter('TITLE', 'Springtime')
>>> str(param)
'#TITLE:Springtime;'
```

This interface is compatible with plain tuple usage, but also allows access through :code:`.key` and :code:`.value` attributes.

When serializing MSD data, prefer to use this method over interpolating the key/value pairs between `#:;` characters yourself. The `str()` implementation inserts escape sequences where required, preventing generation of invalid MSD.

> If your use case requires no escaping (for example, when serializing DWI data), use the alternate method `param.serialize(escapes=False)` instead, which will never escape special characters and will raise :code:`ValueError` if the parameter cannot be serialized without escapes (for example, if a value contains a `;` or a `//`).

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
