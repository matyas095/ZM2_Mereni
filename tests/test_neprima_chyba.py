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

    def test_result_tuple_shape(self):
        class Args:
            input = os.path.join(BASE, "statisticke_vypracovani", "neprima_chyba", "input", "input_file")
            rovnice = None
            konstanty = None

        result = self.nc.run(Args())
        for name, sigma, formatted, mean, latex_str, unit_str in result:
            self.assertIsInstance(name, str)
            self.assertIsInstance(sigma, float)
            self.assertGreater(sigma, 0)
            self.assertIsInstance(mean, float)
            self.assertIsInstance(latex_str, str)
            self.assertGreater(len(latex_str), 0)
            # unit_str is None when no [unit] annotation is present
            self.assertTrue(unit_str is None or isinstance(unit_str, str))

    def test_run_toml(self):
        import tempfile

        toml_src = """# regression fixture
[veliciny.m]
unit = "g"
hodnoty = [25.6338, 25.6339, 25.6338]
typ_b = 0.001

[veliciny.d]
unit = "mm"
hodnoty = [33.05, 33.00, 32.90]
typ_b = { a = 0.05, distribuce = "rovnomerne" }

[funkce.u]
vzorec = "m / (pi*d**3/6)"
unit = "g*mm**-3"
konstanty = { pi = 3.141592653589793 }
"""
        with tempfile.NamedTemporaryFile('w', suffix='.toml', delete=False, encoding='utf-8') as f:
            f.write(toml_src)
            path = f.name

        class Args:
            input = path
            rovnice = None
            konstanty = None
            typ_b = None

        try:
            result = self.nc.run(Args())
            self.assertEqual(len(result), 1)
            name, sigma, formatted, mean, latex_str, unit_str = result[0]
            self.assertEqual(name, "u")
            self.assertEqual(unit_str, "g*mm**-3")
            self.assertAlmostEqual(mean, 0.0013643673, places=8)
            self.assertGreater(sigma, 0)
            self.assertIn("frac", latex_str)
        finally:
            import os

            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
