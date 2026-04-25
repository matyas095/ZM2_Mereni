import json
import math
import numpy as np
from pathlib import Path
from utils import color_print
from statisticke_vypracovani.base import Method
from statisticke_vypracovani.join_tables.logic import JoinTables


class FormatTable(Method):
    name = "format_table"
    description = "Upraví existující LaTeX tabulku (jednotky, caption, precision, subtables)"

    def validate(self, args) -> None:
        import os

        inp = getattr(args, 'input', None)
        if not inp:
            raise ValueError("Chybí vstupní .tex soubor (-i)")
        if not os.path.isfile(inp):
            raise ValueError(f"Soubor '{inp}' neexistuje")

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Vstupní .tex soubor",
                "required": True,
                "is_file": True,
                "type": str,
            },
            {
                "flags": ["-o", "--output"],
                "help": "Název výstupu bez přípony (výchozí: formatted_table)",
                "required": False,
                "default": "formatted_table",
                "type": str,
            },
            {
                "flags": ["--si-normalize"],
                "help": "Převede jednotky na základní SI",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--convert-units"],
                "help": "Převede jednotky dle JSON: '{\"I\":\"A\"}'",
                "required": False,
                "type": str,
            },
            {"flags": ["--caption"], "help": "Nahradí caption", "required": False, "type": str},
            {"flags": ["--label"], "help": "Nahradí label (bez tab: prefix)", "required": False, "type": str},
            {
                "flags": ["--precision"],
                "help": "Počet desetinných míst pro přeformátování hodnot",
                "required": False,
                "type": int,
            },
            {
                "flags": ["--decimal-separator"],
                "help": "Desetinný oddělovač: ',' nebo '.'",
                "required": False,
                "choices": [",", "."],
                "default": ",",
            },
            {
                "flags": ["--rows-per-subtable"],
                "help": "Řádků na subtable (0 = jedna tabulka, >0 = rozdělit)",
                "required": False,
                "type": int,
                "default": 25,
            },
            {
                "flags": ["--dry-run"],
                "help": "Neukládat, jen zobrazit co by se stalo",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--append-stats"],
                "help": "Přidá do captionu průměr ± chybu pro každý sloupec",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--no-caption-stats"],
                "help": "Vynutí vypnutí auto-statistik v captionu",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--auto-scale"],
                "help": "Automaticky zvolí vhodný SI prefix pro každý sloupec",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--interactive"],
                "help": "Interaktivní náhled — umožňuje postupně měnit parametry",
                "required": False,
                "action": "store_true",
            },
        ]

    def _compute_stats(self, headers, rows, dec_sep=","):
        """Pro každý sloupec spočítá aritmetický průměr + chybu, vrátí list LaTeX řádků."""
        import math
        from objects.units import parse_tex_header

        n_cols = len(headers)
        lines = []
        for i in range(n_cols):
            vals = []
            for row in rows:
                if i >= len(row):
                    continue
                v = row[i].strip()
                if v == "-" or not v:
                    continue
                try:
                    vals.append(float(v.replace(",", ".")))
                except ValueError:
                    pass

            if len(vals) < 2:
                continue

            n = len(vals)
            arr = np.asarray(vals, dtype=np.float64)
            mean = float(np.mean(arr))
            variance = float(np.sum((arr - mean) ** 2))
            u_A = math.sqrt(variance / (n * (n - 1)))
            # precision z chyby (0-2): najdi první p, kde round(u_A, p) != 0
            if u_A == 0:
                p = 2
            else:
                p = 2
                for pp in range(3):
                    if round(abs(u_A), pp) != 0:
                        p = pp
                        break
            # pokud je chyba > 1, použij 0 decimals (např. 286 ne 286.0)
            if abs(u_A) >= 1:
                p = 0

            var, unit = parse_tex_header(headers[i])
            from objects.units import display_unit

            mean_str = f"{round(mean, p):.{p}f}".replace(".", dec_sep)
            err_str = f"{round(u_A, p):.{p}f}".replace(".", dec_sep)
            var_clean = var.replace("$", "")
            u_disp = display_unit(unit)
            line = f"${var_clean} = ({mean_str} \\pm {err_str})\\,\\mathrm{{{u_disp}}}$"
            lines.append(line)

        return lines

    def _apply_auto_scale(self, headers, rows, dec_sep):
        """Pro každý sloupec s jednotkou zvolí vhodný SI prefix podle velikosti hodnot."""
        from objects.units import (
            parse_tex_header,
            format_tex_header,
            auto_scale_exponent,
            PREFIX_FOR_EXPONENT,
            parse_unit,
            convert_str_value,
        )

        new_headers = list(headers)
        new_rows = [list(r) for r in rows]
        for i, h in enumerate(headers):
            var, unit = parse_tex_header(h)
            if unit is None:
                continue
            _, base_unit = parse_unit(unit)
            nums = []
            for r in rows:
                if i < len(r) and r[i] != "-":
                    try:
                        nums.append(float(r[i].replace(",", ".")))
                    except ValueError:
                        pass
            if not nums:
                continue
            exp = auto_scale_exponent(nums)
            if exp == 0 or exp not in PREFIX_FOR_EXPONENT:
                continue
            new_unit = PREFIX_FOR_EXPONENT[exp] + base_unit
            scale = 10 ** (-exp)
            new_headers[i] = format_tex_header(var, new_unit)
            for r in new_rows:
                if i < len(r) and r[i] != "-":
                    r[i] = convert_str_value(r[i], scale, dec_sep)
        return new_headers, new_rows

    def _reformat_numbers(self, rows, precision, dec_sep):
        new_rows = []
        for row in rows:
            new_row = []
            for v in row:
                if v == "-" or not v.strip():
                    new_row.append(v)
                    continue
                try:
                    num = float(v.replace(",", "."))
                    new_row.append(f"{num:.{precision}f}".replace(".", dec_sep))
                except ValueError:
                    new_row.append(v)
            new_rows.append(new_row)
        return new_rows

    def _write_tex(self, path, col_spec, headers, rows, caption, label, rows_per_subtable):
        header_line = " & ".join(headers) + " \\\\ \\midrule"
        formatted_rows = [" & ".join(r) + " \\\\" for r in rows]
        n_rows = len(rows)
        with open(path, "w", encoding="utf-8") as f:
            if rows_per_subtable <= 0 or n_rows <= rows_per_subtable or n_rows <= 20:
                f.write("\\begin{table}[H]\n")
                f.write("\t\\centering\n")
                f.write("\t\\small\n")
                f.write("\t\\begin{tabular}{" + col_spec + "}\n")
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
                n_sub = min(4, math.ceil(n_rows / rows_per_subtable))
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
                    f.write("\t\t\\begin{tabular}{" + col_spec + "}\n")
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

    def _interactive_loop(self, args):
        """Jednoduchý interaktivní režim: opakovaně zobrazuje náhled a bere volby."""
        print(f"{color_print.BOLD}format_table — interaktivní režim{color_print.END}")
        print("Každá změna přepočítá náhled. 's' uloží, 'q' ukončí.\n")
        while True:
            print(f"{color_print.CYAN}Aktuální nastavení:{color_print.END}")
            print(f"  si_normalize     = {getattr(args, 'si_normalize', False)}")
            print(f"  auto_scale       = {getattr(args, 'auto_scale', False)}")
            print(f"  precision        = {getattr(args, 'precision', None)}")
            print(f"  decimal_separator= {getattr(args, 'decimal_separator', ',')}")
            print(f"  caption          = {(getattr(args, 'caption', None) or '<auto>')[:50]}")
            print(f"  label            = {getattr(args, 'label', None) or '<auto>'}")
            print(f"  append_stats     = {getattr(args, 'append_stats', False)}")
            print()
            print("Volby: [n] si_normalize  [a] auto_scale  [p] precision  [d] dec. sep.")
            print("       [c] caption       [l] label       [t] append_stats")
            print("       [s] uložit        [q] zavřít")
            choice = input("Volba: ").strip().lower()
            if choice == "q":
                return None
            elif choice == "s":
                return args
            elif choice == "n":
                args.si_normalize = not getattr(args, 'si_normalize', False)
            elif choice == "a":
                args.auto_scale = not getattr(args, 'auto_scale', False)
            elif choice == "p":
                try:
                    args.precision = int(input("Precision (číslo): ").strip())
                except ValueError:
                    args.precision = None
            elif choice == "d":
                sep = input("Oddělovač (, nebo .): ").strip()
                if sep in (",", "."):
                    args.decimal_separator = sep
            elif choice == "c":
                args.caption = input("Nový caption: ").strip() or None
            elif choice == "l":
                args.label = input("Nový label: ").strip() or None
            elif choice == "t":
                args.append_stats = not getattr(args, 'append_stats', False)
            print("")

    def run(self, args: object, do_print: bool = True) -> dict:
        if getattr(args, 'interactive', False):
            result = self._interactive_loop(args)
            if result is None:
                print("Zrušeno uživatelem.")
                return {}
            args = result
            args.interactive = False

        jt = JoinTables()
        col_spec, headers, rows, caption, label = jt._parse_tex(args.input)
        dec_sep = getattr(args, 'decimal_separator', ',') or ','
        si_norm = getattr(args, 'si_normalize', False)
        conv_raw = getattr(args, 'convert_units', None)
        conv_map = json.loads(conv_raw) if conv_raw else {}
        user_caption_override = getattr(args, 'caption', None) is not None
        if si_norm or conv_map:
            headers, rows, warnings = jt._apply_unit_conversion(
                headers, rows, caption, si_norm, conv_map, dec_sep
            )
            if not user_caption_override:
                for w in warnings:
                    print(w)

        if getattr(args, 'auto_scale', False):
            headers, rows = self._apply_auto_scale(headers, rows, dec_sep)

        precision = getattr(args, 'precision', None)
        if precision is not None:
            rows = self._reformat_numbers(rows, precision, dec_sep)
        elif dec_sep == ".":
            rows = [[v.replace(",", ".") for v in row] for row in rows]

        new_caption = getattr(args, 'caption', None) or caption
        new_label = getattr(args, 'label', None) or label
        append_stats = getattr(args, 'append_stats', False) and not getattr(args, 'no_caption_stats', False)
        if append_stats:
            stats_lines = self._compute_stats(headers, rows, dec_sep)
            if stats_lines:
                sep = " \\\\\n        " if new_caption.strip() else ""
                new_caption = new_caption.rstrip() + sep + (" \\\\\n        ".join(stats_lines))
                from utils import balance_math_braces

                new_caption = balance_math_braces(new_caption)

        if getattr(args, 'dry_run', False):
            if do_print:
                print(f"{color_print.YELLOW}[DRY-RUN]{color_print.END}")
                print(f"  Sloupce: {len(headers)} - {', '.join(headers)}")
                print(f"  Řádků: {len(rows)}")
                print(f"  Caption: {new_caption[:80]}{'...' if len(new_caption) > 80 else ''}")
                print(f"  Label: tab:{new_label}")
            return {"headers": headers, "rows": rows, "caption": new_caption, "label": new_label}

        folder = Path("latex_output").resolve()
        folder.mkdir(parents=True, exist_ok=True)
        output_path = folder / f"{args.output}.tex"
        rps = getattr(args, 'rows_per_subtable', 25) or 25
        self._write_tex(output_path, col_spec, headers, rows, new_caption, new_label, rps)
        if do_print:
            print(f"{color_print.GREEN}Tabulka naformátována{color_print.END}: {output_path}")
            print(f"└──sloupce: {len(headers)}, řádků: {len(rows)}")

        return {
            "headers": headers,
            "rows": rows,
            "caption": new_caption,
            "label": new_label,
            "output": str(output_path),
        }
