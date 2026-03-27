# utils.py
import numpy as np;
import math;
import os;
import sys;

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS; # type: ignore
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir);

class color_print:
   PURPLE = '\033[95m';
   CYAN = '\033[96m';
   DARKCYAN = '\033[36m';
   BLUE = '\033[94m';
   GREEN = '\033[92m';
   YELLOW = '\033[93m';
   RED = '\033[91m';
   BOLD = '\033[1m';
   UNDERLINE = '\033[4m';
   END = '\033[0m';

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

def get_Promeny(args):
    """
    Vrátí proměnné z argumentu **"input"**

    Arguments
    ---------
        args : `<Arguments args>`
            - argumenty

    Returns
    -------
        `numpy.ndarray([ ... ])`

            - Metods:
              - arr[:, 0] - získá všechny klíče (před =)
        


    Example
    -------
    >>> get_Promeny(args);
    """
    with open(args.input) as f:
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
    return PROMENA;

def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10**exponent;

    return f"{zaklad:.3f} * 10^{exponent}";