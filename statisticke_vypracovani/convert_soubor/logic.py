import io;
import re;
from pathlib import Path;
from utils import color_print;
from statisticke_vypracovani.base import Method;
from objects.measurement import Measurement;
from objects.measurement_set import MeasurementSet;

class ConvertSoubor(Method):
    name = "convert_soubor";
    description = "Konverze tabulkového souboru do formátu PROMĚNNÁ=data";

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru s daty",
                "required": True,
                "is_file": True
            },
            {
                "flags": ["-o", "--output"],
                "help": "Název výstupu (BEZ PŘÍPONY)",
                "required": False,
                "default": "output_convertor",
                "type": str
            },
        ];

    def run(self, args, returnFile=False):
        dir_name = "outputs";
        folder_path = Path(dir_name).resolve();
        folder_path.mkdir(parents=True, exist_ok=True);

        with open(args.input) as f:
            f = io.StringIO(f.read());

            header_labels = re.split(r'\s{2,}', f.readline().strip());
            header_units = re.split(r'\s{2,}', f.readline().strip());
            labels = header_labels[0].strip().split('\t');
            units = header_units[0].strip().split('\t');

            combined_headers = [f"{label} ({unit})" for label, unit in zip(labels, units)];

            import pandas as pd;
            df = pd.read_csv(f, sep='\t', decimal=',', skiprows=2, names=combined_headers);

            toWrite = {};
            for _, row in df.iterrows():
                for key in combined_headers:
                    if key not in toWrite: toWrite[key] = [];
                    toWrite[key].append(row[key]);

            ms = MeasurementSet();
            all_lines = [];
            for rowKey in toWrite:
                str_list = [str(val) for val in toWrite[rowKey]];
                match = re.search(r'\(([^\)]+)\)', rowKey);
                if match: key = match.group(1);
                else: raise Exception("Chyba v klici");

                line = f'{key}={",".join(str_list)}';
                all_lines.append(line);
                ms.add(Measurement(key, [float(v) for v in toWrite[rowKey]]));

        if returnFile:
            return ms;

        output_name = getattr(args, 'output', 'output_convertor') + '.txt';
        with open(folder_path / output_name, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_lines));

        print(
            f"Soubor {color_print.GREEN}uložen{color_print.END} pod názvem "
            f"{color_print.BOLD}{output_name}{color_print.END} cesta:\n"
            f"└──{folder_path / output_name}"
        );

        return ms;
