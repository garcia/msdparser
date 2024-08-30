import unittest

from msdparser.lexer import MSDToken, lex_msd


class TestLexMSD(unittest.TestCase):
    def test_tokens_with_escapes(self):
        lex = lex_msd(string="#ABC:DEF\\:GHI;\n#JKL:MNO\nPQR# STU")

        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "ABC"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "DEF"), next(lex))
        self.assertEqual((MSDToken.ESCAPE, "\\:"), next(lex))
        self.assertEqual((MSDToken.TEXT, "GHI"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lex))
        self.assertEqual((MSDToken.TEXT, "\n"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "JKL"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "MNO\nPQR"), next(lex))
        self.assertEqual((MSDToken.TEXT, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, " STU"), next(lex))
        self.assertRaises(StopIteration, next, lex)

    def test_tokens_without_escapes(self):
        lex = lex_msd(string="#ABC:DEF\\:GHI;\n#JKL:MNO\nPQR# STU", escapes=False)

        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "ABC"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "DEF\\"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "GHI"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lex))
        self.assertEqual((MSDToken.TEXT, "\n"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "JKL"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "MNO\nPQR"), next(lex))
        self.assertEqual((MSDToken.TEXT, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, " STU"), next(lex))
        self.assertRaises(StopIteration, next, lex)

    def test_stray_metacharacters(self):
        lex = lex_msd(string=":;#A:B;;:#C:D;")

        self.assertEqual((MSDToken.TEXT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, ";"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "A"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "B"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lex))
        self.assertEqual((MSDToken.TEXT, ";"), next(lex))
        self.assertEqual((MSDToken.TEXT, ":"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "C"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "D"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lex))

    def test_missing_semicolon(self):
        lex = lex_msd(
            string="#A:B\nCD;#E:FGH\n#IJKL// comment \n#M:NOP\n \t#Q:RST\n ! #U:V"
        )

        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "A"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "B\nCD"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "E"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "FGH"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, "\n"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "IJKL"), next(lex))
        self.assertEqual((MSDToken.COMMENT, "// comment "), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, "\n"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "M"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "NOP"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, "\n \t"), next(lex))
        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "Q"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "RST\n ! "), next(lex))
        self.assertEqual((MSDToken.TEXT, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "U"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "V"), next(lex))

        self.assertRaises(StopIteration, next, lex)

    def test_comments(self):
        lex = lex_msd(string="#A// comment //\r\nBC:D// ; \nEF;//#NO:PE;")

        self.assertEqual((MSDToken.START_PARAMETER, "#"), next(lex))
        self.assertEqual((MSDToken.TEXT, "A"), next(lex))
        self.assertEqual((MSDToken.COMMENT, "// comment //"), next(lex))
        self.assertEqual((MSDToken.TEXT, "\r\nBC"), next(lex))
        self.assertEqual((MSDToken.NEXT_COMPONENT, ":"), next(lex))
        self.assertEqual((MSDToken.TEXT, "D"), next(lex))
        self.assertEqual((MSDToken.COMMENT, "// ; "), next(lex))
        self.assertEqual((MSDToken.TEXT, "\nEF"), next(lex))
        self.assertEqual((MSDToken.END_PARAMETER, ";"), next(lex))
        self.assertEqual((MSDToken.COMMENT, "//#NO:PE;"), next(lex))
        self.assertRaises(StopIteration, next, lex)
