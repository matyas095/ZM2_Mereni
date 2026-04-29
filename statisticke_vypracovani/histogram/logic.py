import re
from typing import Any
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pathlib import Path
from utils import print_graf_saved
from statisticke_vypracovani.base import Method
from objects.input_parser import InputParser


def _sanitize_for_filename(s: str) -> str:
    """Nahradi vse co neni alfanumericke, podtrzitko nebo tecka, podtrzitkem."""
    return re.sub(r'[^A-Za-z0-9._-]+', '_', s).strip('_')


class Histogram(Method):
    name = "histogram"
    description = "Histogram rozdělení dat + Gaussovka"

    def validate(self, args) -> None:
        import os

        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)")
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje")

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru",
                "required": True,
                "is_file": True,
            },
            {
                "flags": ["-c", "--column"],
                "help": "Sloupec pro histogram (výchozí: ALL — histogram pro každou veličinu)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-b", "--bins"],
                "help": "Počet binů (výchozí: auto = sqrt(n))",
                "required": False,
                "type": int,
            },
            {
                "flags": ["-n", "--name"],
                "help": "Název výstupního grafu (přidá se '_<velicina>' pro multi-mode)",
                "required": False,
                "default": "histogram",
                "type": str,
            },
            {
                "flags": ["--gauss"],
                "help": "Překryje Gaussovkou (normální rozdělení)",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--combined"],
                "help": "Vykreslí všechny veličiny do jednoho grafu místo samostatných souborů.",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--colors"],
                "help": "Čárkou oddělené barvy pro --combined režim (např. 'red,green,blue'). "
                "Výchozí: matplotlib tab10 cyklus.",
                "required": False,
                "type": str,
            },
        ]

    def _bins_for(self, args, n: int) -> int:
        return getattr(args, 'bins', None) or max(5, int(np.sqrt(n)))

    def _label_for(self, col_name: str) -> str:
        from objects.units import extract_name_unit

        var, unit = extract_name_unit(col_name)
        return f"${var}$ [{unit}]" if unit else var

    def _plot_one(self, m, args, output_filename: str, folder: Path) -> dict:
        """Vykresli histogram pro jednu Measurement m a ulozi do folder/output_filename.svg."""
        col_name = m.name
        values = m.values
        n = len(values)
        bins = self._bins_for(args, n)
        plt.figure(figsize=(9, 6))
        counts, bin_edges, _ = plt.hist(
            values,
            bins=bins,
            color='steelblue',
            edgecolor='black',
            alpha=0.7,
            label=f'Data (n={n})',
        )
        if getattr(args, 'gauss', False):
            mu = float(np.mean(values))
            sigma = float(np.std(values, ddof=1))
            x = np.linspace(values.min(), values.max(), 200)
            bin_width = bin_edges[1] - bin_edges[0]
            gauss = (
                n * bin_width * (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
            )
            plt.plot(
                x,
                gauss,
                'r-',
                linewidth=2,
                label=f'Gauss ($\\mu$={mu:.3g}, $\\sigma$={sigma:.3g})',
            )

        ax = plt.gca()
        widths = np.diff(bin_edges)
        smallest_width = float(np.min(widths)) if len(widths) else 1.0
        if smallest_width > 0:
            decimals_needed = max(0, int(np.ceil(-np.log10(smallest_width))) + 1)
        else:
            decimals_needed = 4
        decimals_needed = min(decimals_needed, 6)
        tick_labels = [f"{e:.{decimals_needed}f}" for e in bin_edges]
        ax.set_xticks(bin_edges)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))

        display_label = self._label_for(col_name)
        plt.xlabel(display_label)
        plt.ylabel('Četnost')
        plt.title(f'Histogram: {display_label}')
        plt.grid(True, which='major', alpha=0.3)
        plt.legend()
        plt.savefig(f'{folder}/{output_filename}.svg', format='svg', bbox_inches='tight')
        plt.show()
        plt.close()

        return {
            "column": col_name,
            "bins": bins,
            "n": n,
            "min": float(values.min()),
            "max": float(values.max()),
            "mean": float(np.mean(values)),
            "sigma": float(np.std(values, ddof=1)),
            "save_file": f'{folder}/{output_filename}.svg',
        }

    def _plot_combined(self, measurements: list, args, output_filename: str, folder: Path) -> dict:
        """Vykresli vsechny veliciny do jednoho grafu, kazdou s vlastni barvou."""
        # Vyber barev: --colors prebije, jinak default tab10 cyklus.
        colors_arg = getattr(args, 'colors', None)
        if colors_arg:
            color_list = [c.strip() for c in colors_arg.split(',') if c.strip()]
        else:
            color_list = plt.rcParams['axes.prop_cycle'].by_key()['color']

        plt.figure(figsize=(10, 6))
        per_var_info = {}
        for i, m in enumerate(measurements):
            col_name = m.name
            values = m.values
            n = len(values)
            bins = self._bins_for(args, n)
            color = color_list[i % len(color_list)]
            label_disp = self._label_for(col_name)
            counts, bin_edges, _ = plt.hist(
                values,
                bins=bins,
                color=color,
                edgecolor='black',
                alpha=0.5,
                label=f'{label_disp} (n={n})',
            )
            if getattr(args, 'gauss', False):
                mu = float(np.mean(values))
                sigma = float(np.std(values, ddof=1))
                x = np.linspace(values.min(), values.max(), 200)
                bin_width = bin_edges[1] - bin_edges[0]
                gauss = (
                    n
                    * bin_width
                    * (1 / (sigma * np.sqrt(2 * np.pi)))
                    * np.exp(-0.5 * ((x - mu) / sigma) ** 2)
                )
                plt.plot(
                    x,
                    gauss,
                    color=color,
                    linewidth=2,
                    linestyle='--',
                    label=f'Gauss {label_disp} ($\\mu$={mu:.3g}, $\\sigma$={sigma:.3g})',
                )

            per_var_info[col_name] = {
                "column": col_name,
                "bins": bins,
                "n": n,
                "min": float(values.min()),
                "max": float(values.max()),
                "mean": float(np.mean(values)),
                "sigma": float(np.std(values, ddof=1)),
                "color": color,
            }

        ax = plt.gca()
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        plt.xlabel('Hodnota')
        plt.ylabel('Četnost')
        plt.title('Histogram (kombinovaný)')
        plt.grid(True, which='major', alpha=0.3)
        plt.legend(loc='best')
        save_path = f'{folder}/{output_filename}.svg'
        plt.savefig(save_path, format='svg', bbox_inches='tight')
        plt.show()
        plt.close()

        for v in per_var_info.values():
            v["save_file"] = save_path
        return per_var_info

    def run(self, args: Any, do_print: bool = True) -> dict:
        data = InputParser.from_file(args.input)
        folder = Path("grafy_metoda_graf").resolve()
        folder.mkdir(parents=True, exist_ok=True)
        base_name = getattr(args, 'name', 'histogram') or 'histogram'
        col_arg = getattr(args, 'column', None)
        combined = getattr(args, 'combined', False)

        if col_arg:
            measurements = [data.get(col_arg)]
        else:
            measurements = list(data.measurements)

        results = {}

        if combined and len(measurements) > 1:
            info = self._plot_combined(measurements, args, base_name, folder)
            results.update(info)
            if do_print:
                for col_name, stats in info.items():
                    print(f"{col_name}: n={stats['n']}, bins={stats['bins']}, color={stats['color']}")
                    print(f"├──min = {stats['min']:.4g}")
                    print(f"├──max = {stats['max']:.4g}")
                    print(f"├──mean = {stats['mean']:.4g}")
                    print(f"└──σ = {stats['sigma']:.4g}")
                print_graf_saved(base_name, folder)
        else:
            multi = len(measurements) > 1
            for m in measurements:
                from objects.units import extract_name_unit

                _var, _ = extract_name_unit(m.name)
                output_name = f"{base_name}_{_sanitize_for_filename(_var)}" if multi else base_name
                info = self._plot_one(m, args, output_name, folder)
                results[m.name] = info
                if do_print:
                    print(f"{m.name}: n={info['n']}, bins={info['bins']}")
                    print(f"├──min = {info['min']:.4g}")
                    print(f"├──max = {info['max']:.4g}")
                    print(f"├──mean = {info['mean']:.4g}")
                    print(f"└──σ = {info['sigma']:.4g}")
                    print_graf_saved(output_name, folder)

        return {"histogram": results}
