import math;
from utils import get_Promeny, color_print, return_Cislo_Krat_10_Na;
import matplotlib.pyplot as plt;
from scipy.optimize import curve_fit;
import math;

def fit(t):
    return k * t + q

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

def run(args):
    PROMENA = get_Promeny(args);

    print(f"Zpracovávám údaje pro hodnoty {", ".join(PROMENA[:, 0])}");

    toPrint = {};

    for obj in PROMENA:
        key, data = obj
        if any(not isinstance(x, (int, float)) for x in data): raise ValueError(f"V datech s proměnnou {color_print.BOLD}{color_print.UNDERLINE}{key}{color_print.END} je někde string místo int/float.")
        
        sum_Data = ( 1 / len(data) ) * sum(data);
        odchylka = sum([(x - sum_Data) ** 2 for x in data]);
        sigma_sum_Data = math.sqrt( odchylka / (len(data)*(len(data) - 1)));
        toPrint[key] = [sum_Data, sigma_sum_Data];
 
    
    for key, arr in toPrint.items():
        print(color_print.BOLD + key + color_print.END);

        for j, val in enumerate(arr):
            connector = "└──" if j == len(arr) - 1 else "├──";
            what = "Aritmetický průměr" if j == 0 else "Chyba aritmetického průměru";

            print(f"{connector}{color_print.UNDERLINE}{what}{color_print.END} = {val}");
        print("-" * 100);

    return;
