from typing import Any
import numpy as np
from pathlib import Path
from utils import color_print, locked_open
from statisticke_vypracovani.base import Method
from objects.input_parser import InputParser
from objects.measurement import Measurement
from objects.measurement_set import MeasurementSet


class Derivace(Method):
    name = "derivace"
    description = "Numerická derivace dat (central differences)"

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
                "help": "Název sloupce s nezávislou proměnnou (výchozí: první sloupec)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-y", "--y-col"],
                "help": "Název sloupce s závislou proměnnou (výchozí: druhý sloupec)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["-o", "--output"],
                "help": "Výstupní soubor bez přípony (výchozí: derivace_output)",
                "required": False,
                "default": "derivace_output",
                "type": str,
            },
        ]

    def run(self, args: Any, do_print: bool = True) -> dict:
        data = InputParser.from_file(args.input)
        x_name = getattr(args, 'x_col', None) or data[0].name
        y_name = getattr(args, 'y_col', None) or data[1].name
        x_m = data.get(x_name)
        y_m = data.get(y_name)
        x = x_m.values
        y = y_m.values
        if len(x) != len(y):
            raise ValueError(f"Různá délka sloupců: {x_name}={len(x)}, {y_name}={len(y)}")
        if len(x) < 3:
            raise ValueError("Derivace potřebuje aspoň 3 body")

        dy_dx = np.gradient(y, x)
        deriv_name = f"d{y_name}/d{x_name}"
        result = MeasurementSet()
        result.add(Measurement(x_name, x.tolist()))
        result.add(Measurement(deriv_name, dy_dx.tolist()))
        if do_print:
            print(f"Derivace {y_name} podle {x_name}")
            print(f"├──Počet bodů: {len(x)}")
            print(f"├──Rozsah {x_name}: [{x.min():.4g}, {x.max():.4g}]")
            print(f"├──Průměrná derivace: {dy_dx.mean():.4g}")
            print(f"└──Min/max derivace: [{dy_dx.min():.4g}, {dy_dx.max():.4g}]")
            print("-" * 100)
            folder = Path("outputs").resolve()
            folder.mkdir(parents=True, exist_ok=True)
            output_name = getattr(args, 'output', 'derivace_output') + ".txt"
            with locked_open(folder / output_name, 'w', encoding='utf-8') as f:
                f.write(f"{x_name}=" + ",".join(str(v) for v in x) + "\n")
                f.write(f"{deriv_name}=" + ",".join(str(v) for v in dy_dx) + "\n")
            print(f"{color_print.GREEN}Výstup:{color_print.END} {folder / output_name}")

        return result.to_dict()
