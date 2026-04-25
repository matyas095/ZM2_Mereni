import unittest;
import os;
import sys;
import tempfile;
import shutil;

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))));

from statisticke_vypracovani.format_table.logic import FormatTable;

SAMPLE = """\\begin{table}[H]
\\centering
\\begin{tabular}{@{}cc@{}}
\\toprule
$I [mA]$ & $U [kV]$ \\\\ \\midrule
1500 & 2,5 \\\\
1600 & 2,6 \\\\
\\bottomrule
\\end{tabular}
\\caption{Puvodni mereni}
\\label{tab:puvodni}
\\end{table}
""";


class TestFormatTable(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp();
        self.orig_cwd = os.getcwd();
        os.chdir(self.tmp);
        self.in_path = os.path.join(self.tmp, "in.tex");
        with open(self.in_path, 'w') as f:
            f.write(SAMPLE);
        self.ft = FormatTable();

    def tearDown(self):
        os.chdir(self.orig_cwd);
        shutil.rmtree(self.tmp);

    def _make_args(self, **kwargs):
        class Args:
            pass;
        args = Args();
        args.input = self.in_path;
        args.output = "out";
        args.si_normalize = kwargs.get("si_normalize", False);
        args.convert_units = kwargs.get("convert_units");
        args.caption = kwargs.get("caption");
        args.label = kwargs.get("label");
        args.precision = kwargs.get("precision");
        args.decimal_separator = kwargs.get("decimal_separator", ",");
        args.rows_per_subtable = kwargs.get("rows_per_subtable", 25);
        args.dry_run = kwargs.get("dry_run", False);
        return args;

    def test_si_normalize_headers(self):
        self.ft.run(self._make_args(si_normalize=True));
        with open(os.path.join(self.tmp, "latex_output", "out.tex")) as f:
            content = f.read();
        self.assertIn("$I [A]$", content);
        self.assertIn("$U [V]$", content);

    def test_si_normalize_values(self):
        self.ft.run(self._make_args(si_normalize=True));
        with open(os.path.join(self.tmp, "latex_output", "out.tex")) as f:
            content = f.read();
        self.assertIn("1,5", content);
        self.assertIn("2500", content);

    def test_custom_caption(self):
        self.ft.run(self._make_args(caption="Nový text"));
        with open(os.path.join(self.tmp, "latex_output", "out.tex")) as f:
            content = f.read();
        self.assertIn("\\caption{Nový text}", content);

    def test_custom_label(self):
        self.ft.run(self._make_args(label="novy"));
        with open(os.path.join(self.tmp, "latex_output", "out.tex")) as f:
            content = f.read();
        self.assertIn("\\label{tab:novy}", content);

    def test_precision(self):
        self.ft.run(self._make_args(precision=3));
        with open(os.path.join(self.tmp, "latex_output", "out.tex")) as f:
            content = f.read();
        self.assertIn("1500,000", content);

    def test_decimal_separator_dot(self):
        self.ft.run(self._make_args(precision=1, decimal_separator="."));
        with open(os.path.join(self.tmp, "latex_output", "out.tex")) as f:
            content = f.read();
        self.assertIn("2.5", content);

    def test_convert_units_manual(self):
        self.ft.run(self._make_args(convert_units='{"I":"A"}'));
        with open(os.path.join(self.tmp, "latex_output", "out.tex")) as f:
            content = f.read();
        self.assertIn("$I [A]$", content);
        self.assertIn("$U [kV]$", content);


if __name__ == "__main__":
    unittest.main();
