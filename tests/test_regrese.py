import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from statisticke_vypracovani.regrese.logic import Regrese
from argparse import Namespace


class TestRegrese(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "data.txt")
        with open(self.path, "w") as f:
            f.write("x=1,2,3,4,5\n")
            f.write("y=2.1,4.0,5.9,8.1,10.0\n")
        self.reg = Regrese()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _args(self, **kwargs):
        return Namespace(
            input=self.path,
            x_col=kwargs.get("x_col"),
            y_col=kwargs.get("y_col"),
            sigma=kwargs.get("sigma"),
        )

    def test_linear_slope(self):
        r = self.reg.run(self._args(), do_print=False)
        self.assertAlmostEqual(r["a"][0], 2.0, places=1)

    def test_intercept_near_zero(self):
        r = self.reg.run(self._args(), do_print=False)
        self.assertAlmostEqual(r["b"][0], 0.05, places=1)

    def test_r2_high(self):
        r = self.reg.run(self._args(), do_print=False)
        self.assertGreater(r["R2"], 0.99)

    def test_has_covariance(self):
        r = self.reg.run(self._args(), do_print=False)
        self.assertIn("cov_ab", r)

    def test_no_chi2_without_sigma(self):
        r = self.reg.run(self._args(), do_print=False)
        self.assertNotIn("chi2", r)

    def test_n_dof_with_sigma(self):
        with open(self.path, "w") as f:
            f.write("x=1,2,3,4,5\n")
            f.write("y=2.1,4.0,5.9,8.1,10.0\n")
            f.write("s=0.1,0.1,0.1,0.1,0.1\n")
        r = self.reg.run(self._args(sigma="s"), do_print=False)
        self.assertIn("chi2_red", r)
        self.assertEqual(r["n_dof"], 3)

    def test_validate_missing_file(self):
        args = Namespace(input="/nonexistent.txt")
        with self.assertRaises(ValueError):
            self.reg.validate(args)


if __name__ == "__main__":
    unittest.main()
