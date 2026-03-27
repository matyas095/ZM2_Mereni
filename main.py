import sys;
import os;
import argparse;
import importlib;

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS;
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__));

sys.path = [BASE_DIR, os.path.join(BASE_DIR, "statisticke_vypracovani")] + sys.path;

import requests;
import webbrowser;
from tkinter import messagebox;
import utils;

# CURRENT_VERSION = "v0.1";
CURRENT_VERSION = "v0.1"
VERSION_URL = "https://api.github.com/repos/matyas095/ZM2_Mereni/releases/latest";

def version_to_tuple(v):
    return tuple(map(int, (v.split("."))));

def check_for_updates():
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
                print(f"🚀 Update Available: {CURRENT_VERSION} -> {remote_tag}\nLink:{url}");
            else: pass
                # print(f"✅ Up to date. Local: {local_v}, Remote: {remote_v}");
                
        elif response.status_code == 404:
            print("ℹ️ No releases found yet. Pushing v0.3 via deploy.sh will fix this.");
            
    except Exception as e:
        print(f"❌ Connection error: {e}");

def get_base_path():
    """Finds the base path whether running as .py or .exe"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS; # type: ignore
    return os.path.dirname(os.path.abspath(__file__));

"""base_dir = get_base_path();
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'));"""

def get_available_methods():
    # Use the BASE_DIR we defined at the top
    folder = os.path.join(BASE_DIR, "statisticke_vypracovani")
    if not os.path.exists(folder):
        return []
    return [
        d for d in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, d)) and not d.startswith(("_", "."))
    ]

def CLI_Handler(args):
    if not args.method:
        print("Statistika Tůl - Interaktivní režim");
        print("---------------------------------------");
        methods = get_available_methods();
        print(f"Dostupné metody: {', '.join(methods)}");
        selected = "";
        while selected not in methods:
            selected = input("Zadejte metodu: ").strip();
        args.method = selected;

    module_path = f"statisticke_vypracovani.{args.method}";
    method_module = importlib.import_module(module_path);

    if not getattr(args, 'input', None):
        from tkinter import filedialog, Tk;
        root = Tk();
        root.withdraw();
        print(f"[{args.method}] Vyberte vstupní soubor...");
        args.input = filedialog.askopenfilename(title="Vyberte soubor s daty");
        root.destroy();
        
        if not args.input:
            args.input = input("Vložte cestu k souboru ručně: ").strip().replace('"', '').replace("'", "");

    if hasattr(method_module, "get_args_info"):
        for original_extra in method_module.get_args_info():
            extra = original_extra.copy();
            dest = extra['flags'][-1].lstrip('-').replace('-', '_');
            
            is_boolean = extra.get("action") in ["store_true", "store_false"];
            current_val = getattr(args, dest, None);

            if current_val is None:
                prompt = extra.get('help', dest);
                is_required = extra.get("required", False);

                if is_boolean:
                    choice = input(f"Zapnout {prompt}? (y/n): ").lower().strip();
                    setattr(args, dest, choice == 'y');
                else:
                    default = extra.get('default', None);
                    
                    if not is_required and default is not None:
                        setattr(args, dest, default);
                        continue;

                    user_val = "";
                    if is_required:
                        while not user_val:
                            user_val = input(f"{prompt} (!!REQUIRED!!): ").strip();
                    """else:
                        user_val = input(f"Zadejte {prompt} (volitelné): ").strip();"""

                    if user_val != "":
                        arg_type = extra.get('type', str);
                        setattr(args, dest, arg_type(user_val));
                    else:
                        setattr(args, dest, default);

    if not os.path.isfile(args.input):
        print(f"Error: Soubor '{args.input}' nebyl nalezen.");
        if getattr(sys, 'frozen', False): input("Stiskněte Enter...");
        sys.exit(1);

    return method_module;

def main():
    parser = argparse.ArgumentParser(description="Statistické nástroje");
    subparsers = parser.add_subparsers(dest="method", help="Vyberte metodu");

    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {CURRENT_VERSION}");

    methods = get_available_methods();
    for m_name in methods:
        sub_parser = subparsers.add_parser(m_name, help=f"Nástroj: {m_name}");
        
        sub_parser.add_argument("-i", "--input", help="Cesta k souboru");

        try:
            module = importlib.import_module(f"statisticke_vypracovani.{m_name}");
            if hasattr(module, "get_args_info"):
                for arg in module.get_args_info():
                    flags = arg.pop("flags");
                    sub_parser.add_argument(*flags, **arg);
        except Exception as e:
            print(f"Nepodařilo se načíst extra parametry pro {m_name}: {e}");

    args = parser.parse_args();
    method_module = CLI_Handler(args);

    if hasattr(method_module, "validate"):
        is_valid, message = method_module.validate(args.input);
        if not is_valid:
            print(f"Chybný formát vro dat: {message}");
            sys.exit(1);

    result = method_module.run(args);
    try:
        # result = method_module.run(args);
    
        if getattr(args, 'save', False) and result:
            with open(f"vysledek_{args.method}.txt", "w") as f:
                f.write(str(result))
    except Exception as e:
        print(f"Unexpect error: {e}");

    if getattr(sys, 'frozen', False):
        print("\n---------------------------------------");
        input("Hotovo. Stiskněte Enter pro ukončení...");

if __name__ == "__main__":
    check_for_updates();
    main();