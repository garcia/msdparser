import unittest

from msdparser.lexer import MSDToken, lex_msd


class TestLexMSD(unittest.TestCase):
    def test_tokens(self):
        lexer = lex_msd(string="#ABC:DEF\\:GHI;\n#JKL:MNO\nPQR# STU")

        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "ABC"), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "DEF"), next(lexer))
        self.assertEqual((MSDToken.ESCAPE, "\\:"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "GHI"), next(lexer))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "\n"), next(lexer))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "JKL"), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "MNO\nPQR# STU"), next(lexer))
        self.assertRaises(StopIteration, next, lexer)

    def test_tokens_without_escapes(self):
        lexer = lex_msd(string="#ABC:DEF\\:GHI;\n#JKL:MNO\nPQR# STU", escapes=False)

        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "ABC"), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "DEF\\"), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "GHI"), next(lexer))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "\n"), next(lexer))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "JKL"), next(lexer))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lexer))
        self.assertEqual((MSDToken.TEXT, "MNO\nPQR# STU"), next(lexer))
        self.assertRaises(StopIteration, next, lexer)
