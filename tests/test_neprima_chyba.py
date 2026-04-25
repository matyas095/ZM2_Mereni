import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from statisticke_vypracovani.neprima_chyba.logic import NeprimaChyba

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestNeprimaChyba(unittest.TestCase):
    def setUp(self):
        self.nc = NeprimaChyba()

    def test_run_txt(self):
        class Args:
            input = os.path.join(BASE, "statisticke_vypracovani", "neprima_chyba", "input", "input_file")
            rovnice = None
            konstanty = None

        result = self.nc.run(Args())
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0][0], "R")

    def test_result_has_three_elements(self):
        class Args:
            input = os.path.join(BASE, "statisticke_vypracovani", "neprima_chyba", "input", "input_file")
            rovnice = None
            konstanty = None

        result = self.nc.run(Args())
        for name, sigma, formatted in result:
            self.assertIsInstance(name, str)
            self.assertIsInstance(sigma, float)
            self.assertGreater(sigma, 0)


if __name__ == "__main__":
    unittest.main()
