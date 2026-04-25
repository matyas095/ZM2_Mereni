import unittest;
import math;
import os;
import sys;

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))));

from statisticke_vypracovani.vazeny_prumer.logic import VazenyPrumer;

class TestVazenyPrumer(unittest.TestCase):

    def setUp(self):
        self.vp = VazenyPrumer();

    def _make_args(self, values, uncertainties, name="x"):
        class Args:
            pass;
        args = Args();
        args.values = values;
        args.uncertainties = uncertainties;
        args.name = name;
        return args;

    def test_equal_weights(self):
        args = self._make_args("10,20,30", "1,1,1");
        result = self.vp.run(args, do_print=False);
        self.assertAlmostEqual(result["x"]["vazeny_prumer"], 20.0);

    def test_different_weights(self):
        args = self._make_args("10,20", "1,0.1");
        result = self.vp.run(args, do_print=False);
        self.assertGreater(result["x"]["vazeny_prumer"], 19.0);

    def test_uncertainty_positive(self):
        args = self._make_args("10,20", "1,0.5");
        result = self.vp.run(args, do_print=False);
        self.assertGreater(result["x"]["nejistota"], 0);

    def test_uncertainty_formula(self):
        args = self._make_args("10,20", "1,2");
        result = self.vp.run(args, do_print=False);
        expected = 1.0 / math.sqrt(1/1**2 + 1/2**2);
        self.assertAlmostEqual(result["x"]["nejistota"], expected);

    def test_custom_name(self):
        args = self._make_args("10,20", "1,1", name="R");
        result = self.vp.run(args, do_print=False);
        self.assertIn("R", result);

    def test_mismatched_lengths(self):
        args = self._make_args("10,20,30", "1,2");
        with self.assertRaises(ValueError):
            self.vp.run(args, do_print=False);

    def test_zero_uncertainty(self):
        args = self._make_args("10,20", "1,0");
        with self.assertRaises(ValueError):
            self.vp.run(args, do_print=False);

    def test_n_count(self):
        args = self._make_args("1,2,3,4,5", "0.1,0.1,0.1,0.1,0.1");
        result = self.vp.run(args, do_print=False);
        self.assertEqual(result["x"]["n"], 5);


if __name__ == "__main__":
    unittest.main();
