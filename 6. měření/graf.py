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

def cursed(T_1_Range, T_2_Range, x_Range):
    # Použijeme lineární fit pro T^2 (protože T^2 = (4*pi^2 / g) * l)
    # Tím získáme model matematického kyvadla
    T1_kvadrat = T_1_Range ** 2
    T2_kvadrat = T_2_Range ** 2

    # Proložíme přímky: y = k*x + q
    p1 = np.polyfit(x_Range, T1_kvadrat, 1)
    p2 = np.polyfit(x_Range, T2_kvadrat, 1)

    # Nalezení průsečíku přímek (k1*x + q1 = k2*x + q2)
    # x = (q2 - q1) / (k1 - k2)
    x_prusecik = (p2[1] - p1[1]) / (p1[0] - p2[0])

    # Dosadíme x zpět do libovolné přímky a odmocníme, abychom dostali periodu T
    y_prusecik_kvadrat = np.polyval(p1, x_prusecik)
    y_prusecik = np.sqrt(y_prusecik_kvadrat)

    # --- VÝPOČET GRAVITAČNÍHO ZRYCHLENÍ g ---
    # V průsečíku platí: T = 2 * pi * sqrt(d / g)
    # Kde d je vzdálenost břitů. V programu z prvního screenshotu byla d = 0.8 m.
    # POZOR: x_Range máš v TOML v [cm], musíme převést d na [cm], tedy d = 80 cm
    d_cm = 80.0
    g_vypoctene = (4 * np.pi ** 2 * d_cm) / y_prusecik_kvadrat
    # Převod g z cm/s^2 na m/s^2
    g_vypoctene_ms2 = g_vypoctene / 100

    print(f"--- Výsledky (Model: Matematické kyvadlo) ---")
    print(f"Poloha průsečíku x: {x_prusecik:.4f} cm")
    print(f"Perioda v průsečíku T: {y_prusecik:.4f} s")
    print(f"Vypočtené gravitační zrychlení g: {g_vypoctene_ms2:.4f} m/s^2")

    # --- VYKRESLENÍ ---
    x_line = np.linspace(min(x_Range), max(x_Range), 1000)

    plt.figure(figsize=(9, 6))
    # Kreslíme původní data T (ne kvadráty), abychom zachovali tvůj formát grafu
    plt.scatter(x_Range, T_1_Range, color='blue', s=10, label='$T_1$ [s] (data)')
    plt.scatter(x_Range, T_2_Range, color='red', s=10, label='$T_2$ [s] (data)')

    # Odmocníme přímky, abychom dostali křivky T pro graf
    plt.plot(x_line, np.sqrt(np.polyval(p1, x_line)), color='blue', linestyle='dashed',
             label='Model mat. kyvadla $T_1$')
    plt.plot(x_line, np.sqrt(np.polyval(p2, x_line)), color='red', linestyle='dashed', label='Model mat. kyvadla $T_2$')

    # Vykreslení průsečíku
    plt.scatter(x_prusecik, y_prusecik, color='green', s=50, zorder=5,
                label=f'Průsečík [{x_prusecik:.2f} cm; {y_prusecik:.2f} s]')

    plt.xlabel(f'$C_2$ [cm]')
    plt.ylabel(f'$T_x$ [s]')
    plt.title(f"Fit matematického kyvadla ($g = {g_vypoctene_ms2:.3f}\\,\\text{{m/s}}^2$)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(f'{script_dir}/grafe.svg', format='svg', bbox_inches='tight')


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

    return cursed(T_1_Range, T_2_Range, x_Range);

    mask = x_Range > 91.5
    x_fit = x_Range[mask]
    T_1_fit = T_1_Range[mask]
    T_2_fit = T_2_Range[mask]

    p1 = np.polyfit(x_fit, T_1_fit, 2);
    p2 = np.polyfit(x_fit, T_2_fit, 2);

    x_line = np.linspace(min(x_Range), max(x_Range), 10000);

    plt.figure(figsize=(9, 6));
    plt.scatter(x_Range, T_1_Range, color='blue', s=10, label='$T_1$ [s]');
    plt.scatter(x_Range, T_2_Range, color='red', s=10, label='$T_2$ [s]');
    plt.plot(x_line, np.polyval(p1, x_line), color='blue', linestyle='dashed', label='Fit: $T_1$');
    plt.plot(x_line, np.polyval(p2, x_line), color='red', linestyle='dashed', label='Fit: $T_2$');

    p_diff = p1 - p2;

    roots = np.roots(p_diff);

    pruseciky_x = [float(r.real) for r in roots if np.isreal(r) and min(x_Range) <= r.real <= max(x_Range)];

    if pruseciky_x:
        x_prusecik = pruseciky_x[0];
        y_prusecik = np.polyval(p1, x_prusecik);
        print(f"Přesný průsečík fitu: x = {x_prusecik:.4f} cm, T = {y_prusecik:.4f} s");

        plt.scatter(x_prusecik, y_prusecik, color='green', s=30, zorder=5,
                    label=f'Průsečík [{x_prusecik:.2f}; {y_prusecik:.2f}]');
    else:
        print("Průsečíky nenalezeny gg alkane.");

    plt.xlabel(f'$C_2$ [cm]');
    plt.ylabel(f'$T_x$ [s]');
    plt.title("Eheir");
    plt.legend();
    plt.grid(True, alpha=0.3);

    # plt.show();
    plt.savefig(f'{script_dir}/grafe.svg', format='svg', bbox_inches='tight');


if __name__ == "__main__":
    main();