from typing import Any
import re
import math
from itertools import zip_longest
from pathlib import Path
from utils import color_print, balance_math_braces, locked_open
from statisticke_vypracovani.base import Method


class JoinTables(Method):
    name = "join_tables"
    description = "Horizontálně spojí dvě LaTeX tabulky (včetně caption a label)"

    def validate(self, args) -> None:
        import os

        inputs = getattr(args, 'input', None)
        if not inputs or len(inputs) != 2:
            raise ValueError("join_tables vyžaduje 2 vstupní soubory: -i IN1 IN2")
        for f in inputs:
            if not os.path.isfile(f):
                raise ValueError(f"Soubor '{f}' neexistuje")

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Dva .tex soubory: IN1 IN2",
                "required": True,
                "nargs": 2,
                "type": str,
            },
            {
                "flags": ["-o", "--output"],
                "help": "Název výstupu (BEZ PŘÍPONY)",
                "required": False,
                "default": "joined_table",
                "type": str,
            },
            {
                "flags": ["-m", "--mode"],
                "help": "horizontal: spojí vedle sebe | match: spáruje podle 1. sloupce",
                "choices": ["horizontal", "match"],
                "default": "horizontal",
            },
            {
                "flags": ["--si-normalize"],
                "help": "Převede jednotky v tabulkách na základní SI",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--convert-units"],
                "help": "Převede jednotky dle JSON: '{\"I\":\"A\"}'",
                "required": False,
                "type": str,
            },
        ]

    @staticmethod
    def _extract_braced(content: str, command: str) -> str:
        r"""Extrahuje obsah \command{...} s vyváženými závorkami."""
        idx = content.find(command + "{")
        if idx == -1:
            return ""
        start = idx + len(command) + 1
        depth = 1
        i = start
        while i < len(content) and depth > 0:
            c = content[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return content[start:i].strip()
            i += 1
        return content[start:].strip()

    def _parse_tex(self, path):
        with open(path, encoding='utf-8') as f:
            content = f.read()

        tabulars = re.findall(
            r'\\begin\{tabular\}\{((?:[^{}]|\{[^}]*\})+)\}(.*?)\\end\{tabular\}', content, re.DOTALL
        )
        if not tabulars:
            raise Exception(f"Nenalezena tabulka v {path}")

        col_spec = tabulars[0][0]
        header_cells = None
        data_rows = []
        for spec, body in tabulars:
            body = re.sub(r'\\(top|bottom)rule', '', body)
            parts = body.split(r'\midrule', 1)
            if len(parts) != 2:
                continue
            header_str, data_str = parts
            cells = [c.strip().rstrip('\\').strip() for c in header_str.split('&')]
            cells = [c for c in cells if c]
            if header_cells is None:
                header_cells = cells

            for line in data_str.strip().split('\\\\'):
                row_cells = [c.strip() for c in line.split('&')]
                row_cells = [c for c in row_cells if c]
                if row_cells:
                    row_cells = [re.sub(r'(\d)\.(\d)', r'\1,\2', c) for c in row_cells]
                    data_rows.append(row_cells)

        if header_cells is None:
            raise Exception(f"Chybí \\midrule v {path}")

        caption = self._extract_braced(content, "\\caption")
        label_raw = self._extract_braced(content, "\\label")
        label = label_raw[4:] if label_raw.startswith("tab:") else label_raw
        return col_spec, header_cells, data_rows, caption, label

    @staticmethod
    def _apply_unit_conversion(
        headers: list,
        rows: list,
        caption: str,
        si_normalize: bool = False,
        convert_units: dict = None,
        dec_sep: str = ",",
    ):
        """Převede jednotky v LaTeX headerech a hodnotách. Vrátí (new_headers, new_rows, warnings)."""
        from objects.units import (
            parse_tex_header,
            format_tex_header,
            parse_unit,
            convert_factor,
            convert_str_value,
            caption_contains_unit,
        )

        convert_units = convert_units or {}
        warnings = []
        new_headers = list(headers)
        factors_per_col = [1.0] * len(headers)
        for i, h in enumerate(headers):
            var, unit = parse_tex_header(h)
            if unit is None:
                continue

            target_unit = None
            factor = 1.0
            if var in convert_units:
                target_unit = convert_units[var]
                factor = convert_factor(unit, target_unit)
            elif si_normalize:
                factor, base = parse_unit(unit)
                if factor != 1.0:
                    target_unit = base

            if target_unit is not None and target_unit != unit:
                new_headers[i] = format_tex_header(var, target_unit)
                factors_per_col[i] = factor
                if caption_contains_unit(caption, unit):
                    warnings.append(
                        f"{color_print.YELLOW}Varování:{color_print.END} caption obsahuje '{unit}' — nepřevedlo se automaticky, zvaž --caption"
                    )

        new_rows = []
        for row in rows:
            new_row = [
                convert_str_value(v, factors_per_col[i], dec_sep) if i < len(factors_per_col) else v
                for i, v in enumerate(row)
            ]
            new_rows.append(new_row)

        return new_headers, new_rows, warnings

    def run(self, args: Any, do_print: bool = True) -> dict:
        import json

        spec1, head1, rows1, cap1, lab1 = self._parse_tex(args.input[0])
        spec2, head2, rows2, cap2, lab2 = self._parse_tex(args.input[1])
        si_norm = getattr(args, 'si_normalize', False)
        conv_raw = getattr(args, 'convert_units', None)
        conv_map = json.loads(conv_raw) if conv_raw else {}
        if si_norm or conv_map:
            head1, rows1, warns1 = self._apply_unit_conversion(head1, rows1, cap1, si_norm, conv_map)
            head2, rows2, warns2 = self._apply_unit_conversion(head2, rows2, cap2, si_norm, conv_map)
            for w in warns1 + warns2:
                print(w)

        mode = getattr(args, 'mode', 'horizontal')
        if mode == "match":
            if head1[0] != head2[0]:
                raise Exception(
                    f"Pro --mode match musí být 1. sloupec stejný: IN1='{head1[0]}' vs IN2='{head2[0]}'"
                )

            in2_lookup = {row[0]: row[1:] for row in rows2 if row}
            merged_head = head1 + head2[1:]
            n_cols = len(merged_head)
            n_extra = len(head2) - 1
            merged_rows = []
            matched = 0
            for row in rows1:
                key = row[0]
                if key in in2_lookup:
                    extra = in2_lookup[key]
                    matched += 1
                else:
                    extra = ["-"] * n_extra
                while len(extra) < n_extra:
                    extra = extra + ["-"]
                merged_rows.append(" & ".join(row + extra) + " \\\\")

            info_line = f"└──řádky:   {len(rows1)} (shod: {matched}/{len(rows1)})"
        else:
            merged_head = head1 + head2
            n_cols = len(merged_head)
            merged_rows = []
            for row in zip_longest(rows1, rows2, fillvalue=None):
                r1 = row[0] if row[0] is not None else ["-"] * len(head1)
                r2 = row[1] if row[1] is not None else ["-"] * len(head2)
                while len(r1) < len(head1):
                    r1 = r1 + ["-"]
                while len(r2) < len(head2):
                    r2 = r2 + ["-"]
                merged_rows.append(" & ".join(r1 + r2) + " \\\\")

            info_line = f"└──řádky:   max({len(rows1)}, {len(rows2)}) = {max(len(rows1), len(rows2))}"

        merged_spec = "@{}" + "c" * n_cols + "@{}"
        merged_header = " & ".join(merged_head) + " \\\\ \\midrule"

        def _balance_dollars(s):
            if s.count("$") % 2 == 1:
                s = s + "$"
            return s

        cap1 = _balance_dollars(cap1)
        cap2 = _balance_dollars(cap2)
        if cap1 and cap2:
            merged_caption = cap1 + " \\\\\n " + cap2
        else:
            merged_caption = cap1 or cap2

        merged_caption = balance_math_braces(merged_caption)
        if lab1 and lab2:
            merged_label = f"tab:{lab1}_{lab2}"
        elif lab1 or lab2:
            merged_label = f"tab:{lab1 or lab2}"
        else:
            merged_label = "tab:joined"

        folder_path = Path("outputs").resolve()
        folder_path.mkdir(parents=True, exist_ok=True)
        output_path = folder_path / f"{args.output}.tex"
        n_rows = len(merged_rows)
        with locked_open(output_path, "w", encoding="utf-8") as f:
            if n_rows <= 20:
                f.write("\\begin{table}[H]\n")
                f.write("\t\\centering\n")
                f.write("\t\\small\n")
                f.write("\t\\begin{tabular}{" + merged_spec + "}\n")
                f.write("\t\t\\toprule\n")
                f.write("\t\t" + merged_header + "\n")
                for r in merged_rows:
                    f.write("\t\t" + r + "\n")
                f.write("\t\t\\bottomrule\n")
                f.write("\t\\end{tabular}\n")
                f.write("\t\\caption{" + merged_caption + "}\n")
                f.write("\t\\label{" + merged_label + "}\n")
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
                    sub_rows = merged_rows[start:end]
                    f.write(f"\t\\begin{{subtable}}[t]{{{width}\\textwidth}}\n")
                    f.write("\t\t\\centering\n")
                    f.write("\t\t\\begin{tabular}{" + merged_spec + "}\n")
                    f.write("\t\t\t\\toprule\n")
                    f.write("\t\t\t" + merged_header + "\n")
                    for r in sub_rows:
                        f.write("\t\t\t" + r + "\n")
                    f.write("\t\t\t\\bottomrule\n")
                    f.write("\t\t\\end{tabular}\n")
                    f.write("\t\\end{subtable}\n")
                    if i < n_sub - 1:
                        f.write("\t\\hfill\n")

                f.write("\n\t\\vspace{0.3cm}\n")
                f.write("\t\\captionsetup{justification=centering}\n")
                f.write("\t\\caption{" + merged_caption + "}\n")
                f.write("\t\\label{" + merged_label + "}\n")
                f.write("\\end{table}\n")

        if do_print:
            print(f"{color_print.GREEN}Tabulky spojeny ({mode}){color_print.END}: {output_path}")
            print(f"└──sloupce: {n_cols}")
            print(info_line)

        return {"mode": mode, "cols": n_cols, "rows": len(merged_rows), "output": str(output_path)}
