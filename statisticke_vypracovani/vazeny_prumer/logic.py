import math;
import numpy as np;
from utils import color_print;
from statisticke_vypracovani.base import Method;

class VazenyPrumer(Method):
    name = "vazeny_prumer";
    description = "Vážený průměr s nejistotami jednotlivých měření";

    def get_args_info(self):
        return [
            {
                "flags": ["-v", "--values"],
                "help": "Naměřené hodnoty oddělené čárkou: '10.2,10.3,10.1'",
                "required": True,
                "type": str
            },
            {
                "flags": ["-u", "--uncertainties"],
                "help": "Nejistoty jednotlivých měření: '0.1,0.05,0.2'",
                "required": True,
                "type": str
            },
            {
                "flags": ["-n", "--name"],
                "help": "Název veličiny",
                "required": False,
                "default": "x",
                "type": str
            }
        ];

    def run(self, args, doPrint=True):
        values = np.array([float(x.strip()) for x in args.values.split(",")]);
        sigmas = np.array([float(x.strip()) for x in args.uncertainties.split(",")]);
        name = getattr(args, 'name', 'x') or 'x';

        if len(values) != len(sigmas):
            raise ValueError(f"Počet hodnot ({len(values)}) neodpovídá počtu nejistot ({len(sigmas)})");

        if np.any(sigmas <= 0):
            raise ValueError("Nejistoty musí být kladné");

        weights = 1.0 / sigmas**2;
        w_mean = np.sum(weights * values) / np.sum(weights);
        w_sigma = 1.0 / math.sqrt(np.sum(weights));

        result = {
            name: {
                "vazeny_prumer": w_mean,
                "nejistota": w_sigma,
                "n": len(values),
                "hodnoty": list(values),
                "nejistoty": list(sigmas)
            }
        };

        if doPrint:
            print(color_print.BOLD + name + color_print.END);
            print(f"├──{color_print.UNDERLINE}Vážený průměr{color_print.END} = {w_mean}");
            print(f"├──{color_print.UNDERLINE}Nejistota{color_print.END} = {w_sigma}");
            print(f"├──{color_print.UNDERLINE}Počet měření{color_print.END} = {len(values)}");
            print(f"└──{color_print.UNDERLINE}Výsledek{color_print.END} = {w_mean:.6g} ± {w_sigma:.6g}");
            print("-" * 100);

        return result;
