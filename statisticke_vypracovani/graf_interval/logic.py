import numpy as np;
import matplotlib.pyplot as plt;
from pathlib import Path;
from sympy import symbols, lambdify;
from utils import clean_latex, smart_parse, print_graf_saved;
from statisticke_vypracovani.base import Method;

class GrafInterval(Method):
    name = "graf_interval";
    description = "Graf funkce na zadaném intervalu";

    def get_args_info(self):
        return [
            {
                "flags": ["-n", "--name"],
                "help": "Název grafu",
                "required": True,
                "type": str
            },
            {
                "flags": ["-r", "--rovnice"],
                "help": "Funkční závislost formát 'VELIČINA=VZTAH'\nNutná aby byla jedno proměnná.",
                "required": True,
                "type": str
            },
            {
                "flags": ["-i", "--interval"],
                "help": "Interval na kterým je vztah. Formát -i 10 100; Interval <10, 100>",
                "required": True,
                "nargs": 2,
                "type": float
            }
        ];

    def run(self, args):
        parsed_y, variables, nazev_rce = smart_parse(args.rovnice);

        start_int, end_int = args.interval;

        f = lambdify([symbols(v) for v in variables], parsed_y, 'numpy');
        x_Range = np.linspace(start_int, end_int, 1000);
        y_vals = f(x_Range)

        dir_name = "grafy_metoda_graf";
        folder_path = Path(dir_name).resolve();
        folder_path.mkdir(parents=True, exist_ok=True);

        plt.figure(figsize=(9, 6));
        from sympy import latex;
        plt.plot(x_Range, y_vals, label=r'$' + nazev_rce + ' = ' + latex(parsed_y) + '$');
        plt.xlabel(variables[0]);
        plt.ylabel(nazev_rce);
        plt.title(args.name);
        plt.grid(alpha=0.3);
        plt.legend();
        plt.savefig(f'{folder_path}/{args.name}.svg', format='svg', bbox_inches='tight');
        plt.show();
        print_graf_saved(args.name, folder_path, f"{nazev_rce}={parsed_y}");
        plt.close();
