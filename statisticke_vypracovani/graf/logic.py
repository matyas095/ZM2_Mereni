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
from statisticke_vypracovani.aritmeticky_prumer.logic import run as aritm_Run;

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

def args_Rovnice_2D_Slice(PROMENA, args, pathToDir, fix_var='y', fix_value=None):
    # fix_var: 'x' nebo 'y' (kterou proměnnou zafixujeme)
    # fix_value: konkrétní hodnota z pole PROMENA, pokud není zadána, vezmeme střed
    
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

def args_Rovnice(PROMENA, args, pathToDir):
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

    # Titulek (oprava vnořených dolarů)
    title_str = f"Závislost ${z_label_text}$ na ${variables[0]}$ a ${variables[1]}$\nVztah: ${z_label_text}$ = ${latex(y).replace('mathtt', 'mathrm')}$"
    ax.set_title(title_str, pad=25)

    fig.colorbar(surf, shrink=0.5, aspect=15, pad=0.05);

    plt.show();
    # fig.tight_layout();

    elev = ax.elev;
    azim = ax.azim;

    ax.view_init(elev=elev, azim=azim);
    fig.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight', pad_inches=0.5);

    print(f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{args.name}{color_print.END} a rovnicí {color_print.UNDERLINE}{nazev_rovnice}={rovnice}{color_print.END} \
          se uložil do souboru:\n└──{pathToDir}/{args.name}.svg");

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
            # p0 jsou počáteční odhady, pro expo/mocninné důležité
            popt, _ = curve_fit(func, x, y, maxfev=2000)
            y_pred = func(x, *popt)
            score = r2_score(y, y_pred)
            vysledky[jmeno] = (score, popt, func)
        except:
            continue # Pokud fit neskonverguje, přeskočíme ho

    # Vybere model s nejvyšším R^2
    nejlepsi = max(vysledky, key=lambda k: vysledky[k][0])
    return nejlepsi, vysledky[nejlepsi]

def prep_Plot(PROMENA, args, pathToDir, ignoreRovnice = False):
    if(args.rovnice and not ignoreRovnice): 
        out = args_Rovnice(PROMENA, args, pathToDir);
        return;

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
        aritm = aritm_Run({x_key: x_Range}, False);
        print(aritm)

        print(najdi_nejlepsi_fit(x_Range, y_Range));
        print(aritm[x_key][-1])

        popt, pcov = curve_fit(modely_fitu[args.fit], x_Range, y_Range, absolute_sigma=True, sigma=aritm[x_key][-1] / np.array(PROMENA[1, 1]));

        label_text = f"Fit {args.fit}: " + ", ".join([f"${return_Cislo_Krat_10_Na(p)}$" for p in popt]);

        plt.plot(x_Range, modely_fitu[args.fit](x_Range, *popt), 'b-', 
             label=label_text);

        plt.errorbar(x_Range, y_Range, yerr=aritm[x_key][-1] / np.array(PROMENA[1, 1]), fmt='o', capsize=3, color='darkred', label='Chyba měření');
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

    # popt, pcov = curve_fit(fit, x, ln_U, sigma=chyba_ln_U, absolute_sigma=True);

    # k, q = popt;
    # chyba_k = np.sqrt(pcov[0, 0]);

    plt.figure(figsize=(9, 6));
    # plt.errorbar(t, ln_U, yerr=chyba_ln_U, fmt='o', capsize=3, color='darkred', label='Chyba měření');
    # plt.plot(t, fit(t, k, q), 'b-', 
    #          label=f'Fit přímky ($k={return_Cislo_Krat_10_Na(k)}$, $q={return_Cislo_Krat_10_Na(q)}$)');
    # plt.xticks(x);
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

    # return (k, q, chyba_k);

def run(args):
    PROMENA = get_Promeny(args);

    dir_name = "grafy_metoda_graf";

    folder_path = Path(dir_name).resolve();
    folder_path.mkdir(parents=True, exist_ok=True);

    print(f"Zpracovávám údaje pro hodnoty {', '.join(PROMENA[:, 0])}");
    return prep_Plot(PROMENA, args, str(folder_path));

    toPrint = {};

    for obj in PROMENA:
        key, data = obj
        if any(not isinstance(x, (int, float)) for x in data): raise ValueError(f"V datech s proměnnou {color_print.BOLD}{color_print.UNDERLINE}{key}{color_print.END} je někde string místo int/float.")
        
        sum_Data = ( 1 / len(data) ) * sum(data);
        odchylka = sum([(x - sum_Data) ** 2 for x in data]);
        sigma_sum_Data = math.sqrt( odchylka / (len(data)*(len(data) - 1)));
        toPrint[key] = [sum_Data, sigma_sum_Data];
 
    
    for key, arr in toPrint.items():
        print(color_print.BOLD + key + color_print.END);

        for j, val in enumerate(arr):
            connector = "└──" if j == len(arr) - 1 else "├──";
            what = "Aritmetický průměr" if j == 0 else "Chyba aritmetického průměru";

            print(f"{connector}{color_print.UNDERLINE}{what}{color_print.END} = {val}");
        print("-" * 100);

    return;
