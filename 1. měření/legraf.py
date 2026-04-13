# To RUN: python3 [py] graf_vypocty.py -i INPUT_FILE_PATH

import re;
import argparse;
from pathlib import Path;
import numpy as np;
import math;
import matplotlib.pyplot as plt;
import os;
from scipy.optimize import curve_fit;
import sys;
import json;

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
    zakladZaokr = f"{zaklad:.1f}".replace(".", ",");

    return f"{zakladZaokr} * 10^{exponent}";


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
    # plt.scatter(x_Range, y_Range, color='blue', s=10, label='Naměřená data', zorder=5);

    plt.xlabel(f'{x_Key}');
    plt.ylabel(f'{y_Key}');
    plt.title(title);
    plt.legend();
    plt.grid(True, alpha=0.3);


def save_Graph_And_Leave(nameFile):
    plt.legend();
    plt.grid(True, alpha=0.3);
    plt.savefig(f'{script_dir}/{nameFile}.svg', format='svg', bbox_inches='tight');
    print(f"Graf se jménem {nameFile} se uložil do souboru:\n└──{script_dir}/{nameFile}.svg");
    # plt.show();
    plt.close();

def shockley_model(Vd, Is, n):
    Vt = 0.0252;
    return Is * (np.exp(Vd / (n *Vt)) - 1);


def vypocitej_chybu_I(Vd, Is, n, Is_err, n_err):
    Vt = 0.0252;

    dI_dIs = np.exp(Vd / (n * Vt)) - 1;

    dI_dn = Is * np.exp(Vd / (n * Vt)) * (-Vd / (n ** 2 * Vt));

    return np.sqrt((dI_dIs * Is_err) ** 2 + (dI_dn * n_err) ** 2);


def main():
    parser = argparse.ArgumentParser(description="Process sensor measurement data.");

    args = parser.parse_args();

    parsedDataPath = parent_dir / "data";

    onlyfiles = [parsedDataPath / f for f in os.listdir(parsedDataPath) if os.path.isfile(os.path.join(parsedDataPath, f))];
    files = convertFile(onlyfiles);
    for key, val in files.items():
        I = val["I [A]"];
        U = val["U [V]"];

        # ln(I) = ln(I_s) + V_d / (n * V_t); kde a = 1 / (n * V_t)
        Vt = 0.0252; #25,2 mV
        mask_LN_I = I["hodnoty"] > 0
        ln_I = np.log(I["hodnoty"][mask_LN_I]);
        # a, b = np.polyfit(U["hodnoty"][mask], ln_I[mask], 1);

        """I_s = np.exp(b);
        n = 1 / (a * Vt);"""
        I = I["hodnoty"];
        U = U["hodnoty"];

        mask = I > 0
        U_fit = U[mask];
        I_fit = I[mask];

        popt, pcov = curve_fit(shockley_model, U_fit, I_fit, p0=[1e-12, 3],
                           bounds=([1e-20, 1], [1e-3, 10]));
        Is_fit, n_fit = popt;

        perr = np.sqrt(np.diag(pcov)) if pcov is not None else [np.nan, np.nan]

        Is_err = perr[0];
        n_err = perr[1];

        U_model = np.linspace(min(U), max(U), 10000);
        I_model = shockley_model(U_model, Is_fit, n_fit);
        U_chyba = val["ERR_U"]["hodnoty"];
        I_chyba = val["ERR_I"]["hodnoty"];

        doGraph_SCATTER(U, I, "$U$ [V]", "$I$ [A]", key);
        plt.plot(U_model, I_model, color='red', label=f'Proložení Shockleyovou rovnicí'); #  $I_s$=({return_Cislo_Krat_10_Na(Is_fit)} ± {return_Cislo_Krat_10_Na(Is_err)})

        plt.errorbar(U, I,
                     xerr=U_chyba,
                     yerr=I_chyba,
                     fmt='o',
                     color='blue',
                     ecolor='black',
                     capsize=3,
                     label='Naměřená data s chybou'
        );

        print(color_print.GREEN + color_print.BOLD + key + color_print.END);
        print(f"├──{color_print.UNDERLINE}I_s{color_print.END}: ({Is_fit} ± {Is_err}) A");
        print(f"└──{color_print.UNDERLINE}n{color_print.END}: ({n_fit} ± {n_err}) V");
        print(f"{vypocitej_chybu_I(U, Is_fit, n_fit, Is_err, n_err)[-1]:.2e}")

        save_Graph_And_Leave(key);
        print("-------------------------------------------------------------------------------------------------------------------------------------------------------------")



if __name__ == "__main__":
    main();