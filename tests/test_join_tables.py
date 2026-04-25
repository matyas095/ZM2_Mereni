import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from statisticke_vypracovani.join_tables.logic import JoinTables

SAMPLE_A = """\\begin{table}[H]
\\centering
\\begin{tabular}{@{}cc@{}}
\\toprule
$t$ & $U$ \\\\ \\midrule
0 & 300 \\\\
1 & 297 \\\\
2 & 291 \\\\
\\bottomrule
\\end{tabular}
\\caption{První měření}
\\label{tab:prvni}
\\end{table}
"""
SAMPLE_B = """\\begin{table}[H]
\\centering
\\begin{tabular}{@{}cc@{}}
\\toprule
$t$ & $I$ \\\\ \\midrule
0 & 1.5 \\\\
1 & 1.6 \\\\
5 & 2.0 \\\\
\\bottomrule
\\end{tabular}
\\caption{Druhé měření}
\\label{tab:druhe}
\\end{table}
"""


class TestJoinTables(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp)
        self.path_a = os.path.join(self.tmp, "a.tex")
        self.path_b = os.path.join(self.tmp, "b.tex")
        with open(self.path_a, 'w') as f:
            f.write(SAMPLE_A)
        with open(self.path_b, 'w') as f:
            f.write(SAMPLE_B)
        self.jt = JoinTables()

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp)

    def _make_args(self, mode="horizontal"):
        class Args:
            pass

        args = Args()
        args.input = [self.path_a, self.path_b]
        args.output = "joined"
        args.mode = mode
        return args

    def test_parse_tex(self):
        col_spec, head, rows, cap, lab = self.jt._parse_tex(self.path_a)
        self.assertEqual(col_spec, "@{}cc@{}")
        self.assertEqual(head, ["$t$", "$U$"])
        self.assertEqual(len(rows), 3)
        self.assertEqual(cap, "První měření")
        self.assertEqual(lab, "prvni")

    def test_horizontal_mode(self):
        self.jt.run(self._make_args("horizontal"))
        output_path = os.path.join(self.tmp, "outputs", "joined.tex")
        self.assertTrue(os.path.exists(output_path))
        with open(output_path) as f:
            content = f.read()
        self.assertIn("cccc", content)
        self.assertIn("První měření", content)
        self.assertIn("Druhé měření", content)

    def test_match_mode(self):
        self.jt.run(self._make_args("match"))
        output_path = os.path.join(self.tmp, "outputs", "joined.tex")
        with open(output_path) as f:
            content = f.read()
        self.assertIn("ccc", content)
        self.assertIn("$t$ & $U$ & $I$", content)

    def test_match_mismatch_raises(self):
        path_c = os.path.join(self.tmp, "c.tex")
        with open(path_c, 'w') as f:
            f.write(SAMPLE_A.replace("$t$", "$x$"))

        class Args:
            pass

        args = Args()
        args.input = [self.path_a, path_c]
        args.output = "joined"
        args.mode = "match"
        with self.assertRaises(Exception):
            self.jt.run(args)

    def test_label_merged(self):
        self.jt.run(self._make_args("horizontal"))
        output_path = os.path.join(self.tmp, "outputs", "joined.tex")
        with open(output_path) as f:
            content = f.read()
        self.assertIn("tab:prvni_druhe", content)


if __name__ == "__main__":
    unittest.main()
