# To RUN: python3 [py] graf_vypocty.py -i INPUT_FILE_PATH

import re;
import argparse;
from pathlib import Path;
import numpy as np;
import math;
import matplotlib.pyplot as plt;
import os;
import sys;

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
                vals = np.array([float(x) for x in vals.split(',')]);

                aritmeticky_prumer = (1 / len(vals)) * sum(vals);
                odchylka = sum([(x - aritmeticky_prumer) ** 2 for x in vals]);
                chyba_prumeru = math.sqrt(odchylka / (len(vals) * (len(vals) - 1)));

                if ('T1' in nazev): nazev = 'T1/K'

                hodnoty[inpu.parts[-1]][nazev] = {
                    'hodnoty': vals,
                    'aritmeticky_prumer': aritmeticky_prumer,
                    'chyba_prumeru': chyba_prumeru
                }
                print(inpu.parts[-1], nazev)
                print(vals)
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

    parsedDataPath = parent_dir / "parsedData";

    try:
        onlyfiles = [parsedDataPath / f for f in os.listdir(parsedDataPath) if os.path.isfile(os.path.join(parsedDataPath, f))];
        hodnoty = convertFile(onlyfiles);
        for file_name, vals in hodnoty.items():
            splitName = file_name.split("_")[1];
            num = file_name.split("_")[-1].split(".")[0];
            for velicina, val in vals.items():
                val_hod = val["hodnoty"];
                if(velicina == "X" or velicina == "Time [s]"):
                    x_Range = val_hod;
                    x_Key = "t [s]";
                elif(velicina == "Y"):
                    y_Range = val_hod;

            if(splitName == "E"): title = "Měření celkové energie E vozíček č. " + num;
            elif(splitName == "U"): title = "Měření potenciální energie U vozíček č. " + num;
            elif(splitName == "T"): title = "Měření kinetické energie T vozíček č. " + num;
            else: raise ValueError("Chyba v datech ig..");

            y_Key = splitName + " [J]";

            if(any(v is None for v in [x_Range, y_Range, x_Key, y_Key])): raise ValueError("Chyba v nepridanych datech..");

            doGraph_SCATTER(x_Range, y_Range, x_Key, y_Key, title);
            save_Graph_And_Leave(file_name);

        # Ukol 3
        print();
        print("=" * 150);
        print();

        mereni_1 = np.array([0.124, 0.138, 0.137]) * 2;
        mereni_2 = np.array([0.753, 0.673, 0.722]) * 2;
        mereni_3 = np.array([0.660, 0.761, 0.737]) * 2;
        mereni_4 = np.array([0.132, 0.132, 0.135]) * 2;

        suma_mereni_1 = np.sum(mereni_1) / len(mereni_1);
        suma_mereni_2 = np.sum(mereni_2) / len(mereni_2);
        suma_mereni_3 = np.sum(mereni_3) / len(mereni_3);
        suma_mereni_4 = np.sum(mereni_4) / len(mereni_4);
        chyba_mereni_1 = np.std(mereni_1) / len(mereni_1);
        chyba_mereni_2 = np.std(mereni_2) / len(mereni_2);
        chyba_mereni_3 = np.std(mereni_3) / len(mereni_3);
        chyba_mereni_4 = np.std(mereni_4) / len(mereni_4);

        zavazi1  = 0.008;  # kg
        zavazi2  = 0.049;  # kg
        vozicek1 = 0.215; # kg
        vozicek2 = 0.213; # kg

        def zrychleni_vozicku(m_kladka, M_vozicek):
            return (m_kladka * 9.81) / (M_vozicek + m_kladka);

        def chyba_zrychleni_vozicku(m_kladka, chyba_kladka, M_vozicek, chyba_vozicek):
            return 9.81 / ((M_vozicek + m_kladka) ** 2) * np.sqrt((M_vozicek * chyba_vozicek) ** 2 + (m_kladka * chyba_kladka) ** 2);

        def doThingys(zavazi, vozicek, suma, chyba_mereni, text):
            teoreticke_zrychleni_vozicek1_zavazi1 = zrychleni_vozicku(zavazi, vozicek);
            chyba_teoreticke_1_1 = chyba_zrychleni_vozicku(zavazi, 0.005, vozicek, 0.005);
            print(color_print.GREEN + color_print.BOLD + text + color_print.END);
            print(f"├──{color_print.UNDERLINE}Namerene{color_print.END}: ({suma:.2f} ± {chyba_mereni:.2f}) ms^-1");
            print(f"└────{color_print.UNDERLINE}Teoreticke{color_print.END}: ({teoreticke_zrychleni_vozicek1_zavazi1:.2f} ± {chyba_teoreticke_1_1:.2f}) ms^-1");
            print();

        # Vozicek 1.
        doThingys(zavazi1, vozicek1, suma_mereni_1, chyba_mereni_1, "Vozicek 1. (0.215kg) zavazi 1. (0.008kg)");
        doThingys(zavazi2, vozicek1, suma_mereni_2, chyba_mereni_2, "Vozicek 1. (0.215kg) zavazi 2. (0.049kg)");

        # Vozicek 2.
        doThingys(zavazi1, vozicek2, suma_mereni_4, chyba_mereni_4, "Vozicek 2. (0.213kg) zavazi 1. (0.008kg)");
        doThingys(zavazi2, vozicek2, suma_mereni_3, chyba_mereni_3, "Vozicek 2. (0.213kg) zavazi 2. (0.049kg)");

    except FileNotFoundError:
        print(f"Error: The file '{args.input}' was not found.");
        sys.exit(1);
    except Exception as e:
        print(f"An error occurred: {e}");
        sys.exit(1);


if __name__ == "__main__":
    main();