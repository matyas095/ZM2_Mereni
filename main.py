import sys;
import os;
import argparse;
import importlib;

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS; # type: ignore
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__));

sys.path = [BASE_DIR, os.path.join(BASE_DIR, "statisticke_vypracovani")] + sys.path;

# CURRENT_VERSION = "v0.5";
CURRENT_VERSION = "v0.5"
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

def get_available_methods():
    folder = os.path.join(BASE_DIR, "statisticke_vypracovani");
    if not os.path.exists(folder):
        return [];
    return [
        d for d in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, d)) and not d.startswith(("_", "."))
    ];

def CLI_Handler(args):
    if not args.method:
        print("Statistika Tůl - Interaktivní režim")
        print("---------------------------------------")
        methods = get_available_methods()
        print(f"Dostupné metody: {', '.join(methods)}")
        selected = ""
        while selected not in methods:
            selected = input("Zadejte metodu: ").strip()
        args.method = selected

    module_path = f"statisticke_vypracovani.{args.method}"
    method_module = importlib.import_module(module_path)

    if hasattr(method_module, "get_args_info"):
        for original_extra in method_module.get_args_info():
            extra = original_extra.copy()
            # Convert flags like ['-i', '--input'] to 'input'
            dest = extra['flags'][-1].lstrip('-').replace('-', '_')
            
            current_val = getattr(args, dest, None)

            if current_val is None:
                prompt = extra.get('help', dest)
                is_required = extra.get("required", False)

                # --- 1. HANDLE FILE PICKER ---
                if extra.get("is_file") and is_required:
                    from tkinter import filedialog, Tk
                    root = Tk()
                    root.withdraw()
                    print(f"[{args.method}] Vyberte {prompt}...")
                    picked_path = filedialog.askopenfilename(title=prompt)
                    root.destroy()
                    
                    if picked_path:
                        setattr(args, dest, picked_path)
                    else:
                        user_val = input(f"Vložte cestu k {dest} ručně: ").strip().replace('"', '').replace("'", "")
                        setattr(args, dest, user_val if user_val else None)
                    
                    # File is handled, move to next argument
                    continue 

                # --- 2. HANDLE BOOLEANS ---
                is_boolean = extra.get("action") in ["store_true", "store_false"]
                if is_boolean and current_val is True:
                    continue

                if current_val is None or (is_boolean and current_val is False):
                    prompt = extra.get('help', dest)
                    is_required = extra.get("required", False)

                    # Pokud nejsme v čistě interaktivním režimu (nějaké args už máme), 
                    # tak se na nepovinné booleany neptej
                    if is_boolean and not is_required:
                        # Pokud uživatel zadal aspoň něco (třeba -i), 
                        # předpokládáme, že zbytek flagů nechtěl
                        if any(vars(args).values()): 
                            continue

                    # ... zbytek tvé logiky (file picker, atd.) ...

                    if is_boolean:
                        choice = input(f"Zapnout {prompt}? (y/n): ").lower().strip()
                        setattr(args, dest, choice == 'y')
                        continue

                # --- 3. HANDLE REGULAR INPUTS ---
                default = extra.get('default', None)
                if not is_required and default is not None:
                    setattr(args, dest, default)
                    continue

                user_val = ""
                if is_required:
                    while not user_val:
                        user_val = input(f"{prompt} (!!REQUIRED!!): ").strip()
                
                if user_val != "":
                    arg_type = extra.get('type', str)
                    setattr(args, dest, arg_type(user_val))
                else:
                    setattr(args, dest, default)

    # --- FINAL VALIDATION ---
    # We check the 'input' attribute only if it exists, otherwise check specific files
    file_to_check = getattr(args, 'input', None)
    if file_to_check and not os.path.isfile(file_to_check):
        print(f"❌ Error: Soubor '{file_to_check}' nebyl nalezen.")
        if getattr(sys, 'frozen', False): input("Stiskněte Enter...")
        sys.exit(1)

    return method_module

def main():
    parser = argparse.ArgumentParser(description="Statistické nástroje");
    subparsers = parser.add_subparsers(dest="method", help="Vyberte metodu");

    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {CURRENT_VERSION}");

    methods = get_available_methods();
    for m_name in methods:
        sub_parser = subparsers.add_parser(m_name, help=f"Nástroj: {m_name}");

        try:
            module = importlib.import_module(f"statisticke_vypracovani.{m_name}");
            if hasattr(module, "get_args_info"):
                for arg in module.get_args_info():
                    arg_to_add = arg.copy();
                    
                    flags = arg_to_add.pop("flags");
                    
                    if "is_file" in arg_to_add:
                        arg_to_add.pop("is_file");
                    
                    arg_to_add["required"] = False;

                    sub_parser.add_argument(*flags, **arg_to_add);
                    
        except Exception as e:
            print(f"Nepodařilo se načíst extra parametry pro {m_name}: {e}");

    args = parser.parse_args();
    
    method_module = CLI_Handler(args);

    current_input = getattr(args, 'input', None);
    if current_input and hasattr(method_module, "validate"):
        pass
        """is_valid, message = method_module.validate(current_input);
        if not is_valid:
            print(f"Chybný formát dat: {message}");
            if getattr(sys, 'frozen', False): input("Stiskněte Enter...");
            sys.exit(1);"""

    result = method_module.run(args);
    try:
        # result = method_module.run(args);
    
        if getattr(args, 'save', False) and result:
            output_file = f"vysledek_{args.method}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(str(result))
            print(f"💾 Výsledek uložen do: {output_file}")
    except Exception as e:
        print(f"❌ Neočekávaná chyba při běhu: {e}");

    if getattr(sys, 'frozen', False):
        print("\n---------------------------------------");
        input("Hotovo. Stiskněte Enter pro ukončení...");

if __name__ == "__main__":
    check_for_updates();
    main();