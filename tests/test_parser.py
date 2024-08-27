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
        parse = parse_msd(string="// hi\n#A:B;\n#C:D\n#E:F;// test\n")
        
        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        self.assertEqual("// hi\n", parameter.preamble)
        self.assertEqual("\n", parameter.suffix)
        
        parameter = next(parse)
        self.assertEqual(("C", "D\n"), parameter.components)
        self.assertIsNone(parameter.preamble)
        self.assertEqual("", parameter.suffix)

        parameter = next(parse)
        self.assertEqual(("E", "F"), parameter.components)
        self.assertIsNone(parameter.preamble)
        self.assertEqual("// test\n", parameter.suffix)

        self.assertRaises(StopIteration, next, parse)

    def test_comments(self):
        parse = parse_msd(string="#A// comment //\r\nBC:D// ; \nEF;//#NO:PE;")

        parameter = next(parse)
        self.assertEqual(("A\r\nBC", "D\nEF"), parameter.components)
        self.assertEqual({0: "// comment //", 1: "// ; "}, parameter.comments)
        self.assertRaises(StopIteration, next, parse)

    def test_comment_with_no_newline_at_eof(self):
        parse = parse_msd(string="#ABC:DEF// eof")

        parameter = next(parse)
        self.assertEqual(("ABC", "DEF"), parameter.components)
        self.assertEqual({0: "// eof"}, parameter.comments)
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
        self.assertIsNone(parameter.value)
        parameter = next(parse)
        self.assertEqual(("DEF",), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_missing_semicolon(self):
        parse = parse_msd(string="#A:B\nCD;#E:FGH\n#IJKL// comment\n#M:NOP")

        parameter = next(parse)
        self.assertEqual(("A", "B\nCD"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("E", "FGH\n"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("IJKL\n",), parameter.components)
        parameter = next(parse)
        self.assertEqual(("M", "NOP"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_missing_value_and_semicolon(self):
        parse = parse_msd(string="#A\n#B\n#C\n")

        parameter = next(parse)
        self.assertEqual(("A\n",), parameter.components)
        parameter = next(parse)
        self.assertEqual(("B\n",), parameter.components)
        parameter = next(parse)
        self.assertEqual(("C\n",), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_unicode(self):
        parse = parse_msd(string="#TITLE:実例;\n#ARTIST:楽士;")

        parameter = next(parse)
        self.assertEqual(("TITLE", "実例"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("ARTIST", "楽士"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_stray_text(self):
        parse = parse_msd(string="#A:B;#C:D;n#E:F;")

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        self.assertRaisesRegex(
            MSDParserError,
            "stray 'n' encountered after 'C' parameter",
            next,
            parse,
        )

    def test_stray_text_at_start(self):
        parse = parse_msd(string="TITLE:oops;")

        self.assertRaisesRegex(
            MSDParserError,
            "stray 'T' encountered at start of document",
            next,
            parse,
        )

    def test_stray_semicolon(self):
        parse = parse_msd(string="#A:B;#C:D;;#E:F;")

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        self.assertRaisesRegex(
            MSDParserError,
            "stray ';' encountered after 'C' parameter",
            next,
            parse,
        )

    def test_stray_text_with_ignore_stray_text(self):
        parse = parse_msd(string="#A:B;n#C:D;", ignore_stray_text=True)

        parameter = next(parse)
        self.assertEqual(("A", "B"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("C", "D"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_escapes(self):
        parse = parse_msd(string="#A\\:B:C\\;D;#E\\#F:G\\\\H;#LF:\\\nLF;")

        parameter = next(parse)
        self.assertEqual(("A:B", "C;D"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("E#F", "G\\H"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("LF", "\nLF"), parameter.components)
        self.assertRaises(StopIteration, next, parse)

    def test_no_escapes(self):
        parse = parse_msd(
            string="#A\\:B:C\\;D;#E\\#F:G\\\\H;#LF:\\\nLF;",
            escapes=False,
            ignore_stray_text=True,
        )

        parameter = next(parse)
        self.assertEqual(("A\\", "B", "C\\"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("E\\#F", "G\\\\H"), parameter.components)
        parameter = next(parse)
        self.assertEqual(("LF", "\\\nLF"), parameter.components)
        self.assertRaises(StopIteration, next, parse)
