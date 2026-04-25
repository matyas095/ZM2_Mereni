import numpy as np
from pathlib import Path
from itertools import zip_longest
from utils import color_print, locked_open
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

    def add(self, measurement: Measurement):
        self.measurements.append(measurement)
        return self

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
            return f"${var} [{_du(unit)}]$"

        headers = [_latex_header(m.name) for m in self.measurements]
        body = []
        for m in self.measurements:
            p = max(m.precision, 1)
            body.append([f"{round(v, p):.{p}f}".replace(".", _dec_sep()) for v in m.values])
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

        # Auto-caption: soubor + VELIČINA = $(mean \pm u_c)$ per line
        caption_parts = []
        if source_file:
            caption_parts.append(os.path.basename(source_file))
        from objects.units import extract_name_unit, display_unit

        for m in self.measurements:
            p = max(m.precision, 1)
            mean_str = f"{round(m.mean, p):.{p}f}".replace(".", _dec_sep())
            err_str = f"{round(m.u_c, p):.{p}f}".replace(".", _dec_sep())
            var, unit = extract_name_unit(m.name)
            var_clean = var.replace("$", "")
            u_disp = display_unit(unit)
            caption_parts.append(f"${var_clean} = ({mean_str} \\pm {err_str})\\,\\mathrm{{{u_disp}}}$")
        caption = " \\\\ ".join(caption_parts)
        from utils import balance_math_braces

        caption = balance_math_braces(caption)
        if custom_caption:
            caption = custom_caption

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
                f.write("\t\\caption{" + caption + "}\n")
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
                f.write("\t\\caption{" + caption + "}\n")
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
