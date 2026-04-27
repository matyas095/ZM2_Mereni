from typing import Any
import json
from sympy import symbols, lambdify, latex
from sympy.parsing.sympy_parser import parse_expr
import numpy as np
from utils import color_print, return_Cislo_Krat_10_Na, extract_variables, gum_round, parse_composite_unit, pick_display
from objects.units import extract_name_unit
from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer, _parse_typ_b
from statisticke_vypracovani.base import Method
from objects.input_parser import InputParser


class NeprimaChyba(Method):
    name = "neprima_chyba"
    description = "Nepřímá chyba měření (propagace chyby přes parciální derivace)"

    def validate(self, args) -> None:
        import os

        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)")
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje")
        if args.input.endswith(".xlsx"):
            if not getattr(args, 'rovnice', None):
                raise ValueError("Pro .xlsx vstup je nutný flag -r [--rovnice]")
            if "=" not in args.rovnice:
                raise ValueError("V rovnici chybí oddělovač '='; Formát: 'VELIČINA=VZTAH'")

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru s daty",
                "required": True,
                "is_file": True,
            },
            {"flags": ["-r", "--rovnice"], "help": "Specifikace rovnice pokud chybí", "type": str},
            {
                "flags": ["-k", "--konstanty"],
                "help": "Dospecifikuje konstanty, mimo input file. Ve tvaru dict: '{ \"KEY\": ... }'",
                "type": json.loads,
            },
            {
                "flags": ["-tb", "--typ-b"],
                "help": "Nejistota typu B. Opakovatelný flag: -tb t=0.5 -tb U=1:rovnomerne, nebo JSON",
                "required": False,
                "action": "append",
                "type": str,
            },
        ]

    def _derivace(self, data, aritmety=None):
        aritm = AritmetickyPrumer()
        resulte = []
        if not aritmety:
            aritmety = aritm.run(data["ELEMENTY"], False)
        for full_name_rce, v in data["FUNKCE"].items():
            name_rce, unit_str = extract_name_unit(full_name_rce)
            rce = v
            local_const_dict = v.get("FUNC_KONSTANTY", {}) if isinstance(v, dict) else {}
            try:
                if isinstance(v, dict):
                    rce = v.get("__value__")
                variables = extract_variables(rce, list(local_const_dict.keys()))
            except TypeError as e:
                raise TypeError(f"Někde v FUNC_KONSTANTY je chyba {e}")

            missing_vars = set(extract_variables(rce, list(local_const_dict))) - set(data["ELEMENTY"].keys())
            if len(missing_vars) > 0:
                raise Exception(
                    f"Chybí mi tu data v 'ELEMENTY':\n{color_print.BOLD}{missing_vars}{color_print.END}"
                )

            SYMPY_RESERVED = {'I', 'E', 'pi', 'oo', 'S', 'N', 'O', 'Q', 'C'}
            collisions = SYMPY_RESERVED & set(variables)
            if collisions:
                raise ValueError(
                    f"Názvy proměnných {sorted(collisions)} kolidují s vyhrazenými symboly SymPy "
                    f"(I=imag. jednotka, E=Eulerovo č., pi, oo=∞, S, N, O, Q, C). "
                    f"Přejmenuj je v ELEMENTY i FUNKCE (např. I → I_c)."
                )

            sym_map = {name: symbols(name) for name in variables}
            y = parse_expr(rce, local_dict=sym_map)  # type: ignore
            latex_str = latex(y)  # LaTeX zdroj pro vložení do protokolu
            derivatives = [y.diff(x) for x in sym_map]
            variablesNEW = variables + list(local_const_dict.keys())
            f = lambdify(variablesNEW, derivatives, 'numpy')
            f_val = lambdify(variablesNEW, y, 'numpy')  # samotná funkce — pro střední hodnotu
            chyby = list(aritmety.keys())
            sorted_keys = sorted(aritmety.keys())
            test = (
                [[aritmety[k][0]] for k in sorted_keys]
                + [[local_const_dict[n]] for n in variablesNEW if n in local_const_dict]
                + [[aritmety[k][-1]] for k in sorted_keys]
            )
            for val in zip(*test, strict=False):  # type: ignore
                toEval = val[: len(val) - len(chyby)]
                ch = val[-len(chyby) :]
                clean_results = np.asarray([float(x) for x in f(*toEval)], dtype=np.float64)
                ch_arr = np.asarray(ch, dtype=np.float64)
                sig_R = float(np.sqrt(np.sum((clean_results * ch_arr) ** 2)))
                mean_R = float(np.asarray(f_val(*toEval), dtype=np.float64))
                resulte.append((name_rce, sig_R, return_Cislo_Krat_10_Na(sig_R), mean_R, latex_str, unit_str))

        for k, cislo, na_desatou, mean_R, latex_str, unit_str in resulte:
            print(color_print.BOLD + k + color_print.END)
            print(f"├──{color_print.UNDERLINE}LaTeX{color_print.END}    = ${k} = {latex_str}$")
            print(
                f"├──{color_print.UNDERLINE}Hodnota{color_print.END}  = "
                f"{return_Cislo_Krat_10_Na(mean_R)} ({mean_R})"
            )
            print(f"├──{color_print.UNDERLINE}Chyba{color_print.END}    = {na_desatou} ({cislo})")
            orig_disp = gum_round(mean_R, cislo)
            if unit_str:
                try:
                    factor, si_unit = parse_composite_unit(unit_str)
                    if factor != 1.0:
                        si_disp = gum_round(mean_R * factor, cislo * factor)
                        chosen, chosen_unit = pick_display(orig_disp, si_disp, unit_str, si_unit)
                    else:
                        chosen, chosen_unit = orig_disp, unit_str
                except Exception:
                    chosen, chosen_unit = orig_disp, unit_str
                print(f"└──{color_print.UNDERLINE}Výsledek{color_print.END} = {chosen} {chosen_unit}")
            else:
                print(f"└──{color_print.UNDERLINE}Výsledek{color_print.END} = {orig_disp}")
            print("-" * 100)

        return resulte

    def _toml_input(self, args):
        """Parsuje TOML soubor — alternativa k indentovanemu .txt formatu.

        Ocekavana struktura:
            [veliciny.<nazev>]
            unit = "<jednotka>"      # volitelne, nepouziva se pri propagaci
            hodnoty = [<float>, ...]
            typ_b = <float>                         # primy u_B
            typ_b = { a = <float>, distribuce = "rovnomerne" | "trojuhelnikove" | "normalni" }

            [funkce.<nazev>]
            vzorec = "<vyraz>"
            unit = "<jednotka>"      # napr. "g*mm**-3"; aktivuje SI prevod
            konstanty = { <jmeno> = <float>, ... }   # volitelne (vc. pi)
        """
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # Python 3.10 fallback
        import math

        with open(args.input, "rb") as f:
            cfg = tomllib.load(f)

        veliciny = cfg.get("veliciny", {})
        funkce_cfg = cfg.get("funkce", {})
        if not veliciny:
            raise ValueError("TOML musi obsahovat alespon jednu sekci [veliciny.<nazev>]")
        if not funkce_cfg:
            raise ValueError("TOML musi obsahovat alespon jednu sekci [funkce.<nazev>]")

        elementy = {}
        aritmety = {}
        has_type_b = False

        for name, vinfo in veliciny.items():
            values = vinfo.get("hodnoty")
            if values is None:
                raise ValueError(f"Velicina '{name}' nema klic 'hodnoty'")
            elementy[name] = list(values)

            tb = vinfo.get("typ_b")
            if tb is not None:
                has_type_b = True
                if isinstance(tb, (int, float)):
                    u_B = float(tb)
                elif isinstance(tb, dict):
                    a = float(tb.get("a", 0.0))
                    dist = str(tb.get("distribuce", "rovnomerne")).strip()
                    if dist == "rovnomerne":
                        u_B = a / math.sqrt(3)
                    elif dist == "trojuhelnikove":
                        u_B = a / math.sqrt(6)
                    elif dist == "normalni":
                        u_B = a / 2.0
                    else:
                        raise ValueError(
                            f"Velicina '{name}': nezname rozlozeni '{dist}'. "
                            f"Pouzij 'rovnomerne', 'trojuhelnikove' nebo 'normalni'."
                        )
                else:
                    raise ValueError(
                        f"Velicina '{name}': typ_b musi byt cislo nebo "
                        f"dict {{ a = ..., distribuce = ... }}"
                    )

                n = len(values)
                mean = sum(values) / n if n else 0.0
                if n > 1:
                    var = sum((x - mean) ** 2 for x in values) / (n * (n - 1))
                    u_A = math.sqrt(var)
                else:
                    u_A = 0.0
                u_c = math.sqrt(u_A**2 + u_B**2)
                aritmety[name] = [mean, u_c]

        funkce = {}
        for fname, finfo in funkce_cfg.items():
            formula = finfo.get("vzorec")
            if formula is None:
                raise ValueError(f"Funkce '{fname}' nema klic 'vzorec'")
            unit = finfo.get("unit")
            key = f"{fname} [{unit}]" if unit else fname
            body = {"__value__": formula}
            consts = finfo.get("konstanty")
            if consts:
                body["FUNC_KONSTANTY"] = dict(consts)
            funkce[key] = body

        data = {"ELEMENTY": elementy, "FUNKCE": funkce}
        if has_type_b:
            return self._derivace(data, aritmety)
        return self._derivace(data)

    def _xlsxExtension(self, args):
        if not args.rovnice:
            raise ValueError("Chybí tag -r [--rovnice] pro rovnici, pro soubor .xlsx.")
        if "=" not in args.rovnice:
            raise ValueError("V rovnici [-r; --rovnice] chybí oddělovač =; Mějte formát VELIČINA=ROVNICE")

        try:
            nazev_rce, rce = args.rovnice.split("=")
        except Exception:
            raise ValueError("Chyba v rovnice [-r; --rovnice]")

        u_B_map = _parse_typ_b(getattr(args, 'typ_b', None))
        data = InputParser.parse_xlsx(args.input)
        aritmety = {}
        for m in data:
            u_b = u_B_map.get(m.name, 0.0)
            import math

            u_c = math.sqrt(m.u_A**2 + u_b**2)
            aritmety[m.name] = [m.mean, u_c]

        return self._derivace(
            {
                "FUNKCE": {
                    nazev_rce: {
                        "__value__": rce,
                        **({"FUNC_KONSTANTY": args.konstanty} if args.konstanty else {}),
                    }
                },
                "ELEMENTY": data.to_raw_dict(),
            },
            aritmety,
        )

    def _txt_with_typ_b(self, args):
        u_B_map = _parse_typ_b(getattr(args, 'typ_b', None))
        parsed = InputParser.parse_indent(args.input)
        if u_B_map and "ELEMENTY" in parsed:
            data = InputParser.parse_dict(parsed["ELEMENTY"], u_B_map)
            aritmety = {m.name: [m.mean, m.u_c] for m in data}
            return self._derivace(parsed, aritmety)

        return self._derivace(parsed)

    def run(self, args: Any, do_print: bool = True) -> dict:
        match args.input:
            case name if name.endswith(".xlsx"):
                return self._xlsxExtension(args)
            case name if name.endswith(".toml"):
                return self._toml_input(args)
            case _:
                if getattr(args, 'typ_b', None):
                    return self._txt_with_typ_b(args)
                return self._derivace(InputParser.parse_indent(args.input))
