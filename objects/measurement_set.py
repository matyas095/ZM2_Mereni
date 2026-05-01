import math
import numpy as np
from pathlib import Path
from itertools import zip_longest
from utils import color_print, locked_open, round_half_up
from objects.measurement import Measurement


def _dec_sep() -> str:
    try:
        from objects.config import config

        return config().get("decimal_separator", ",")
    except Exception:
        return ","


class MeasurementSet:
    def __init__(self, measurements: list = None):
        self.measurements: list[Measurement] = measurements or []
        self.computation_errors: list[str] = []

    def add(self, measurement: Measurement):
        self.measurements.append(measurement)
        return self

    def add_derived(
        self, name: str, unit: str, formula: str, constants: dict | None = None
    ) -> list[str]:
        """Spocita derivovany sloupec '<name> [<unit>]' = formula(...) per radek
        a prida do setu jako DerivedMeasurement. Vraci seznam chyb (deleni nulou,
        domena, ...) pro radky, kde vzorec selhal — ty radky maji NaN.

        constants: slovnik konstant, ktere ve vzorci vystupuji jako nazvy
        (napr. {'R_0': 0.05, 'k_B': 1.381e-23}). Substituuji se per radek
        spolu s velicinami.

        Selze rychle pri:
            - chybejici promenna ve free_symbols (neni mezi velicinami ani konstantami)
            - kolize konstanty s existujici velicinou
            - ruzne delky vstupnich sloupcu
            - neparsovatelny vzorec
            - kolize jmena s existujici velicinou
        """
        constants = constants or {}
        from sympy import Symbol, symbols
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication,
        )
        from objects.units import extract_name_unit
        from objects.measurement import DerivedMeasurement

        existing_names = {extract_name_unit(m.name)[0] for m in self.measurements}
        if name in existing_names:
            raise ValueError(f"Vypocet '{name}': jmeno koliduje s existujici velicinou")

        vars_in_set = {extract_name_unit(m.name)[0]: m for m in self.measurements}

        const_collisions = set(constants) & vars_in_set.keys()
        if const_collisions:
            raise ValueError(
                f"Vypocet '{name}': konstanty {sorted(const_collisions)} se jmenuji stejne jako veliciny"
            )

        try:
            import re
            from sympy import asin, acos, atan, asinh, acosh, atanh, E as Euler

            # Aliasy pro fyzikalni notaci + 'e' jako Eulerovo cislo (sympy default
            # mapuje jen 'E' na Eulera, my chceme explicitne 'e').
            fn_aliases = {
                "arcsin": asin, "arccos": acos, "arctan": atan,
                "arcsinh": asinh, "arccosh": acosh, "arctanh": atanh,
                "e": Euler,
            }
            # Matematicke funkce, ktere sympy zna sam — neprepisovat je na Symbol.
            math_fns = {
                "sin", "cos", "tan", "cot", "sec", "csc",
                "asin", "acos", "atan", "acot", "asec", "acsc", "atan2",
                "sinh", "cosh", "tanh", "coth", "sech", "csch",
                "asinh", "acosh", "atanh", "acoth", "asech", "acsch",
                "exp", "log", "ln", "sqrt", "Abs", "abs", "floor", "ceiling",
                "Min", "Max", "pi", "e",
            } | fn_aliases.keys()

            # Vsechny identifikatory ve vzorci preventivne pretypovat na Symbol,
            # aby sympy nezamenil napr. 'Q'/'S'/'O' za vestavene AssumptionKeys.
            ids = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", formula)) - math_fns
            ldict = {v: symbols(v) for v in ids}
            ldict.update(fn_aliases)
            # implicit_multiplication: '2l' → '2*l', '2(x+y)' → '2*(x+y)'.
            # Nepouzivame split_symbols, takze viceznakove identifikatory ('R_0', 'theta')
            # zustavaji jednim symbolem.
            transformations = standard_transformations + (implicit_multiplication,)
            expr = parse_expr(formula, local_dict=ldict, transformations=transformations)
        except Exception as e:
            raise ValueError(f"Vypocet '{name}': neparsovatelny vzorec '{formula}' — {e}")

        free = {str(s) for s in expr.free_symbols}
        free_vars = free & vars_in_set.keys()
        free_consts = free & set(constants)
        missing = free - vars_in_set.keys() - set(constants)
        if missing:
            raise ValueError(f"Vypocet '{name}': v setu chybi promenne {sorted(missing)}")

        if not free_vars:
            raise ValueError(
                f"Vypocet '{name}': vzorec musi obsahovat aspon jednu promennou (ne jen konstanty)"
            )

        lengths = {len(vars_in_set[v].values) for v in free_vars}
        if len(lengths) > 1:
            raise ValueError(f"Vypocet '{name}': vstupy maji ruzne delky {sorted(lengths)}")
        n = lengths.pop()

        const_subs = {Symbol(c): float(constants[c]) for c in free_consts}

        from sympy import zoo, oo

        computed = []
        errors = []
        for i in range(n):
            subs = {Symbol(v): float(vars_in_set[v].values[i]) for v in free_vars}
            subs.update(const_subs)
            try:
                substituted = expr.subs(subs)
                if substituted in (zoo, oo, -oo):
                    raise ValueError("deleni nulou")
                val = float(substituted.evalf())
                if not math.isfinite(val):
                    raise ValueError("vysledek neni konecne cislo (mimo definicni obor)")
                computed.append(val)
            except ValueError as e:
                computed.append(float("nan"))
                errors.append(f"Vypocet '{name}', radek {i + 1}: {e}")
            except Exception as e:
                computed.append(float("nan"))
                errors.append(f"Vypocet '{name}', radek {i + 1}: vyhodnoceni selhalo ({type(e).__name__})")

        display_name = f"{name} [{unit}]" if unit else name
        dm = DerivedMeasurement(display_name, computed)

        # Propagace nejistoty (GUM) pres parcialni derivace pri <x_i> = mean(x_i).
        # Pokud nejaka derivace selze (nedef. v stredni hodnote, sympy chyba),
        # caption fallback na statistickou u_A z per-radkovych hodnot.
        try:
            means_at = {Symbol(v): float(vars_in_set[v].mean) for v in free_vars}
            means_at.update(const_subs)

            mean_at = expr.subs(means_at)
            if mean_at in (zoo, oo, -oo):
                raise ValueError("propagace selhala — nedef. v <x>")
            mean_propagated = float(mean_at.evalf())

            if math.isfinite(mean_propagated):
                uc_sq = 0.0
                for v in free_vars:
                    partial = expr.diff(Symbol(v))
                    partial_val = float(partial.subs(means_at).evalf())
                    uc_sq += (partial_val * float(vars_in_set[v].u_c)) ** 2
                uc_propagated = math.sqrt(uc_sq)
                dm.mean_propagated = mean_propagated
                dm.uc_propagated = uc_propagated
        except Exception:
            pass  # tichy fallback na statisticke u_A

        self.add(dm)
        self.computation_errors.extend(errors)
        return errors

    @classmethod
    def from_dict(cls, data: dict, u_B_map: dict = None):
        u_B_map = u_B_map or {}
        ms = cls()
        for key, values in data.items():
            u_b = u_B_map.get(key, 0.0)
            ms.add(Measurement(key, values, u_B=u_b))
        return ms

    @classmethod
    def from_numpy(cls, promena: np.ndarray, u_B_map: dict = None):
        u_B_map = u_B_map or {}
        ms = cls()
        for row in promena:
            key, data = row
            u_b = u_B_map.get(key, 0.0)
            ms.add(Measurement(key, data, u_B=u_b))
        return ms

    def si_normalize(self) -> "MeasurementSet":
        new = MeasurementSet()
        for m in self.measurements:
            new.add(m.si_normalize())
        return new

    def convert_units(self, conversions: dict) -> "MeasurementSet":
        """conversions: {"I": "A", "U": "mV"} — podle 'var' části názvu."""
        from objects.units import extract_name_unit

        new = MeasurementSet()
        for m in self.measurements:
            var, _ = extract_name_unit(m.name)
            if var in conversions:
                new.add(m.convert_to(conversions[var]))
            else:
                new.add(m)
        return new

    def get(self, name: str) -> Measurement:
        for m in self.measurements:
            if m.name == name:
                return m
        raise KeyError(f"Měření '{name}' nenalezeno")

    @property
    def names(self) -> list:
        return [m.name for m in self.measurements]

    def to_dict(self) -> dict:
        return {m.name: [m.mean, m.u_c] for m in self.measurements}

    def to_raw_dict(self) -> dict:
        return {m.name: list(m.values) for m in self.measurements}

    def to_numpy(self) -> np.ndarray:
        return np.array([[m.name, list(m.values)] for m in self.measurements], dtype=object)

    def print_results(self, quiet: bool = False):
        if not quiet:
            print(f"Zpracovávám údaje pro hodnoty {', '.join(self.names)}")
        for m in self.measurements:
            m.print_result(quiet=quiet)

    def to_latex_table(
        self,
        source_file: str = None,
        custom_caption: str = None,
        custom_label: str = None,
        dry_run: bool = False,
        include_rel_uncertainty: bool = False,
        precision_source: str = "u_c",
    ):
        import math
        import os
        import re

        dir_name = "latex_output"
        folder_path = Path(dir_name).resolve()
        folder_path.mkdir(parents=True, exist_ok=True)
        from objects.units import extract_name_unit as _eu, display_unit as _du

        def _latex_header(name):
            var, unit = _eu(name)
            if unit is None or not str(unit).strip():
                return f"${var} [-]$"
            return f"${var} \\, [\\mathrm{{{_du(unit)}}}]$"

        headers = [_latex_header(m.name) for m in self.measurements]
        body = []
        for m in self.measurements:
            p = max(m.precision_for(precision_source), 1)
            body.append([
                "-" if (isinstance(v, float) and math.isnan(v))
                else f"{round_half_up(v, p):.{p}f}".replace(".", _dec_sep())
                for v in m.values
            ])
        rows = list(zip_longest(*body, fillvalue="-"))
        col_widths = []
        for i in range(len(headers)):
            column_cells = [str(r[i]) for r in rows]
            max_w = max(len(headers[i]), max([len(c) for c in column_cells] or [0]))
            col_widths.append(max_w)

        formatted_headers = [headers[i].ljust(col_widths[i]) for i in range(len(headers))]
        header_line = " & ".join(formatted_headers) + " \\\\ \\midrule"
        formatted_rows = []
        for row in rows:
            formatted_cells = [str(row[i]).ljust(col_widths[i]) for i in range(len(row))]
            formatted_rows.append(" & ".join(formatted_cells) + " \\\\")

        # Auto-caption: prvni radek = custom_caption nebo nazev souboru,
        # za nim VELIČINA = $(mean \pm u_c)$ per line.
        caption_parts = []
        if custom_caption:
            caption_parts.append(custom_caption)
        elif source_file:
            caption_parts.append(os.path.basename(source_file))
        from objects.units import extract_name_unit, display_unit

        import math as _math

        for m in self.measurements:
            if not _math.isfinite(m.mean):
                continue
            p = max(m.precision_for(precision_source), 1)
            mean_str = f"{round_half_up(m.mean, p):.{p}f}".replace(".", _dec_sep())
            err_str = f"{round_half_up(m.u_c, p):.{p}f}".replace(".", _dec_sep())
            var, unit = extract_name_unit(m.name)
            var_clean = var.replace("$", "")
            u_disp = display_unit(unit)
            line = f"${var_clean} = ({mean_str} \\pm {err_str})\\,\\mathrm{{{u_disp}}}$"
            if include_rel_uncertainty and _math.isfinite(m.mean) and m.mean != 0:
                rel_pct = abs(m.u_c / m.mean) * 100.0
                if 0.001 <= rel_pct < 1000:
                    rel_str = f"{rel_pct:.3g}\\,\\%"
                else:
                    rel_str = f"{rel_pct:.2e}\\,\\%"
                # Vlozit "(\delta = X.X %)" za stats radek
                line += f"\\quad(\\delta_{{{var_clean}}} = {rel_str})"
            caption_parts.append(line)
        from utils import balance_math_braces

        caption_parts = [balance_math_braces(p) for p in caption_parts]
        caption = " \\\\ ".join(caption_parts)

        def _write_caption(f, parts, indent):
            if len(parts) <= 1:
                f.write(indent + "\\caption{" + (parts[0] if parts else "") + "}\n")
                return
            f.write(indent + "\\caption{\n")
            for i, p in enumerate(parts):
                suffix = " \\\\" if i < len(parts) - 1 else ""
                f.write(indent + "\t" + p + suffix + "\n")
            f.write(indent + "}\n")

        if custom_label:
            label = custom_label
        elif source_file:
            base = os.path.splitext(os.path.basename(source_file))[0]
            label = re.sub(r'[^a-zA-Z0-9_]', '_', base).lower()
            label = re.sub(r'_+', '_', label).strip('_')
        else:
            label = input("Jakej label chceš míti: ")

        tex_File_Name = f"table_{'_'.join([m.name.split(' ')[0] for m in self.measurements])}.tex"
        tex_File_Path = folder_path / tex_File_Name
        if dry_run:
            print(color_print.YELLOW + f"[DRY-RUN] Soubor by byl zapsán: {tex_File_Path}" + color_print.END)
            print(f"  Caption: {caption[:80]}...")
            print(f"  Label:   tab:{label}")
            print(f"  Řádků:   {len(rows)}")
            return

        n_rows = len(rows)
        n_cols_tab = len(headers)
        tabular_spec = "@{}" + "c" * n_cols_tab + "@{}"
        with locked_open(tex_File_Path, "w", encoding="utf-8") as f:
            if n_rows <= 20:
                f.write("\\begin{table}[H]\n")
                f.write("\t\\centering\n")
                f.write("\t\\small\n")
                f.write("\t\\begin{tabular}{" + tabular_spec + "}\n")
                f.write("\t\t\\toprule\n")
                f.write("\t\t" + header_line + "\n")
                for r in formatted_rows:
                    f.write("\t\t" + r + "\n")
                f.write("\t\t\\bottomrule\n")
                f.write("\t\\end{tabular}\n")
                f.write("\t\\captionsetup{justification=centering}\n")
                _write_caption(f, caption_parts, "\t")
                f.write("\t\\label{tab:" + label + "}\n")
                f.write("\\end{table}\n")
            else:
                n_sub = min(4, math.ceil(n_rows / 25))
                width = {2: "0.48", 3: "0.31", 4: "0.23"}[n_sub]
                chunk = math.ceil(n_rows / n_sub)
                f.write("\\begin{table}[H]\n")
                f.write("\t\\centering\n")
                f.write("\t\\small\n")
                for i in range(n_sub):
                    start = i * chunk
                    end = min(start + chunk, n_rows)
                    sub_rows = formatted_rows[start:end]
                    f.write(f"\t\\begin{{subtable}}[t]{{{width}\\textwidth}}\n")
                    f.write("\t\t\\centering\n")
                    f.write("\t\t\\begin{tabular}{" + tabular_spec + "}\n")
                    f.write("\t\t\t\\toprule\n")
                    f.write("\t\t\t" + header_line + "\n")
                    for r in sub_rows:
                        f.write("\t\t\t" + r + "\n")
                    f.write("\t\t\t\\bottomrule\n")
                    f.write("\t\t\\end{tabular}\n")
                    f.write("\t\\end{subtable}\n")
                    if i < n_sub - 1:
                        f.write("\t\\hfill\n")

                f.write("\n\t\\vspace{0.3cm}\n")
                f.write("\t\\captionsetup{justification=centering}\n")
                _write_caption(f, caption_parts, "\t")
                f.write("\t\\label{tab:" + label + "}\n")
                f.write("\\end{table}\n")

        print(color_print.GREEN + f"Soubor {tex_File_Name} uložen na adrese{color_print.END}")
        print("└──" + str(tex_File_Path))

    def to_csv(self, path: str):
        """Exportuje výsledky do CSV: name, mean, u_A, u_B, u_c, n"""
        import csv

        with locked_open(path, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "mean", "u_A", "u_B", "u_c", "n"])
            for m in self.measurements:
                writer.writerow([m.name, m.mean, m.u_A, m.u_B, m.u_c, m.n])

    def to_json(self) -> str:
        import json

        return json.dumps(
            {
                m.name: {"mean": m.mean, "u_A": m.u_A, "u_B": m.u_B, "u_c": m.u_c, "n": m.n}
                for m in self.measurements
            },
            indent=2,
            ensure_ascii=False,
        )

    def __len__(self):
        return len(self.measurements)

    def __iter__(self):
        return iter(self.measurements)

    def __getitem__(self, index):
        return self.measurements[index]

    def __repr__(self):
        return f"MeasurementSet({', '.join(repr(m) for m in self.measurements)})"
