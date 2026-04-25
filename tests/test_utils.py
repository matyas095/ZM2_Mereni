import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import extract_variables, parse_rovnice, r2_score, return_Cislo_Krat_10_Na


class TestExtractVariables(unittest.TestCase):
    def test_simple(self):
        result = extract_variables("a + b * c")
        self.assertEqual(result, ["a", "b", "c"])

    def test_ignores_functions(self):
        result = extract_variables("sin(x) + log(y)")
        self.assertEqual(result, ["x", "y"])

    def test_ignores_custom(self):
        result = extract_variables("a + b + C", toIgnore=["C"])
        self.assertEqual(result, ["a", "b"])

    def test_deduplication(self):
        result = extract_variables("x + x + x")
        self.assertEqual(result, ["x"])

    def test_sorted(self):
        result = extract_variables("z + a + m")
        self.assertEqual(result, ["a", "m", "z"])


class TestParseRovnice(unittest.TestCase):
    def test_basic(self):
        nazev, vztah = parse_rovnice("R=U/I")
        self.assertEqual(nazev, "R")
        self.assertEqual(vztah, "U/I")

    def test_complex(self):
        nazev, vztah = parse_rovnice("y=a*x**2+b*x+c")
        self.assertEqual(nazev, "y")
        self.assertEqual(vztah, "a*x**2+b*x+c")

    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_rovnice("neni_rovnice")


class TestR2Score(unittest.TestCase):
    def test_perfect_fit(self):
        y = [1, 2, 3, 4, 5]
        self.assertAlmostEqual(r2_score(y, y), 1.0)

    def test_bad_fit(self):
        y = [1, 2, 3, 4, 5]
        pred = [5, 4, 3, 2, 1]
        self.assertLess(r2_score(y, pred), 0)


class TestSmartParse(unittest.TestCase):
    def test_python_expression(self):
        from utils import smart_parse

        parsed, vars, name = smart_parse("y=x**2")
        self.assertEqual(name, "y")
        self.assertIn("x", vars)

    def test_no_equals(self):
        from utils import smart_parse

        parsed, vars, name = smart_parse("x**2+1")
        self.assertEqual(name, "y")


class TestReturnCislo(unittest.TestCase):
    def test_positive(self):
        result = return_Cislo_Krat_10_Na(1234.5)
        self.assertIn("10^3", result)

    def test_small(self):
        result = return_Cislo_Krat_10_Na(0.0056)
        self.assertIn("10^-3", result)


if __name__ == "__main__":
    unittest.main()
