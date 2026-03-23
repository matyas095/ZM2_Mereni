import numpy as np;
import matplotlib.pyplot as plt;
from scipy.optimize import curve_fit;
import math;

def fit(t, k, q):
    return k * t + q;

def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10**exponent;

    return f"{zaklad:.3f} * 10^{exponent}";

def prep_Plot(hodnoty, chyby, title):
    t = hodnoty[0];
    U = hodnoty[1];

    ln_U = np.log(U);
    chyba_ln_U = chyby[1] / U;

    popt, pcov = curve_fit(fit, t, ln_U, sigma=chyba_ln_U, absolute_sigma=True);

    k, q = popt;
    chyba_k = np.sqrt(pcov[0, 0]);

    plt.figure(figsize=(9, 6));
    plt.errorbar(t, ln_U, yerr=chyba_ln_U, fmt='o', capsize=3, color='darkred', label='Chyba měření');
    plt.plot(t, fit(t, k, q), 'b-', 
             label=f'Fit přímky ($k={return_Cislo_Krat_10_Na(k)}$, $q={return_Cislo_Krat_10_Na(q)}$)');

    plt.xticks(t);

    plt.xlabel('t [s]');
    plt.ylabel('ln(U/V) [-]');
    plt.title(title);
    plt.legend();
    plt.grid(alpha=0.3);
    plt.savefig(f'grafy/{title}.svg', format='svg', bbox_inches='tight');
    plt.close();

    return (k, q, chyba_k);

hodnoty = {};

with open("input.txt", "r") as f:
    current_tag = "";
    select_Tag = False;
    for line in f:
        if("-----------" in line): select_Tag = True; continue;
        spl = line.split("=");
        if(select_Tag == True): 
            select_Tag = False; 
            current_tag = spl[0].split("\n")[0]; 
            hodnoty[current_tag] = {}; 
            hodnoty[current_tag]["hodnoty"] = [];
            hodnoty[current_tag]["chyby"] = [];
            continue;

        hodnoty[current_tag]["hodnoty"].append(np.array([float(x) for x in spl[-2].split(",")]));
        hodnoty[current_tag]["chyby"].append(np.array([float(x) for x in spl[-1].split(",")]));

kapacita_C = 0.0000000470;
R_0 = 1;
R_0_chyba = 1;
R = 1;
R_chyba = 1;

for k, v in hodnoty.items():
    k_primky, q_primky, chyba_k = prep_Plot(
        v["hodnoty"],
        v["chyby"],
        k
    );

    if "bez" in k:
        R_0 = (-1 / (k_primky * kapacita_C));
        R_0_chyba = (R_0 * chyba_k / abs(k_primky));
    else:
        R = (-1 / (k_primky * kapacita_C));
        R_chyba = (R * chyba_k / abs(k_primky));

R_x = (R * R_0)/(R_0 - R);
R_x_Chyba = 1 / ((R_0 - R) ** 2) * math.sqrt((R_0 ** 4) * (R_0_chyba ** 2) + (R ** 4) * (R_chyba ** 2));

print(f"R_0 = {R_0}");
print(f"> Chyba R_0 = {R_0_chyba}");
print(f"R = {R}");
print(f"> Chyba R = {R_chyba}");
print(f"R_x = {R_x}");
print(f"> Chyba R_x = {R_x_Chyba}");

