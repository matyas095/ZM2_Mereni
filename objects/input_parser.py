from objects.measurement import Measurement;
from objects.measurement_set import MeasurementSet;

def try_convert(s):
    if not isinstance(s, str): return s;
    try:
        return int(s);
    except ValueError:
        try:
            return float(s);
        except ValueError:
            return s;

class InputParser:
    @staticmethod
    def parse_standard(file_path: str, u_B_map: dict = None) -> MeasurementSet:
        u_B_map = u_B_map or {};
        with open(file_path) as f:
            lines = [x for x in f.read().split("\n") if x.strip()];

        ms = MeasurementSet();
        for line in lines:
            parts = line.split("=");
            key = parts[0].strip();
            values = [try_convert(v.strip()) for v in parts[1].split(",")];

            if any(not isinstance(x, (int, float)) for x in values):
                raise ValueError(f"V datech s proměnnou '{key}' je někde string místo čísla.");

            u_b = u_B_map.get(key, 0.0);
            ms.add(Measurement(key, values, u_B=u_b));

        return ms;

    @staticmethod
    def parse_dict(data: dict, u_B_map: dict = None) -> MeasurementSet:
        return MeasurementSet.from_dict(data, u_B_map);

    @staticmethod
    def parse_indent(file_path: str) -> dict:
        result = {};
        path = {-4: result};

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue;

                indent = len(line) - len(line.lstrip());
                clean_line = line.strip();

                if "=" in clean_line:
                    key, val = [x.strip() for x in clean_line.split("=", 1)];
                    try:
                        parts = [float(x.strip()) for x in val.split(",") if x.strip()];
                        if len(parts) == 1:
                            processed_val = parts[0];
                        else:
                            processed_val = parts;
                    except ValueError:
                        processed_val = val;
                else:
                    key = clean_line;
                    processed_val = {};

                parent_level = indent - 4;
                while parent_level not in path and parent_level > -4:
                    parent_level -= 4;

                parent_dict = path[parent_level];
                parent_dict[key] = processed_val;

                if isinstance(processed_val, dict):
                    path[indent] = processed_val;
                else:
                    path[indent] = parent_dict[key] = {
                        "__value__": processed_val
                    };

        return InputParser._cleanup_structure(result);

    @staticmethod
    def parse_xlsx(file_path: str) -> MeasurementSet:
        import pandas as pd;
        df = pd.read_excel(file_path).dropna(how='all');
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')];

        ms = MeasurementSet();
        for col in df.columns:
            values = df[col].astype(float).tolist();
            ms.add(Measurement(col, values));

        return ms;

    @staticmethod
    def parse_cassy(file_path: str, u_B_map: dict = None) -> MeasurementSet:
        import re;
        u_B_map = u_B_map or {};

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [l.rstrip() for l in f if l.strip()];

        header_line = lines[1];

        headers = re.findall(r'(\S+)\s*\(([^)]*)\)', header_line);
        if not headers:
            parts = re.split(r'\s{2,}|\t', header_line);
            headers = [(p.strip(), "") for p in parts if p.strip()];

        col_names = [name for name, unit in headers];
        columns = {name: [] for name in col_names};

        for line in lines[2:]:
            values = re.split(r'\s{2,}|\t', line.strip());
            for i, val in enumerate(values):
                if i < len(col_names):
                    num = float(val.strip().replace(',', '.'));
                    columns[col_names[i]].append(num);

        ms = MeasurementSet();
        for name, unit in headers:
            unit_clean = unit.strip() if unit else "";
            display_name = f"{name} [{unit_clean if unit_clean else '-'}]";
            u_b = u_B_map.get(name, u_B_map.get(display_name, 0.0));
            ms.add(Measurement(display_name, columns[name], u_B=u_b));

        return ms;

    @staticmethod
    def _detect_cassy(file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.readline();
                second_line = f.readline();
            return '(' in second_line and ')' in second_line;
        except Exception:
            return False;

    @staticmethod
    def from_file(file_path: str, u_B_map: dict = None) -> MeasurementSet:
        if file_path.endswith(".xlsx"):
            return InputParser.parse_xlsx(file_path);
        if InputParser._detect_cassy(file_path):
            return InputParser.parse_cassy(file_path, u_B_map);
        return InputParser.parse_standard(file_path, u_B_map);

    @staticmethod
    def _cleanup_structure(d):
        if not isinstance(d, dict): return d;
        if "__value__" in d and len(d) == 1: return d["__value__"];
        return {k: InputParser._cleanup_structure(v) for k, v in d.items()};
