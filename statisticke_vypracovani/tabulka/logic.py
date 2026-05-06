from typing import Any
from pathlib import Path
import math
from itertools import zip_longest

from utils import color_print, locked_open, extract_variables, round_half_up
from statisticke_vypracovani.base import Method
from objects.measurement import Measurement
from objects.measurement_set import MeasurementSet


def _dec_sep() -> str:
    try:
        from objects.config import config
        return config().get("decimal_separator", ",")
    except Exception:
        return ","


class Tabulka(Method):
    name = "tabulka"
    description = (
        "LaTeX tabulka z TOML: sloupce = [veliciny.*] + (volitelne) hodnota [funkce.*] po radcich. "
        "S -lt prida mean +- nejistotu (jako aritmeticky_prumer)."
    )

    def validate(self, args) -> None:
        import os
        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)")
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje")
        if not str(args.input).lower().endswith(".toml"):
            raise ValueError("Tabulka přijímá pouze .toml vstup")

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k TOML souboru se sekcemi [veliciny.*] a volitelne [funkce.*]",
                "required": True,
                "is_file": True,
            },
            {
                "flags": ["-lt", "--latextable"],
                "help": "Pripoji mean +- nejistotu (aritmeticky_prumer styl) do popisku tabulky",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["-o", "--output"],
                "help": "Vystupni soubor bez pripony (vychozi: tabulka_output)",
                "required": False,
                "default": "tabulka_output",
                "type": str,
            },
            {
                "flags": ["-c", "--caption"],
                "help": "Vlastni popisek (caption) tabulky",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-l", "--label"],
                "help": "Vlastni LaTeX label tabulky",
                "required": False,
                "type": str,
            },
            {
                "flags": ["--rel-uncertainty"],
                "help": "S -lt: pridej do caption relativni nejistotu",
                "required": False,
                "action": "store_true",
            },
        ]

    # ---------- TOML -> MeasurementSet ----------

    def _build_set(self, args) -> MeasurementSet:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore

        from sympy import symbols, asin, acos, atan, asinh, acosh, atanh, E as Euler, lambdify, Symbol
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication,
        )

        with open(args.input, "rb") as f:
            cfg = tomllib.load(f)

        veliciny = cfg.get("veliciny", {}) or {}
        funkce_cfg = cfg.get("funkce", {}) or {}
        if not veliciny:
            raise ValueError("TOML musí obsahovat alespoň jednu sekci [veliciny.<nazev>]")

        ms = MeasurementSet()
        velicina_values: dict[str, list[float]] = {}

        # 1) [veliciny.*] -> Measurement na velicina
        for vname, vinfo in veliciny.items():
            vals = vinfo.get("hodnoty")
            if vals is None:
                raise ValueError(f"Velicina '{vname}' nema klic 'hodnoty'")
            unit = vinfo.get("unit", "")
            full_name = f"{vname} [{unit}]" if unit else vname
            float_vals = [float(x) for x in vals]
            ms.add(Measurement(full_name, float_vals))
            velicina_values[vname] = float_vals

        # 2) [funkce.*] -> Measurement s 1-na-1 dosazenim hodnot
        if funkce_cfg:
            transformations = standard_transformations + (implicit_multiplication,)
            for fname, finfo in funkce_cfg.items():
                formula = finfo.get("vzorec")
                if not formula:
                    continue
                unit = finfo.get("unit", "")
                konstanty = finfo.get("konstanty", {}) or {}

                full_name = f"{fname} [{unit}]" if unit else fname

                in_formula = extract_variables(formula, list(konstanty.keys()))
                unknown = [v for v in in_formula
                           if v not in velicina_values and v not in konstanty]
                if unknown:
                    raise ValueError(
                        f"Funkce '{fname}': promenne {unknown} nejsou ve [veliciny.*] "
                        f"ani v 'konstanty'"
                    )

                # sympy parse
                sym_map = {n: symbols(n) for n in in_formula}
                parse_dict = dict(sym_map)
                parse_dict.update({
                    "arcsin": asin, "arccos": acos, "arctan": atan,
                    "arcsinh": asinh, "arccosh": acosh, "arctanh": atanh,
                    "e": Euler,
                })
                for k in konstanty:
                    parse_dict.setdefault(k, symbols(k))

                try:
                    expr = parse_expr(formula, local_dict=parse_dict, transformations=transformations)
                except Exception as e:
                    raise ValueError(f"Funkce '{fname}': chyba parseru sympy: {e}") from e

                # Substituce konstant na cisla
                const_subs = {Symbol(k): v for k, v in konstanty.items()}
                expr_subbed = expr.subs(const_subs)

                # Promenne, ktere ve vzorci jeste zustaly (po substituci) — ty jsou veliciny
                remaining = [v for v in in_formula if v in velicina_values]
                if not remaining:
                    raise ValueError(
                        f"Funkce '{fname}': po substituci konstant nezbyla zadna promenna"
                    )

                f_eval = lambdify(remaining, expr_subbed, 'numpy')

                # 1-na-1: i-ty radek = i-te hodnoty kazde veliciny
                n_rows = max(len(velicina_values[v]) for v in remaining)
                row_values: list[float] = []
                for i in range(n_rows):
                    inputs = []
                    ok = True
                    for v in remaining:
                        vals = velicina_values[v]
                        if i >= len(vals):
                            ok = False
                            break
                        inputs.append(vals[i])
                    if not ok:
                        row_values.append(float('nan'))
                        continue
                    try:
                        result = float(f_eval(*inputs))
                    except Exception:
                        result = float('nan')
                    row_values.append(result)

                ms.add(Measurement(full_name, row_values))

        return ms

    # ---------- Vystup ----------

    def _write_simple_tabular(self, ms: MeasurementSet, args) -> Path:
        """Tabulka bez aritmetickeho prumeru — header + body, jednoducha caption."""
        from objects.units import extract_name_unit as _eu, display_unit as _du

        def _latex_header(name: str) -> str:
            var, unit = _eu(name)
            if unit is None or not str(unit).strip():
                return f"${var} [-]$"
            return f"${var} \\, [\\mathrm{{{_du(unit)}}}]$"

        headers = [_latex_header(m.name) for m in ms.measurements]
        n_cols = len(headers)
        col_spec = "c" * n_cols

        body = []
        for m in ms.measurements:
            try:
                p = max(m.precision_for("u_c"), 1)
            except Exception:
                p = 4
            cells = []
            for v in m.values:
                if isinstance(v, float) and math.isnan(v):
                    cells.append("-")
                else:
                    cells.append(f"{round_half_up(float(v), p):.{p}f}".replace(".", _dec_sep()))
            body.append(cells)

        rows = list(zip_longest(*body, fillvalue="-"))

        # Sirky sloupcu
        col_widths = []
        for i in range(n_cols):
            cells_i = [str(r[i]) for r in rows]
            max_w = max(len(headers[i]), max([len(c) for c in cells_i] or [0]))
            col_widths.append(max_w)

        formatted_headers = [headers[i].ljust(col_widths[i]) for i in range(n_cols)]
        header_line = " & ".join(formatted_headers) + " \\\\ \\midrule"
        formatted_rows = []
        for row in rows:
            cells = [str(row[i]).ljust(col_widths[i]) for i in range(n_cols)]
            formatted_rows.append(" & ".join(cells) + " \\\\")

        # Caption + label
        import os, re
        caption = (
            getattr(args, 'caption', None)
            or os.path.basename(getattr(args, 'input', '') or '')
            or "Tabulka hodnot"
        )
        if getattr(args, 'label', None):
            label = args.label
        else:
            base = os.path.splitext(os.path.basename(args.input))[0]
            label = re.sub(r'[^a-zA-Z0-9_]', '_', base).lower()
            label = re.sub(r'_+', '_', label).strip('_') or "tabulka"

        # Soubor
        folder = Path("latex_output").resolve()
        folder.mkdir(parents=True, exist_ok=True)
        out_name = (getattr(args, 'output', None) or "tabulka_output") + ".tex"
        out_path = folder / out_name

        with locked_open(out_path, "w", encoding="utf-8") as f:
            f.write("\\begin{table}[H]\n")
            f.write("\t\\centering\n")
            f.write("\t\\small\n")
            f.write(f"\t\\begin{{tabular}}{{{col_spec}}}\n")
            f.write("\t\t\\toprule\n")
            f.write("\t\t" + header_line + "\n")
            for r in formatted_rows:
                f.write("\t\t" + r + "\n")
            f.write("\t\t\\bottomrule\n")
            f.write("\t\\end{tabular}\n")
            f.write(f"\t\\caption{{{caption}}}\n")
            f.write(f"\t\\label{{tab:{label}}}\n")
            f.write("\\end{table}\n")

        return out_path

    # ---------- Vstupni bod ----------

    def run(self, args: Any, do_print: bool = True) -> dict:
        ms = self._build_set(args)

        if do_print:
            if getattr(args, 'latextable', False):
                # -lt: plna tabulka s mean +- u_c v caption (jako aritmeticky_prumer)
                ms.to_latex_table(
                    source_file=getattr(args, 'input', None),
                    custom_caption=getattr(args, 'caption', None),
                    custom_label=getattr(args, 'label', None),
                    dry_run=False,
                    include_rel_uncertainty=getattr(args, 'rel_uncertainty', False),
                    precision_source='u_c',
                )
            else:
                # Bez -lt: jednoducha tabulka bez statistik
                out_path = self._write_simple_tabular(ms, args)
                print(f"{color_print.GREEN}Výstup:{color_print.END} {out_path}")
            print("-" * 100)

        return {m.name: list(m.values) for m in ms.measurements}
