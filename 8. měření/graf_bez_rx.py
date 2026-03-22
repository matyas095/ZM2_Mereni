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

def prep_Plot(h, name, title):
    t = h[0];
    U = h[1];

    chyby_U = h[2];

    ln_U = np.log(U);
    chyba_ln_U = chyby_U / U;

    popt, pcov = curve_fit(fit, t, ln_U, sigma=chyba_ln_U, absolute_sigma=True);

    k, q = popt;
    chyba_k = np.sqrt(pcov[0, 0]);

    plt.figure(figsize=(9, 6));
    plt.errorbar(t, ln_U, yerr=chyba_ln_U, fmt='o', capsize=3, color='darkred', label='Chyba měření');
    plt.plot(t, fit(t, k, q), 'b-', 
             label=f'Fit přímky ($k={return_Cislo_Krat_10_Na(k)}$, $q={return_Cislo_Krat_10_Na(q)}$)');

    plt.xticks(t);

    plt.xlabel('t [s]');
    plt.ylabel('ln(U) [V]');
    plt.title(title);
    plt.legend();
    plt.grid(alpha=0.3);
    plt.savefig(f'grafy/{name}.svg', format='svg', bbox_inches='tight');
    plt.close();

hodnoty = [];

with open("input") as f:
    for line in f:
        spl = line.split("=");
        hodnoty.append(np.array([float(x) for x in spl[-1].split(",")]));

print(hodnoty)

prep_Plot(
    hodnoty[0] + hodnoty[1] + hodnoty[2], 
    "graf_bez_rx",
    "Semilogaritmická regrese napětí vybíjenýho kondenzátoru bez připojeného odporu $R_x$"
);

