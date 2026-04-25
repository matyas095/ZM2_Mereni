import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from objects.measurement import Measurement


class TestOutlierRemoval(unittest.TestCase):
    def test_no_outliers_small_data(self):
        m = Measurement("x", [1, 2, 3])
        cleaned = m.remove_outliers("3sigma")
        self.assertEqual(cleaned.n, 3)
        self.assertEqual(cleaned.removed_values, [])

    def test_iqr_removes_extreme(self):
        m = Measurement("x", [10, 10, 10, 10, 10, 10, 10, 10, 50])
        cleaned = m.remove_outliers("iqr")
        self.assertIn(50.0, cleaned.removed_values)

    def test_2sigma_removes_outlier(self):
        m = Measurement("x", [10.0, 10.1, 9.9, 10.0, 10.2, 9.8, 10.1, 50.0, 10.0, 9.9])
        cleaned = m.remove_outliers("2sigma")
        self.assertGreater(len(cleaned.removed_values), 0)

    def test_iterative_3sigma(self):
        m = Measurement("x", [1.0] * 20 + [100.0, 200.0])
        cleaned = m.remove_outliers("3sigma")
        self.assertGreater(len(cleaned.removed_values), 0)

    def test_preserves_u_B(self):
        m = Measurement("x", [1.0, 2.0, 3.0, 4.0, 5.0, 100.0], u_B=0.5)
        cleaned = m.remove_outliers("iqr")
        self.assertAlmostEqual(cleaned.u_B, 0.5)

    def test_original_n_preserved(self):
        m = Measurement("x", [1, 2, 3, 4, 5, 100])
        cleaned = m.remove_outliers("iqr")
        self.assertEqual(cleaned.original_n, 6)

    def test_unchanged_when_zero_std(self):
        m = Measurement("x", [5, 5, 5, 5, 5])
        cleaned = m.remove_outliers("3sigma")
        self.assertEqual(cleaned.n, 5)

    def test_custom_k(self):
        m = Measurement("x", [10.0, 10.1, 9.9, 10.0, 10.2, 9.8, 10.1, 50.0, 10.0, 9.9])
        c5 = m.remove_outliers("5sigma")
        c2 = m.remove_outliers("2sigma")
        self.assertLessEqual(len(c5.removed_values), len(c2.removed_values))


if __name__ == "__main__":
    unittest.main()
