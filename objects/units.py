"""SI jednotky a převody."""
import re;

# SI prefixy a jejich násobky
SI_PREFIXES = {
    "y":  1e-24, "z":  1e-21, "a":  1e-18, "f":  1e-15,
    "p":  1e-12, "n":  1e-9,  "μ":  1e-6,  "u":  1e-6,
    "m":  1e-3,  "c":  1e-2,  "d":  1e-1,
    "da": 1e1,   "h":  1e2,   "k":  1e3,
    "M":  1e6,   "G":  1e9,   "T":  1e12,  "P":  1e15,
    "E":  1e18,  "Z":  1e21,  "Y":  1e24,
};

# Známé základní a odvozené SI jednotky (bez prefixu)
BASE_UNITS = {
    "m", "s", "A", "K", "mol", "cd",
    "Hz", "N", "Pa", "J", "W", "C", "V", "F",
    "Ω", "Ohm", "ohm", "S", "Wb", "T", "H",
    "lm", "lx", "Bq", "Gy", "Sv", "kat",
    "rad", "sr", "eV", "L", "l", "bar", "min", "h", "d",
    "g",
};

# Aliasy — normalizace různých zápisů stejné jednotky
UNIT_ALIASES = {
    "Ohm": "Ω", "ohm": "Ω",
    "deg": "°", "°C": "C_temp",
};

def _normalize_unit_str(unit: str) -> str:
    unit = unit.strip();
    return UNIT_ALIASES.get(unit, unit);

def parse_unit(unit_str: str):
    """Vrátí (factor_to_base, base_unit) pro danou jednotku.

    Příklady:
        'mA' -> (1e-3, 'A')
        'kΩ' -> (1e3, 'Ω')
        's'  -> (1.0, 's')
        'Hz' -> (1.0, 'Hz')
        'foo'-> (1.0, 'foo')  (neznámé)
    """
    if not unit_str or not unit_str.strip():
        return 1.0, unit_str;

    unit = _normalize_unit_str(unit_str);

    if unit in BASE_UNITS:
        return 1.0, _normalize_unit_str(unit);

    # zkusit dvouznakový prefix (da)
    if len(unit) > 2 and unit[:2] == "da":
        remainder = _normalize_unit_str(unit[2:]);
        if remainder in BASE_UNITS or remainder in UNIT_ALIASES.values():
            return SI_PREFIXES["da"], remainder;

    # zkusit jednoznakový prefix
    if len(unit) >= 2:
        prefix = unit[0];
        remainder_raw = unit[1:];
        remainder = _normalize_unit_str(remainder_raw);
        if prefix in SI_PREFIXES and prefix != "da":
            if remainder in BASE_UNITS or remainder in UNIT_ALIASES.values():
                return SI_PREFIXES[prefix], remainder;

    return 1.0, unit;

def extract_name_unit(full_name: str):
    """'I [mA]' -> ('I', 'mA'), 'R' -> ('R', None)"""
    match = re.match(r'(.+?)\s*\[([^\]]*)\]\s*$', full_name);
    if match:
        return match.group(1).strip(), match.group(2).strip() or None;
    return full_name.strip(), None;

def format_name_unit(name: str, unit: str = None) -> str:
    if unit is None or not unit:
        return name;
    return f"{name} [{unit}]";

def display_unit(unit) -> str:
    """Vrátí unit nebo '-' pokud je prázdná/None."""
    if unit is None or not str(unit).strip():
        return "-";
    return str(unit);

def auto_scale_exponent(values) -> int:
    """Vrátí nejlepší SI exponent (násobek 3) pro danou sadu hodnot."""
    import math;
    vals = [abs(v) for v in values if isinstance(v, (int, float)) and v != 0];
    if not vals:
        return 0;
    mean_abs = sum(vals) / len(vals);
    if mean_abs == 0:
        return 0;
    exp_raw = math.log10(mean_abs);
    return int(math.floor(exp_raw / 3) * 3);

PREFIX_FOR_EXPONENT = {
    -24: "y", -21: "z", -18: "a", -15: "f", -12: "p", -9: "n",
    -6: "μ", -3: "m", 0: "", 3: "k", 6: "M", 9: "G",
    12: "T", 15: "P", 18: "E", 21: "Z", 24: "Y"
};

def apply_auto_scale(values, base_unit: str):
    """Vrátí (scaled_values, new_unit) pro danou sadu hodnot v base_unit."""
    exp = auto_scale_exponent(values);
    if exp == 0 or exp not in PREFIX_FOR_EXPONENT:
        return list(values), base_unit;
    factor = 10 ** (-exp);
    new_values = [v * factor for v in values];
    new_unit = PREFIX_FOR_EXPONENT[exp] + base_unit;
    return new_values, new_unit;

def parse_tex_header(tex_header: str):
    """'$I [mA]$' -> ('I', 'mA'). Strip $...$ and extract."""
    s = tex_header.strip();
    if s.startswith("$") and s.endswith("$"):
        s = s[1:-1];
    s = s.strip();
    return extract_name_unit(s);

def format_tex_header(var: str, unit: str = None) -> str:
    return "$" + format_name_unit(var, unit) + "$";

def convert_str_value(s: str, factor: float, dec_sep: str = ",") -> str:
    """Převede stringovou hodnotu číslem × factor. Zachovává počet des. míst ze vstupu."""
    if s is None or s == "-" or not s.strip():
        return s;
    original = s.strip();
    try:
        num = float(original.replace(",", "."));
    except ValueError:
        return s;

    # Počet desetinných míst ve vstupu
    normalized = original.replace(",", ".");
    if "." in normalized:
        input_decimals = len(normalized.split(".", 1)[1]);
    else:
        input_decimals = 0;

    converted = num * factor;

    # Posun o exponent faktoru
    import math;
    if factor != 1.0 and factor != 0:
        shift = -int(round(math.log10(abs(factor))));
    else:
        shift = 0;

    if converted == 0:
        out_decimals = input_decimals;
    else:
        out_decimals = max(0, input_decimals + shift);

    formatted = f"{converted:.{out_decimals}f}";
    return formatted.replace(".", dec_sep);

def caption_contains_unit(caption: str, unit: str) -> bool:
    """Kontrola zda caption obsahuje danou jednotku (ke zobrazení varování)."""
    import re;
    pattern = r'(\[' + re.escape(unit) + r'\]|\b' + re.escape(unit) + r'\b)';
    return bool(re.search(pattern, caption));

def convert_factor(from_unit: str, to_unit: str) -> float:
    """Faktor pro převod z 'from_unit' na 'to_unit'. Musí být stejná fyzikální veličina."""
    f_from, base_from = parse_unit(from_unit);
    f_to, base_to = parse_unit(to_unit);

    if base_from != base_to:
        raise ValueError(f"Nelze převést {from_unit} ({base_from}) na {to_unit} ({base_to}) — různé veličiny");

    return f_from / f_to;
