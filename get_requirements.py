import os
import ast
import pkgutil

def generate_requirements():
    imports = set() 
    
    # 1. Get a list of all built-in Python modules to ignore them
    stdlib: set[str] = {m.name for m in pkgutil.iter_modules() if m.module_finder is None}
    # Add common ones that sometimes hide
    extras = {'os', 'sys', 'argparse', 'math', 'ast', 'unittest', 'logging', 'json', "re"}
    stdlib.update(extras)

    # 2. Get a list of LOCAL folders and files to ignore them
    local_stuff = {name for name in os.listdir(".") if os.path.isdir(name) or name.endswith(".py")}

    for root, dirs, files in os.walk("."):
        # Skip virtual envs and build artifacts
        if any(x in root for x in [".venv", "venv", ".git", "__pycache__", "dist", "build"]):
            continue
            
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for n in node.names:
                                    imports.add(n.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom) and node.module:
                                imports.add(node.module.split('.')[0])
                except Exception:
                    continue

    # 1. Get names of ALL local .py files in the root (logic, utils, main, etc.)
    local_files = {f.replace('.py', '') for f in os.listdir('.') if f.endswith('.py')}

    # 2. Get names of local folders (statisticke_vypracovani)
    local_folders = {name for name in os.listdir(".") if os.path.isdir(name)}

    # 3. Add the "stubborn" standard libs manually to the filter
    stdlib.update(['importlib', 'pkgutil', 'webbrowser', 'tkinter', 'math', 'ast'])
    manual_ignore = {'logic', 'utils', 'main', 'get_requirements', 'tkinter', 'pkgutil', 'importlib', 'webbrowser'}

    # 4. THE FINAL FILTER:
    final_reqs = [
        i for i in imports 
        if i not in stdlib 
        and i not in local_folders 
        and i not in local_files
        and i not in manual_ignore
    ]
    
    with open("requirements.txt", "w") as f:
        for req in final_reqs:
            f.write(f"{req}\n")
    
    print(f"Generated requirements.txt with: {', '.join(final_reqs)}")

if __name__ == "__main__":
    generate_requirements()