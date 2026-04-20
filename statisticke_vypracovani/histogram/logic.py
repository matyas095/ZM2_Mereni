import numpy as np;
import matplotlib.pyplot as plt;
from pathlib import Path;
from utils import print_graf_saved;
from statisticke_vypracovani.base import Method;
from objects.input_parser import InputParser;

class Histogram(Method):
    name = "histogram";
    description = "Histogram rozdělení dat + Gaussovka";

    def validate(self, args) -> None:
        import os;
        if not getattr(args, 'input', None):
            raise ValueError("Chybí vstupní soubor (-i)");
        if not os.path.isfile(args.input):
            raise ValueError(f"Soubor '{args.input}' neexistuje");

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru",
                "required": True,
                "is_file": True
            },
            {
                "flags": ["-c", "--column"],
                "help": "Sloupec pro histogram (výchozí: první)",
                "required": False,
                "type": str
            },
            {
                "flags": ["-b", "--bins"],
                "help": "Počet binů (výchozí: auto = sqrt(n))",
                "required": False,
                "type": int
            },
            {
                "flags": ["-n", "--name"],
                "help": "Název výstupního grafu",
                "required": False,
                "default": "histogram",
                "type": str
            },
            {
                "flags": ["--gauss"],
                "help": "Překryje Gaussovkou (normální rozdělení)",
                "required": False,
                "action": "store_true"
            }
        ];

    def run(self, args, do_print=True):
        data = InputParser.from_file(args.input);
        col_name = getattr(args, 'column', None) or data[0].name;
        m = data.get(col_name);

        values = m.values;
        n = len(values);
        bins = getattr(args, 'bins', None) or max(5, int(np.sqrt(n)));

        plt.figure(figsize=(9, 6));
        counts, bin_edges, _ = plt.hist(values, bins=bins, color='steelblue',
                                        edgecolor='black', alpha=0.7, label=f'Data (n={n})');

        if getattr(args, 'gauss', False):
            mu = float(np.mean(values));
            sigma = float(np.std(values, ddof=1));
            x = np.linspace(values.min(), values.max(), 200);
            bin_width = bin_edges[1] - bin_edges[0];
            gauss = n * bin_width * (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2);
            plt.plot(x, gauss, 'r-', linewidth=2, label=f'Gauss ($\\mu$={mu:.3g}, $\\sigma$={sigma:.3g})');

        plt.xlabel(col_name);
        plt.ylabel('Četnost');
        plt.title(f'Histogram: {col_name}');
        plt.grid(alpha=0.3);
        plt.legend();

        folder = Path("grafy_metoda_graf").resolve();
        folder.mkdir(parents=True, exist_ok=True);
        name = getattr(args, 'name', 'histogram');
        plt.savefig(f'{folder}/{name}.svg', format='svg', bbox_inches='tight');
        plt.show();
        plt.close();

        if do_print:
            print(f"{col_name}: n={n}, bins={bins}");
            print(f"├──min = {values.min():.4g}");
            print(f"├──max = {values.max():.4g}");
            print(f"├──mean = {np.mean(values):.4g}");
            print(f"└──σ = {np.std(values, ddof=1):.4g}");
            save_Location = print_graf_saved(name, folder);
        else: save_Location = None;

        return { "histogram": { "bins": bins, "n": n, "min": float(values.min()), "max": float(values.max()), "save_file": save_Location } };
