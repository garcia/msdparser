# msdparser

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

## Installing

`msdparser` is available on PyPI. During the current beta phase, make sure to pass `--pre` to `pip`:

    pip install --pre msdparser

## Usage

`parse_msd` takes a named `file` or `string` argument and yields parameters as (key, value) pairs of strings:

    from msdparser import parse_msd

    with open('simfile.sm', 'r', encoding='utf-8') as simfile:
        for (key, value) in parse_msd(file=simfile):
            if key == 'NOTES':
                break
            print(key, '=', repr(value))

## Documentation

https://msdparser.readthedocs.io/en/latest/

## The MSD format

In general, MSD key-value pairs look like `#KEY:VALUE;` - the `#` starts a parameter, the first `:` separates the key from the value, and the `;` terminates the value. Keys are not expected to be unique.

Most applications of MSD (such as the SM and SSC formats) have escape sequences: any character can be treated as regular text by prefixing it with a `\`. Older applications like DWI treat backslashes as regular text.

Comments start with `//` and persist until the end of the line.

Keys can contain any text except for `:`, `//`, and a newline followed by a `#` (see below). Values are the same, except `:` is allowed.

Keys and values can be blank. The `:` separator can even be omitted, which has the same result as a blank value.

StepMania recovers from a missing `;` if it finds a `#` marker at the start of a line, so this parser does too.