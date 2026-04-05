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

        with open(args.input, encoding='utf-8') as f:
            lines = [l for l in f.read().splitlines() if l.strip()];

        if len(lines) < 2:
            raise Exception("Soubor má méně než 2 řádky");

        # Detekce formátu: CASSY má hlavičku s "(...)" na druhém řádku (první je metadata)
        if '(' in lines[1] and ')' in lines[1]:
            combined_headers = [x.strip() for x in lines[1].split('\t') if x.strip()];
            data_start = 2;
        else:
            labels = [x.strip() for x in lines[0].split('\t') if x.strip()];
            units = [x.strip() for x in lines[1].split('\t') if x.strip()];
            combined_headers = [f"{label} ({unit})" for label, unit in zip(labels, units)];
            data_start = 2;

        toWrite = {h: [] for h in combined_headers};
        for raw in lines[data_start:]:
            cells = [c.strip().replace(',', '.') for c in raw.split('\t')];
            for i, h in enumerate(combined_headers):
                if i < len(cells) and cells[i]:
                    toWrite[h].append(cells[i]);

        ms = MeasurementSet();
        all_lines = [];
        for rowKey in combined_headers:
            match = re.match(r'\s*([^\s(]+)\s*\(([^)]*)\)', rowKey);
            if match:
                var_name = match.group(1).strip();
                unit = match.group(2).strip();
                key = f"{var_name} [{unit}]" if unit else var_name;
            else:
                key = rowKey.strip();
            line = f'{key}={",".join(toWrite[rowKey])}';
            all_lines.append(line);
            try:
                ms.add(Measurement(key, [float(v) for v in toWrite[rowKey]]));
            except ValueError:
                pass;

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
