from typing import Any
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import chi2 as chi2_dist
from pathlib import Path
from sympy import symbols, lambdify, latex
from utils import color_print, return_Cislo_Krat_10_Na, contains_substring, return_FirstWord
from utils import clean_latex, smart_parse, parse_rovnice, print_graf_saved, r2_score
from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer
from statisticke_vypracovani.base import Method
from objects.input_parser import InputParser


def linear(x, a, b):
    return a * x + b


def quadratic(x, a, b, c):
    return a * x**2 + b * x + c


def exponential(x, a, b):
    return a * np.exp(b / x)


def power_law(x, a, b):
    return a * x**b


MODELY_FITU = {
    "linearni": linear,
    "kvadraticky": quadratic,
    "exponencialni": exponential,
    "mocninny": power_law,
}


class Graf(Method):
    name = "graf"
    description = "2D/3D graf s volitelným fitem a rovnicí"

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru s daty",
                "required": True,
                "is_file": True,
            },
            {"flags": ["-n", "--name"], "help": "Název grafu", "required": True, "type": str},
            {
                "flags": ["-r", "--rovnice"],
                "help": "Závislost prvních linky dat do druhé",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-p", "--parametr"],
                "help": "Vypočítá data jako 2D graf dle parametru f(x), funguje jenom s -r [--rovnice]",
                "type": str,
            },
            {
                "flags": ["-log", "--logaritmicky"],
                "help": "Zobrazí y-ovou osu v logaritmickým měřítku",
                "action": "store_true",
            },
            {
                "flags": ["-f", "--fit"],
                "help": "Udělá fit dle zadaného stavu. Format -f [linearni, kvadraticky, exponenciali, mocninny]\nNapř.: .. -f kvadraticky",
                "choices": ["linearni", "kvadraticky", "exponencialni", "mocninny"],
                "default": None,
                "required": False,
            },
            {
                "flags": ["--chi2"],
                "help": "Zobrazí chi-squared statistiku a panel reziduí",
                "action": "store_true",
            },
            {
                "flags": ["--plot-outliers"],
                "help": "Označí odlehlé body (3sigma) červeně",
                "required": False,
                "type": str,
                "const": "3sigma",
                "nargs": "?",
            },
            {
                "flags": ["--custom-fit"],
                "help": "Vlastní fit funkce ve formátu SymPy: 'a*sin(b*x+c)'",
                "required": False,
                "type": str,
            },
        ]

    def _compile_custom_fit(self, expr_str: str):
        """Převede 'a*sin(b*x+c)' na numpy funkci a seznam parametrů."""
        from sympy import symbols, lambdify
        from sympy.parsing.sympy_parser import parse_expr
        from utils import extract_variables

        all_vars = extract_variables(expr_str)
        if "x" not in all_vars:
            raise ValueError(f"Custom fit musí obsahovat proměnnou 'x': {expr_str}")
        params = [v for v in all_vars if v != "x"]
        sym_map = {name: symbols(name) for name in all_vars}
        expr = parse_expr(expr_str, local_dict=sym_map)
        fit_func = lambdify([symbols("x")] + [symbols(p) for p in params], expr, 'numpy')
        return fit_func, params

    def _print_fit_stats(self, popt, pcov, x, y, y_pred, sigma, fit_name):
        param_errors = np.sqrt(np.diag(pcov))
        param_names = ["a", "b", "c", "d"][: len(popt)]
        print(color_print.BOLD + f"Fit: {fit_name}" + color_print.END)
        for name, val, err in zip(param_names, popt, param_errors, strict=False):
            print(
                f"├──{color_print.UNDERLINE}{name}{color_print.END} = {return_Cislo_Krat_10_Na(val)} ± {return_Cislo_Krat_10_Na(err)}"
            )

        r2 = r2_score(y, y_pred)
        print(f"├──{color_print.UNDERLINE}R²{color_print.END} = {r2:.6f}")
        if sigma is not None and np.all(sigma > 0):
            chi2_val = np.sum(((y - y_pred) / sigma) ** 2)
            n_dof = len(x) - len(popt)
            chi2_red = chi2_val / n_dof if n_dof > 0 else float('inf')
            p_value = 1 - chi2_dist.cdf(chi2_val, n_dof) if n_dof > 0 else 0
            print(f"├──{color_print.UNDERLINE}χ²{color_print.END} = {chi2_val:.4f}")
            print(f"├──{color_print.UNDERLINE}χ²_red{color_print.END} = {chi2_red:.4f}  (ν = {n_dof})")
            print(f"└──{color_print.UNDERLINE}p-hodnota{color_print.END} = {p_value:.4f}")
        else:
            print(f"└──{color_print.UNDERLINE}χ²{color_print.END} = nelze (chybí nejistoty)")
        print("-" * 100)

    def _plot_with_residuals(
        self, x, y, y_pred, sigma, popt, pcov, fit_func, fit_name, args, pathToDir, x_key, y_key
    ):
        fig, (ax_main, ax_res) = plt.subplots(
            2, 1, figsize=(9, 8), gridspec_kw={'height_ratios': [3, 1]}, sharex=True
        )
        label_text = f"Fit {fit_name}: " + ", ".join([f"${return_Cislo_Krat_10_Na(p)}$" for p in popt])
        x_fit = np.linspace(min(x), max(x), 500)
        y_fit = fit_func(x_fit, *popt)
        ax_main.errorbar(x, y, yerr=sigma, fmt='o', capsize=3, color='darkred', label='Data')
        ax_main.plot(x_fit, y_fit, 'b-', label=label_text)
        if sigma is not None and np.all(sigma > 0):
            chi2_val = np.sum(((y - y_pred) / sigma) ** 2)
            n_dof = len(x) - len(popt)
            chi2_red = chi2_val / n_dof if n_dof > 0 else float('inf')
            ax_main.text(
                0.02,
                0.95,
                f"$\\chi^2_{{red}} = {chi2_red:.2f}$",
                transform=ax_main.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.5},
            )

        ax_main.set_ylabel(f'{y_key}')
        ax_main.set_title(args.name)
        ax_main.legend()
        ax_main.grid(alpha=0.3)
        if sigma is not None and np.all(sigma > 0):
            norm_residuals = (y - y_pred) / sigma
        else:
            norm_residuals = y - y_pred

        ax_res.errorbar(
            x,
            norm_residuals,
            yerr=1 if sigma is not None and np.all(sigma > 0) else None,
            fmt='o',
            capsize=3,
            color='darkred',
        )
        ax_res.axhline(0, color='gray', linestyle='--')
        ax_res.axhspan(-1, 1, alpha=0.1, color='gray')
        ax_res.set_xlabel(f'{x_key}')
        ax_res.set_ylabel('Rezidua / σ' if sigma is not None and np.all(sigma > 0) else 'Rezidua')
        ax_res.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight')
        plt.show()
        plt.close()

    def _args_Rovnice_2D_Slice(self, PROMENA, args, pathToDir, fix_var='y', fix_value=None):
        x_vals = PROMENA[0, 1]
        y_vals = PROMENA[1, 1]
        nazev_rovnice, rovnice = parse_rovnice(args.rovnice)
        parsed_y, clean_vars, _ = smart_parse(rovnice)
        var_x = return_FirstWord(PROMENA[0, 0])
        var_y = return_FirstWord(PROMENA[1, 0])
        if not contains_substring(var_x, clean_vars) or not contains_substring(var_y, clean_vars):
            raise ValueError("Chybí mi veličiny v rovnici...")

        variables = [return_FirstWord(PROMENA[0, 0]), return_FirstWord(PROMENA[1, 0])]
        f = lambdify(variables, parsed_y, 'numpy')
        plt.figure(figsize=(8, 5))
        if fix_var == 'y':
            val = fix_value if fix_value is not None else y_vals[len(y_vals) // 2]
            Z_slice = [f(x, val) for x in x_vals]
            plt.plot(x_vals, Z_slice, 'b-', linewidth=2)
            plt.xlabel(f"${clean_latex(PROMENA[0, 0])}$")
            plt.title(f"Řez grafem pro ${clean_latex(PROMENA[1, 0])} = {val}$")
        else:
            val = fix_value if fix_value is not None else x_vals[len(x_vals) // 2]
            Z_slice = [f(val, y) for y in y_vals]
            plt.plot(y_vals, Z_slice, 'r-', linewidth=2)
            plt.xlabel(f"${clean_latex(PROMENA[1, 0])}$")
            plt.title(f"Řez grafem pro ${clean_latex(PROMENA[0, 0])} = {val}$")

        plt.ylabel(f"${clean_latex(nazev_rovnice)}$")
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{pathToDir}/{args.name}_2D_slice.svg', bbox_inches='tight')
        plt.show()

    def _args_Rovnice(self, PROMENA, args, pathToDir):
        nazev_rovnice, rovnice = parse_rovnice(args.rovnice)
        parsed_y, clean_vars, _ = smart_parse(rovnice)
        if getattr(args, 'parametr', False):
            sym_list = [symbols(args.parametr)]
            f = lambdify(sym_list, parsed_y, 'numpy')
            U_range = np.linspace(min(PROMENA[0, 1]), max(PROMENA[0, 1]), 1000)
            plt.figure(figsize=(9, 6))
            plt.plot(U_range, f(U_range), label=rf'$R = {latex(parsed_y)}$')
            plt.xlabel(PROMENA[0, 0])
            plt.ylabel(nazev_rovnice)
            plt.title(args.name)
            plt.grid(alpha=0.3)
            plt.legend()
            plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight', pad_inches=0.5)
            plt.show()
            print_graf_saved(args.name, pathToDir, f"{nazev_rovnice}={rovnice}")
            plt.close()
            return

        x_vals = np.array(PROMENA[0, 1])
        y_vals = np.array(PROMENA[1, 1])
        var_x = return_FirstWord(PROMENA[0, 0])
        var_y = return_FirstWord(PROMENA[1, 0])
        if not contains_substring(var_x, clean_vars) or not contains_substring(var_y, clean_vars):
            raise ValueError("Chybí mi veličiny v rovnici...")

        variables = [return_FirstWord(PROMENA[0, 0]), return_FirstWord(PROMENA[1, 0])]
        f = lambdify(variables, parsed_y, 'numpy')
        X_vals, Y_vals = np.meshgrid(x_vals, y_vals)
        Z_vals = f(X_vals, Y_vals)
        fig = plt.figure(figsize=(10, 7))
        fig.subplots_adjust(left=0.1, right=0.85, bottom=0.1, top=0.85)
        ax = fig.add_subplot(111, projection='3d')
        ax.set_box_aspect(None, zoom=0.8)  # type: ignore

        surf = ax.plot_surface(X_vals, Y_vals, Z_vals, cmap='coolwarm', antialiased=True)  # type: ignore

        ax.set_xlabel(f"${clean_latex(PROMENA[0, 0])}$", labelpad=10)
        ax.set_ylabel(f"${clean_latex(PROMENA[1, 0])}$", labelpad=10)

        z_label_text = clean_latex(nazev_rovnice)
        ax.set_zlabel(f"${z_label_text}$", labelpad=20)

        title_str = f"Závislost ${z_label_text}$ na ${variables[0]}$ a ${variables[1]}$\nVztah: ${z_label_text}$ = ${latex(parsed_y).replace('mathtt', 'mathrm')}$"
        ax.set_title(title_str, pad=25)

        fig.colorbar(surf, shrink=0.5, aspect=15, pad=0.05)
        plt.show()
        ax.view_init(elev=ax.elev, azim=ax.azim)
        fig.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight', pad_inches=0.5)
        print_graf_saved(args.name, pathToDir, f"{nazev_rovnice}={rovnice}")

    def _prep_Plot(self, data, args, pathToDir, ignoreRovnice=False):
        PROMENA = data.to_numpy()
        if args.rovnice and not ignoreRovnice:
            self._args_Rovnice(PROMENA, args, pathToDir)
            return

        aritm = AritmetickyPrumer()
        x_m = data[0]
        y_m = data[1]
        x_Range = np.array(x_m.values)
        x_key = x_m.name
        y_Range = np.array(y_m.values)
        y_key = y_m.name
        custom_fit_expr = getattr(args, 'custom_fit', None)
        if custom_fit_expr:
            fit_func_raw, params = self._compile_custom_fit(custom_fit_expr)

            def fit_func(x, *p):
                return fit_func_raw(x, *p)

            if args.logaritmicky:
                y_Range = np.log(y_Range)
            aritm_result = aritm.run({x_key: list(x_m.values)}, False)
            sigma = aritm_result[x_key][-1] / np.array(y_m.values) if aritm_result[x_key][-1] > 0 else None
            p0 = [1.0] * len(params)
            popt, pcov = curve_fit(
                fit_func,
                x_Range,
                y_Range,
                p0=p0,
                sigma=sigma,
                absolute_sigma=bool(sigma is not None),
                maxfev=5000,
            )
            y_pred = fit_func(x_Range, *popt)
            param_errors = np.sqrt(np.diag(pcov))
            print(color_print.BOLD + f"Custom fit: {custom_fit_expr}" + color_print.END)
            for name, val, err in zip(params, popt, param_errors, strict=False):
                print(f"├──{color_print.UNDERLINE}{name}{color_print.END} = {val:.4g} ± {err:.4g}")
            print(f"└──{color_print.UNDERLINE}R²{color_print.END} = {r2_score(y_Range, y_pred):.6f}")
            print("-" * 100)
            label_text = f"Fit: {custom_fit_expr}"
            plt.figure(figsize=(9, 6))
            x_fit = np.linspace(x_Range.min(), x_Range.max(), 500)
            plt.plot(x_fit, fit_func(x_fit, *popt), 'b-', label=label_text)
            plt.plot(x_Range, y_Range, 'ro', label='Data')
            plt.xlabel(f'{x_key}')
            plt.ylabel(f'{y_key}')
            plt.title(args.name)
            plt.legend()
            plt.grid(alpha=0.3)
            plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight')
            plt.show()
            plt.close()
            print_graf_saved(args.name, pathToDir)
            return

        if args.fit:
            fit_func = MODELY_FITU[args.fit]
            if args.logaritmicky:
                y_Range = np.log(y_Range)

            aritm_result = aritm.run({x_key: list(x_m.values)}, False)
            sigma = aritm_result[x_key][-1] / np.array(y_m.values) if aritm_result[x_key][-1] > 0 else None
            popt, pcov = curve_fit(
                fit_func, x_Range, y_Range, absolute_sigma=True, sigma=sigma if sigma is not None else None
            )
            y_pred = fit_func(x_Range, *popt)
            if getattr(args, 'chi2', False):
                self._print_fit_stats(popt, pcov, x_Range, y_Range, y_pred, sigma, args.fit)
                self._plot_with_residuals(
                    x_Range,
                    y_Range,
                    y_pred,
                    sigma,
                    popt,
                    pcov,
                    fit_func,
                    args.fit,
                    args,
                    pathToDir,
                    x_key,
                    y_key,
                )
            else:
                label_text = f"Fit {args.fit}: " + ", ".join(
                    [f"${return_Cislo_Krat_10_Na(p)}$" for p in popt]
                )
                plt.figure(figsize=(9, 6))
                plt.plot(x_Range, fit_func(x_Range, *popt), 'b-', label=label_text)
                if sigma is not None:
                    plt.errorbar(
                        x_Range,
                        y_Range,
                        yerr=sigma,
                        fmt='o',
                        capsize=3,
                        color='darkred',
                        label='Chyba měření',
                    )
                else:
                    plt.plot(x_Range, y_Range, 'ro', label='Data')
                plt.xlabel(f'{x_key}')
                plt.ylabel(f'{y_key}')
                plt.title(args.name)
                plt.legend()
                plt.grid(alpha=0.3)
                plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight')
                plt.show()
                plt.close()

            print_graf_saved(args.name, pathToDir)
            return

        plt.figure(figsize=(9, 6))
        plot_outliers = getattr(args, 'plot_outliers', None)
        if plot_outliers:
            cleaned = y_m.remove_outliers(plot_outliers)
            outlier_set = set(cleaned.removed_values)
            outlier_mask = np.array([v in outlier_set for v in y_Range])
            if outlier_mask.any():
                plt.plot(x_Range[~outlier_mask], y_Range[~outlier_mask], 'bo-', label='Data')
                plt.plot(
                    x_Range[outlier_mask],
                    y_Range[outlier_mask],
                    'ro',
                    markersize=10,
                    label=f'Outlier ({plot_outliers})',
                )
                print(f"Odstraněno outlierů ({plot_outliers}): {int(outlier_mask.sum())}/{len(y_Range)}")
            else:
                plt.plot(x_Range, y_Range, 'b-', label='Graf závislosti')
        else:
            plt.plot(x_Range, y_Range, 'b-', label='Graf závislosti')

        plt.xlabel(f'{x_key}')
        plt.ylabel(f'{y_key}')
        plt.title(args.name)
        plt.legend()
        plt.grid(alpha=0.3)
        plt.savefig(f'{pathToDir}/{args.name}.svg', format='svg', bbox_inches='tight')
        plt.show()
        plt.close()
        print_graf_saved(args.name, pathToDir)

    def validate(self, args) -> None:
        import os

        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)")
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje")
        if not getattr(args, 'name', None):
            raise ValueError("Chybí název grafu (-n)")

    def run(self, args: Any, do_print: bool = True) -> dict:
        data = InputParser.from_file(args.input)
        dir_name = "grafy_metoda_graf"
        folder_path = Path(dir_name).resolve()
        folder_path.mkdir(parents=True, exist_ok=True)
        if do_print:
            print(f"Zpracovávám údaje pro hodnoty {', '.join(data.names)}")
        self._prep_Plot(data, args, str(folder_path))
        return {"name": args.name, "path": str(folder_path / f"{args.name}.svg"), "n_series": len(data)}
