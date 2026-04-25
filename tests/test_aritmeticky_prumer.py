import unittest
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer, _parse_typ_b

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestAritmetickyPrumer(unittest.TestCase):
    def setUp(self):
        self.ap = AritmetickyPrumer()

    def test_run_dict(self):
        result = self.ap.run({"x": [1, 2, 3]}, do_print=False)
        self.assertIn("x", result)
        self.assertAlmostEqual(result["x"][0], 2.0)

    def test_run_dict_error(self):
        result = self.ap.run({"x": [10, 10, 10]}, do_print=False)
        self.assertAlmostEqual(result["x"][1], 0.0)

    def test_run_file(self):
        class Args:
            input = os.path.join(
                BASE, "statisticke_vypracovani", "aritmeticky_prumer", "input", "input_aritm_prumer"
            )
            latextable = None
            typ_b = None

        result = self.ap.run(Args(), do_print=False)
        self.assertIn("R_i", result)
        self.assertGreater(result["R_i"][0], 0)


class TestParseTypB(unittest.TestCase):
    def test_none(self):
        self.assertEqual(_parse_typ_b(None), {})

    def test_direct_value(self):
        result = _parse_typ_b({"R": 0.5})
        self.assertAlmostEqual(result["R"], 0.5)

    def test_rovnomerne(self):
        result = _parse_typ_b({"R": [0.6, "rovnomerne"]})
        self.assertAlmostEqual(result["R"], 0.6 / math.sqrt(3))

    def test_trojuhelnikove(self):
        result = _parse_typ_b({"R": [0.6, "trojuhelnikove"]})
        self.assertAlmostEqual(result["R"], 0.6 / math.sqrt(6))

    def test_normalni(self):
        result = _parse_typ_b({"R": [0.6, "normalni"]})
        self.assertAlmostEqual(result["R"], 0.3)

    def test_json_string(self):
        result = _parse_typ_b('{"R": 0.5}')
        self.assertAlmostEqual(result["R"], 0.5)


if __name__ == "__main__":
    unittest.main()
