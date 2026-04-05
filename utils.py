# utils.py
import numpy as np;
import math;
import sys;
import os;
import re;

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS; # type: ignore
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir);

def _color_scheme():
    try:
        from objects.config import config;
        return config().get("color_scheme", "auto");
    except Exception:
        return "auto";

def _colors_enabled():
    scheme = os.environ.get("ZM2_COLORS", _color_scheme());
    if scheme == "none" or os.environ.get("NO_COLOR"):
        return False;
    if not sys.stdout.isatty() and scheme == "auto":
        return False;
    return True;

class _ColorMeta(type):
    _codes = {
        "PURPLE": '\033[95m',
        "CYAN": '\033[96m',
        "DARKCYAN": '\033[36m',
        "BLUE": '\033[94m',
        "GREEN": '\033[92m',
        "YELLOW": '\033[93m',
        "RED": '\033[91m',
        "BOLD": '\033[1m',
        "UNDERLINE": '\033[4m',
        "END": '\033[0m',
    };
    def __getattr__(cls, name):
        if name in cls._codes:
            return cls._codes[name] if _colors_enabled() else "";
        raise AttributeError(name);

class color_print(metaclass=_ColorMeta):
    pass;

def try_convert(s):
    if not isinstance(s, str): return s;
    try:
        return int(s);
    except ValueError:
        try:
            return float(s);
        except ValueError:
            return s;

def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10**exponent;
    return f"{zaklad:.3f} * 10^{exponent}";

def extract_variables(formula_str, toIgnore = []):
    ignored_functions = ['log', 'ln', 'sin', 'cos', 'tan', 'exp', 'sqrt', 'abs'] + toIgnore;

    ignore_pattern = r'\b(?:' + '|'.join(ignored_functions) + r')\b';
    regex_pattern = rf'\b(?!{ignore_pattern}|[0-9])[a-zA-Z_][a-zA-Z0-9_]*\b';

    variables = re.findall(regex_pattern, formula_str);

    return sorted(list(set(variables)));

def extract_latex_logic(cli_input):
    clean_input = cli_input.strip("'\"")
    logic = re.sub(r'\\frac\{(.+?)\}\{(.+?)\}', r'(\1)/(\2)', clean_input)
    logic = logic.replace(r'\Omega', 'Omega')
    return logic

def return_FirstWord(str):
    regex = rf"^\w"
    var = re.search(regex, str);
    if var: return var.group();
    return None;

def contains_substring(str, array):
    regex = rf"^({'|'.join(array)})";
    var = re.search(regex, str);
    if var: return True;
    return False;

def clean_latex(text):
    from sympy import latex;
    if not isinstance(text, str):
        text = latex(text);

    text = text.replace(r'\mathtt', '').replace(r'\text', '').replace(r'\mathrm', '');
    text = text.replace('backslashtext', '').replace('backslash', '');
    text = text.replace(r'\\', '').replace('\\', '');
    text = text.replace('Ohm', r'\Omega').replace('Omega', r'\Omega');
    text = text.replace('{', '').replace('}', '');

    return text.strip();

def smart_parse(rovnice_str):
    """Detekuje LaTeX nebo Python a vrátí SymPy objekt, proměnné a název."""
    from sympy import symbols, E, pi, exp;
    from sympy.parsing.sympy_parser import parse_expr;
    from sympy.parsing.latex import parse_latex;

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
        found_vars = extract_variables(vyraz_str);
        ldict = {name: symbols(name) for name in found_vars};
        ldict.update(base_dict);
        parsed = parse_expr(vyraz_str, local_dict=ldict);

    forbidden = {'e', 'E', 'pi', 'exp', 'log', 'ln', 'sin', 'cos', 'tan'};
    seen = set();
    clean_vars = [];
    for v in found_vars:
        if v not in forbidden and not v.startswith('Dummy') and v not in seen:
            clean_vars.append(v);
            seen.add(v);

    if "exp" in vyraz_str:
        clean_vars = [v for v in clean_vars if v not in ['e', 'x', 'p']];

    return parsed, clean_vars, nazev;

def parse_rovnice(rovnice_str):
    """Rozdělí 'VELIČINA=VZTAH' a vrátí (název, vztah)."""
    try:
        nazev, vztah = rovnice_str.split("=", 1);
        return nazev, vztah;
    except ValueError:
        raise ValueError("Chyba v rovnici; Formát: 'VELIČINA=VZTAH'");

def print_graf_saved(name, pathToDir, rovnice_info=None):
    msg = f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{name}{color_print.END}";
    if rovnice_info:
        msg += f" a rovnicí {color_print.UNDERLINE}{rovnice_info}{color_print.END}";
    msg += f" se uložil do souboru:\n└──{pathToDir}/{name}.svg";
    print(msg);

def balance_math_braces(s: str) -> str:
    """Vyvážení { } uvnitř každého $..$ bloku."""
    result = "";
    i = 0;
    while i < len(s):
        if s[i] == '$':
            j = s.find('$', i + 1);
            if j == -1:
                result += s[i:];
                break;
            content = s[i+1:j];
            open_c = content.count('{');
            close_c = content.count('}');
            if open_c > close_c:
                content = content + '}' * (open_c - close_c);
            elif close_c > open_c:
                excess = close_c - open_c;
                while excess > 0 and content.endswith('}'):
                    content = content[:-1];
                    excess -= 1;
            result += '$' + content + '$';
            i = j + 1;
        else:
            result += s[i];
            i += 1;
    return result;

def r2_score(y_true, y_pred):
    ss_res = np.sum((np.array(y_true) - np.array(y_pred)) ** 2);
    ss_tot = np.sum((np.array(y_true) - np.mean(y_true)) ** 2);
    return 1 - ss_res / ss_tot;
