# To RUN: python3 [py] graf_vypocty.py -i INPUT_FILE_PATH

import re;
import argparse;
from pathlib import Path;
import numpy as np;
import math;
import matplotlib.pyplot as plt;
import os;
import sys;
import shutil
import tomllib;

parent_dir = Path(__file__).resolve().parent;
script_dir = parent_dir / "grafy";
script_dir.mkdir(parents=True, exist_ok=True);


def print_centered_header(text, filler="="):
    terminal_width = shutil.get_terminal_size(fallback=(80, 24)).columns;

    padded_text = f" {text} " if text else "";

    print(padded_text.center(terminal_width, filler));


def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10 ** exponent;

    return f"{zaklad:.3f} * 10^{exponent}";


def plt_Legend():
    handles, labels = plt.gca().get_legend_handles_labels();

    data_points = [];
    fits = [];
    intersections = [];

    for h, l in zip(handles, labels):
        if hasattr(h, 'lines') or "Container" in type(h).__name__:
            data_points.append((h, l));
        elif "PathCollection" in type(h).__name__ or "Průsečík" in l:
            intersections.append((h, l));
        else:
            fits.append((h, l));

    sorted_pairs = data_points + fits + intersections;

    ordered_handles = [pair[0] for pair in sorted_pairs];
    ordered_labels = [pair[1] for pair in sorted_pairs];

    plt.legend(ordered_handles, ordered_labels);

def monte_Carl(p1, p2, chyby_p1, chyby_p2, x_Range, x_prusecik):
    N_simulaci = 1000;
    simulovane_pruseciky = [];

    for _ in range(N_simulaci):
        p1_nahodny = np.random.normal(p1, chyby_p1)
        p2_nahodny = np.random.normal(p2, chyby_p2)

        # Spočítáme průsečík pro tuto simulaci
        p_diff_nahodny = p1_nahodny - p2_nahodny
        roots_nahodny = np.roots(p_diff_nahodny)

        pruseciky_x_nahodny = [
            float(r.real) for r in roots_nahodny
            if np.isreal(r) and min(x_Range) <= r.real <= max(x_Range)
        ]

        if pruseciky_x_nahodny:
            simulovane_pruseciky.append(pruseciky_x_nahodny[0])

    # Výsledná směrodatná odchylka je chybou našeho průsečíku
    if simulovane_pruseciky:
        sigma_x_prusecik = np.std(simulovane_pruseciky)
        print_centered_header("MONTE KÁRL", filler="=")
        print(f"Statistická chyba průsečíku x (z fitu): ± {sigma_x_prusecik:.4f} cm")
        print(f"Konečný zápis: x = ({x_prusecik:.2f} ± {sigma_x_prusecik:.2f}) cm")
        print_centered_header("", filler="=")
    else:
        sigma_x_prusecik = 0
        print("Chybu průsečíku nebylo možné nasimulovat.")


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

    mask = x_Range > 91.5
    x_fit = x_Range[mask]
    T_1_fit = T_1_Range[mask]
    T_2_fit = T_2_Range[mask]

    p1, cov1 = np.polyfit(x_fit, T_1_fit, 2, cov=True);
    p2, cov2 = np.polyfit(x_fit, T_2_fit, 2, cov=True);

    a1, b1, c1 = p1;
    a2, b2, c2 = p2;

    chyby_p1 = np.sqrt(np.diagonal(cov1));
    chyby_p2 = np.sqrt(np.diagonal(cov2));


    print_centered_header("Koeficienty kvadratických fitů");

    print("P1");
    print(f"├─a = {a1:.4f} ± {chyby_p1[0]:.4f} cm");
    print(f"├─b = {b1:.4f} ± {chyby_p1[1]:.4f} cm");
    print(f"└─c = {c1:.4f} ± {chyby_p1[2]:.4f} cm");

    print("P2")
    print(f"├─a = {a2:.4f} ± {chyby_p2[0]:.4f} cm");
    print(f"├─b = {b2:.4f} ± {chyby_p2[1]:.4f} cm");
    print(f"└─c = {c2:.4f} ± {chyby_p2[2]:.4f} cm");

    print_centered_header("");
    print("")


    x_line = np.linspace(min(x_Range), max(x_Range), 10000);

    plt.figure(figsize=(9, 6));
    # plt.scatter(x_Range, T_1_Range, color='blue', s=10, label='$T_1$ [s]');
    # plt.scatter(x_Range, T_2_Range, color='red', s=10, label='$T_2$ [s]');
    plt.errorbar(x_Range, T_1_Range,
                 xerr=0.5, yerr=0.0001,
                 fmt='o', color='blue', ecolor='lightblue', elinewidth=1, capsize=3, markersize=5,
                 label='$T_1$ [s]');
    plt.errorbar(x_Range, T_2_Range,
                 xerr=0.5, yerr=0.0001,
                 fmt='o', color='red', ecolor='tomato', elinewidth=1, capsize=3, markersize=5,
                 label='$T_2$ [s]');
    plt.plot(x_line, np.polyval(p1, x_line), color='blue', linestyle='dashed', label='Kvadratický fit: $T_1$');
    plt.plot(x_line, np.polyval(p2, x_line), color='red', linestyle='dashed', label='Kvadratický fit: $T_2$');

    p_diff = p1 - p2;

    roots = np.roots(p_diff);

    pruseciky_x = [float(r.real) for r in roots if np.isreal(r) and min(x_Range) <= r.real <= max(x_Range)];

    if pruseciky_x:
        x_prusecik = pruseciky_x[0];
        y_prusecik = np.polyval(p1, x_prusecik);
        print(f"Přesný průsečík fitu: x = {x_prusecik:.4f} cm, T = {y_prusecik:.4f} s");

        plt.scatter(x_prusecik, y_prusecik, color='green', s=30, zorder=5,
                    label=f'Průsečík [{x_prusecik:.1f}; {y_prusecik:.1f}]');
        monte_Carl(p1, p2, chyby_p1, chyby_p2, x_Range, x_prusecik);
    else:
        print("Průsečíky nenalezeny gg alkane.");

    plt.xlabel(f'$C_2$ [cm]');
    plt.ylabel(f'$T_x$ [s]');
    plt.title("Grafické znázornění měření doby kmitů v závislosti na vzdálenosti");
    plt_Legend();
    plt.grid(True, alpha=0.1);

    # plt.show();
    plt.savefig(f'{script_dir}/grafe.svg', format='svg', bbox_inches='tight');


if __name__ == "__main__":
    main();