import unittest
from io import StringIO

from msdparser import MSDParser

class TestMSDParser(unittest.TestCase):
    
    def test_constructor(self):
        data = "#A:B;"
        unit_from_file = MSDParser(file=StringIO(data))
        unit_from_string = MSDParser(string=data)
        iterator_from_file = iter(unit_from_file)
        iterator_from_string = iter(unit_from_string)
        
        self.assertEqual(next(iterator_from_file), next(iterator_from_string))
        self.assertRaises(StopIteration, next, iterator_from_file)
        self.assertRaises(StopIteration, next, iterator_from_string)
    
    def test_empty(self):
        unit = MSDParser(string="")
        iterator = iter(unit)
        
        self.assertRaises(StopIteration, next, iterator)
    
    def test_normal_characters(self):
        unit = MSDParser(string='#A1,./\'"[]\{\}|`~!@#$%^&*()-_=+ \r\n\t:A1,./\'"[]\{\}|`~!@#$%^&*()-_=+ \r\n\t:;')
        iterator = iter(unit)
        key, value = next(iterator)

        self.assertEqual('A1,./\'"[]\{\}|`~!@#$%^&*()-_=+ \r\n\t', key)
        self.assertEqual('A1,./\'"[]\{\}|`~!@#$%^&*()-_=+ \r\n\t:', value)
        self.assertRaises(StopIteration, next, iterator)
    
    def test_comments(self):
        unit = MSDParser(string='#A// comment //\r\nBC:D// ; \nEF;//#NO:PE;')
        iterator = iter(unit)
        
        self.assertEqual(('A\r\nBC', 'D\nEF'), next(iterator))
        self.assertRaises(StopIteration, next, iterator)
    
    def test_comment_with_no_newline_at_eof(self):
        unit = MSDParser(string='#ABC:DEF// eof')
        iterator = iter(unit)

        self.assertEqual(('ABC', 'DEF'), next(iterator))
        self.assertRaises(StopIteration, next, iterator)

    def test_empty_key(self):
        unit = MSDParser(string='#:ABC;#:DEF;')
        iterator = iter(unit)

        self.assertEqual(('', 'ABC'), next(iterator))
        self.assertEqual(('', 'DEF'), next(iterator))
        self.assertRaises(StopIteration, next, iterator)
    
    def test_empty_value(self):
        unit = MSDParser(string='#ABC:;#DEF:;')
        iterator = iter(unit)

        self.assertEqual(('ABC', ''), next(iterator))
        self.assertEqual(('DEF', ''), next(iterator))
        self.assertRaises(StopIteration, next, iterator)

    def test_missing_value(self):
        unit = MSDParser(string='#ABC;#DEF;')
        iterator = iter(unit)

        self.assertEqual(('ABC', ''), next(iterator))
        self.assertEqual(('DEF', ''), next(iterator))
        self.assertRaises(StopIteration, next, iterator)

    def test_missing_semicolon(self):
        unit = MSDParser(string='#A:B\nCD;#E:FGH\n#IJKL// comment\n#M:NOP')
        iterator = iter(unit)
        
        self.assertEqual(('A', 'B\nCD'), next(iterator))
        self.assertEqual(('E', 'FGH\n'), next(iterator))
        self.assertEqual(('IJKL\n', ''), next(iterator))
        self.assertEqual(('M', 'NOP'), next(iterator))
        self.assertRaises(StopIteration, next, iterator)
    
    def test_missing_value_and_semicolon(self):
        unit = MSDParser(string='#A\n#B\n#C\n')
        iterator = iter(unit)

        self.assertEqual(('A\n', ''), next(iterator))
        self.assertEqual(('B\n', ''), next(iterator))
        self.assertEqual(('C\n', ''), next(iterator))
        self.assertRaises(StopIteration, next, iterator)
    
    def test_unicode(self):
        unit = MSDParser(string='#TITLE:実例;\n#ARTIST:楽士;')
        iterator = iter(unit)
        
        self.assertEqual(('TITLE', '実例'), next(iterator))
        self.assertEqual(('ARTIST', '楽士'), next(iterator))
        self.assertRaises(StopIteration, next, iterator)


if __name__ == '__main__':
    unittest.main()