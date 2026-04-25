import json;
from pathlib import Path;

DEFAULT_CONFIG = {
    "decimal_separator": ",",
    "default_outliers": None,
    "default_output_format": "text",
    "color_scheme": "auto",
    "verbose": False,
};

CONFIG_LOCATIONS = [
    Path.cwd() / ".zm2rc",
    Path.home() / ".zm2rc",
    Path.home() / ".config" / "zm2_mereni" / "config.json",
];

def load_config() -> dict:
    """Načte config z prvního nalezeného místa, zbytek z DEFAULT_CONFIG."""
    config = dict(DEFAULT_CONFIG);
    for path in CONFIG_LOCATIONS:
        if path.exists():
            try:
                with open(path, encoding='utf-8') as f:
                    user_config = json.load(f);
                unknown = set(user_config) - set(DEFAULT_CONFIG);
                if unknown:
                    import sys;
                    print(f"⚠ Neznámé klíče v {path}: {sorted(unknown)}", file=sys.stderr);
                    print(f"  Povolené klíče: {sorted(DEFAULT_CONFIG.keys())}", file=sys.stderr);
                config.update(user_config);
                break;
            except json.JSONDecodeError as e:
                import sys;
                print(f"⚠ Chyba v config souboru {path}: {e}", file=sys.stderr);
            except OSError:
                pass;
    return config;

def get_config_path() -> Path:
    """Vrátí cestu k aktivnímu config souboru (nebo výchozí kde by měl být)."""
    for path in CONFIG_LOCATIONS:
        if path.exists():
            return path;
    return CONFIG_LOCATIONS[1];

_config_cache = None;

def config() -> dict:
    global _config_cache;
    if _config_cache is None:
        _config_cache = load_config();
    return _config_cache;
