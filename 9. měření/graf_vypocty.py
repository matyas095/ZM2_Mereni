# To RUN: python3 [py] graf_vypocty.py -i INPUT_FILE_PATH

import re;
import argparse;
from pathlib import Path;
import numpy as np;
import math;
import matplotlib.pyplot as plt;
import sys;

script_dir = Path(__file__).resolve().parent / "grafy";
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

def to_Kelvin(i): return i + 273.15;

def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10**exponent;

    return f"{zaklad:.3f} * 10^{exponent}";

def convertFile(inpu):
    hodnoty = {};
    with open(inpu) as f:
        for line in f:
            nazev, vals = line.split("=");
            vals = np.array([float(x) for x in vals.split(',')]);

            aritmeticky_prumer = ( 1 / len(vals) ) * sum(vals);
            odchylka = sum([(x - aritmeticky_prumer) ** 2 for x in vals]);
            chyba_prumeru = math.sqrt( odchylka / (len(vals)*(len(vals) - 1)));

            if('T1' in nazev): nazev = 'T1/K'
            

            hodnoty[nazev] = {
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
    script_dir = Path(__file__).resolve().parent / "grafy";
    script_dir.mkdir(parents=True, exist_ok=True);
    
    parser = argparse.ArgumentParser(description="Process sensor measurement data.");
    parser.add_argument("-i", "--input", required=True, help="Path to the input measurement file");
    parser.add_argument("-o", "--output", default="output_data.txt", help="Path to the output file (default: output_data.txt)");
    
    args = parser.parse_args();

    try:
        hodnoty = convertFile(args.input);
        hodnoty['T1/K']['hodnoty'] = hodnoty['T1/K']['hodnoty'] + 273.15

        U_T = np.abs(hodnoty['U2/V']['hodnoty']);
        U_N = np.abs(hodnoty['U1/V']['hodnoty']);
        
        x_Range = 1 / hodnoty['T1/K']['hodnoty'];
        R = (U_T / U_N) * 330.12;
        y_Range = np.log(R);
        x_Key = '1/T [$K^{-1}$]';
        y_Key = r'ln (R / $\Omega$) [-]';
        title = 'Změřené hodnoty 1/T a ln R s lineárním fitem';
        
        doGraph_SCATTER(x_Range, y_Range, x_Key, y_Key, title);
        
        (k, q), pcov = np.polyfit(x_Range, y_Range, 1, cov=True); # Koeficienty fitu + id

        plt.axvline(1 / 273.15, color='green', linestyle=':', label='Hranice 0°C')

        x_extractPolace = np.linspace(1 / max(hodnoty['T1/K']['hodnoty']), 1 / 273.15, 100); # max dat, 0˚C, 100 hodnot
        y_extractPolace = k * x_extractPolace + q;

        plt.plot(x_extractPolace, y_extractPolace, 'r-', label=f'Lineární fit (y = {k:.2f} * 1/T + {q:.2f})'); # Fit 
        plt.legend();

        R_0_calc = np.exp(k * ( 1 / 273.15 ) + q);
        grad = np.array([1 / 273.15, 1]);

        dR_0 = R_0_calc * np.sqrt(grad.T @ pcov @ grad)
        print(f"Vypočtená konstanta B: {k:.2f} K");
        print(f"{color_print.BOLD}{color_print.UNDERLINE}Fitovaný odpor při 0°C{color_print.END}: ({color_print.BOLD}{R_0_calc:.2f}{color_print.END} ± {color_print.BOLD}{dR_0:.2f}{color_print.END}) Ohm");

        save_Graph_And_Leave("".join(title.split("/")));
        dvoje_1, dvoje_2 = (min(hodnoty['T1/K']['hodnoty']), max(R)), (max(hodnoty['T1/K']['hodnoty']), min(R));
        B = ( np.log(dvoje_1[-1]) - np.log(dvoje_2[-1]) ) / ( 1 / dvoje_1[0] - 1 / dvoje_2[0] );
        R_infty = dvoje_1[-1] / ( np.exp( B / dvoje_1[0] ) );
        
        dk = np.sqrt(pcov[0, 0]) # Chyba  (chyba B)
        dq = np.sqrt(pcov[1, 1]) # chyba průsečíku (chyba ln R_inf) 
        R_C_0 = R_infty * np.exp( B / to_Kelvin(0) );
        chyba_R_C_0 = R_C_0 * np.sqrt((dk / (to_Kelvin(0)))**2 + dq**2);

        print(dk, dq)

        print("");

        toPrint = [
            fr"({color_print.BOLD}{R_C_0}{color_print.END} ± {color_print.BOLD}{chyba_R_C_0}{color_print.END}) Ohm",
            fr"├──{color_print.RED}{color_print.BOLD}B{color_print.END} = ({color_print.UNDERLINE}{B} ± {dk}{color_print.END}) K",
            fr"├────{color_print.RED}{color_print.BOLD}B{color_print.END} ≐ ({color_print.UNDERLINE}{return_Cislo_Krat_10_Na(B)} ± {return_Cislo_Krat_10_Na(dk)}{color_print.END}) K",
            fr"├──{color_print.BLUE}{color_print.BOLD}R_infty{color_print.END} = ({color_print.UNDERLINE}{R_infty} ± {dq}{color_print.END}) Ohm",
            fr"└────{color_print.BLUE}{color_print.BOLD}R_infty{color_print.END} ≐ ({color_print.UNDERLINE}{return_Cislo_Krat_10_Na(R_infty)} ± {return_Cislo_Krat_10_Na(dq)}{color_print.END}) Ohm"
        ];

        title_PRINT = f"{color_print.UNDERLINE}R při teplotě 0˚C{color_print.END}";

        leToPrint = max(len_no_color(s) for s in toPrint);
        leTitle = len_no_color(title_PRINT);

        # Výpočet mezer pro nadpis
        side_len = (leToPrint - leTitle) // 2;
        extra = (leToPrint - leTitle) % 2;

        # 1. Horní linka s nadpisem
        print("╔" + "═" * side_len + " " +  title_PRINT + " " + "═" * (side_len + extra) + "╗");

        for s in toPrint:
            mezery = " " * (leToPrint - len_no_color(s));
            print(f"║ {s}{mezery} ║");

        print("╚" + "═" * (leToPrint + 2) + "╝");


    except FileNotFoundError:
        print(f"Error: The file '{args.input}' was not found.");
        sys.exit(1);
    except Exception as e:
        print(f"An error occurred: {e}");
        sys.exit(1);

if __name__ == "__main__":
    main();