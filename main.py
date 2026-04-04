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
                print(f"Update Available: {CURRENT_VERSION} -> {remote_tag}\nLink:{url}");
            else: pass

        elif response.status_code == 404:
            print("ℹ️ No releases found yet. Pushing v0.3 via deploy.sh will fix this.");

    except Exception as e:
        print(f"❌ Connection error: {e}");

class CLIApp:
    def __init__(self):
        self.methods: dict[str, Method] = {};
        self._discover_methods();

    def _discover_methods(self):
        folder = os.path.join(BASE_DIR, "statisticke_vypracovani");
        if not os.path.exists(folder):
            return;
        method_dirs = [
            d for d in os.listdir(folder)
            if os.path.isdir(os.path.join(folder, d)) and not d.startswith(("_", "."))
        ];
        for m_name in method_dirs:
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
            except Exception as e:
                print(f"Nepodařilo se načíst modul {m_name}: {e}");

    def _build_parser(self):
        parser = argparse.ArgumentParser(description="Statistické nástroje");
        subparsers = parser.add_subparsers(dest="method", help="Vyberte metodu");

        parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {CURRENT_VERSION}");

        for m_name, method_instance in self.methods.items():
            sub_parser = subparsers.add_parser(m_name, help=method_instance.description);

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
        if not args.method:
            print("Statistika Tůl - Interaktivní režim");
            print("---------------------------------------");
            print(f"Dostupné metody: {', '.join(self.methods.keys())}");
            selected = "";
            while selected not in self.methods:
                selected = input("Zadejte metodu: ").strip();
            args.method = selected;

        method_instance = self.methods[args.method];

        for original_extra in method_instance.get_args_info():
            extra = original_extra.copy();
            dest = extra['flags'][-1].lstrip('-').replace('-', '_');

            current_val = getattr(args, dest, None);

            if current_val is None:
                prompt = extra.get('help', dest);
                is_required = extra.get("required", False);

                if extra.get("is_file") and is_required:
                    from tkinter import filedialog, Tk;
                    root = Tk();
                    root.withdraw();
                    print(f"[{args.method}] Vyberte {prompt}...");
                    picked_path = filedialog.askopenfilename(title=prompt);
                    root.destroy();

                    if picked_path: setattr(args, dest, picked_path);
                    else:
                        user_val = input(f"Vložte cestu k {dest} ručně: ").strip().replace('"', '').replace("'", "");
                        setattr(args, dest, user_val if user_val else None);

                    continue ;

                is_boolean = extra.get("action") in ["store_true", "store_false"];
                if is_boolean and current_val is True: continue;

                if current_val is None or (is_boolean and current_val is False):
                    prompt = extra.get('help', dest);
                    is_required = extra.get("required", False);

                    if is_boolean and not is_required:
                        if any(vars(args).values()): continue;

                    if is_boolean:
                        choice = input(f"Zapnout {prompt}? (y/n): ").lower().strip();
                        setattr(args, dest, choice == 'y');
                        continue;

                default = extra.get('default', None);
                if not is_required and default is not None:
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
        if file_to_check and not os.path.isfile(file_to_check):
            print(f"Error: Soubor '{file_to_check}' nebyl nalezen.");
            if getattr(sys, 'frozen', False): input("Stiskněte Enter...");
            sys.exit(1);

        return method_instance;

    def run(self):
        parser = self._build_parser();
        args = parser.parse_args();

        method_instance = self._interactive_handler(args);

        method_instance.validate(args);

        result = method_instance.run(args);
        try:
            if getattr(args, 'save', False) and result:
                output_file = f"vysledek_{args.method}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(str(result))
                print(f"💾 Výsledek uložen do: {output_file}")
        except Exception as e:
            print(f"Chyba incident: {e}");

        if getattr(sys, 'frozen', False):
            print("\n---------------------------------------");
            input("Hotovo. Stiskni Enter pro ukončení vro...");

if __name__ == "__main__":
    check_for_updates();
    app = CLIApp();
    app.run();
