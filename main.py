import argparse
import importlib
import os
import sys

def get_available_methods():
    """Scans the folder for Python files to use as valid methods."""
    folder = "statisticke_vypracovani";
    if not os.path.exists(folder):
        return [];

    return [
        d for d in os.listdir(folder)
        if os.path.isdir(os.path.join(folder, d)) and not d.startswith("__") and not d.startswith(".")
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
    except ImportError:
        print(f"Error: Method '{args.method}' not found in statisticke_vypracovani.");
    except AttributeError:
        print(f"Error: Module '{args.method}' doesn't have a 'run' function.");
    except Exception as e:
        print(f"Neočekávaná chyba: {e}");

if __name__ == "__main__":
    main();