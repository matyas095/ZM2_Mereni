import math;
import numpy as np;
from pathlib import Path;
from itertools import zip_longest;
from utils import color_print;

def APPEND_ARR_NUMPY(arr: np.ndarray, val):
    """
    Parameters:
    -----------
        arr - numpy.array
        val - valued to be appended

    Example
    -------
    >>> APPEND_ARR_NUMPY(array, 3);
    """
    return np.append(arr, val);

def try_convert(s):
    """
    Tries to convert a string to int, then float, then returns as-is.
    """
    if not isinstance(s, str): return s;
    try:
        return int(s);
    except ValueError:
        try:
            return float(s);
        except ValueError:
            return s;

def run(args, doPrint = True):
    if(isinstance(args, dict)):
        result = [
            [group, [try_convert(sub) for sub in args[group]]]
            for group in args.keys()
        ];
        PROMENA = np.array(result, dtype=object);
    else:
        with open(args.input) as f: # type: ignore
            result = [
                [
                    [try_convert(i) for i in sub][0] if len(sub) == 1 
                    else [try_convert(i) for i in sub]
                    for sub in group
                ]
                for group in [[m.split(",") for m in x.split("=")] for x in f.read().split("\n") if x]
            ]
            PROMENA = np.array(result, dtype=object);   # arr[:, 0] - získá všechny klíče (před =);
                                                        # arr[0, 1] - ziská první data v prvním řádku inputu

    if(doPrint): print(f"Zpracovávám údaje pro hodnoty {', '.join(PROMENA[:, 0])}");

    toPrint = {};
    header = [];
    body = [];

    for obj in PROMENA:
        key, data = obj;
        if any(not isinstance(x, (int, float)) for x in data): raise ValueError(f"V datech s proměnnou {color_print.BOLD}{color_print.UNDERLINE}{key}{color_print.END} je někde string místo int/float.")
        
        if(doPrint and getattr(args, 'latextable', None)):
            header.append(key);
            body.append([str(x) for x in data]);

        sum_Data = ( 1 / len(data) ) * sum(data);
        odchylka = sum([(x - sum_Data) ** 2 for x in data]);
        sigma_sum_Data = math.sqrt( odchylka / (len(data)*(len(data) - 1)));
        toPrint[key] = [sum_Data, sigma_sum_Data];
 
    if(doPrint):
        if(getattr(args, 'latextable', None)):
            dir_name = "latex_output";

            folder_path = Path(dir_name).resolve();
            folder_path.mkdir(parents=True, exist_ok=True);

            pairs = list(zip_longest(*body, fillvalue="-"));

            latex_table_HEAD = (
                "\\begin{table}[H]\n"
                "\t\\centering\n"
                "\t\\small\n"
                "\t\\begin{tabular}{@{}" + "c" * len(header) + "@{}}\n"
                "\t\t\\toprule\n"
            );
            latex_table_END = (
                "\n\t\\end{tabular}\n"
                "\t\\caption{" + input("Jakej text chceš míti: ") + "}\n"
                "\t\\label{tab:" + input("Jakej label chceš míti: ") + "}\n"
                "\\end{table}"
            );
            math_header = [f"${h}$" for h in header];
            col1_width = max(len(str(pair[0])) for pair in pairs + [(math_header[0],)]);

            tex_File_Name = f"table_{'_'.join([x.split(" ")[0] for x in PROMENA[:, 0]])}.tex";
            tex_File_Path = folder_path / tex_File_Name;

            with open(tex_File_Path, "w", encoding="utf-8") as f:
                f.write(latex_table_HEAD);
                f.write("\t\t" + " & ".join([math_header[0].ljust(col1_width), math_header[1]]) + " \\\\ \\midrule\n");
                result_str = "\t\t" + " \\\\ \n\t\t".join([" & ".join(map(str, pair)) for pair in pairs]) + r" \\ \bottomrule";
                f.write(result_str);
                f.write(latex_table_END);
                print(color_print.GREEN + f"Soubor {tex_File_Name} uložen na adrese{color_print.END}");
                print("└──" + str(tex_File_Path));

        for key, arr in toPrint.items():
            print(color_print.BOLD + key + color_print.END);

            for j, val in enumerate(arr):
                connector = "└──" if j == len(arr) - 1 else "├──";
                what = "Aritmetický průměr" if j == 0 else "Chyba aritmetického průměru";

                print(f"{connector}{color_print.UNDERLINE}{what}{color_print.END} = {val}");
            print("-" * 100);

    return toPrint;
