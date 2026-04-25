import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from objects.input_parser import InputParser, try_convert
from objects.measurement import Measurement

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestTryConvert(unittest.TestCase):
    def test_int(self):
        self.assertEqual(try_convert("10"), 10)

    def test_float(self):
        self.assertEqual(try_convert("10.5"), 10.5)

    def test_string(self):
        self.assertEqual(try_convert("chyba"), "chyba")

    def test_passthrough(self):
        self.assertEqual(try_convert(42), 42)


class TestParseStandard(unittest.TestCase):
    def test_parse_real_file(self):
        path = os.path.join(
            BASE, "statisticke_vypracovani", "aritmeticky_prumer", "input", "input_aritm_prumer"
        )
        ms = InputParser.parse_standard(path)
        self.assertGreater(len(ms), 0)
        self.assertIsInstance(ms[0], Measurement)

    def test_parse_with_u_B(self):
        path = os.path.join(
            BASE, "statisticke_vypracovani", "aritmeticky_prumer", "input", "input_aritm_prumer"
        )
        ms = InputParser.parse_standard(path, u_B_map={"R_i": 100.0})
        self.assertAlmostEqual(ms.get("R_i").u_B, 100.0)


class TestParseDict(unittest.TestCase):
    def test_basic(self):
        ms = InputParser.parse_dict({"t": [1, 2, 3]})
        self.assertEqual(len(ms), 1)
        self.assertEqual(ms[0].name, "t")

    def test_with_u_B(self):
        ms = InputParser.parse_dict({"t": [1, 2, 3]}, u_B_map={"t": 0.1})
        self.assertAlmostEqual(ms[0].u_B, 0.1)


class TestParseIndent(unittest.TestCase):
    def test_real_file(self):
        path = os.path.join(BASE, "statisticke_vypracovani", "neprima_chyba", "input", "input_file")
        result = InputParser.parse_indent(path)
        self.assertIn("ELEMENTY", result)
        self.assertIn("FUNKCE", result)

    def test_elementy_keys(self):
        path = os.path.join(BASE, "statisticke_vypracovani", "neprima_chyba", "input", "input_file")
        result = InputParser.parse_indent(path)
        self.assertIn("t", result["ELEMENTY"])
        self.assertIn("U", result["ELEMENTY"])


class TestParseCassy(unittest.TestCase):
    def test_parse_cassy(self):
        path = os.path.join(TESTS_DIR, "test_cassy_data.txt")
        ms = InputParser.parse_cassy(path)
        self.assertEqual(len(ms), 2)
        self.assertEqual(ms[0].name, "U [V]")
        self.assertEqual(ms[1].name, "I [mA]")

    def test_cassy_values(self):
        path = os.path.join(TESTS_DIR, "test_cassy_data.txt")
        ms = InputParser.parse_cassy(path)
        self.assertAlmostEqual(ms[0].values[0], 0.056)
        self.assertAlmostEqual(ms[1].values[0], 0.240)
        self.assertEqual(ms[0].n, 5)

    def test_cassy_decimal_comma(self):
        path = os.path.join(TESTS_DIR, "test_cassy_data.txt")
        ms = InputParser.parse_cassy(path)
        self.assertAlmostEqual(ms[0].values[2], 0.256)

    def test_cassy_with_u_B(self):
        path = os.path.join(TESTS_DIR, "test_cassy_data.txt")
        ms = InputParser.parse_cassy(path, u_B_map={"U": 0.01})
        self.assertAlmostEqual(ms[0].u_B, 0.01)

    def test_detect_cassy(self):
        path = os.path.join(TESTS_DIR, "test_cassy_data.txt")
        self.assertTrue(InputParser._detect_cassy(path))

    def test_detect_not_cassy(self):
        path = os.path.join(
            BASE, "statisticke_vypracovani", "aritmeticky_prumer", "input", "input_aritm_prumer"
        )
        self.assertFalse(InputParser._detect_cassy(path))

    def test_from_file_autodetect(self):
        path = os.path.join(TESTS_DIR, "test_cassy_data.txt")
        ms = InputParser.from_file(path)
        self.assertEqual(len(ms), 2)
        self.assertEqual(ms[0].name, "U [V]")


class TestFromFile(unittest.TestCase):
    def test_auto_detect_txt(self):
        path = os.path.join(
            BASE, "statisticke_vypracovani", "aritmeticky_prumer", "input", "input_aritm_prumer"
        )
        ms = InputParser.from_file(path)
        self.assertGreater(len(ms), 0)


if __name__ == "__main__":
    unittest.main()
