import unittest
from io import StringIO

from msdparser import MSDParserError, parse_msd

class TestMSDParser(unittest.TestCase):
    
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
        key, value = next(parse)

        self.assertEqual('A1,./\'"[]{\\}|`~!@#$%^&*()-_=+ \r\n\t', key)
        self.assertEqual('A1,./\'"[]{\\}|`~!@#$%^&*()-_=+ \r\n\t:', value)
        self.assertRaises(StopIteration, next, parse)
    
    def test_comments(self):
        parse = parse_msd(string='#A// comment //\r\nBC:D// ; \nEF;//#NO:PE;')
        
        self.assertEqual(('A\r\nBC', 'D\nEF'), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_comment_with_no_newline_at_eof(self):
        parse = parse_msd(string='#ABC:DEF// eof')

        self.assertEqual(('ABC', 'DEF'), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_empty_key(self):
        parse = parse_msd(string='#:ABC;#:DEF;')

        self.assertEqual(('', 'ABC'), next(parse))
        self.assertEqual(('', 'DEF'), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_empty_value(self):
        parse = parse_msd(string='#ABC:;#DEF:;')

        self.assertEqual(('ABC', ''), next(parse))
        self.assertEqual(('DEF', ''), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_missing_value(self):
        parse = parse_msd(string='#ABC;#DEF;')

        self.assertEqual(('ABC', ''), next(parse))
        self.assertEqual(('DEF', ''), next(parse))
        self.assertRaises(StopIteration, next, parse)

    def test_missing_semicolon(self):
        parse = parse_msd(string='#A:B\nCD;#E:FGH\n#IJKL// comment\n#M:NOP')
        
        self.assertEqual(('A', 'B\nCD'), next(parse))
        self.assertEqual(('E', 'FGH\n'), next(parse))
        self.assertEqual(('IJKL\n', ''), next(parse))
        self.assertEqual(('M', 'NOP'), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_missing_value_and_semicolon(self):
        parse = parse_msd(string='#A\n#B\n#C\n')

        self.assertEqual(('A\n', ''), next(parse))
        self.assertEqual(('B\n', ''), next(parse))
        self.assertEqual(('C\n', ''), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_unicode(self):
        parse = parse_msd(string='#TITLE:実例;\n#ARTIST:楽士;')
        
        self.assertEqual(('TITLE', '実例'), next(parse))
        self.assertEqual(('ARTIST', '楽士'), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_stray_text(self):
        parse = parse_msd(string='#A:B;n#C:D;')

        self.assertEqual(('A', 'B'), next(parse))
        self.assertRaises(MSDParserError, next, parse)
    
    def test_stray_semicolon(self):
        parse = parse_msd(string='#A:B;;#C:D;')

        self.assertEqual(('A', 'B'), next(parse))
        self.assertRaises(MSDParserError, next, parse)
    
    def test_stray_text_with_ignore_stray_text(self):
        parse = parse_msd(string='#A:B;n#C:D;', ignore_stray_text=True)

        self.assertEqual(('A', 'B'), next(parse))
        self.assertEqual(('C', 'D'), next(parse))
        self.assertRaises(StopIteration, next, parse)
    
    def test_escaped_characters(self):
        parse = parse_msd(string=r'#A\:B:C\;D;#E\#F:G\\H;#LF:\\\nLF;')

        self.assertEqual(('A:B', 'C;D'), next(parse))
        self.assertEqual(('E#F', r'G\H'), next(parse))
        self.assertEqual(('LF', r'\nLF'), next(parse))
        self.assertRaises(StopIteration, next, parse)

if __name__ == '__main__':
    unittest.main()