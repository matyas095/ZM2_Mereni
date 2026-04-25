import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from objects.input_parser import InputParser
from statisticke_vypracovani.join_tables.logic import JoinTables
from statisticke_vypracovani.extract_table.logic import ExtractTable

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCassyToLatexWorkflow(unittest.TestCase):
    """CASSY → MeasurementSet → LaTeX tabulka."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp)
        self.cassy_path = os.path.join(self.tmp, "cassy.txt")
        with open(self.cassy_path, 'w', encoding='utf-8') as f:
            f.write("E, Run #1\n")
            f.write("U (V)\tI (mA)\n")
            f.write("0,1\t10,0\n")
            f.write("0,2\t20,0\n")
            f.write("0,3\t30,0\n")
            f.write("0,4\t40,0\n")

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp)

    def test_cassy_parse_compute(self):
        ms = InputParser.from_file(self.cassy_path)
        self.assertEqual(len(ms), 2)
        self.assertEqual(ms[0].name, "U [V]")
        self.assertAlmostEqual(ms[0].mean, 0.25)
        self.assertAlmostEqual(ms[1].mean, 25.0)

    def test_cassy_si_normalize(self):
        ms = InputParser.from_file(self.cassy_path)
        si = ms.si_normalize()
        self.assertEqual(si[0].name, "U [V]")
        self.assertEqual(si[1].name, "I [A]")
        self.assertAlmostEqual(si[1].mean, 0.025)


class TestFormatExtractRoundtrip(unittest.TestCase):
    """format_table → extract_table → zkontrolovat že data odpovídají."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp)
        tex = """\\begin{table}[H]
\\centering
\\begin{tabular}{@{}cc@{}}
\\toprule
$U [V]$ & $I [mA]$ \\\\ \\midrule
0,1 & 10,0 \\\\
0,2 & 20,0 \\\\
\\bottomrule
\\end{tabular}
\\caption{Test}
\\label{tab:test}
\\end{table}
"""
        self.tex_path = os.path.join(self.tmp, "in.tex")
        with open(self.tex_path, 'w') as f:
            f.write(tex)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp)

    def test_extract_table(self):
        et = ExtractTable()

        class Args:
            pass

        args = Args()
        args.input = self.tex_path
        args.output = "out"
        args.keep_units = False
        result = et.run(args, do_print=False)
        self.assertIn("U", result)
        self.assertIn("I", result)
        self.assertEqual(result["U"], ["0.1", "0.2"])
        self.assertEqual(result["I"], ["10.0", "20.0"])

    def test_extract_keep_units(self):
        et = ExtractTable()

        class Args:
            pass

        args = Args()
        args.input = self.tex_path
        args.output = "out"
        args.keep_units = True
        result = et.run(args, do_print=False)
        self.assertIn("U [V]", result)
        self.assertIn("I [mA]", result)


class TestJoinThenFormat(unittest.TestCase):
    """join_tables → format_table — zřetězení dvou tabulek a úprava."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp)

        def make_tex(name, var, unit, values):
            content = f"""\\begin{{table}}[H]
\\centering
\\begin{{tabular}}{{@{{}}cc@{{}}}}
\\toprule
$t [s]$ & ${var} [{unit}]$ \\\\ \\midrule
"""
            for i, v in enumerate(values):
                content += f"{i} & {v} \\\\\n"
            content += (
                """\\bottomrule
\\end{tabular}
"""
                + f"\\caption{{{name}}}\n\\label{{tab:{name.lower()}}}\n\\end{{table}}\n"
            )
            return content

        with open(os.path.join(self.tmp, "a.tex"), 'w') as f:
            f.write(make_tex("First", "U", "V", ["1,0", "2,0", "3,0"]))
        with open(os.path.join(self.tmp, "b.tex"), 'w') as f:
            f.write(make_tex("Second", "I", "A", ["0,1", "0,2", "0,3"]))

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp)

    def test_join_then_format(self):
        jt = JoinTables()

        class Args:
            pass

        args = Args()
        args.input = [os.path.join(self.tmp, "a.tex"), os.path.join(self.tmp, "b.tex")]
        args.output = "joined"
        args.mode = "match"
        args.si_normalize = False
        args.convert_units = None
        jt.run(args)
        joined_path = os.path.join(self.tmp, "outputs", "joined.tex")
        self.assertTrue(os.path.exists(joined_path))
        with open(joined_path) as f:
            content = f.read()
        self.assertIn("$I [A]$", content)
        self.assertIn("$U [V]$", content)


if __name__ == "__main__":
    unittest.main()
