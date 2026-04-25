import math;
import numpy as np;
from scipy.optimize import curve_fit;
from scipy.stats import chi2 as chi2_dist;
from utils import color_print, r2_score;
from statisticke_vypracovani.base import Method;
from objects.input_parser import InputParser;


def _linear(x, a, b):
    return a * x + b;


class Regrese(Method):
    name = "regrese";
    description = "Lineární regrese: a, b, R², χ², kovariance (bez grafu)";

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru",
                "required": True,
                "is_file": True
            },
            {
                "flags": ["-x", "--x-col"],
                "help": "Sloupec nezávislé proměnné (výchozí: první)",
                "required": False,
                "type": str
            },
            {
                "flags": ["-y", "--y-col"],
                "help": "Sloupec závislé proměnné (výchozí: druhý)",
                "required": False,
                "type": str
            },
            {
                "flags": ["-s", "--sigma"],
                "help": "Sloupec s nejistotami y (pro chi-squared)",
                "required": False,
                "type": str
            }
        ];

    def validate(self, args) -> None:
        import os;
        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)");
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje");

    def run(self, args, do_print: bool = True) -> dict:
        data = InputParser.from_file(args.input);

        x_name = getattr(args, 'x_col', None) or data[0].name;
        y_name = getattr(args, 'y_col', None) or data[1].name;
        sigma_name = getattr(args, 'sigma', None);

        x = np.asarray(data.get(x_name).values, dtype=float);
        y = np.asarray(data.get(y_name).values, dtype=float);

        sigma = None;
        if sigma_name:
            sigma = np.asarray(data.get(sigma_name).values, dtype=float);

        popt, pcov = curve_fit(_linear, x, y, sigma=sigma, absolute_sigma=bool(sigma is not None));
        a, b = popt;
        a_err, b_err = np.sqrt(np.diag(pcov));

        y_pred = _linear(x, a, b);
        r2 = r2_score(y, y_pred);

        result = {
            "a": [float(a), float(a_err)],
            "b": [float(b), float(b_err)],
            "R2": float(r2),
            "n": int(len(x)),
            "cov_ab": float(pcov[0, 1]),
        };

        if sigma is not None and np.all(sigma > 0):
            chi2 = float(np.sum(((y - y_pred) / sigma) ** 2));
            n_dof = len(x) - 2;
            chi2_red = chi2 / n_dof if n_dof > 0 else float("inf");
            p_value = float(1 - chi2_dist.cdf(chi2, n_dof)) if n_dof > 0 else 0.0;
            result["chi2"] = chi2;
            result["chi2_red"] = chi2_red;
            result["n_dof"] = n_dof;
            result["p_value"] = p_value;

        if do_print:
            print(color_print.BOLD + f"Lineární regrese: y = a·x + b" + color_print.END);
            print(f"├──{color_print.UNDERLINE}a{color_print.END} = ({a:.4g} ± {a_err:.4g})");
            print(f"├──{color_print.UNDERLINE}b{color_print.END} = ({b:.4g} ± {b_err:.4g})");
            print(f"├──{color_print.UNDERLINE}R²{color_print.END} = {r2:.6f}");
            print(f"├──{color_print.UNDERLINE}Cov(a,b){color_print.END} = {pcov[0, 1]:.4g}");
            if "chi2" in result:
                print(f"├──{color_print.UNDERLINE}χ²{color_print.END} = {result['chi2']:.4f}");
                print(f"├──{color_print.UNDERLINE}χ²_red{color_print.END} = {result['chi2_red']:.4f} (ν = {result['n_dof']})");
                print(f"└──{color_print.UNDERLINE}p-hodnota{color_print.END} = {result['p_value']:.4f}");
            else:
                print(f"└──{color_print.UNDERLINE}n{color_print.END} = {result['n']}");
            print("-" * 100);

        return result;
