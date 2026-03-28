import math;
from utils import get_Promeny, color_print, return_Cislo_Krat_10_Na, extract_variables, contains_substring, return_FirstWord, extract_latex_logic;
import numpy as np;
import matplotlib.pyplot as plt;
from scipy.optimize import curve_fit;
import math;
from pathlib import Path;
from sympy import symbols, lambdify, latex, log, E, pi, exp;
from sympy.parsing.sympy_parser import parse_expr;
from sympy.parsing.latex import parse_latex;

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
    """Detekuje LaTeX nebo Python a vrátí SymPy objekt a očištěné proměnné."""
    base_dict = {'e': E, 'E': E, 'pi': pi, 'exp': exp}
    rovnice_str = rovnice_str.strip("'\" ")

    if "=" in rovnice_str:
        nazev, vyraz_str = rovnice_str.split("=", 1);
    else:
        nazev, vyraz_str = "y", rovnice_str;

    if "\\" in vyraz_str:
        if "exp" in vyraz_str and "\\exp" not in vyraz_str:
            vyraz_str = vyraz_str.replace("exp", "\\exp");
            
        parsed = parse_latex(vyraz_str);
        found_vars = [s.name for s in parsed.free_symbols];
    else:
        # Python styl
        found_vars = extract_variables(vyraz_str);
        ldict = {name: symbols(name) for name in found_vars};
        ldict.update(base_dict);
        parsed = parse_expr(vyraz_str, local_dict=ldict);

    forbidden = {'e', 'E', 'pi', 'exp', 'log', 'ln', 'sin', 'cos', 'tan'};
    clean_vars = [v for v in found_vars if v not in forbidden and not v.startswith('Dummy')];

    if "exp" in vyraz_str:
        clean_vars = [v for v in clean_vars if v not in ['e', 'x', 'p']];

    return parsed, clean_vars, nazev;

def doGraph(x, y, promena, rovnice, nazev_rce, title, pathToDir):
    plt.figure(figsize=(9, 6));
    plt.plot(x, y, label=rf'$R = {latex(rovnice)}$');
    plt.xlabel(promena);
    plt.ylabel(nazev_rce);
    plt.title(title);
    plt.grid(alpha=0.3);
    plt.legend();
    plt.savefig(f'{pathToDir}/{title}.svg', format='svg', bbox_inches='tight');
    plt.show();

    print(f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{title}{color_print.END} a rovnicí {color_print.UNDERLINE}{nazev_rce}={rovnice}{color_print.END}" + 
        f"se uložil do souboru:\n└──{pathToDir}/{title}.svg");
    plt.close();

def run(args):
    nazev_rce, rovnice = args.rovnice.split("=");
    parsed_y, variables, nazev_veliciny = smart_parse(args.rovnice);

    start_int, end_int = args.interval;

    f = lambdify([symbols(v) for v in variables], parsed_y, 'numpy');
    x_Range = np.linspace(start_int, end_int, 1000);
    y_vals = f(x_Range)

    dir_name = "grafy_metoda_graf";

    folder_path = Path(dir_name).resolve();
    folder_path.mkdir(parents=True, exist_ok=True);

    return doGraph(x_Range, y_vals, variables[0], parsed_y, nazev_rce, args.name, folder_path,);
