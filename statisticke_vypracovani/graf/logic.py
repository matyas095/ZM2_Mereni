import math;
from utils import get_Promeny, color_print, return_Cislo_Krat_10_Na, extract_variables, contains_substring, return_FirstWord, extract_latex_logic;
import numpy as np;
import matplotlib.pyplot as plt;
from scipy.optimize import curve_fit;
from sklearn.metrics import r2_score;
import math;
from pathlib import Path;
from sympy import symbols, lambdify, latex, log;
from sympy.parsing.sympy_parser import parse_expr;
from sympy.parsing.latex import parse_latex;
from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer;
from statisticke_vypracovani.base import Method;

def clean_latex(text):
    if not isinstance(text, str):
        text = latex(text);

    text = text.replace(r'\mathtt', '').replace(r'\text', '').replace(r'\mathrm', '');

    text = text.replace('backslashtext', '').replace('backslash', '');
    text = text.replace(r'\\', '').replace('\\', '');
    text = text.replace('Ohm', r'\Omega').replace('Omega', r'\Omega');

    text = text.replace('{', '').replace('}', '');

    return text.strip();


def smart_parse(rovnice_str):
    """Detekuje LaTeX nebo Python a vrátí SymPy objekt."""
    rovnice_str = rovnice_str.strip("'\"");
    if "\\" in rovnice_str:
        return parse_latex(rovnice_str), extract_latex_logic(rovnice_str);
    return parse_expr(rovnice_str, local_dict={ name: symbols(name) for name in extract_variables(rovnice_str) }), extract_variables(rovnice_str);

def linear(x, a, b): return a * x + b;
def quadratic(x, a, b, c): return a * x**2 + b * x + c;
def exponential(x, a, b): return a * np.exp(b / x);
def power_law(x, a, b): return a * x**b;

def najdi_nejlepsi_fit(x, y):
    modely = {
        "Lineární": linear,
        "Kvadratický": quadratic,
        "Exponenciální": exponential,
        "Mocninný": power_law
    }

    vysledky = {}

    for jmeno, func in modely.items():
        try:
            popt, _ = curve_fit(func, x, y, maxfev=2000)
            y_pred = func(x, *popt)
            score = r2_score(y, y_pred)
            vysledky[jmeno] = (score, popt, func)
        except:
            continue

    nejlepsi = max(vysledky, key=lambda k: vysledky[k][0])
    return nejlepsi, vysledky[nejlepsi]

class Graf(Method):
    name = "graf";
    description = "2D/3D graf s volitelným fitem a rovnicí";

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru s daty",
                "required": True,
                "is_file": True
            },
            {
                "flags": ["-n", "--name"],
                "help": "Název grafu",
                "required": True,
                "type": str
            },
            {
                "flags": ["-r", "--rovnice"],
                "help": "Závislost prvních linky dat do druhé",
                "required": False,
                "type": str
            },
            {
                "flags": ["-p", "--parametr"],
                "help": "Vypočítá data jako 2D graf dle parametru f(x), funguje jenom s -r [--rovnice]",
                "type": str
            },
            {
                "flags": ["-log", "--logaritmicky"],
                "help": "Zobrazí y-ovou osu v logaritmickým měřítku",
                "action": "store_true"
            },
            {
                "flags": ["-f", "--fit"],
                "help": "Udělá fit dle zadaného stavu. Format -f [linearni, kvadraticky, exponenciali, mocninny]\nNapř.: .. -f kvadraticky",
                "choices": ["linearni", "kvadraticky", "exponencialni", "mocninny"],
                "default": None,
                "required": False
            }
        ];

    def _args_Rovnice_2D_Slice(self, PROMENA, args, pathToDir, fix_var='y', fix_value=None):
        x_vals = PROMENA[0, 1];
        y_vals = PROMENA[1, 1];

        try:
            nazev_rovnice, rovnice = args.rovnice.split("=");
        except Exception:
            raise Exception("Chyba v rovnici, ve vztahu musí být všechny datové vstupy!; Formát: 'VELIČINA=VZTAH");
        y, variables = smart_parse(rovnice);
        var_x = return_FirstWord(PROMENA[0, 0]);
        var_y = return_FirstWord(PROMENA[1, 0]);
        if(not contains_substring(var_x, variables) or not contains_substring(var_y, variables)):
            raise ValueError(f"Chybí mi veličiny v rovnici...");

        variables = [return_FirstWord(PROMENA[0, 0]), return_FirstWord(PROMENA[1, 0])];
        f = lambdify(variables, y, 'numpy');

        plt.figure(figsize=(8, 5));

        if fix_var == 'y':
            val = fix_value if fix_value is not None else y_vals[len(y_vals)//2];
            Z_slice = [f(x, val) for x in x_vals];

            plt.plot(x_vals, Z_slice, 'b-', linewidth=2);
            plt.xlabel(f"${clean_latex(PROMENA[0,0])}$");
            plt.title(f"Řez grafem pro ${clean_latex(PROMENA[1,0])} = {val}$");

        else:
            val = fix_value if fix_value is not None else x_vals[len(x_vals)//2];
            Z_slice = [f(val, y) for y in y_vals];

            plt.plot(y_vals, Z_slice, 'r-', linewidth=2);
            plt.xlabel(f"${clean_latex(PROMENA[1,0])}$");
            plt.title(f"Řez grafem pro ${clean_latex(PROMENA[0,0])} = {val}$");

        plt.ylabel(f"${clean_latex(nazev_rovnice)}$");
        plt.grid(True, alpha=0.3);
        plt.savefig(f'{pathToDir}/{args.name}_2D_slice.svg', bbox_inches='tight');
        plt.show();

    def _args_Rovnice(self, PROMENA, args, pathToDir):
        try:
            nazev_rovnice, rovnice = args.rovnice.split("=");
        except Exception:
            raise Exception("Chyba v rovnici, ve vztahu musí být všechny datové vstupy!; Formát: 'VELIČINA=VZTAH");
        y, variables = smart_parse(rovnice);

        if getattr(args, 'parametr', False):
            sym_list = [symbols(args.parametr)];
            f = lambdify(sym_list, y, 'numpy');
            U_range = np.linspace(min(PROMENA[0, 1]), max(PROMENA[0, 1]), 1000);

            plt.figure(figsize=(9, 6));
            plt.plot(U_range, f(U_range), label=rf'$R = {latex(y)}$');
            plt.xlabel(PROMENA[0, 0]);
            plt.ylabel(nazev_rovnice);
            plt.title(args.name);
            plt.grid(alpha=0.3);
            plt.legend();
            plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight', pad_inches=0.5);
            plt.show();

            print(f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{args.name}{color_print.END} a rovnicí {color_print.UNDERLINE}{nazev_rovnice}={rovnice}{color_print.END}" +
              f"se uložil do souboru:\n└──{pathToDir}/{args.name}.svg");
            plt.close();

            return;

        x_vals = np.array(PROMENA[0, 1]);
        y_vals = np.array(PROMENA[1, 1]);

        try:
            nazev_rovnice, rovnice = args.rovnice.split("=");
        except Exception:
            raise Exception("Chyba v rovnici, ve vztahu musí být všechny datové vstupy!; Formát: 'VELIČINA=VZTAH");
        y, variables = smart_parse(rovnice);
        var_x = return_FirstWord(PROMENA[0, 0]);
        var_y = return_FirstWord(PROMENA[1, 0]);
        if(not contains_substring(var_x, variables) or not contains_substring(var_y, variables)):
            raise ValueError(f"Chybí mi veličiny v rovnici...");

        variables = [return_FirstWord(PROMENA[0, 0]), return_FirstWord(PROMENA[1, 0])];
        f = lambdify(variables, y, 'numpy');

        X_vals, Y_vals = np.meshgrid(x_vals, y_vals);

        Z_vals = f(X_vals, Y_vals);

        fig = plt.figure(figsize=(10, 7));
        fig.subplots_adjust(left=0.1, right=0.85, bottom=0.1, top=0.85)
        ax = fig.add_subplot(111, projection='3d');
        ax.set_box_aspect(None, zoom=0.8) # type: ignore

        surf = ax.plot_surface(X_vals, Y_vals, Z_vals, cmap='coolwarm', antialiased=True); # type: ignore

        ax.set_xlabel(f"${clean_latex(PROMENA[0,0])}$", labelpad=10)
        ax.set_ylabel(f"${clean_latex(PROMENA[1,0])}$", labelpad=10)

        z_label_text = clean_latex(nazev_rovnice)
        ax.set_zlabel(f"${z_label_text}$", labelpad=20)

        title_str = f"Závislost ${z_label_text}$ na ${variables[0]}$ a ${variables[1]}$\nVztah: ${z_label_text}$ = ${latex(y).replace('mathtt', 'mathrm')}$"
        ax.set_title(title_str, pad=25)

        fig.colorbar(surf, shrink=0.5, aspect=15, pad=0.05);

        plt.show();

        elev = ax.elev;
        azim = ax.azim;

        ax.view_init(elev=elev, azim=azim);
        fig.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight', pad_inches=0.5);

        print(f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{args.name}{color_print.END} a rovnicí {color_print.UNDERLINE}{nazev_rovnice}={rovnice}{color_print.END} \
              se uložil do souboru:\n└──{pathToDir}/{args.name}.svg");

    def _prep_Plot(self, PROMENA, args, pathToDir, ignoreRovnice = False):
        if(args.rovnice and not ignoreRovnice):
            out = self._args_Rovnice(PROMENA, args, pathToDir);
            return;

        aritm = AritmetickyPrumer();

        x_Range = np.array(PROMENA[0, 1]);
        x_key = PROMENA[0, 0];
        y_Range = np.array(PROMENA[1, 1]);
        y_key = PROMENA[1, 0];

        if(args.logaritmicky and args.fit):
            modely_fitu = {
                "linearni": linear,
                "kvadraticky": quadratic,
                "exponencialni": exponential,
                "mocninny": power_law
            };

            plt.figure(figsize=(9, 6));

            y_Range = np.log(y_Range);
            aritm_result = aritm.run({x_key: x_Range}, False);
            print(aritm_result)

            print(najdi_nejlepsi_fit(x_Range, y_Range));
            print(aritm_result[x_key][-1])

            popt, pcov = curve_fit(modely_fitu[args.fit], x_Range, y_Range, absolute_sigma=True, sigma=aritm_result[x_key][-1] / np.array(PROMENA[1, 1]));

            label_text = f"Fit {args.fit}: " + ", ".join([f"${return_Cislo_Krat_10_Na(p)}$" for p in popt]);

            plt.plot(x_Range, modely_fitu[args.fit](x_Range, *popt), 'b-',
                 label=label_text);

            plt.errorbar(x_Range, y_Range, yerr=aritm_result[x_key][-1] / np.array(PROMENA[1, 1]), fmt='o', capsize=3, color='darkred', label='Chyba měření');
            plt.xlabel(f'{x_key}');
            plt.ylabel(f'{y_key}');
            plt.title(args.name);
            plt.legend();
            plt.grid(alpha=0.3);
            plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight');
            plt.show();
            plt.close();
            print(f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{args.name}{color_print.END} se uložil do souboru:\n└──{pathToDir}/{args.name}.svg")
            return;

        plt.figure(figsize=(9, 6));
        plt.plot(x_Range, y_Range, 'b-',
                  label=f'Graf závislosti');

        plt.xlabel(f'{x_key}');
        plt.ylabel(f'{y_key}');
        plt.title(args.name);
        plt.legend();
        plt.grid(alpha=0.3);
        plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight');
        plt.show();
        plt.close();
        print(f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{args.name}{color_print.END} se uložil do souboru:\n└──{pathToDir}/{args.name}.svg")

    def run(self, args):
        PROMENA = get_Promeny(args);

        dir_name = "grafy_metoda_graf";

        folder_path = Path(dir_name).resolve();
        folder_path.mkdir(parents=True, exist_ok=True);

        print(f"Zpracovávám údaje pro hodnoty {', '.join(PROMENA[:, 0])}");
        return self._prep_Plot(PROMENA, args, str(folder_path));
