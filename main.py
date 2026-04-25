import sys;
import os;
import argparse;
import importlib;
import inspect;

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS; # type: ignore
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__));

sys.path = [BASE_DIR, os.path.join(BASE_DIR, "statisticke_vypracovani")] + sys.path;

from statisticke_vypracovani.base import Method;

# CURRENT_VERSION = "v0.2";
CURRENT_VERSION = "v0.2"
VERSION_URL = "https://api.github.com/repos/matyas095/ZM2_Mereni/releases/latest";

def version_to_tuple(v):
    return tuple(map(int, (v.split("."))));

def check_for_updates():
    import requests;
    headers = {'User-Agent': 'StatistikaApp-Updater'};

    try:
        response = requests.get(VERSION_URL, headers=headers, timeout=5);

        if response.status_code == 200:
            data = response.json();

            remote_tag = data.get("tag_name");
            url = data.get("url");

            if not remote_tag: return print("Could not find tag_name in API response.");

            remote_v = remote_tag.lstrip('v').strip();
            local_v = CURRENT_VERSION.lstrip('v').strip();

            if version_to_tuple(remote_v) > version_to_tuple(local_v):
                print(f"Update Available: {CURRENT_VERSION} -> {remote_tag}\nLink: {url}");
            else: pass

        elif response.status_code == 404:
            print("ℹ️ No releases found yet. Pushing v0.3 via deploy.sh will fix this.");

    except Exception as e:
        print(f"❌ Connection error: {e}");

_METHOD_ALIASES = {
    "ap": "aritmeticky_prumer",
    "nc": "neprima_chyba",
    "vp": "vazeny_prumer",
    "der": "derivace",
    "cs": "convert_soubor",
    "jt": "join_tables",
    "ft": "format_table",
    "et": "extract_table",
    "gi": "graf_interval",
    "hist": "histogram",
    "g": "graf",
    "reg": "regrese",
};


class CLIApp:
    def __init__(self, only: set = None):
        self.methods: dict[str, Method] = {};
        self._discover_methods(only);

    def _discover_methods(self, only: set = None):
        folder = os.path.join(BASE_DIR, "statisticke_vypracovani");
        if not os.path.exists(folder):
            return;
        method_dirs = [
            d for d in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, d)) and not d.startswith(("_", "."))
        ];
        for m_name in method_dirs:
            if only and m_name not in only:
                continue;
            try:
                module = importlib.import_module(f"statisticke_vypracovani.{m_name}");
                for attr_name in dir(module):
                    attr = getattr(module, attr_name);
                    if (inspect.isclass(attr)
                        and issubclass(attr, Method)
                        and attr is not Method):
                        instance = attr();
                        self.methods[m_name] = instance;
                        break;
            except ImportError:
                pass;
            except Exception as e:
                print(f"Nepodařilo se načíst modul {m_name}: {e}");

    def _build_parser(self):
        parser = argparse.ArgumentParser(description="Statistické nástroje");
        subparsers = parser.add_subparsers(dest="method", help="Vyberte metodu");

        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {CURRENT_VERSION}");
        parser.add_argument("--list-units", action="store_true",
                           help="Vypíše podporované SI jednotky a prefixy");

        ALIASES = {
            "aritmeticky_prumer": ["ap"],
            "neprima_chyba": ["nc"],
            "vazeny_prumer": ["vp"],
            "derivace": ["der"],
            "convert_soubor": ["cs"],
            "join_tables": ["jt"],
            "format_table": ["ft"],
            "extract_table": ["et"],
            "graf_interval": ["gi"],
            "histogram": ["hist"],
            "graf": ["g"],
            "regrese": ["reg"],
        };

        for m_name, method_instance in self.methods.items():
            aliases = ALIASES.get(m_name, []);
            sub_parser = subparsers.add_parser(m_name, aliases=aliases, help=method_instance.description);
            sub_parser.add_argument("--output-format", choices=["text", "json"], default="text",
                                   help="Formát výstupu: text (výchozí) nebo json");
            sub_parser.add_argument("--no-color", action="store_true",
                                   help="Vypne barevný výstup");
            sub_parser.add_argument("-q", "--quiet", action="store_true",
                                   help="Minimální výstup (jen hodnoty, bez dekorací)");

            try:
                for arg in method_instance.get_args_info():
                    arg_to_add = arg.copy();

                    flags = arg_to_add.pop("flags");

                    if "is_file" in arg_to_add:
                        arg_to_add.pop("is_file");

                    arg_to_add["required"] = False;

                    sub_parser.add_argument(*flags, **arg_to_add);

            except Exception as e:
                print(f"Nepodařilo se načíst extra parametry pro {m_name}: {e}");

        return parser;

    def _interactive_handler(self, args):
        is_tty = sys.stdin.isatty();

        if not args.method:
            if not is_tty:
                print("Error: Metoda nezadána a stdin není terminál (nelze interaktivně promptovat).");
                sys.exit(2);
            print("Statistika Tůl - Interaktivní režim");
            print("---------------------------------------");
            print(f"Dostupné metody: {', '.join(self.methods.keys())}");
            selected = "";
            while selected not in self.methods:
                selected = input("Zadejte metodu: ").strip();
            args.method = selected;

        # Alias → canonical name
        if args.method in _METHOD_ALIASES:
            args.method = _METHOD_ALIASES[args.method];

        method_instance = self.methods[args.method];

        # Pokud je zadaný --batch, přeskočíme požadavek na --input
        has_batch = getattr(args, 'batch', None);

        for original_extra in method_instance.get_args_info():
            extra = original_extra.copy();
            dest = extra['flags'][-1].lstrip('-').replace('-', '_');

            current_val = getattr(args, dest, None);

            if current_val is None:
                prompt = extra.get('help', dest);
                is_required = extra.get("required", False);
                default = extra.get('default', None);

                if has_batch and dest == "input":
                    continue;

                if extra.get("is_file") and is_required:
                    if not is_tty:
                        continue;
                    picked_path = None;
                    try:
                        from tkinter import filedialog, Tk;
                        root = Tk();
                        root.withdraw();
                        print(f"[{args.method}] Vyberte {prompt}...");
                        picked_path = filedialog.askopenfilename(title=prompt);
                        root.destroy();
                    except Exception:
                        pass;

                    if picked_path:
                        setattr(args, dest, picked_path);
                    else:
                        user_val = input(f"Vložte cestu k {dest}: ").strip().replace('"', '').replace("'", "");
                        setattr(args, dest, user_val if user_val else None);

                    continue;

                is_boolean = extra.get("action") in ["store_true", "store_false"];
                if is_boolean and current_val is True: continue;

                if current_val is None or (is_boolean and current_val is False):
                    if is_boolean and not is_required:
                        if any(vars(args).values()): continue;

                    if is_boolean:
                        if not is_tty:
                            setattr(args, dest, False);
                            continue;
                        choice = input(f"Zapnout {prompt}? (y/n): ").lower().strip();
                        setattr(args, dest, choice == 'y');
                        continue;

                if not is_required and default is not None:
                    setattr(args, dest, default);
                    continue;

                if not is_tty:
                    if is_required:
                        print(f"Error: Chybí povinný parametr --{dest} ({prompt}) a stdin není terminál.");
                        sys.exit(2);
                    setattr(args, dest, default);
                    continue;

                user_val = "";
                if is_required:
                    while not user_val:
                        user_val = input(f"{prompt} (!!REQUIRED!!): ").strip();

                if user_val != "":
                    arg_type = extra.get('type', str);
                    setattr(args, dest, arg_type(user_val));
                else:
                    setattr(args, dest, default);

        file_to_check = getattr(args, 'input', None);
        if has_batch:
            file_to_check = None;
        if file_to_check:
            files = file_to_check if isinstance(file_to_check, list) else [file_to_check];
            for f in files:
                if isinstance(f, str) and not os.path.isfile(f):
                    print(f"Error: Soubor '{f}' nebyl nalezen.");
                    if getattr(sys, 'frozen', False): input("Stiskněte Enter...");
                    sys.exit(1);

        return method_instance;

    def _print_units(self):
        from objects.units import SI_PREFIXES, BASE_UNITS, UNIT_ALIASES;
        print("Podporované SI jednotky a prefixy\n");
        print("Základní/odvozené jednotky:");
        units_sorted = sorted(BASE_UNITS);
        for i in range(0, len(units_sorted), 10):
            print("  " + ", ".join(units_sorted[i:i+10]));
        print("\nSI prefixy:");
        items = sorted(SI_PREFIXES.items(), key=lambda kv: kv[1]);
        for prefix, mult in items:
            import math;
            try:
                exp = int(math.log10(mult));
            except Exception:
                exp = 0;
            print(f"  {prefix:4s} 10^{exp:+d}");
        print("\nAliasy:");
        for alias, canonical in UNIT_ALIASES.items():
            print(f"  {alias} → {canonical}");
        print("\nPříklady převodů:");
        examples = ["mA → A", "kV → V", "MΩ → Ω", "GHz → Hz", "μs → s", "km → m"];
        print("  " + ", ".join(examples));

    def run(self):
        parser = self._build_parser();

        try:
            import argcomplete;
            argcomplete.autocomplete(parser);
        except ImportError:
            pass;

        args = parser.parse_args();

        if getattr(args, 'list_units', False):
            self._print_units();
            return;

        if getattr(args, 'no_color', False):
            os.environ["ZM2_COLORS"] = "none";

        from objects.logger import configure as _configure_logger;
        _configure_logger(
            verbose=getattr(args, 'verbose', False),
            quiet=getattr(args, 'quiet', False),
            no_color=getattr(args, 'no_color', False),
        );

        output_format = getattr(args, 'output_format', 'text');

        method_instance = self._interactive_handler(args);

        method_instance.validate(args);

        if output_format == "json":
            result = method_instance.run(args);
            if isinstance(result, dict):
                from objects.measurement_set import MeasurementSet;
                ms = MeasurementSet.from_dict({k: [v[0]] for k, v in result.items()});
                for m_name, vals in result.items():
                    m = ms.get(m_name);
                    m._mean = vals[0];
                    m._u_A = vals[1] if len(vals) > 1 else 0;
                print(ms.to_json());
            else:
                import json;
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str));
        else:
            result = method_instance.run(args);
            try:
                if getattr(args, 'save', False) and result:
                    output_file = f"vysledek_{args.method}.txt"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(str(result))
                    print(f"Výsledek uložen do: {output_file}")
            except Exception as e:
                print(f"Chyba incident: {e}");

        if getattr(sys, 'frozen', False):
            print("\n---------------------------------------");
            try:
                input("Hotovo. Stiskni Enter pro ukončení vro...");
            except EOFError:
                pass;

if __name__ == "__main__":
    check_for_updates();
    app = CLIApp();
    app.run();
