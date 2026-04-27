from objects.measurement import Measurement
from objects.measurement_set import MeasurementSet


def try_convert(s):
    if not isinstance(s, str):
        return s
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


class InputParser:
    @staticmethod
    def parse_standard(file_path: str, u_B_map: dict = None) -> MeasurementSet:
        u_B_map = u_B_map or {}
        with open(file_path) as f:
            lines = [x for x in f.read().split("\n") if x.strip()]

        ms = MeasurementSet()
        for line in lines:
            parts = line.split("=")
            key = parts[0].strip()
            values = [try_convert(v.strip()) for v in parts[1].split(",")]
            if any(not isinstance(x, (int, float)) for x in values):
                raise ValueError(f"V datech s proměnnou '{key}' je někde string místo čísla.")

            u_b = u_B_map.get(key, 0.0)
            ms.add(Measurement(key, values, u_B=u_b))

        return ms

    @staticmethod
    def parse_dict(data: dict, u_B_map: dict = None) -> MeasurementSet:
        return MeasurementSet.from_dict(data, u_B_map)

    @staticmethod
    def parse_indent(file_path: str) -> dict:
        result = {}
        path = {-4: result}
        with open(file_path, encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                indent = len(line) - len(line.lstrip())
                clean_line = line.strip()
                if "=" in clean_line:
                    key, val = [x.strip() for x in clean_line.split("=", 1)]
                    try:
                        parts = [float(x.strip()) for x in val.split(",") if x.strip()]
                        if len(parts) == 1:
                            processed_val = parts[0]
                        else:
                            processed_val = parts
                    except ValueError:
                        processed_val = val
                else:
                    key = clean_line
                    processed_val = {}

                parent_level = indent - 4
                while parent_level not in path and parent_level > -4:
                    parent_level -= 4

                parent_dict = path[parent_level]
                parent_dict[key] = processed_val
                if isinstance(processed_val, dict):
                    path[indent] = processed_val
                else:
                    path[indent] = parent_dict[key] = {"__value__": processed_val}

        return InputParser._cleanup_structure(result)

    @staticmethod
    def parse_xlsx(file_path: str) -> MeasurementSet:
        import pandas as pd

        df = pd.read_excel(file_path).dropna(how='all')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        ms = MeasurementSet()
        for col in df.columns:
            values = df[col].astype(float).tolist()
            ms.add(Measurement(col, values))

        return ms

    @staticmethod
    def parse_cassy(file_path: str, u_B_map: dict = None) -> MeasurementSet:
        import re

        u_B_map = u_B_map or {}
        with open(file_path, encoding='utf-8') as f:
            lines = [l.rstrip() for l in f if l.strip()]

        header_line = lines[1]
        headers = re.findall(r'(\S+)\s*\(([^)]*)\)', header_line)
        if not headers:
            parts = re.split(r'\s{2,}|\t', header_line)
            headers = [(p.strip(), "") for p in parts if p.strip()]

        col_names = [name for name, unit in headers]
        columns = {name: [] for name in col_names}
        for line in lines[2:]:
            values = re.split(r'\s{2,}|\t', line.strip())
            for i, val in enumerate(values):
                if i < len(col_names):
                    num = float(val.strip().replace(',', '.'))
                    columns[col_names[i]].append(num)

        ms = MeasurementSet()
        for name, unit in headers:
            unit_clean = unit.strip() if unit else ""
            display_name = f"{name} [{unit_clean if unit_clean else '-'}]"
            u_b = u_B_map.get(name, u_B_map.get(display_name, 0.0))
            ms.add(Measurement(display_name, columns[name], u_B=u_b))

        return ms

    @staticmethod
    def _detect_cassy(file_path: str) -> bool:
        try:
            with open(file_path, encoding='utf-8') as f:
                f.readline()
                second_line = f.readline()
            return '(' in second_line and ')' in second_line
        except Exception:
            return False

    @staticmethod
    def parse_toml(file_path: str, u_B_map: dict = None) -> MeasurementSet:
        """Parsuje TOML soubor s `[veliciny.<nazev>]` sekcemi do MeasurementSet.

        Pro `ap`, `regrese`, `derivace`, `graf`, `histogram`, `integrace`.
        Pro `neprima_chyba` se pouziva slozitejsi schema, viz `NeprimaChyba._toml_input`.
        """
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # Python 3.10 fallback
        import math

        u_B_map = u_B_map or {}
        with open(file_path, "rb") as f:
            cfg = tomllib.load(f)

        veliciny = cfg.get("veliciny", {})
        if not veliciny:
            raise ValueError(
                f"TOML soubor '{file_path}' nema zadnou sekci [veliciny.<nazev>]."
            )

        ms = MeasurementSet()
        for name, vinfo in veliciny.items():
            values = vinfo.get("hodnoty")
            if values is None:
                raise ValueError(f"Velicina '{name}' nema klic 'hodnoty'")

            tb = vinfo.get("typ_b")
            if tb is None:
                u_B = u_B_map.get(name, 0.0)
            elif isinstance(tb, (int, float)):
                u_B = float(tb)
            elif isinstance(tb, dict):
                a = float(tb.get("a", 0.0))
                dist = str(tb.get("distribuce", "rovnomerne")).strip()
                if dist == "rovnomerne":
                    u_B = a / math.sqrt(3)
                elif dist == "trojuhelnikove":
                    u_B = a / math.sqrt(6)
                elif dist == "normalni":
                    u_B = a / 2.0
                else:
                    raise ValueError(f"Velicina '{name}': nezname rozlozeni '{dist}'.")
            else:
                raise ValueError(f"Velicina '{name}': typ_b musi byt cislo nebo dict.")

            unit = vinfo.get("unit")
            display_name = f"{name} [{unit}]" if unit else name
            ms.add(Measurement(display_name, list(values), u_B=u_B))

        return ms

    @staticmethod
    def from_file(file_path: str, u_B_map: dict = None) -> MeasurementSet:
        if file_path.endswith(".xlsx"):
            return InputParser.parse_xlsx(file_path)
        if file_path.endswith(".toml"):
            return InputParser.parse_toml(file_path, u_B_map)
        if InputParser._detect_cassy(file_path):
            return InputParser.parse_cassy(file_path, u_B_map)
        return InputParser.parse_standard(file_path, u_B_map)

    @staticmethod
    def _cleanup_structure(d):
        if not isinstance(d, dict):
            return d
        if "__value__" in d and len(d) == 1:
            return d["__value__"]
        return {k: InputParser._cleanup_structure(v) for k, v in d.items()}
