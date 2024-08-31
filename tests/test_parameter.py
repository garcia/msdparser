import unittest

from msdparser.parameter import MSDParameter
from msdparser.parser import parse_msd


class TestMSDParameter(unittest.TestCase):
    def test_constructor(self):
        param = MSDParameter(("key", "value"))

        self.assertEqual("key", param.key)
        self.assertEqual("value", param.value)
        self.assertIs(param.components[0], param.key)
        self.assertIs(param.components[1], param.value)

    def test_key_without_value(self):
        param = MSDParameter(("key",))

        self.assertEqual("key", param.key)
        self.assertEqual("", param.value)

    def test_stringify_with_escapes(self):
        param = MSDParameter(("key", "value"))
        evil_param = MSDParameter(("ABC:DEF;GHI//JKL\\MNO", "abc:def;ghi//jkl\\mno"))

        self.assertEqual("#key:value;", str(param))
        self.assertEqual(
            "#ABC\\:DEF\\;GHI\\//JKL\\\\MNO:abc\\:def\\;ghi\\//jkl\\\\mno;",
            str(evil_param),
        )

    def test_stringify_without_escapes(self):
        param = MSDParameter(("key", "value"))
        multi_value_param = MSDParameter(("key", "abc", "def"))
        param_with_literal_backslashes = MSDParameter(("ABC\\DEF", "abc\\def"))
        invalid_params = (
            # `:` separator in key
            MSDParameter(("ABC:DEF", "abcdef")),
            # `;` terminator in key or value
            MSDParameter(("ABC;DEF", "abcdef")),
            MSDParameter(("ABCDEF", "abc;def")),
            # `//` comment initializer in key or value
            MSDParameter(("ABC//DEF", "abcdef")),
            MSDParameter(("ABCDEF", "abc//def")),
        )

        self.assertEqual("#key:value;", param.stringify(escapes=False))
        self.assertEqual("#key:abc:def;", multi_value_param.stringify(escapes=False))
        self.assertEqual(
            "#ABC\\DEF:abc\\def;",
            param_with_literal_backslashes.stringify(escapes=False),
        )

        for invalid_param in invalid_params:
            self.assertRaises(ValueError, invalid_param.stringify, escapes=False)

    def test_stringify_with_literal_pound_sign(self):
        param = MSDParameter(("key", "#value"))
        self.assertEqual("#key:#value;", param.stringify(escapes=False))
        self.assertEqual("#key:\\#value;", param.stringify(escapes=True))

