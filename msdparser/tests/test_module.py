from typing import Iterator, Tuple
import unittest
from io import StringIO

from msdparser import MSDParameter, MSDParserError, MSDToken, parse_msd, lex_msd


class TestMSDParameter(unittest.TestCase):
    def test_constructor(self):
        param = MSDParameter(('key', 'value'))
        
        self.assertEqual('key', param.key)
        self.assertEqual('value', param.value)
        self.assertIs(param.components[0], param.key)
        self.assertIs(param.components[1], param.value)
    
    def test_str_with_escapes(self):
        param = MSDParameter(('key', 'value'))
        evil_param = MSDParameter(('ABC:DEF;GHI//JKL\\MNO', 'abc:def;ghi//jkl\\mno'))

        self.assertEqual('#key:value;', str(param))
        self.assertEqual('#ABC\\:DEF\\;GHI\\//JKL\\\\MNO:abc\\:def\\;ghi\\//jkl\\\\mno;', str(evil_param))
    
    def test_str_without_escapes(self):
        param = MSDParameter(('key', 'value'))
        multi_value_param = MSDParameter(('key', 'abc', 'def'))
        param_with_literal_backslashes = MSDParameter(('ABC\\DEF', 'abc\\def'))
        invalid_params = (
            # `:` separator in key
            MSDParameter(('ABC:DEF', 'abcdef')),
            # `;` terminator in key or value
            MSDParameter(('ABC;DEF', 'abcdef')),
            MSDParameter(('ABCDEF', 'abc;def')),
            # `//` comment initializer in key or value
            MSDParameter(('ABC//DEF', 'abcdef')),
            MSDParameter(('ABCDEF', 'abc//def')),
        )

        self.assertEqual('#key:value;', param.__str__(escapes=False))
        self.assertEqual('#key:abc:def;', multi_value_param.__str__(escapes=False))
        self.assertEqual('#ABC\\DEF:abc\\def;', param_with_literal_backslashes.__str__(escapes=False))

        for invalid_param in invalid_params:
            self.assertRaises(ValueError, invalid_param.__str__, escapes=False)


class TestParseMSD(unittest.TestCase):
    
    def test_constructor(self):
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
        parse = parse_msd(string='#A1,./\'"[]{\\\\}|`~!@#$%^&*()-_=+ \r\n\t:A1,./\'"[]{\\\\}|`~!@#$%^&*()-_=+ \r\n\t:;')
        param = next(parse)

        self.assertEqual(
            (
                'A1,./\'"[]{\\}|`~!@#$%^&*()-_=+ \r\n\t',
                'A1,./\'"[]{\\}|`~!@#$%^&*()-_=+ \r\n\t',
                '',
            ),
            param.components
        )
        self.assertRaises(StopIteration, next, parse)
    
    def test_comments(self):
        parse = parse_msd(string='#A// comment //\r\nBC:D// ; \nEF;//#NO:PE;')
        
        self.assertEqual(MSDParameter(('A\r\nBC', 'D\nEF')), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_comment_with_no_newline_at_eof(self):
        parse = parse_msd(string='#ABC:DEF// eof')

        self.assertEqual(MSDParameter(('ABC', 'DEF')), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_empty_key(self):
        parse = parse_msd(string='#:ABC;#:DEF;')

        self.assertEqual(MSDParameter(('', 'ABC')), next(parse))
        self.assertEqual(MSDParameter(('', 'DEF')), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_empty_value(self):
        parse = parse_msd(string='#ABC:;#DEF:;')

        self.assertEqual(MSDParameter(('ABC', '')), next(parse))
        self.assertEqual(MSDParameter(('DEF', '')), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_missing_value(self):
        parse = parse_msd(string='#ABC;#DEF;')

        param = next(parse)
        self.assertEqual(MSDParameter(('ABC',)), param)
        self.assertIsNone(param.value)
        self.assertEqual(MSDParameter(('DEF',)), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_missing_semicolon(self):
        parse = parse_msd(string='#A:B\nCD;#E:FGH\n#IJKL// comment\n#M:NOP')
        
        self.assertEqual(MSDParameter(('A', 'B\nCD')), next(parse))
        self.assertEqual(MSDParameter(('E', 'FGH\n')), next(parse))
        self.assertEqual(MSDParameter(('IJKL\n',)), next(parse))
        self.assertEqual(MSDParameter(('M', 'NOP')), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_missing_value_and_semicolon(self):
        parse = parse_msd(string='#A\n#B\n#C\n')

        self.assertEqual(MSDParameter(('A\n',)), next(parse))
        self.assertEqual(MSDParameter(('B\n',)), next(parse))
        self.assertEqual(MSDParameter(('C\n',)), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_unicode(self):
        parse = parse_msd(string='#TITLE:実例;\n#ARTIST:楽士;')
        
        self.assertEqual(MSDParameter(('TITLE', '実例')), next(parse))
        self.assertEqual(MSDParameter(('ARTIST', '楽士')), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_stray_text(self):
        parse = parse_msd(string='#A:B;n#C:D;')

        self.assertEqual(MSDParameter(('A', 'B')), next(parse))
        self.assertRaises(MSDParserError, next, parse)
    
    def test_stray_semicolon(self):
        parse = parse_msd(string='#A:B;;#C:D;')

        self.assertEqual(MSDParameter(('A', 'B')), next(parse))
        self.assertRaises(MSDParserError, next, parse)
    
    def test_stray_text_with_ignore_stray_text(self):
        parse = parse_msd(string='#A:B;n#C:D;', ignore_stray_text=True)

        self.assertEqual(MSDParameter(('A', 'B')), next(parse))
        self.assertEqual(MSDParameter(('C', 'D')), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_escapes(self):
        parse = parse_msd(string='#A\\:B:C\\;D;#E\\#F:G\\\\H;#LF:\\\nLF;')

        self.assertEqual(MSDParameter(('A:B', 'C;D')), next(parse))
        self.assertEqual(MSDParameter(('E#F', 'G\\H')), next(parse))
        self.assertEqual(MSDParameter(('LF', '\nLF')), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_no_escapes(self):
        parse = parse_msd(
            string='#A\\:B:C\\;D;#E\\#F:G\\\\H;#LF:\\\nLF;',
            escapes=False,
            ignore_stray_text=True,
        )

        self.assertEqual(MSDParameter(('A\\', 'B', 'C\\')), next(parse))
        self.assertEqual(MSDParameter(('E\\#F', 'G\\\\H')), next(parse))
        self.assertEqual(MSDParameter(('LF', '\\\nLF')), next(parse))
        self.assertRaises(StopIteration, next, parse)


class TestLexMSD(unittest.TestCase):

    def test_tokens(self):
        lexer = lex_msd(string='#ABC:DEF\\:GHI;\n#JKL:MNO\nPQR# STU')

        self.assertEqual((MSDToken.START_PARAMETER, '#'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'ABC'), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ':'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'DEF'), next(lexer))
        self.assertEqual((MSDToken.ESCAPE, '\\:'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'GHI'), next(lexer))
        self.assertEqual((MSDToken.END_PARAMETER, ';'), next(lexer))
        self.assertEqual((MSDToken.TEXT, '\n'), next(lexer))
        self.assertEqual((MSDToken.START_PARAMETER, '#'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'JKL'), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ':'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'MNO\nPQR# STU'), next(lexer))
        self.assertRaises(StopIteration, next, lexer)
    
    def test_tokens_without_escapes(self):
        lexer = lex_msd(string='#ABC:DEF\\:GHI;\n#JKL:MNO\nPQR# STU', escapes=False)

        self.assertEqual((MSDToken.START_PARAMETER, '#'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'ABC'), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ':'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'DEF\\'), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ':'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'GHI'), next(lexer))
        self.assertEqual((MSDToken.END_PARAMETER, ';'), next(lexer))
        self.assertEqual((MSDToken.TEXT, '\n'), next(lexer))
        self.assertEqual((MSDToken.START_PARAMETER, '#'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'JKL'), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ':'), next(lexer))
        self.assertEqual((MSDToken.TEXT, 'MNO\nPQR# STU'), next(lexer))
        self.assertRaises(StopIteration, next, lexer)


if __name__ == '__main__':
    unittest.main()