import argparse;
import importlib;
import os;
import sys;

import requests;
import webbrowser;
from tkinter import messagebox;

# CURRENT_VERSION = "v0.5";
CURRENT_VERSION = "v0.5"
VERSION_URL = "https://api.github.com/repos/matyas095/ZM2_Mereni/releases/latest";

def check_for_updates():
    headers = {'User-Agent': 'MyPythonApp-Updater'}
    
    try:
        response = requests.get(VERSION_URL, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # The API always uses 'tag_name'
            remote_tag = data.get("tag_name") 
            
            if not remote_tag:
                print("⚠️ Could not find tag_name in API response.")
                return

            # Normalize: "v0.2" -> "0.2"
            remote_v = remote_tag.lstrip('v').strip()
            local_v = CURRENT_VERSION.lstrip('v').strip()

            # 3. CRITICAL: Only show if Remote is GREATER than Local
            if float(remote_v) > float(local_v):
                print(f"🚀 Update Available: {remote_tag}")
                # 
                # Trigger your popup here
            else:
                print(f"✅ Up to date. Local: {local_v}, Remote: {remote_v}")
                
        elif response.status_code == 404:
            print("ℹ️ No releases found yet. Pushing v0.3 via deploy.sh will fix this.")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

def get_base_path():
    """Finds the base path whether running as .py or .exe"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS;
    return os.path.dirname(os.path.abspath(__file__));

base_dir = get_base_path();
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'));

def get_available_methods():
    base = get_base_path();
    folder = os.path.join(base, "statisticke_vypracovani");
    
    if not os.path.exists(folder):
        return [];

    return [
        d for d in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, d)) and not d.startswith(("_", "."))
    ];

    # return [
    #     f[:-3] for f in os.listdir(folder) 
    #     if f.endswith(".py") and f != "__init__.py"
    # ];

def main():
    parser = argparse.ArgumentParser(description="Statistické nástroje");
    
    # We remove 'required=True' to allow the script to start when double-clicked
    parser.add_argument("-m", "--method", choices=get_available_methods(), help="Jméno metody");
    parser.add_argument("-i", "--input", help="Cesta k souboru");
    
    args = parser.parse_args();

    # --- CLI vs DOUBLE-CLICK LOGIC ---
    # If either argument is missing, we switch to interactive mode
    if not args.method or not args.input:
        print("📊 Statistika Tool - Interaktivní režim");
        print("---------------------------------------");
        
        if not args.method:
            methods = get_available_methods();
            print(f"Dostupné metody: {', '.join(methods)}");
            while args.method not in methods:
                args.method = input("Zadejte metodu: ").strip();
        
        if not args.input:
            from tkinter import filedialog, Tk;
            root = Tk();
            root.withdraw();
            print("Vyberte vstupní soubor v otevřeném okně...");
            args.input = filedialog.askopenfilename(title="Vyberte soubor s daty");
            root.destroy();
            
            if not args.input:
                args.input = input("Vložte cestu k souboru ručně: ").strip().replace('"', '').replace("'", "");

    # --- VALIDATION ---
    if not os.path.isfile(args.input):
        print(f"❌ Chyba: Soubor '{args.input}' nebyl nalezen.")
        if getattr(sys, 'frozen', False): input("Stiskněte Enter..."); 
        sys.exit(1)

    # --- EXECUTION ---
    try:
        module_path = f"statisticke_vypracovani.{args.method}"
        method_module = importlib.import_module(module_path)
        method_module.run(args.input)
        print("\n✅ Výpočet dokončen.")
    except Exception as e:
        print(f"❌ Neočekávaná chyba: {e}")

    # --- PREVENT WINDOW FROM CLOSING ---
    # This only triggers if the app is run as a compiled EXE
    if getattr(sys, 'frozen', False):
        print("\n---------------------------------------")
        input("Hotovo. Stiskněte Enter pro ukončení...")

if __name__ == "__main__":
    check_for_updates()
    main();