import math;
import numpy as np;


class color_print:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

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
        ]
        PROMENA = np.array(result, dtype=object)
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

    for obj in PROMENA:
        key, data = obj;
        if any(not isinstance(x, (int, float)) for x in data): raise ValueError(f"V datech s proměnnou {color_print.BOLD}{color_print.UNDERLINE}{key}{color_print.END} je někde string místo int/float.")
        
        sum_Data = ( 1 / len(data) ) * sum(data);
        odchylka = sum([(x - sum_Data) ** 2 for x in data]);
        sigma_sum_Data = math.sqrt( odchylka / (len(data)*(len(data) - 1)));
        toPrint[key] = [sum_Data, sigma_sum_Data];
 
    if(doPrint): 
        for key, arr in toPrint.items():
            print(color_print.BOLD + key + color_print.END);

            for j, val in enumerate(arr):
                connector = "└──" if j == len(arr) - 1 else "├──";
                what = "Aritmetický průměr" if j == 0 else "Chyba aritmetického průměru";

                print(f"{connector}{color_print.UNDERLINE}{what}{color_print.END} = {val}");
            print("-" * 100);

    return toPrint;
