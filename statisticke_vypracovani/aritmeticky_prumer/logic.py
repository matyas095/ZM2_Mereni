from typing import Any
import math
import json
from statisticke_vypracovani.base import Method
from objects.input_parser import InputParser


def _apply_distribution(a: float, rozlozeni: str) -> float:
    match rozlozeni:
        case "rovnomerne":
            return a / math.sqrt(3)
        case "trojuhelnikove":
            return a / math.sqrt(6)
        case "normalni":
            return a / 2
        case _:
            return float(a)


def _parse_typ_b_simple(spec: str) -> tuple[str, float]:
    """Parsuje 'KEY=hodnota[:rozlozeni]' → (KEY, u_B). Default rozlozeni: rovnomerne."""
    if "=" not in spec:
        raise ValueError(f"Neplatný --typ-b zápis '{spec}'. Očekávaný formát: KEY=hodnota[:rozlozeni]")
    key, rest = spec.split("=", 1)
    if ":" in rest:
        a_str, rozlozeni = rest.split(":", 1)
        return key.strip(), _apply_distribution(float(a_str), rozlozeni.strip())
    return key.strip(), _apply_distribution(float(rest), "rovnomerne")


def _parse_typ_b(raw) -> dict:
    """Parsuje --typ-b. Podporuje:
    - JSON string/dict: {"t": 0.5, "U": [1, "rovnomerne"]}
    - Seznam stringů (z opakovatelného flagu): ["t=0.5", "U=1:rovnomerne"]
    - Seznam s jediným JSON stringem: ['{"R": 0.01}']
    """
    if not raw:
        return {}
    if isinstance(raw, list):
        if len(raw) == 1 and raw[0].lstrip().startswith("{"):
            raw = raw[0]
        else:
            u_B_map = {}
            for spec in raw:
                key, val = _parse_typ_b_simple(spec)
                u_B_map[key] = val
            return u_B_map
    if isinstance(raw, str):
        raw = json.loads(raw)
    u_B_map = {}
    for key, val in raw.items():
        if isinstance(val, list):
            a, rozlozeni = val[0], val[1] if len(val) > 1 else "rovnomerne"
            u_B_map[key] = _apply_distribution(a, rozlozeni)
        else:
            u_B_map[key] = float(val)
    return u_B_map


class AritmetickyPrumer(Method):
    name = "aritmeticky_prumer"
    description = "Aritmetický průměr + chyba aritmetického průměru"

    def validate(self, args) -> None:
        import os

        if isinstance(args, dict):
            if not args:
                raise ValueError("Prázdný vstupní dict pro aritmeticky_prumer")
            return
        batch = getattr(args, 'batch', None)
        inp = getattr(args, 'input', None)
        if batch:
            import glob

            if not glob.glob(batch):
                raise ValueError(f"Batch glob '{batch}' neodpovídá žádnému souboru")
        elif inp:
            if not os.path.isfile(inp):
                raise ValueError(f"Soubor '{inp}' neexistuje")
        else:
            raise ValueError("Chybí vstup: použij -i SOUBOR nebo --batch GLOB")

    def get_args_info(self):
        return [
            {
                "flags": ["-i", "--input"],
                "help": "Cesta k vstupnímu souboru s daty",
                "required": True,
                "is_file": True,
            },
            {
                "flags": ["-lt", "--latextable"],
                "help": "Vypíše data do tabulek v LaTeXu.",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["-tb", "--typ-b"],
                "help": "Nejistota typu B. Opakovatelný flag: -tb R=0.01 -tb U=1:rovnomerne, nebo JSON: '{\"R\": [0.01, \"rovnomerne\"]}'",
                "required": False,
                "action": "append",
                "type": str,
            },
            {
                "flags": ["-ol", "--outliers"],
                "help": "Odstranění outlierů: '3sigma' (výchozí), '2sigma', 'iqr'",
                "required": False,
                "type": str,
                "const": "3sigma",
                "nargs": "?",
            },
            {
                "flags": ["--caption"],
                "help": "Vlastní caption pro LaTeX tabulku (jinak auto-generace)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["--label"],
                "help": "Vlastní label pro LaTeX tabulku (bez tab: prefix)",
                "required": False,
                "type": str,
            },
            {
                "flags": ["--verbose"],
                "help": "Vypisovat detaily parsování a výpočtů",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--dry-run"],
                "help": "Ukáže co by se udělalo ale nic nezapíše",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--export-csv"],
                "help": "Exportuje výsledky do CSV souboru",
                "required": False,
                "type": str,
            },
            {
                "flags": ["--batch"],
                "help": "Glob pro zpracování více souborů najednou (např. 'input/*.txt')",
                "required": False,
                "type": str,
            },
            {
                "flags": ["--si-normalize"],
                "help": "Převede jednotky na základní SI (mA → A, kV → V, ...)",
                "required": False,
                "action": "store_true",
            },
            {
                "flags": ["--convert-units"],
                "help": "Převede jednotky dle JSON: '{\"I\": \"A\", \"U\": \"mV\"}'",
                "required": False,
                "type": json.loads,
            },
            {
                "flags": ["-ru", "--rel-uncertainty"],
                "help": "Doplní relativní nejistotu (δ = u_c/|μ|·100%) do captionu LaTeX tabulky. Vyžaduje -lt.",
                "required": False,
                "action": "store_true",
            },
        ]

    def run(self, args: Any, do_print: bool = True) -> dict:
        from objects.config import config

        cfg = config()
        batch = getattr(args, 'batch', None) if not isinstance(args, dict) else None
        if batch:
            import glob

            files = sorted(glob.glob(batch))
            if not files:
                from utils import color_print

                print(f"{color_print.RED}Žádné soubory neodpovídají: {batch}{color_print.END}")
                return {}
            try:
                from tqdm import tqdm

                iterator = tqdm(files, desc="Zpracovávám", unit="soubor")
                use_tqdm = True
            except ImportError:
                iterator = files
                use_tqdm = False
                print(f"Zpracovávám {len(files)} souborů...")
            results = {}
            for idx, f in enumerate(iterator, 1):
                if not use_tqdm:
                    print(f"\n  [{idx}/{len(files)}] {f}")
                args.input = f
                args.batch = None
                results[f] = self.run(args, do_print=do_print and not use_tqdm)
            return results

        u_B_map = {}
        verbose = getattr(args, 'verbose', False) if not isinstance(args, dict) else False
        verbose = verbose or cfg.get("verbose", False)
        dry_run = getattr(args, 'dry_run', False) if not isinstance(args, dict) else False
        if not isinstance(args, dict):
            u_B_map = _parse_typ_b(getattr(args, 'typ_b', None))

        if verbose:
            from utils import color_print

            src = args if isinstance(args, dict) else args.input
            print(f"{color_print.DARKCYAN}[verbose]{color_print.END} Vstup: {src}")
            if u_B_map:
                print(f"{color_print.DARKCYAN}[verbose]{color_print.END} u_B_map: {u_B_map}")

        if isinstance(args, dict):
            data = InputParser.parse_dict(args, u_B_map)
        else:
            data = InputParser.from_file(args.input, u_B_map)

        if verbose:
            from utils import color_print

            print(
                f"{color_print.DARKCYAN}[verbose]{color_print.END} Načteno {len(data)} veličin: {', '.join(data.names)}"
            )
            for m in data:
                print(
                    f"{color_print.DARKCYAN}[verbose]{color_print.END}   {m.name}: n={m.n}, precision={m.precision}"
                )

        if not isinstance(args, dict):
            if getattr(args, 'si_normalize', False):
                data = data.si_normalize()
                if verbose:
                    from utils import color_print

                    print(
                        f"{color_print.DARKCYAN}[verbose]{color_print.END} SI normalized: {', '.join(data.names)}"
                    )
            conversions = getattr(args, 'convert_units', None)
            if conversions:
                data = data.convert_units(conversions)
                if verbose:
                    from utils import color_print

                    print(
                        f"{color_print.DARKCYAN}[verbose]{color_print.END} Converted: {', '.join(data.names)}"
                    )

        outliers_mode = getattr(args, 'outliers', None) if not isinstance(args, dict) else None
        if outliers_mode is None:
            outliers_mode = cfg.get("default_outliers")
        if outliers_mode:
            from objects.measurement_set import MeasurementSet

            cleaned = MeasurementSet()
            for m in data:
                cleaned.add(m.remove_outliers(outliers_mode))
            data = cleaned
            if verbose:
                from utils import color_print

                total_removed = sum(len(m.removed_values) for m in data)
                print(
                    f"{color_print.DARKCYAN}[verbose]{color_print.END} Outlier mode: {outliers_mode}, odstraněno {total_removed}"
                )

        if do_print:
            quiet = getattr(args, 'quiet', False) if not isinstance(args, dict) else False
            data.print_results(quiet=quiet)

        if do_print and getattr(args, 'latextable', None):
            source = getattr(args, 'input', None) if not isinstance(args, dict) else None
            data.to_latex_table(
                source_file=source,
                custom_caption=getattr(args, 'caption', None),
                custom_label=getattr(args, 'label', None),
                dry_run=dry_run,
                include_rel_uncertainty=getattr(args, 'rel_uncertainty', False),
            )

        export_csv = getattr(args, 'export_csv', None) if not isinstance(args, dict) else None
        if export_csv and not dry_run:
            data.to_csv(export_csv)
            from utils import color_print

            print(f"{color_print.GREEN}CSV exportováno:{color_print.END} {export_csv}")
        elif export_csv and dry_run:
            from utils import color_print

            print(f"{color_print.YELLOW}[DRY-RUN] CSV by bylo: {export_csv}{color_print.END}")

        return data.to_dict()
