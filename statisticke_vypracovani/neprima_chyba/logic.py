import json;
from sympy import symbols, lambdify;
from sympy.parsing.sympy_parser import parse_expr;
import numpy as np;
from utils import color_print, return_Cislo_Krat_10_Na, extract_variables;
from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer, _parse_typ_b;
from statisticke_vypracovani.base import Method;
from objects.input_parser import InputParser;

class NeprimaChyba(Method):
    name = "neprima_chyba";
    description = "Nepřímá chyba měření (propagace chyby přes parciální derivace)";

    def validate(self, args) -> None:
        import os;
        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)");
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje");
        if args.input.endswith(".xlsx"):
            if not getattr(args, 'rovnice', None):
                raise ValueError("Pro .xlsx vstup je nutný flag -r [--rovnice]");
            if "=" not in args.rovnice:
                raise ValueError("V rovnici chybí oddělovač '='; Formát: 'VELIČINA=VZTAH'");

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru s daty",
                "required": True,
                "is_file": True
            },
            {
                "flags": ["-r", "--rovnice"],
                "help": "Specifikace rovnice pokud chybí",
                "type": str
            },
            {
                "flags": ["-k", "--konstanty"],
                "help": "Dospecifikuje konstanty, mimo input file. Ve tvaru dict: '{ \"KEY\": ... }'",
                "type": json.loads
            },
            {
                "flags": ["-tb", "--typ-b"],
                "help": "Nejistota typu B jako JSON: '{\"t\": 0.5, \"U\": [1, \"rovnomerne\"]}'",
                "required": False,
                "type": json.loads
            }
        ];

    def _derivace(self, data, aritmety=None):
        aritm = AritmetickyPrumer();
        resulte = [];
        if not aritmety:
            aritmety = aritm.run(data["ELEMENTY"], False);
        for name_rce, v in data["FUNKCE"].items():
            rce = v;
            local_const_dict = v.get("FUNC_KONSTANTY", {}) if isinstance(v, dict) else {};
            try:
                if isinstance(v, dict):
                    rce = v.get("__value__");
                variables = extract_variables(rce, list(local_const_dict.keys()));
            except TypeError as e:
                raise TypeError(f"Někde v FUNC_KONSTANTY je chyba {e}");

            missing_vars = set(extract_variables(rce, list(local_const_dict))) - set(data["ELEMENTY"].keys())
            if len(missing_vars) > 0:
                raise Exception(f"Chybí mi tu data v 'ELEMENTY':\n{color_print.BOLD}{missing_vars}{color_print.END}");

            SYMPY_RESERVED = {'I', 'E', 'pi', 'oo', 'S', 'N', 'O', 'Q', 'C'};
            collisions = SYMPY_RESERVED & set(variables);
            if collisions:
                raise ValueError(
                    f"Názvy proměnných {sorted(collisions)} kolidují s vyhrazenými symboly SymPy "
                    f"(I=imag. jednotka, E=Eulerovo č., pi, oo=∞, S, N, O, Q, C). "
                    f"Přejmenuj je v ELEMENTY i FUNKCE (např. I → I_c)."
                );

            sym_map = {name: symbols(name) for name in variables};
            y = parse_expr(rce, local_dict=sym_map); # type: ignore
            derivatives = [y.diff(x) for x in sym_map];

            variablesNEW = variables + list(local_const_dict.keys());
            f = lambdify(variablesNEW, derivatives, 'numpy');

            chyby = [x for x in aritmety.keys()];
            sorted_keys = sorted(aritmety.keys());

            test = [[aritmety[k][0]] for k in sorted_keys] + \
                    [[local_const_dict[n]] for n in variablesNEW if n in local_const_dict] + \
                    [[aritmety[k][-1]] for k in sorted_keys];

            for val in zip(*test): # type: ignore
                toEval = val[:len(val) - len(chyby)];
                ch = val[-len(chyby):];

                clean_results = [float(x) for x in f(*toEval)];
                sig_R = np.sqrt(sum([(x * y) ** 2 for x, y in zip(clean_results, ch)]));
                resulte.append((name_rce, sig_R, return_Cislo_Krat_10_Na(sig_R)));

        for k, cislo, na_desatou in resulte:
            print(color_print.BOLD + k + color_print.END);
            print(f"└──{color_print.UNDERLINE}Chyba{color_print.END} = {na_desatou} ({cislo})");
            print("-" * 100);

        return resulte;

    def _xlsxExtension(self, args):
        if not args.rovnice:
            raise ValueError("Chybí tag -r [--rovnice] pro rovnici, pro soubor .xlsx.");
        if "=" not in args.rovnice:
            raise ValueError("V rovnici [-r; --rovnice] chybí oddělovač =; Mějte formát VELIČINA=ROVNICE");

        try:
            nazev_rce, rce = args.rovnice.split("=");
        except Exception:
            raise ValueError("Chyba v rovnice [-r; --rovnice]");

        u_B_map = _parse_typ_b(getattr(args, 'typ_b', None));
        data = InputParser.parse_xlsx(args.input);

        aritmety = {};
        for m in data:
            u_b = u_B_map.get(m.name, 0.0);
            import math;
            u_c = math.sqrt(m.u_A**2 + u_b**2);
            aritmety[m.name] = [m.mean, u_c];

        return self._derivace(
            {
                "FUNKCE": {
                    nazev_rce: {
                        "__value__": rce,
                        **( {"FUNC_KONSTANTY": args.konstanty} if args.konstanty else {} )
                    }
                },
                "ELEMENTY": data.to_raw_dict()
            },
            aritmety
        );

    def _txt_with_typ_b(self, args):
        u_B_map = _parse_typ_b(getattr(args, 'typ_b', None));
        parsed = InputParser.parse_indent(args.input);

        if u_B_map and "ELEMENTY" in parsed:
            data = InputParser.parse_dict(parsed["ELEMENTY"], u_B_map);
            aritmety = {m.name: [m.mean, m.u_c] for m in data};
            return self._derivace(parsed, aritmety);

        return self._derivace(parsed);

    def run(self, args, do_print=True):
        match args.input:
            case name if name.endswith(".xlsx"):
                return self._xlsxExtension(args);
            case _:
                if getattr(args, 'typ_b', None):
                    return self._txt_with_typ_b(args);
                return self._derivace(InputParser.parse_indent(args.input));
