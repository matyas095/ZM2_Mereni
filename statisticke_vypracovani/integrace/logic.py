from typing import Any
import numpy as np
from pathlib import Path
from scipy.integrate import cumulative_trapezoid
from utils import color_print, locked_open
from statisticke_vypracovani.base import Method
from objects.input_parser import InputParser
from objects.measurement import Measurement
from objects.measurement_set import MeasurementSet


class Integrace(Method):
    name = "integrace"
    description = "Numerická integrace (kumulativní lichoběžníková metoda)"

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
                "flags": ["-x", "--x-col"],
                "help": "Sloupec nezávislé proměnné (výchozí: první)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-y", "--y-col"],
                "help": "Sloupec integrované veličiny (výchozí: druhý)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["--initial"],
                "help": "Počáteční hodnota integrálu (výchozí: 0)",
                "required": False,
                "default": 0.0,
                "type": float,
            },
            {
                "flags": ["-o", "--output"],
                "help": "Výstupní soubor bez přípony (výchozí: integrace_output)",
                "required": False,
                "default": "integrace_output",
                "type": str,
            },
        ]

    def run(self, args: Any, do_print: bool = True) -> dict:
        data = InputParser.from_file(args.input)
        x_name = getattr(args, 'x_col', None) or data[0].name
        y_name = getattr(args, 'y_col', None) or data[1].name
        x_m = data.get(x_name)
        y_m = data.get(y_name)
        x = np.array(x_m.values)
        y = np.array(y_m.values)
        if len(x) != len(y):
            raise ValueError(f"Různá délka sloupců: {x_name}={len(x)}, {y_name}={len(y)}")
        if len(x) < 2:
            raise ValueError("Integrace potřebuje aspoň 2 body")

        initial = float(getattr(args, 'initial', 0.0))
        integ = cumulative_trapezoid(y, x, initial=initial)
        integ_name = f"∫{y_name}d{x_name}"
        result = MeasurementSet()
        result.add(Measurement(x_name, x.tolist()))
        result.add(Measurement(integ_name, integ.tolist()))
        if do_print:
            print(f"Integrace {y_name} podle {x_name}")
            print(f"├──Počet bodů: {len(x)}")
            print(f"├──Rozsah {x_name}: [{x.min():.4g}, {x.max():.4g}]")
            print(f"├──Počáteční hodnota: {initial:.4g}")
            print(f"└──Hodnota integrálu: {integ[-1]:.4g}")
            print("-" * 100)
            folder = Path("outputs").resolve()
            folder.mkdir(parents=True, exist_ok=True)
            output_name = getattr(args, 'output', 'integrace_output') + ".txt"
            with locked_open(folder / output_name, 'w', encoding='utf-8') as f:
                f.write(f"{x_name}=" + ",".join(str(v) for v in x) + "\n")
                f.write(f"{integ_name}=" + ",".join(str(v) for v in integ) + "\n")
            print(f"{color_print.GREEN}Výstup:{color_print.END} {folder / output_name}")

        return result.to_dict()
