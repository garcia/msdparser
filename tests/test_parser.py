import codecs
from io import StringIO
import unittest
from msdparser.parameter import MSDParameter
from msdparser.parser import MSDParserError, parse_msd


class TestParseMSD(unittest.TestCase):
    def test_file_and_string_args(self):
        data = "#A:B;"
        from_file = parse_msd(file=StringIO(data))
        from_string = parse_msd(string=data)

        self.assertEqual(next(from_file), next(from_string))
        self.assertRaises(StopIteration, next, from_file)
        self.assertRaises(StopIteration, next, from_string)

    def test_real_file_args(self):
        testdata = [
            "tests/testdata/#Fairy_dancing_in_lake.sm",
            "tests/testdata/backup.sm",
            "tests/testdata/backup.ssc",
        ]
        for testfile in testdata:
            with self.subTest(testfile=testfile):
                with codecs.open(testfile, encoding="utf-8") as infile:
                    string_copy = infile.read()
                    infile.seek(0)
                    parameters = list(parse_msd(file=infile))

                joined_parameters = "".join(p.stringify(exact=True) for p in parameters)

                # Literal "#" gets escaped by default
                # TODO: maybe store components unescaped for true exactness?
                if testfile == "tests/testdata/#Fairy_dancing_in_lake.sm":
                    self.assertNotEqual(string_copy, joined_parameters)
                    joined_parameters = joined_parameters.replace(":\\#", ":#")

                self.assertEqual(string_copy, joined_parameters)

    def test_empty(self):
        parse = parse_msd(string="")

        self.assertRaises(StopIteration, next, parse)

    def test_normal_characters(self):
        parse = parse_msd(
            string="#A1,./'\"[]{\\\\}|`~!@#$%^&*()-_=+ \r\n\t:A1,./'\"[]{\\\\}|`~!@#$%^&*()-_=+ \r\n\t:;"
        )
        param = next(parse)

        self.assertEqual(
            (
                "A1,./'\"[]{\\}|`~!@#$%^&*()-_=+ \r\n\t",
                "A1,./'\"[]{\\}|`~!@#$%^&*()-_=+ \r\n\t",
                "",
            ),
            param.components,
        )
        self.assertRaises(StopIteration, next, parse)

    def test_preamble(self):
        parse = parse_msd(string="// Copyright (c) Ash Garcia 2024\n#TITLE:asdf;")

        parameter = next(parse)
        self.assertEqual(("TITLE", "asdf"), parameter.components)
        self.assertEqual("// Copyright (c) Ash Garcia 2024\n", parameter.preamble)

    def test_suffix(self):
        parse = parse_msd(string="// hi\n#A:B;\n#C:D\n#E:F;#G:H;// test\n")

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        self.assertEqual("// hi\n", parameter.preamble)
        self.assertEqual(";\n", parameter.suffix)

        parameter = next(parse)
        self.assertEqual(("C", "D"), parameter.components)
        self.assertIsNone(parameter.preamble)
        self.assertEqual("\n", parameter.suffix)

        parameter = next(parse)
        self.assertEqual(("E", "F"), parameter.components)
        self.assertEqual(";", parameter.suffix)

        parameter = next(parse)
        self.assertEqual(("G", "H"), parameter.components)
        self.assertEqual(";// test\n", parameter.suffix)

        self.assertRaises(StopIteration, next, parse)

    def test_comments(self):
        parse = parse_msd(string="#A// comment //\r\nBC:D// ; \nEF;//#NO:PE;")

        parameter = next(parse)
        self.assertEqual(("A\r\nBC", "D\nEF"), parameter.components)
        self.assertEqual(((0, "// comment //"), (1, "// ; ")), parameter.comments)
        self.assertRaises(StopIteration, next, parse)

    def test_comment_with_no_newline_at_eof(self):
        parse = parse_msd(string="#ABC:DEF// eof")

        parameter = next(parse)
        self.assertEqual(("ABC", "DEF"), parameter.components)
        self.assertEqual(((0, "// eof"),), parameter.comments)
        self.assertEqual("", parameter.suffix)
        self.assertRaises(StopIteration, next, parse)

    def test_empty_key(self):
        parse = parse_msd(string="#:ABC;#:DEF;")

        parameter = next(parse)
        self.assertEqual(("", "ABC"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("", "DEF"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_empty_value(self):
        parse = parse_msd(string="#ABC:;#DEF:;")

        parameter = next(parse)
        self.assertEqual(("ABC", ""), parameter.components)
        parameter = next(parse)
        self.assertEqual(("DEF", ""), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_missing_value(self):
        parse = parse_msd(string="#ABC;#DEF;")

        parameter = next(parse)
        self.assertEqual(("ABC",), parameter.components)
        self.assertEqual("", parameter.value)
        parameter = next(parse)
        self.assertEqual(("DEF",), parameter.components)
        self.assertEqual("", parameter.value)
        self.assertRaises(StopIteration, next, parse)

    def test_missing_semicolon(self):
        parse = parse_msd(string="#A:B\nCD;#E:FGH\n#IJKL // comment\n#M:NOP")

        parameter = next(parse)
        self.assertEqual(("A", "B\nCD"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("E", "FGH"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("IJKL ",), parameter.components)
        parameter = next(parse)
        self.assertEqual(("M", "NOP"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_missing_value_and_semicolon(self):
        parse = parse_msd(string="#A\n#B\n\n#C")

        parameter = next(parse)
        self.assertEqual(("A",), parameter.components)
        self.assertEqual("\n", parameter.suffix)
        parameter = next(parse)
        self.assertEqual(("B",), parameter.components)
        self.assertEqual("\n\n", parameter.suffix)
        parameter = next(parse)
        self.assertEqual(("C",), parameter.components)
        self.assertEqual("", parameter.suffix)
        self.assertRaises(StopIteration, next, parse)

    def test_unicode(self):
        parse = parse_msd(string="#TITLE:実例;\n#ARTIST:楽士;")

        parameter = next(parse)
        self.assertEqual(("TITLE", "実例"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("ARTIST", "楽士"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_stray_text_with_strict_parsing(self):
        parse = parse_msd(string="#A:B;#C:D;n#E:F;", strict=True)

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("C", "D"), parameter.components)
        self.assertRaisesRegex(
            MSDParserError,
            "stray 'n' encountered after 'C' parameter",
            next,
            parse,
        )

    def test_stray_escape_with_strict_parsing(self):
        parse = parse_msd(string="#A:B;#C:D;\\##E:F;", strict=True)

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("C", "D"), parameter.components)
        self.assertRaisesRegex(
            MSDParserError,
            r"stray '\\\\' encountered after 'C' parameter",
            next,
            parse,
        )

    def test_stray_text_at_start_with_strict_parsing(self):
        parse = parse_msd(string="TITLE:oops;", strict=True)

        self.assertRaisesRegex(
            MSDParserError,
            "stray 'T' encountered at start of document",
            next,
            parse,
        )

    def test_stray_semicolon_with_strict_parsing(self):
        parse = parse_msd(string="#A:B;#C:D;;#E:F;", strict=True)

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("C", "D"), parameter.components)
        self.assertRaisesRegex(
            MSDParserError,
            "stray ';' encountered after 'C' parameter",
            next,
            parse,
        )

    def test_stray_text_without_strict_parsing(self):
        parse = parse_msd(string="#A:B;n#C:D;")

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        self.assertEqual(";n", parameter.suffix)
        parameter = next(parse)
        self.assertEqual(("C", "D"), parameter.components)
        self.assertEqual(";", parameter.suffix)
        self.assertRaises(StopIteration, next, parse)

    def test_escapes(self):
        parse = parse_msd(string="#A\\:B:C\\;D;#EF\\#:G\\\\H;#LF:\\\nLF;")

        parameter = next(parse)
        self.assertEqual(("A:B", "C;D"), parameter.components)
        self.assertEqual((2, 7), parameter.escape_positions)
        parameter = next(parse)
        self.assertEqual(("EF#", "G\\H"), parameter.components)
        self.assertEqual((3, 7), parameter.escape_positions)
        parameter = next(parse)
        self.assertEqual(("LF", "\nLF"), parameter.components)
        self.assertEqual((4,), parameter.escape_positions)
        self.assertRaises(StopIteration, next, parse)

    def test_no_escapes(self):
        parse = parse_msd(
            string="#A\\:B:C\\;D;#E\\#F:G\\\\H;#LF:\\\nLF;",
            escapes=False,
        )

        parameter = next(parse)
        self.assertEqual(("A\\", "B", "C\\"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("E\\#F", "G\\\\H"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("LF", "\\\nLF"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_preamble_and_comment_and_escapes(self):
        parse = parse_msd(
            string="// Copyright 2024\n\n#key:value\\: // comment //\nline two\\;\nline\\//3\n;\n",
            escapes=True,
        )

        parameter = next(parse)
        self.assertEqual(("key", "value: \nline two;\nline//3\n"), parameter.components)
        self.assertEqual("// Copyright 2024\n\n", parameter.preamble)
        self.assertEqual(((0, "// comment //"),), parameter.comments)
        self.assertEqual((10, 35, 42), parameter.escape_positions)
        self.assertEqual(";\n", parameter.suffix)

        self.assertRaises(StopIteration, next, parse)

    def test_preamble_and_comment_and_escapes_disabled(self):
        parse = parse_msd(
            string="// Copyright 2024\n\n#key:value\\: // comment //\nline two\\;\nline\\//3\n;\n",
            escapes=False,
        )

        parameter = next(parse)
        self.assertEqual(("key", "value\\", " \nline two\\"), parameter.components)
        self.assertEqual("// Copyright 2024\n\n", parameter.preamble)
        self.assertEqual(((0, "// comment //"),), parameter.comments)
        self.assertIsNone(parameter.escape_positions)
        self.assertEqual(";\nline\\//3\n;\n", parameter.suffix)

        self.assertRaises(StopIteration, next, parse)
