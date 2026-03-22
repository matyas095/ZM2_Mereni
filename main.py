import argparse;
import importlib;
import os;
import sys;

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
    parser = argparse.ArgumentParser(description="Statistické nástroje type shi");
    
    parser.add_argument("-m", "--method", required=True, choices=get_available_methods(), help="Jméno metody (aritcketicky_prumer)");
    parser.add_argument("-i", "--input", required=True, help="Cesta k souboru kde se načtou počáteční data");
    
    args = parser.parse_args();

    if not os.path.isfile(args.input):
        print(f"Error: File {args.input} not found.");
        sys.exit(1);

    try:
        module_path = f"statisticke_vypracovani.{args.method}";
        method_module = importlib.import_module(module_path);

        result = method_module.run(args.input);
        # print(f"Result from {args.method}: {result}");
    except ImportError as e:
        print(f"Error: Method '{args.method}' not found in statisticke_vypracovani.\n{e}");
    except AttributeError:
        print(f"Error: Module '{args.method}' doesn't have a 'run' function.");
    except Exception as e:
        print(f"Neočekávaná chyba: {e}");

if __name__ == "__main__":
    main();