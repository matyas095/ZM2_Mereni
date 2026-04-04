import math;
from sympy import symbols, lambdify;
from sympy.parsing.sympy_parser import parse_expr;
from sympy.parsing.latex import parse_latex;
import numpy as np;
import re;
from utils import color_print, return_Cislo_Krat_10_Na;
from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer;
from statisticke_vypracovani.base import Method;

import pandas as pd;

def extract_variables(formula_str, toIgnore = []):
    ignored_functions = ['log', 'ln', 'sin', 'cos', 'tan', 'exp', 'sqrt', 'abs'] + toIgnore;

    ignore_pattern = r'\b(?:' + '|'.join(ignored_functions) + r')\b';
    regex_pattern = r'\b(?!' + ignore_pattern + r'|[0-9])[a-zA-Z_][a-zA-Z0-9_]*\b';

    variables = re.findall(regex_pattern, formula_str);

    return sorted(list(set(variables)));

def universal_indent_mapper(input_path):
    result = {};
    path = {-4: result};

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue;

            indent = len(line) - len(line.lstrip());
            clean_line = line.strip();

            if "=" in clean_line:
                key, val = [x.strip() for x in clean_line.split("=", 1)];
                try:
                    parts = [float(x.strip()) for x in val.split(",") if x.strip()];

                    if len(parts) == 1:
                        processed_val = parts[0];
                    else:
                        processed_val = parts;
                except ValueError:
                    processed_val = val;
            else:
                key = clean_line;
                processed_val = {};

            parent_level = indent - 4;
            while parent_level not in path and parent_level > -4:
                parent_level -= 4;

            parent_dict = path[parent_level];

            parent_dict[key] = processed_val;

            if isinstance(processed_val, dict):
                path[indent] = processed_val;
            else:
                path[indent] = parent_dict[key] = {
                    "__value__": processed_val
                };

    return result;

def cleanup_structure(d):
    """Recursively simplifies dicts that only contain a __value__."""
    if not isinstance(d, dict): return d;

    if "__value__" in d and len(d) == 1: return d["__value__"];

    return {k: cleanup_structure(v) for k, v in d.items()};

def get__value__(funkce_dict, key):
    entry = funkce_dict.get(key);
    if isinstance(entry, dict): return entry.get("__value__");
    return entry;

class NeprimaChyba(Method):
    name = "neprima_chyba";
    description = "Nepřímá chyba měření (propagace chyby přes parciální derivace)";

    def get_args_info(self):
        import json;
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
            }
        ];

    def _derivace(self, data, aritmety = None):
        aritm = AritmetickyPrumer();
        resulte = [];
        if(not aritmety): aritmety = aritm.run(data["ELEMENTY"], False);
        for name_rce, v in data["FUNKCE"].items():
            rce = v;
            variables = None;
            local_const_dict = v.get("FUNC_KONSTANTY", {}) if isinstance(v, dict) else {};
            funkcni_konstanty = [];
            try:
                if(isinstance(v, dict)):
                    funkcni_konstanty = v.get("FUNC_KONSTANTY", {});
                    rce = v.get("__value__");
                variables = extract_variables(rce, list(local_const_dict.keys()));
            except TypeError as e:
                raise TypeError(f"Někde v FUNC_KONSTANTY je chyba {e}");
            except Exception as e:
                raise Exception(e);

            missing_vars = set(extract_variables(rce, list(local_const_dict))) - set(data["ELEMENTY"].keys())
            if(len(missing_vars) > 0):
                missing_str = "\n".join(missing_vars);

                raise Exception(f"Chybí mi tu data v 'ELEMENTY':\n{color_print.BOLD}{missing_vars}{color_print.END}");

            sym_map = { name: symbols(name) for name in variables };
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

        return;

    def _xlsxExtension(self, args):
        if(not args.rovnice): raise ValueError("Chybí tag -r [--rovnice] pro rovnici, pro soubor .xlsx.");
        if("=" not in args.rovnice): raise ValueError("V rovnici [-r; --rovnice] chybí oddělovač =; Mějte formát VELIČINA=ROVNICE")

        try:
            nazev_rce, rce = args.rovnice.split("=");
        except Exception as e:
            raise ValueError("Chyba v rovnice [-r; --rovnice]");

        df = pd.read_excel(args.input).dropna(how='all');
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')];

        keys = df.columns.tolist();
        return self._derivace(
            {
                "FUNKCE": {
                    nazev_rce: {
                        "__value__": rce,
                        **( { "FUNC_KONSTANTY": args.konstanty } if args.konstanty else {} )
                    }
                },
                "ELEMENTY": {
                    key: df[key].astype(float).tolist() for key in keys
                }
            },
            {
                key: [
                    df[key].mean(),
                    df[key].std() / np.sqrt(len(df))
                ] for key in keys
            }
        );

    def run(self, args):
        match args.input:
            case name if(name.endswith(".xlsx")):
                self._xlsxExtension(args);

            case _:
                return self._derivace(cleanup_structure(universal_indent_mapper(args.input)));
