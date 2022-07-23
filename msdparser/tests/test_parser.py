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

    def test_comments(self):
        parse = parse_msd(string="#A// comment //\r\nBC:D// ; \nEF;//#NO:PE;")

        self.assertEqual(MSDParameter(("A\r\nBC", "D\nEF")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_comment_with_no_newline_at_eof(self):
        parse = parse_msd(string="#ABC:DEF// eof")

        self.assertEqual(MSDParameter(("ABC", "DEF")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_empty_key(self):
        parse = parse_msd(string="#:ABC;#:DEF;")

        self.assertEqual(MSDParameter(("", "ABC")), next(parse))
        self.assertEqual(MSDParameter(("", "DEF")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_empty_value(self):
        parse = parse_msd(string="#ABC:;#DEF:;")

        self.assertEqual(MSDParameter(("ABC", "")), next(parse))
        self.assertEqual(MSDParameter(("DEF", "")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_missing_value(self):
        parse = parse_msd(string="#ABC;#DEF;")

        param = next(parse)
        self.assertEqual(MSDParameter(("ABC",)), param)
        self.assertIsNone(param.value)
        self.assertEqual(MSDParameter(("DEF",)), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_missing_semicolon(self):
        parse = parse_msd(string="#A:B\nCD;#E:FGH\n#IJKL// comment\n#M:NOP")

        self.assertEqual(MSDParameter(("A", "B\nCD")), next(parse))
        self.assertEqual(MSDParameter(("E", "FGH\n")), next(parse))
        self.assertEqual(MSDParameter(("IJKL\n",)), next(parse))
        self.assertEqual(MSDParameter(("M", "NOP")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_missing_value_and_semicolon(self):
        parse = parse_msd(string="#A\n#B\n#C\n")

        self.assertEqual(MSDParameter(("A\n",)), next(parse))
        self.assertEqual(MSDParameter(("B\n",)), next(parse))
        self.assertEqual(MSDParameter(("C\n",)), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_unicode(self):
        parse = parse_msd(string="#TITLE:実例;\n#ARTIST:楽士;")

        self.assertEqual(MSDParameter(("TITLE", "実例")), next(parse))
        self.assertEqual(MSDParameter(("ARTIST", "楽士")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_stray_text(self):
        parse = parse_msd(string="#A:B;n#C:D;")

        self.assertEqual(MSDParameter(("A", "B")), next(parse))
        self.assertRaisesRegex(
            MSDParserError,
            "stray 'n' encountered after 'A' parameter",
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
        parse = parse_msd(string="#A:B;;#C:D;")

        self.assertEqual(MSDParameter(("A", "B")), next(parse))
        self.assertRaisesRegex(
            MSDParserError,
            "stray ';' encountered after 'A' parameter",
            next,
            parse,
        )

    def test_stray_text_with_ignore_stray_text(self):
        parse = parse_msd(string="#A:B;n#C:D;", ignore_stray_text=True)

        self.assertEqual(MSDParameter(("A", "B")), next(parse))
        self.assertEqual(MSDParameter(("C", "D")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_escapes(self):
        parse = parse_msd(string="#A\\:B:C\\;D;#E\\#F:G\\\\H;#LF:\\\nLF;")

        self.assertEqual(MSDParameter(("A:B", "C;D")), next(parse))
        self.assertEqual(MSDParameter(("E#F", "G\\H")), next(parse))
        self.assertEqual(MSDParameter(("LF", "\nLF")), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_no_escapes(self):
        parse = parse_msd(
            string="#A\\:B:C\\;D;#E\\#F:G\\\\H;#LF:\\\nLF;",
            escapes=False,
            ignore_stray_text=True,
        )

        self.assertEqual(MSDParameter(("A\\", "B", "C\\")), next(parse))
        self.assertEqual(MSDParameter(("E\\#F", "G\\\\H")), next(parse))
        self.assertEqual(MSDParameter(("LF", "\\\nLF")), next(parse))
        self.assertRaises(StopIteration, next, parse)
