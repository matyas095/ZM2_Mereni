from typing import Any
import numpy as np
from pathlib import Path
from utils import color_print, locked_open, extract_variables
from statisticke_vypracovani.base import Method
from objects.input_parser import InputParser
from objects.measurement import Measurement
from objects.measurement_set import MeasurementSet


class Derivace(Method):
    name = "derivace"
    description = "Numerická derivace dat (central differences) nebo symbolická derivace z TOML"

    def validate(self, args) -> None:
        import os

        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)")
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje")

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru (.txt pro numerickou, .toml pro symbolickou derivaci)",
                "required": True,
                "is_file": True,
            },
            {
                "flags": ["-x", "--x-col"],
                "help": "Název sloupce s nezávislou proměnnou (výchozí: první sloupec)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-y", "--y-col"],
                "help": "Název sloupce s závislou proměnnou (výchozí: druhý sloupec)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-o", "--output"],
                "help": "Výstupní soubor bez přípony (výchozí: derivace_output)",
                "required": False,
                "default": "derivace_output",
                "type": str,
            },
        ]

    def _toml_symbolic(self, args) -> dict:
        """Symbolická derivace z TOML.

        Formát stejný jako u `neprima_chyba`:
            [veliciny.<nazev>]
            hodnoty = [...]                     # ignoruje se zde
            typ_b = ...                         # ignoruje se zde

            [funkce.<nazev>]
            vzorec = "<výraz>"
            unit = "<jednotka>"                 # volitelné, ignoruje se zde
            konstanty = { name = value, ... }   # volitelné — tyto symboly se nederivují

        Derivuje se podle každé veličiny z [veliciny.*], která se ve vzorci
        vyskytuje a není uvedená v `konstanty`.
        """
        try:
            import tomllib
        except ImportError:  # Python 3.10 fallback
            import tomli as tomllib  # type: ignore

        from sympy import symbols, latex, asin, acos, atan, asinh, acosh, atanh, E as Euler
        from sympy.parsing.sympy_parser import (
            parse_expr,
            standard_transformations,
            implicit_multiplication,
        )

        with open(args.input, "rb") as f:
            cfg = tomllib.load(f)

        veliciny = cfg.get("veliciny", {}) or {}
        funkce_cfg = cfg.get("funkce", {}) or {}
        if not funkce_cfg:
            raise ValueError("TOML musí obsahovat alespoň jednu sekci [funkce.<nazev>]")

        velicina_names = set(veliciny.keys())
        SYMPY_RESERVED = {'I', 'pi', 'oo', 'S', 'N', 'O', 'Q', 'C'}
        transformations = standard_transformations + (implicit_multiplication,)

        out: dict[str, dict[str, str]] = {}
        for fname, finfo in funkce_cfg.items():
            formula = finfo.get("vzorec")
            if not formula:
                raise ValueError(f"Funkce '{fname}' nemá klíč 'vzorec'")
            konstanty = finfo.get("konstanty", {}) or {}

            # Vsechny symboly v rovnici (bez matematickych funkci a bez konstant)
            all_in_formula = extract_variables(formula, list(konstanty.keys()))
            collisions = SYMPY_RESERVED & set(all_in_formula)
            if collisions:
                raise ValueError(
                    f"Funkce '{fname}': názvy {sorted(collisions)} kolidují s vyhrazenými "
                    f"symboly SymPy (I, pi, oo, S, N, O, Q, C). Přejmenuj je."
                )

            # Promenne k derivovani: prunik formule ∩ veliciny.
            # Pokud uzivatel neuvedl zadnou velicinu, derivuj podle vsech symbolu ve vzorci.
            if velicina_names:
                deriv_vars = [v for v in all_in_formula if v in velicina_names]
                ignored = [v for v in all_in_formula if v not in velicina_names]
            else:
                deriv_vars = list(all_in_formula)
                ignored = []

            if not deriv_vars:
                print(
                    color_print.YELLOW
                    + f"Funkce '{fname}' nemá žádnou proměnnou k derivaci "
                    + f"(vzorec: {formula})"
                    + color_print.END
                )
                continue

            sym_map = {name: symbols(name) for name in all_in_formula}
            parse_dict = dict(sym_map)
            parse_dict.update({
                "arcsin": asin, "arccos": acos, "arctan": atan,
                "arcsinh": asinh, "arccosh": acosh, "arctanh": atanh,
                "e": Euler,
            })
            # Konstanty necht zustanou jako pojmenovane Symboly v derivaci.
            for k in konstanty:
                parse_dict.setdefault(k, symbols(k))

            try:
                expr = parse_expr(formula, local_dict=parse_dict, transformations=transformations)
            except Exception as e:
                raise ValueError(f"Funkce '{fname}': chyba parseru sympy: {e}") from e

            derivs = [(v, expr.diff(sym_map[v])) for v in deriv_vars]

            # --- Vystup ---
            print(color_print.BOLD + fname + color_print.END)
            print(f"├──{color_print.UNDERLINE}Vzorec{color_print.END}      = {formula}")
            print(f"├──{color_print.UNDERLINE}LaTeX{color_print.END}       = ${fname} = {latex(expr)}$")
            print(f"├──{color_print.UNDERLINE}Derivuji dle{color_print.END} = {', '.join(deriv_vars)}")
            if ignored:
                print(
                    f"├──{color_print.UNDERLINE}Ignoruji{color_print.END}    = "
                    f"{', '.join(ignored)} (nejsou ve [veliciny.*])"
                )
            if konstanty:
                const_disp = ", ".join(f"{k}={v}" for k, v in konstanty.items())
                print(f"├──{color_print.UNDERLINE}Konstanty{color_print.END}   = {const_disp}")

            out_per_func: dict[str, str] = {}
            for i, (v, d) in enumerate(derivs):
                connector = "└──" if i == len(derivs) - 1 else "├──"
                label = f"∂{fname}/∂{v}"
                print(f"{connector}{color_print.UNDERLINE}{label}{color_print.END} = {d}")
                indent = "    " if i == len(derivs) - 1 else "│   "
                print(f"{indent}└─LaTeX: {latex(d)}")
                out_per_func[v] = str(d)
            print("-" * 100)
            out[fname] = out_per_func

        return out

    def run(self, args: Any, do_print: bool = True) -> dict:
        if str(args.input).lower().endswith(".toml"):
            return self._toml_symbolic(args)

        data = InputParser.from_file(args.input)
        x_name = getattr(args, 'x_col', None) or data[0].name
        y_name = getattr(args, 'y_col', None) or data[1].name
        x_m = data.get(x_name)
        y_m = data.get(y_name)
        x = x_m.values
        y = y_m.values
        if len(x) != len(y):
            raise ValueError(f"Různá délka sloupců: {x_name}={len(x)}, {y_name}={len(y)}")
        if len(x) < 3:
            raise ValueError("Derivace potřebuje aspoň 3 body")

        dy_dx = np.gradient(y, x)
        deriv_name = f"d{y_name}/d{x_name}"
        result = MeasurementSet()
        result.add(Measurement(x_name, x.tolist()))
        result.add(Measurement(deriv_name, dy_dx.tolist()))
        if do_print:
            print(f"Derivace {y_name} podle {x_name}")
            print(f"├──Počet bodů: {len(x)}")
            print(f"├──Rozsah {x_name}: [{x.min():.4g}, {x.max():.4g}]")
            print(f"├──Průměrná derivace: {dy_dx.mean():.4g}")
            print(f"└──Min/max derivace: [{dy_dx.min():.4g}, {dy_dx.max():.4g}]")
            print("-" * 100)
            folder = Path("outputs").resolve()
            folder.mkdir(parents=True, exist_ok=True)
            output_name = getattr(args, 'output', 'derivace_output') + ".txt"
            with locked_open(folder / output_name, 'w', encoding='utf-8') as f:
                f.write(f"{x_name}=" + ",".join(str(v) for v in x) + "\n")
                f.write(f"{deriv_name}=" + ",".join(str(v) for v in dy_dx) + "\n")
            print(f"{color_print.GREEN}Výstup:{color_print.END} {folder / output_name}")

        return result.to_dict()
