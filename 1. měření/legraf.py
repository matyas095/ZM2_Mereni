# To RUN: python3 [py] graf_vypocty.py -i INPUT_FILE_PATH

import re;
import argparse;
from pathlib import Path;
import numpy as np;
import math;
import matplotlib.pyplot as plt;
import os;
import sys;
import json;

from pandas.core.array_algos import replace

parent_dir = Path(__file__).resolve().parent;
script_dir = parent_dir / "grafy";
script_dir.mkdir(parents=True, exist_ok=True);


def len_no_color(s):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])');
    return len(ansi_escape.sub('', s));


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


def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10 ** exponent;

    return f"{zaklad:.3f} * 10^{exponent}";


def convertFile(inpu_Paths):
    hodnoty = {};
    for inpu in inpu_Paths:
        with open(inpu) as f:
            hodnoty[inpu.parts[-1]] = {
            }
            for line in f:
                nazev, vals = line.split("=");
                strs = [s.replace(",", ".") for s in vals.split(";")];
                vals = np.array([float(x) for x in strs]);

                aritmeticky_prumer = (1 / len(vals)) * sum(vals);
                odchylka = sum([(x - aritmeticky_prumer) ** 2 for x in vals]);
                chyba_prumeru = math.sqrt(odchylka / (len(vals) * (len(vals) - 1)));

                if ('T1' in nazev): nazev = 'T1/K'

                hodnoty[inpu.parts[-1]][nazev] = {
                    'hodnoty': vals,
                    'aritmeticky_prumer': aritmeticky_prumer,
                    'chyba_prumeru': chyba_prumeru
                }
    return hodnoty;


def doGraph_SCATTER(x_Range, y_Range, x_Key, y_Key, title):
    plt.figure(figsize=(9, 6));
    # plt.errorbar(t, ln_U, yerr=chyba_ln_U, fmt='o', capsize=3, color='darkred', label='Chyba měření');
    # plt.plot(t, fit(t, k, q), 'b-',
    #          label=f'Fit přímky ($k={return_Cislo_Krat_10_Na(k)}$, $q={return_Cislo_Krat_10_Na(q)}$)');
    # plt.xticks(x);
    plt.scatter(x_Range, y_Range, color='blue', s=10, label='Naměřená data');

    plt.xlabel(f'{x_Key}');
    plt.ylabel(f'{y_Key}');
    plt.title(title);
    plt.legend();
    plt.grid(True, alpha=0.3);


def save_Graph_And_Leave(nameFile):
    plt.savefig(f'{script_dir}/{nameFile}.svg', format='svg', bbox_inches='tight');
    print(f"Graf se jménem {nameFile} se uložil do souboru:\n└──{script_dir}/{nameFile}.svg");
    # plt.show();
    plt.close();


def main():
    parser = argparse.ArgumentParser(description="Process sensor measurement data.");

    args = parser.parse_args();

    parsedDataPath = parent_dir / "data";

    onlyfiles = [parsedDataPath / f for f in os.listdir(parsedDataPath) if os.path.isfile(os.path.join(parsedDataPath, f))];
    files = convertFile(onlyfiles);
    for key, val in files.items():
        I = val["I [A]"];
        U = val["U [V]"];
        print(I, U)




if __name__ == "__main__":
    main();