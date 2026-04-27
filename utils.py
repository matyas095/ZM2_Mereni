# utils.py
import numpy as np
import math
import sys
import os
import re
import contextlib
from decimal import Decimal, ROUND_HALF_UP

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS  # type: ignore
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)


def round_half_up(value: float, ndigits: int = 0) -> float:
    """Zaokrouhlí 'půlku nahoru' (od nuly) — školní zaokrouhlování.

    Vestavěný Python `round()` používá bankovní zaokrouhlování (round half to even)
    a navíc trpí binární reprezentací floatů (např. `33.05` se reálně uloží jako
    `33.04999…`, takže `round(33.05, 1)` vrací `33.0` místo `33.1`).

    Tento helper převede přes `Decimal(repr(value))` (krátká round-trip reprezentace),
    takže `33.05` se interpretuje skutečně jako 33.05, a aplikuje `ROUND_HALF_UP`.

    Příklady:
        round_half_up(33.05, 1)  → 33.1
        round_half_up(2.5, 0)    → 3.0
        round_half_up(-2.5, 0)   → -3.0
    """
    if not math.isfinite(value):
        return value
    quant = Decimal(10) ** -ndigits
    return float(Decimal(repr(float(value))).quantize(quant, rounding=ROUND_HALF_UP))


def _color_scheme():
    try:
        from objects.config import config

        return config().get("color_scheme", "auto")
    except Exception:
        return "auto"


def _colors_enabled():
    scheme = os.environ.get("ZM2_COLORS", _color_scheme())
    if scheme == "none" or os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty() and scheme == "auto":
        return False
    return True


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
    }

    def __getattr__(cls, name):
        if name in cls._codes:
            return cls._codes[name] if _colors_enabled() else ""
        raise AttributeError(name)


class color_print(metaclass=_ColorMeta):
    pass


def try_convert(s):
    if not isinstance(s, str):
        return s
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def return_Cislo_Krat_10_Na(x):
    # Bezpecne pro x=0 a non-finite (inf/-inf/nan), kde by log10 selhal.
    if x == 0 or not math.isfinite(x):
        return f"{x}"
    exponent = math.floor(math.log10(abs(x)))
    zaklad = x / 10**exponent
    return f"{zaklad:.3f} * 10^{exponent}"


def gum_round(value: float, uncertainty: float) -> str:
    """Vrati (hodnota ± nejistota) zaokrouhlene dle GUM 7.2.6:
    - nejistota na 2 sig. cifry pokud jeji vedouci cislice je 1 nebo 2, jinak na 1 sig. cifru,
    - hodnota zaokrouhlena na stejne desetinne misto jako nejistota,
    - obe vyjadrene se sdilenym exponentem (pokud je vubec potreba).
    """
    if not math.isfinite(value) or not math.isfinite(uncertainty):
        return f"({value} ± {uncertainty})"
    if uncertainty == 0:
        return f"({value} ± 0)"
    unc_exp = math.floor(math.log10(abs(uncertainty)))
    # Vzdy 2 sig. cifry na nejistote (dle preference protokolu).
    # GUM §7.2.6 to dovoluje, NIST doporucuje 2 cifry pro vetsi cestnost zobrazene presnosti.
    sig_figs = 2
    round_to_pos = unc_exp - (sig_figs - 1)
    decimals = -round_to_pos
    val_r = round_half_up(value, decimals)
    unc_r = round_half_up(uncertainty, decimals)
    if val_r == 0:
        val_exp = round_to_pos
    else:
        val_exp = math.floor(math.log10(abs(val_r)))
    # Plain notation pro |val| v <0.01, 99 999 999) — sirsi rozsah aby
    # rescaled hodnoty (napr. 25 023 300 μg) nepadaly do scientific.
    if -2 <= val_exp <= 7:
        dp = max(0, decimals)
        if dp == 0:
            return f"({int(val_r)} ± {int(unc_r)})"
        return f"({val_r:.{dp}f} ± {unc_r:.{dp}f})"
    val_norm = val_r / 10**val_exp
    unc_norm = unc_r / 10**val_exp
    dp = max(0, val_exp - round_to_pos)
    return f"({val_norm:.{dp}f} ± {unc_norm:.{dp}f}) * 10^{val_exp}"


def parse_composite_unit(unit_str: str) -> tuple:
    """Parsuje slozitou jednotku ('g*mm**-3', 'm/s', 'kg/m^3') na (faktor_do_si, si_jednotka).

    SI base units: kg (hmotnost), m (delka), s (cas), A, K, mol, cd, atd.
    Hmotnostni jednotky se prevadi na kg (oproti `objects.units.parse_unit`,
    ktere pouziva `g` jako base).

    Priklady:
        parse_composite_unit('g*mm**-3')  -> (1e6, 'kg*m^-3')
        parse_composite_unit('g/cm**3')   -> (1e3, 'kg*m^-3')
        parse_composite_unit('m/s')       -> (1.0, 'm*s^-1')
        parse_composite_unit('km/h')      -> (1/3.6, 'm*s^-1')
    """
    MASS_TO_KG = {
        'g': 1e-3,
        'mg': 1e-6,
        'ug': 1e-9,
        'μg': 1e-9,
        'ng': 1e-12,
        'pg': 1e-15,
        'kg': 1.0,
        'Mg': 1e3,
        't': 1e3,
    }
    SPECIAL = {'h': (3600.0, 's'), 'min': (60.0, 's')}

    s = unit_str.strip().replace('^', '**')
    if '/' in s:
        head, *tail = s.split('/')
        s = head
        for piece in tail:
            for tok in re.split(r'(?<!\*)\*(?!\*)', piece):
                tok = tok.strip()
                if not tok:
                    continue
                if '**' in tok:
                    b, e = tok.split('**', 1)
                    s += f'*{b.strip()}**(-({e.strip()}))'
                else:
                    s += f'*{tok}**-1'

    tokens = re.split(r'(?<!\*)\*(?!\*)', s)
    total = 1.0
    terms = []
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if '**' in token:
            base, exp_str = token.split('**', 1)
            base = base.strip()
            try:
                exp = eval(exp_str.strip(), {'__builtins__': {}}, {})
            except Exception:
                exp = float(exp_str.strip().lstrip('(').rstrip(')'))
            exp = float(exp)
        else:
            base = token
            exp = 1.0
        if base in MASS_TO_KG:
            factor, base_si = MASS_TO_KG[base], 'kg'
        elif base in SPECIAL:
            factor, base_si = SPECIAL[base]
        else:
            from objects.units import parse_unit

            factor, base_si = parse_unit(base)
        total *= factor**exp
        terms.append((base_si, exp))

    coalesced = {}
    order = []
    for b, e in terms:
        if b in coalesced:
            coalesced[b] += e
        else:
            coalesced[b] = e
            order.append(b)
    parts = []
    for b in order:
        e = coalesced[b]
        if e == 0:
            continue
        if e == 1:
            parts.append(b)
        elif float(e).is_integer():
            parts.append(f'{b}^{int(e)}')
        else:
            parts.append(f'{b}^{e}')
    return total, '*'.join(parts) if parts else ''


def rescale_simple_unit(mean: float, sigma: float, unit: str) -> tuple:
    """Pokud je `unit` jednoducha SI base jednotka bez prefixu (napr. 'm', 'g', 's', 'A')
    a sigma je 'nepekny' (< 0.01 nebo >= 1000), prepocte hodnotu i nejistotu na vhodny
    SI prefix tak, aby sigma spadla do rozsahu [1, 1000).

    Funguje jen pro jednoduche jednotky bez prefixu a bez slozitych vyrazu (*/^).
    Pro slozite jednotky (`g*mm**-3` ap.) vraci puvodni triple bez zmeny — tam se
    pouziva `parse_composite_unit` pro SI prevod.

    Priklady:
        rescale_simple_unit(32.3432, 0.003, 'm')   -> (32343.2, 3.0, 'mm')
        rescale_simple_unit(32.3432, 1.1643, 'm')  -> (32.3432, 1.1643, 'm')   (no change)
        rescale_simple_unit(0.05, 5e-7, 's')       -> (5e4, 0.5, 'us')         (here returns 'μs')
    """
    SIMPLE_BASES = {
        'm',
        'g',
        's',
        'A',
        'K',
        'mol',
        'cd',
        'Hz',
        'N',
        'Pa',
        'J',
        'W',
        'V',
        'F',
        'C',
        'T',
        'Wb',
        'lx',
        'lm',
        'rad',
    }
    # Mapuje "scaling" exponent (jakym 10^k nasobime hodnoty) -> SI prefix.
    # k=3 znamena nasobeni *1000 -> jdeme na 1000x mensi jednotku ('m' jako mili).
    SCALING_TO_PREFIX = {
        15: 'f',
        12: 'p',
        9: 'n',
        6: 'μ',
        3: 'm',
        -3: 'k',
        -6: 'M',
        -9: 'G',
        -12: 'T',
        -15: 'P',
    }

    if unit not in SIMPLE_BASES:
        return mean, sigma, unit
    if sigma == 0 or not math.isfinite(sigma) or not math.isfinite(mean):
        return mean, sigma, unit

    sig_exp = math.floor(math.log10(abs(sigma)))
    # Pocet desetinnych mist potrebnych pro zobrazeni sigma na 2 sig. cifry.
    # Napr. sigma = 0.0075 (sig_exp=-3) -> sig_decimals=4 ("0.0075")
    #       sigma = 5.8e-5 (sig_exp=-5) -> sig_decimals=6 ("0.000058")
    #       sigma = 1.16   (sig_exp=0)  -> sig_decimals=1 ("1.2")
    sig_decimals = max(0, -(sig_exp - 1))

    scaling = 0
    if sig_decimals > 2:
        # Sigma ma vic nez 2 desetinna mista -> downscale (jdeme na mensi jednotku).
        # Hledame nejmensi nasobek 3 takovy, aby new_sig_decimals <= 2.
        # new_sig_exp = sig_exp + scaling -> sig_decimals_new = max(0, -(new_sig_exp - 1)) <= 2
        # => scaling >= -1 - sig_exp
        needed = -1 - sig_exp
        scaling = math.ceil(needed / 3) * 3
    elif abs(sigma) >= 1000:
        # Sigma >= 1000 -> upscale (jdeme na vetsi jednotku, kg, Mg, ...).
        # Hledame nejmensi |scaling| (zaporny) takovy, aby new_sig_exp <= 2.
        needed = sig_exp - 2
        scaling = -math.ceil(needed / 3) * 3

    if scaling == 0 or scaling not in SCALING_TO_PREFIX:
        return mean, sigma, unit

    factor = 10**scaling
    new_unit = SCALING_TO_PREFIX[scaling] + unit
    return mean * factor, sigma * factor, new_unit


def pick_display(orig_str: str, si_str: str, orig_unit: str, si_unit: str) -> tuple:
    """Vybere lepsi z (orig, si) zobrazeni:
    - SI forma se pouzije pouze pokud splnuje OBE podminky:
      bez `* 10^` a maximalne 2 desetinna mista.
    - Jinak zustava puvodni jednotka (i kdyz orig ma 10^ nebo vic des. mist).
    Vraci (zvolena_forma_str, zvolena_jednotka_str).
    """
    no_power_si = '* 10^' not in si_str
    decimals_si = 0
    for m in re.finditer(r'-?\d+\.(\d+)', si_str):
        decimals_si = max(decimals_si, len(m.group(1)))
    if no_power_si and decimals_si <= 2:
        return si_str, si_unit
    return orig_str, orig_unit


def extract_variables(formula_str, toIgnore=None):
    if toIgnore is None:
        toIgnore = []
    ignored_functions = ['log', 'ln', 'sin', 'cos', 'tan', 'exp', 'sqrt', 'abs'] + toIgnore
    ignore_pattern = r'\b(?:' + '|'.join(ignored_functions) + r')\b'
    regex_pattern = rf'\b(?!{ignore_pattern}|[0-9])[a-zA-Z_][a-zA-Z0-9_]*\b'
    variables = re.findall(regex_pattern, formula_str)
    return sorted(set(variables))


def extract_latex_logic(cli_input):
    clean_input = cli_input.strip("'\"")
    logic = re.sub(r'\\frac\{(.+?)\}\{(.+?)\}', r'(\1)/(\2)', clean_input)
    logic = logic.replace(r'\Omega', 'Omega')
    return logic


def return_FirstWord(str):
    regex = r"^\w"
    var = re.search(regex, str)
    if var:
        return var.group()
    return None


def contains_substring(str, array):
    regex = rf"^({'|'.join(array)})"
    var = re.search(regex, str)
    if var:
        return True
    return False


def clean_latex(text):
    from sympy import latex

    if not isinstance(text, str):
        text = latex(text)

    text = text.replace(r'\mathtt', '').replace(r'\text', '').replace(r'\mathrm', '')
    text = text.replace('backslashtext', '').replace('backslash', '')
    text = text.replace(r'\\', '').replace('\\', '')
    text = text.replace('Ohm', r'\Omega').replace('Omega', r'\Omega')
    text = text.replace('{', '').replace('}', '')
    return text.strip()


def smart_parse(rovnice_str):
    """Detekuje LaTeX nebo Python a vrátí SymPy objekt, proměnné a název."""
    from sympy import symbols, E, pi, exp
    from sympy.parsing.sympy_parser import parse_expr
    from sympy.parsing.latex import parse_latex

    base_dict = {'e': E, 'E': E, 'pi': pi, 'exp': exp}
    rovnice_str = rovnice_str.strip("'\" ")

    if "=" in rovnice_str:
        nazev, vyraz_str = rovnice_str.split("=", 1)
    else:
        nazev, vyraz_str = "y", rovnice_str

    if "\\" in vyraz_str:
        if "exp" in vyraz_str and "\\exp" not in vyraz_str:
            vyraz_str = vyraz_str.replace("exp", "\\exp")
        parsed = parse_latex(vyraz_str)
        found_vars = [s.name for s in parsed.free_symbols]
    else:
        found_vars = extract_variables(vyraz_str)
        ldict = {name: symbols(name) for name in found_vars}
        ldict.update(base_dict)
        parsed = parse_expr(vyraz_str, local_dict=ldict)

    forbidden = {'e', 'E', 'pi', 'exp', 'log', 'ln', 'sin', 'cos', 'tan'}
    seen = set()
    clean_vars = []
    for v in found_vars:
        if v not in forbidden and not v.startswith('Dummy') and v not in seen:
            clean_vars.append(v)
            seen.add(v)

    if "exp" in vyraz_str:
        clean_vars = [v for v in clean_vars if v not in ['e', 'x', 'p']]

    return parsed, clean_vars, nazev


def parse_rovnice(rovnice_str):
    """Rozdělí 'VELIČINA=VZTAH' a vrátí (název, vztah)."""
    try:
        nazev, vztah = rovnice_str.split("=", 1)
        return nazev, vztah
    except ValueError:
        raise ValueError("Chyba v rovnici; Formát: 'VELIČINA=VZTAH'")


def print_graf_saved(name, pathToDir, rovnice_info=None) -> str:
    msg = f"Graf se jménem {color_print.BOLD}{color_print.BLUE}{name}{color_print.END}"
    if rovnice_info:
        msg += f" a rovnicí {color_print.UNDERLINE}{rovnice_info}{color_print.END}"
    msg += f" se uložil do souboru:\n└──{pathToDir}/{name}.svg"
    print(msg)
    return f"{pathToDir}/{name}.svg"


def balance_math_braces(s: str) -> str:
    """Vyvážení { } uvnitř každého $..$ bloku."""
    result = ""
    i = 0
    while i < len(s):
        if s[i] == '$':
            j = s.find('$', i + 1)
            if j == -1:
                result += s[i:]
                break
            content = s[i + 1 : j]
            open_c = content.count('{')
            close_c = content.count('}')
            if open_c > close_c:
                content = content + '}' * (open_c - close_c)
            elif close_c > open_c:
                excess = close_c - open_c
                while excess > 0 and content.endswith('}'):
                    content = content[:-1]
                    excess -= 1
            result += '$' + content + '$'
            i = j + 1
        else:
            result += s[i]
            i += 1
    return result


def r2_score(y_true, y_pred):
    ss_res = np.sum((np.array(y_true) - np.array(y_pred)) ** 2)
    ss_tot = np.sum((np.array(y_true) - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot


@contextlib.contextmanager
def locked_open(path, mode="w", encoding="utf-8"):
    """Otevře soubor s exclusive lockem (Linux/Mac fcntl, Windows msvcrt).

    Brání závodění při paralelním běhu více metod do stejného outputu.
    """
    with open(path, mode, encoding=encoding) as f:
        try:
            import fcntl

            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            try:
                import msvcrt

                msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
            except (ImportError, OSError):
                pass
        try:
            yield f
        finally:
            try:
                import fcntl

                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (ImportError, OSError):
                pass
