import numpy as np;
import matplotlib.pyplot as plt;
from scipy.optimize import curve_fit;
import math;

def model_funkce(t, k, q):
    return k * t + q;

def return_Cislo_Krat_10_Na(x):
    exponent = math.floor(math.log10(abs(x)));
    zaklad = x / 10**exponent;

    return f"{zaklad:.3f} * 10^{exponent}";

hodnoty = [];

with open("input") as f:
    for line in f:
        spl = line.split("=");
        hodnoty.append(np.array([float(x) for x in spl[-1].split(",")]));

print(hodnoty)

t = np.array([0, 600, 1200, 1800, 2400, 3000, 3600]);
U = np.array([300, 297, 291, 287, 284, 278, 274]);

sigma_U = np.array([0.1, 0.1, 0.1, 0.08, 0.08, 0.05, 0.05]);

ln_U = np.log(U);
sigma_ln_U = sigma_U / U;

popt, pcov = curve_fit(model_funkce, t, ln_U, sigma=sigma_ln_U, absolute_sigma=True);

k, q = popt;
sigma_k = np.sqrt(pcov[0, 0]);

plt.figure(figsize=(9, 6));
plt.errorbar(t, ln_U, yerr=sigma_ln_U, fmt='o', capsize=3, color='darkred', label='Chyba měření');
plt.plot(t, model_funkce(t, k, q), 'b-', label=f'Fit přímky ($k={return_Cislo_Krat_10_Na(k)}$)');

plt.xticks(t);

plt.xlabel('t [s]');
plt.ylabel('ln(U) [V]');
plt.title('Semilogaritmická regrese napětí vybíjenýho kondenzátoru bez připojeného odporu $R_x$');
plt.legend();
plt.grid(alpha=0.3);
plt.savefig('grafy/graf_vyrovnani.svg', format='svg', bbox_inches='tight');
# plt.show();


