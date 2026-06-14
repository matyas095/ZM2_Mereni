# To RUN: python3 [py] graf_vypocty.py -i INPUT_FILE_PATH

import re;
import argparse;
from pathlib import Path;
import numpy as np;
import math;
import matplotlib.pyplot as plt;
import os;
import sys;
import tomllib;

parent_dir = Path(__file__).resolve().parent;
script_dir = parent_dir / "grafy";
script_dir.mkdir(parents=True, exist_ok=True);



def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10 ** exponent;

    return f"{zaklad:.3f} * 10^{exponent}";



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

    parsedDataPath = parent_dir / "inputfiles"; # ber při 0,12

    x_Range = None;
    T_1_Range = None;
    T_2_Range = None;

    with open(parsedDataPath / "hodnoty.toml", "rb") as f:
        data = tomllib.load(f)
        veli = data["veliciny"];
        x_Range = np.array(veli["x"]["hodnoty"]);
        T_1_Range = np.array(veli["T_1"]["hodnoty"]);
        T_2_Range = np.array(veli["T_2"]["hodnoty"]);

    p1 = np.polyfit(x_Range, T_1_Range, 2);
    p2 = np.polyfit(x_Range, T_2_Range, 2);

    x_line = np.linspace(min(x_Range), max(x_Range), 10000);

    plt.figure(figsize=(9, 6));
    plt.scatter(x_Range, T_1_Range, color='blue', s=10, label='$T_1$ [s]');
    plt.scatter(x_Range, T_2_Range, color='red', s=10, label='$T_2$ [s]');
    plt.plot(x_line, np.polyval(p1, x_line), color='blue', linestyle='dashed', label='Fit: $T_1$');
    plt.plot(x_line, np.polyval(p2, x_line), color='red', linestyle='dashed', label='Fit: $T_2$');

    idx = np.argwhere(np.diff(np.sign(T_1_Range - T_2_Range))).flatten();
    print(x_Range[idx], T_1_Range[idx]);

    plt.xlabel(f'$C_2$ [cm]');
    plt.ylabel(f'$T_x$ [s]');
    plt.title("Eheir");
    plt.legend();
    plt.grid(True, alpha=0.3);

    # plt.show();
    plt.savefig(f'{script_dir}/grafe.svg', format='svg', bbox_inches='tight');


if __name__ == "__main__":
    main();