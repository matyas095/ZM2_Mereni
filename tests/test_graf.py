import unittest
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import matplotlib

matplotlib.use('Agg')
from statisticke_vypracovani.graf.logic import Graf
from statisticke_vypracovani.graf_interval.logic import GrafInterval

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE, "grafy_metoda_graf")


class TestGraf(unittest.TestCase):
    def setUp(self):
        self.graf = Graf()

    def tearDown(self):
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)

    def _make_args(self, **kwargs):
        class Args:
            pass

        args = Args()
        args.input = kwargs.get(
            "input", os.path.join(BASE, "statisticke_vypracovani", "graf", "input", "input_File")
        )
        args.name = kwargs.get("name", "test_graf")
        args.rovnice = kwargs.get("rovnice")
        args.parametr = kwargs.get("parametr")
        args.logaritmicky = kwargs.get("logaritmicky", False)
        args.fit = kwargs.get("fit")
        args.chi2 = kwargs.get("chi2", False)
        args.output_format = kwargs.get("output_format", "text")
        return args

    def test_run_basic(self):
        args = self._make_args()
        self.graf.run(args)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, "test_graf.svg")))

    def test_get_args_info(self):
        info = self.graf.get_args_info()
        self.assertIsInstance(info, list)
        self.assertGreater(len(info), 0)
        flags = [a["flags"] for a in info]
        self.assertIn(["-i", "--input"], flags)
        self.assertIn(["-n", "--name"], flags)
        self.assertIn(["--chi2"], flags)


class TestGrafInterval(unittest.TestCase):
    def setUp(self):
        self.gi = GrafInterval()

    def tearDown(self):
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)

    def _make_args(self, **kwargs):
        class Args:
            pass

        args = Args()
        args.name = kwargs.get("name", "test_interval")
        args.rovnice = kwargs.get("rovnice", "y=x**2")
        args.interval = kwargs.get("interval", [0, 10])
        args.output_format = kwargs.get("output_format", "text")
        return args

    def test_run_basic(self):
        args = self._make_args()
        self.gi.run(args)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, "test_interval.svg")))

    def test_run_custom_function(self):
        args = self._make_args(name="test_sin", rovnice="y=x**3-2*x")
        self.gi.run(args)
        self.assertTrue(os.path.exists(os.path.join(OUTPUT_DIR, "test_sin.svg")))

    def test_get_args_info(self):
        info = self.gi.get_args_info()
        self.assertIsInstance(info, list)
        flags = [a["flags"] for a in info]
        self.assertIn(["-r", "--rovnice"], flags)
        self.assertIn(["-i", "--interval"], flags)


if __name__ == "__main__":
    unittest.main()
