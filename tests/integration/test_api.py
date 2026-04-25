import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import zm2


class TestProgrammaticAPI(unittest.TestCase):
    """Testuje knihovní API v zm2/__init__.py."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp)

    def test_aritmeticky_prumer_dict(self):
        r = zm2.aritmeticky_prumer({"U": [1.0, 2.0, 3.0]})
        self.assertIn("U", r)
        self.assertAlmostEqual(r["U"][0], 2.0)

    def test_aritmeticky_prumer_file(self):
        path = os.path.join(self.tmp, "data.txt")
        with open(path, "w") as f:
            f.write("U=1.0,2.0,3.0\n")
        r = zm2.aritmeticky_prumer(path)
        self.assertAlmostEqual(r["U"][0], 2.0)

    def test_aritmeticky_prumer_with_typ_b(self):
        r = zm2.aritmeticky_prumer({"x": [1.0, 2.0, 3.0]}, typ_b={"x": 0.5})
        self.assertGreater(r["x"][1], 0)

    def test_vazeny_prumer(self):
        r = zm2.vazeny_prumer([10.2, 10.3, 10.1], [0.1, 0.05, 0.2], "R")
        self.assertIn("R", r)
        self.assertAlmostEqual(r["R"]["vazeny_prumer"], 10.2714, places=3)

    def test_regrese_api(self):
        path = os.path.join(self.tmp, "reg.txt")
        with open(path, "w") as f:
            f.write("x=1,2,3,4,5\n")
            f.write("y=2.1,4.0,5.9,8.1,10.0\n")
        r = zm2.regrese(path)
        self.assertIn("a", r)
        self.assertIn("b", r)
        self.assertIn("R2", r)
        self.assertAlmostEqual(r["a"][0], 2.0, places=1)

    def test_derivace_api(self):
        path = os.path.join(self.tmp, "deriv.txt")
        with open(path, "w") as f:
            f.write("t=0,1,2,3,4\n")
            f.write("x=0,1,4,9,16\n")
        r = zm2.derivace(path)
        self.assertIsInstance(r, dict)


class TestValidation(unittest.TestCase):
    """Testuje že validate() odchytává chyby."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp)

    def test_aritm_missing_file(self):
        from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer
        from argparse import Namespace

        args = Namespace(input="/nonexistent/file.txt", batch=None)
        with self.assertRaises(ValueError):
            AritmetickyPrumer().validate(args)

    def test_graf_missing_name(self):
        from statisticke_vypracovani.graf.logic import Graf
        from argparse import Namespace

        args = Namespace(input="/tmp/x", name=None)
        with self.assertRaises(ValueError):
            Graf().validate(args)

    def test_graf_interval_bad_interval(self):
        from statisticke_vypracovani.graf_interval.logic import GrafInterval
        from argparse import Namespace

        args = Namespace(name="test", rovnice="y=x**2", interval=[10.0, 5.0])
        with self.assertRaises(ValueError):
            GrafInterval().validate(args)

    def test_vazeny_prumer_mismatched(self):
        from statisticke_vypracovani.vazeny_prumer.logic import VazenyPrumer
        from argparse import Namespace

        args = Namespace(values="1,2,3", uncertainties="0.1,0.2")
        with self.assertRaises(ValueError):
            VazenyPrumer().validate(args)

    def test_join_tables_one_input(self):
        from statisticke_vypracovani.join_tables.logic import JoinTables
        from argparse import Namespace

        args = Namespace(input=["only_one.tex"])
        with self.assertRaises(ValueError):
            JoinTables().validate(args)


if __name__ == "__main__":
    unittest.main()
