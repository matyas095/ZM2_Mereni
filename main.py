import argparse;
import importlib;
import os;
import sys;

import requests;
import webbrowser;
from tkinter import messagebox;

# CURRENT_VERSION = "v0.2";
CURRENT_VERSION = "v0.2"
VERSION_URL = "https://raw.githubusercontent.com/matyas095/ZM2_Mereni/main/version.json";

def check_for_updates():
    try:
        response = requests.get(VERSION_URL, timeout=5);
        data = response.json();
        latest_version = data.get("version");
        print(latest_version)
        download_url = data.get("url");
        print(download_url)

        if latest_version != CURRENT_VERSION:
            root = messagebox.askyesno("Update Available", 
                f"A new version ({latest_version}) is available!\n"
                "Would you like to download it now?");
            if root:
                webbrowser.open(download_url);
    except Exception as e:
        print(f"Update check failed: {e}");

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