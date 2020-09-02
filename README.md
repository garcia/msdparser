# msdparser

Simple MSD parser for Python. MSD is the underlying file format for many rhythm games, most notably both StepMania simfile formats (.sm and .ssc).

## Installing

    pip install msdparser

## Usage

`MSDParser` takes a named `file` or `string` from its constructor. It supports context management and iteration. Parameters are yielded as (key, value) pairs of strings.

    from msdparser import MSDParser

    with open('simfile.sm', 'r', encoding='utf-8') as simfile:
        with MSDParser(file=simfile) as parser:
            for (key, value) in parser:
                if key == 'NOTES':
                    break
                print(key, '=', repr(value))

## The MSD format

In general, MSD key-value pairs look like `#KEY:VALUE;` - the `#` starts a parameter, the first `:` separates the key from the value, and the `;` terminates the value. Keys are not expected to be unique. There are no escape sequences.

Comments start with `//` and persist until the end of the line.

Keys can contain any text except for `:`, `//`, and a newline followed by a `#` (see below). Values are the same, except `:` is allowed.

Keys and values can be blank. The `:` separator can even be omitted, which has the same result as a blank value.

StepMania recovers from a missing `;` if it finds a `#` marker at the start of a line, so `MSDParser` does too.