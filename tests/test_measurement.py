import unittest
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from objects.measurement import Measurement
from objects.measurement_set import MeasurementSet


class TestMeasurement(unittest.TestCase):
    def test_mean(self):
        m = Measurement("x", [1.0, 2.0, 3.0])
        self.assertAlmostEqual(m.mean, 2.0)

    def test_mean_single(self):
        m = Measurement("x", [5.0])
        self.assertAlmostEqual(m.mean, 5.0)

    def test_u_A_identical(self):
        m = Measurement("x", [10.0, 10.0, 10.0])
        self.assertAlmostEqual(m.u_A, 0.0)

    def test_u_A_known(self):
        m = Measurement("x", [1.0, 2.0, 3.0])
        expected = math.sqrt(2.0 / (3 * 2))
        self.assertAlmostEqual(m.u_A, expected)

    def test_u_c_without_B(self):
        m = Measurement("x", [1.0, 2.0, 3.0])
        self.assertAlmostEqual(m.u_c, m.u_A)

    def test_u_c_with_B(self):
        m = Measurement("x", [1.0, 2.0, 3.0], u_B=0.5)
        expected = math.sqrt(m.u_A**2 + 0.5**2)
        self.assertAlmostEqual(m.u_c, expected)

    def test_expanded_uncertainty(self):
        m = Measurement("x", [1.0, 2.0, 3.0], u_B=0.1)
        self.assertAlmostEqual(m.expanded_uncertainty(2), 2 * m.u_c)
        self.assertAlmostEqual(m.expanded_uncertainty(3), 3 * m.u_c)

    def test_format_contains_plusminus(self):
        m = Measurement("x", [1.0, 2.0, 3.0])
        self.assertIn("±", m.format())

    def test_n(self):
        m = Measurement("x", [1, 2, 3, 4, 5])
        self.assertEqual(m.n, 5)

    def test_repr(self):
        m = Measurement("x", [1.0, 2.0])
        self.assertIn("Measurement", repr(m))


class TestMeasurementSet(unittest.TestCase):
    def test_from_dict(self):
        ms = MeasurementSet.from_dict({"a": [1, 2, 3], "b": [4, 5, 6]})
        self.assertEqual(len(ms), 2)

    def test_names(self):
        ms = MeasurementSet.from_dict({"x": [1], "y": [2]})
        self.assertEqual(ms.names, ["x", "y"])

    def test_to_dict(self):
        ms = MeasurementSet.from_dict({"x": [1.0, 2.0, 3.0]})
        d = ms.to_dict()
        self.assertIn("x", d)
        self.assertAlmostEqual(d["x"][0], 2.0)

    def test_to_raw_dict(self):
        ms = MeasurementSet.from_dict({"x": [1, 2, 3]})
        d = ms.to_raw_dict()
        self.assertEqual(d["x"], [1, 2, 3])

    def test_get(self):
        ms = MeasurementSet.from_dict({"x": [1], "y": [2]})
        self.assertEqual(ms.get("y").name, "y")

    def test_get_missing_raises(self):
        ms = MeasurementSet.from_dict({"x": [1]})
        with self.assertRaises(KeyError):
            ms.get("neexistuje")

    def test_iteration(self):
        ms = MeasurementSet.from_dict({"a": [1], "b": [2]})
        names = [m.name for m in ms]
        self.assertEqual(names, ["a", "b"])

    def test_u_B_map(self):
        ms = MeasurementSet.from_dict({"x": [1, 2, 3]}, u_B_map={"x": 0.5})
        self.assertAlmostEqual(ms.get("x").u_B, 0.5)


if __name__ == "__main__":
    unittest.main()
