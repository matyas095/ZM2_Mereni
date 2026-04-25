import unittest;
import os;
import sys;
import tempfile;
import shutil;

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))));

from statisticke_vypracovani.derivace.logic import Derivace;

class TestDerivace(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp();
        self.orig_cwd = os.getcwd();
        os.chdir(self.tmp);
        self.input_path = os.path.join(self.tmp, "data.txt");
        with open(self.input_path, 'w') as f:
            f.write("t=0,1,2,3,4\n");
            f.write("x=0,1,4,9,16\n");
        self.der = Derivace();

    def tearDown(self):
        os.chdir(self.orig_cwd);
        shutil.rmtree(self.tmp);

    def _make_args(self, **kwargs):
        class Args:
            pass;
        args = Args();
        args.input = kwargs.get("input", self.input_path);
        args.x_col = kwargs.get("x_col");
        args.y_col = kwargs.get("y_col");
        args.output = kwargs.get("output", "derivace");
        return args;

    def test_x_squared_derivative(self):
        result = self.der.run(self._make_args(), do_print=False);
        self.assertIn("t", result);
        self.assertIn("dx/dt", result);

    def test_output_file_created(self):
        self.der.run(self._make_args(output="myderiv"), do_print=True);
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "outputs", "myderiv.txt")));

    def test_too_few_points(self):
        with open(self.input_path, 'w') as f:
            f.write("t=0,1\n");
            f.write("x=0,1\n");
        with self.assertRaises(ValueError):
            self.der.run(self._make_args(), do_print=False);


if __name__ == "__main__":
    unittest.main();
