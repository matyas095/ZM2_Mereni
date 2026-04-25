from typing import Any;
from pathlib import Path;
from utils import color_print, locked_open;
from statisticke_vypracovani.base import Method;
from statisticke_vypracovani.join_tables.logic import JoinTables;

class ExtractTable(Method):
    name = "extract_table";
    description = "Vytáhne data z LaTeX tabulky zpět do formátu VELIČINA=data";

    def validate(self, args) -> None:
        import os;
        inp = getattr(args, 'input', None);
        if not inp:
            raise ValueError("Chybí vstupní soubor (-i)");
        if not os.path.isfile(inp):
            raise ValueError(f"Soubor '{inp}' neexistuje");

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Vstupní .tex soubor",
                "required": True,
                "is_file": True,
                "type": str
            },
            {
                "flags": ["-o", "--output"],
                "help": "Výstupní soubor bez přípony (výchozí: extracted)",
                "required": False,
                "default": "extracted",
                "type": str
            },
            {
                "flags": ["--keep-units"],
                "help": "Zachová jednotku v názvu sloupce (X [s]=...)",
                "required": False,
                "action": "store_true"
            }
        ];

    def _clean_header(self, header: str, keep_units: bool) -> str:
        from objects.units import parse_tex_header, format_name_unit;
        var, unit = parse_tex_header(header);
        if keep_units and unit:
            return format_name_unit(var, unit);
        return var;

    def run(self, args: Any, do_print: bool = True) -> dict:
        jt = JoinTables();
        _, headers, rows, _, _ = jt._parse_tex(args.input);

        keep_units = getattr(args, 'keep_units', False);

        clean_headers = [self._clean_header(h, keep_units) for h in headers];

        columns = {h: [] for h in clean_headers};
        for row in rows:
            for i, h in enumerate(clean_headers):
                if i >= len(row):
                    continue;
                v = row[i].strip();
                if v == "-" or not v:
                    continue;
                v = v.replace(",", ".");
                columns[h].append(v);

        folder = Path("outputs").resolve();
        folder.mkdir(parents=True, exist_ok=True);
        output_name = getattr(args, 'output', 'extracted') + ".txt";
        output_path = folder / output_name;

        with locked_open(output_path, 'w', encoding='utf-8') as f:
            for h, vals in columns.items():
                f.write(f"{h}=" + ",".join(vals) + "\n");

        if do_print:
            print(f"{color_print.GREEN}Data extrahována{color_print.END}: {output_path}");
            print(f"└──sloupce: {len(clean_headers)} ({', '.join(clean_headers)})");
            print(f"└──řádků:   {len(rows)}");

        return dict(columns);
