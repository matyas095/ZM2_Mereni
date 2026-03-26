import numpy as np;
import matplotlib.pyplot as plt;
from scipy.optimize import curve_fit;
import math;

B = 2500;
R_inf = 0.1;
T_min, T_max = 293, 343;
T_range = np.linspace(T_min, T_max, 1000);

title1 = "Závislost R = R(T)";
R_vals = R_inf * np.exp(B / T_range);

plt.figure(figsize=(9, 6));
plt.plot(T_range, R_vals, label=r'$R = R_{\infty} e^{B/T}$');
plt.xlabel('T [K]');
plt.ylabel('R [$\Omega$]');
plt.title(title1);
plt.grid(alpha=0.3);
plt.legend();
plt.savefig(f'grafy/{title1}.svg', format='svg', bbox_inches='tight');
plt.close();

title2 = r"Závislost $\ln R = f(1/T)$";

inv_T = 1 / T_range;
ln_R_vals = np.log(R_inf) + B * inv_T;

plt.figure(figsize=(9, 6));
plt.plot(inv_T, ln_R_vals, label=r'$\ln R = \ln R_{\infty} + B/T$');

plt.xlabel('1/T [$K^{-1}$]');
plt.ylabel('ln R [-]');
plt.title(title2);
plt.grid(alpha=0.3);
plt.legend();

tick_temps = np.linspace(T_min, T_max, 6);
plt.xticks(1 / tick_temps);

plt.savefig(f'grafy/Závislost_logaritmická.svg', format='svg', bbox_inches='tight');
plt.close();