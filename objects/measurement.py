import math
from collections.abc import Sequence
import numpy as np
from utils import color_print, return_Cislo_Krat_10_Na, round_half_up


class Measurement:
    name: str
    values: np.ndarray
    u_B: float
    removed_values: list
    original_n: int
    is_derived: bool = False

    def __init__(self, name: str, values: Sequence[int | float], u_B: float = 0.0) -> None:
        self.name = name
        self.values = np.array(values, dtype=float)
        self.u_B = u_B
        self._mean: float | None = None
        self._u_A: float | None = None
        self._u_c: float | None = None
        self._precision: int | None = None
        self.removed_values = []
        self.original_n = len(self.values)

    @property
    def n(self) -> int:
        return len(self.values)

    @property
    def mean(self) -> float:
        if self._mean is None:
            self._mean = float(np.mean(self.values))
        return self._mean

    @property
    def u_A(self) -> float:
        if self._u_A is None:
            arr = np.asarray(self.values, dtype=np.float64)
            odchylka = float(np.sum((arr - self.mean) ** 2))
            self._u_A = math.sqrt(odchylka / (self.n * (self.n - 1)))
        return self._u_A

    @property
    def u_c(self) -> float:
        if self._u_c is None:
            self._u_c = math.sqrt(self.u_A**2 + self.u_B**2)
        return self._u_c

    @property
    def precision(self) -> int:
        return self.precision_for("u_c")

    def precision_for(self, source: str = "u_c") -> int:
        """Pocet des. mist odvozeny z chyby zvoleneho typu (u_c / u_A / u_B).

        Pro `u_B = 0` (typ B nedeklarovan) padaji volajici zpet na `u_c`,
        jinak by precision = 2 z fallbacku skryval skutecny rozsah dat.
        """
        key = source.lower().replace("_", "")
        if key in ("uc", "c"):
            err = self.u_c
        elif key in ("ua", "a"):
            err = self.u_A
        elif key in ("ub", "b"):
            err = self.u_B
            if err == 0:
                err = self.u_c
        else:
            raise ValueError(f"Neznamy zdroj precision: {source!r} (povolene: u_c, u_A, u_B)")
        if err == 0:
            return 2
        for p in range(3):
            if round(abs(err), p) != 0:
                return p
        return 2

    def expanded_uncertainty(self, k: int = 2) -> float:
        return k * self.u_c

    def si_normalize(self) -> "Measurement":
        """Převede hodnoty na základní SI jednotku (mA → A atd.)."""
        from objects.units import extract_name_unit, parse_unit, format_name_unit

        var, unit = extract_name_unit(self.name)
        if unit is None:
            return self
        factor, base_unit = parse_unit(unit)
        if factor == 1.0 and base_unit == unit:
            return self
        new_name = format_name_unit(var, base_unit)
        new_values = (self.values * factor).tolist()
        new = Measurement(new_name, new_values, u_B=self.u_B * factor)
        new.removed_values = [v * factor for v in self.removed_values]
        new.original_n = self.original_n
        return new

    def convert_to(self, target_unit: str) -> "Measurement":
        """Převede hodnoty na zadanou jednotku (např. 'A' z 'mA')."""
        from objects.units import extract_name_unit, convert_factor, format_name_unit

        var, unit = extract_name_unit(self.name)
        if unit is None:
            raise ValueError(f"Veličina '{self.name}' nemá jednotku, nelze převést")
        factor = convert_factor(unit, target_unit)
        new_name = format_name_unit(var, target_unit)
        new_values = (self.values * factor).tolist()
        new = Measurement(new_name, new_values, u_B=self.u_B * factor)
        new.removed_values = [v * factor for v in self.removed_values]
        new.original_n = self.original_n
        return new

    def remove_outliers(self, method: str = "3sigma") -> "Measurement":
        """Vrátí novou Measurement bez outlierů."""
        if self.n < 4:
            return self

        vals = self.values
        if method == "iqr":
            q1, q3 = np.percentile(vals, [25, 75])
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (vals >= lo) & (vals <= hi)
            if np.all(mask):
                return self
            removed = vals[~mask].tolist()
            kept = vals[mask].tolist()
        else:
            try:
                k = float(method.replace("sigma", "").strip() or "3")
            except ValueError:
                k = 3.0
            kept = vals.tolist()
            removed = []
            for _ in range(10):
                arr = np.array(kept)
                if len(arr) < 4:
                    break
                mean_val = float(np.mean(arr))
                std_val = float(np.std(arr, ddof=1))
                if std_val == 0:
                    break
                new_mask = np.abs(arr - mean_val) < k * std_val
                if np.all(new_mask):
                    break
                removed.extend(arr[~new_mask].tolist())
                kept = arr[new_mask].tolist()
            if not removed:
                return self

        new = Measurement(self.name, kept, u_B=self.u_B)
        new.removed_values = removed
        new.original_n = self.original_n
        return new

    def round_value(self, value: float) -> float:
        return round_half_up(value, self.precision)

    def format(self) -> str:
        return f"{self.round_value(self.mean)} ± {self.round_value(self.u_c)}"

    def format_scientific(self) -> str:
        return f"{return_Cislo_Krat_10_Na(self.mean)} ± {return_Cislo_Krat_10_Na(self.u_c)}"

    def _fmt(self, val: float) -> str:
        p = self.precision
        from objects.units import extract_name_unit, display_unit

        _, unit = extract_name_unit(self.name)
        base = f"{val} ({round_half_up(val, p):.{p}f})"
        return f"{base} {display_unit(unit)}"

    def print_result(self, show_type_b: bool = False, quiet: bool = False) -> None:
        if quiet:
            if show_type_b or self.u_B > 0:
                print(f"{self.name} {self.mean} {self.u_A} {self.u_B} {self.u_c}")
            else:
                print(f"{self.name} {self.mean} {self.u_A}")
            return
        print(color_print.BOLD + self.name + color_print.END)
        if self.removed_values:
            rem_short = [f"{r:.4g}" for r in self.removed_values]
            print(
                f"├──{color_print.YELLOW}Odstraněno outlierů{color_print.END} = {len(self.removed_values)}/{self.original_n} ({', '.join(rem_short)})"
            )
        # Relativni nejistota = sigma / |mean| (sigma = u_c pokud je type B, jinak u_A).
        # Pouziva se v posledni radce stromu; vraci "—" pokud mean == 0 nebo neni finite.
        sigma_rel = self.u_c if (show_type_b or self.u_B > 0) else self.u_A
        if math.isfinite(self.mean) and math.isfinite(sigma_rel) and self.mean != 0:
            rel_pct = abs(sigma_rel / self.mean) * 100.0
            if 0.001 <= rel_pct < 1000:
                rel_str = f"{rel_pct:.3g} %"
            else:
                rel_str = f"{rel_pct:.2e} %"
        else:
            rel_str = "—"

        if show_type_b or self.u_B > 0:
            print(f"├──{color_print.UNDERLINE}Aritmetický průměr{color_print.END} = {self._fmt(self.mean)}")
            print(f"├──{color_print.UNDERLINE}Nejistota typu A{color_print.END} = {self._fmt(self.u_A)}")
            print(f"├──{color_print.UNDERLINE}Nejistota typu B{color_print.END} = {self._fmt(self.u_B)}")
            print(f"├──{color_print.UNDERLINE}Kombinovaná nejistota{color_print.END} = {self._fmt(self.u_c)}")
            print(
                f"├──{color_print.UNDERLINE}Rozšířená nejistota (k=2){color_print.END} = {self._fmt(self.expanded_uncertainty())}"
            )
            print(f"└──{color_print.UNDERLINE}Relativní nejistota{color_print.END} = {rel_str}")
        else:
            print(f"├──{color_print.UNDERLINE}Aritmetický průměr{color_print.END} = {self._fmt(self.mean)}")
            print(
                f"├──{color_print.UNDERLINE}Chyba aritmetického průměru{color_print.END} = {self._fmt(self.u_A)}"
            )
            print(f"└──{color_print.UNDERLINE}Relativní nejistota{color_print.END} = {rel_str}")
        print("-" * 100)

    def __repr__(self) -> str:
        return f"Measurement({self.name}, n={self.n}, mean={self.mean:.4g}, u_c={self.u_c:.4g})"


class DerivedMeasurement(Measurement):
    """Measurement vznikla aplikaci vzorce na hodnoty jine veliciny (per-radek).

    Ignoruje NaN hodnoty pri vypoctu mean/u_A — ty vznikaji u radku, kde vzorec
    selhal (typicky deleni nulou). Nema u_B (chyba pristroje neni definovana
    pro derivovane veliciny).
    """

    is_derived: bool = True

    @property
    def mean(self) -> float:
        # Pokud byla spoctena propagovana hodnota f(<x>, <y>, ...) — tu vrat.
        # Jinak fallback na nanmean per-radkovych vysledku.
        mp = getattr(self, "mean_propagated", None)
        if mp is not None and math.isfinite(mp):
            return mp
        if self._mean is None:
            arr = np.asarray(self.values, dtype=np.float64)
            valid = arr[~np.isnan(arr)]
            self._mean = float(np.mean(valid)) if len(valid) > 0 else float("nan")
        return self._mean

    @property
    def u_c(self) -> float:
        # Nejistota propagovana pres parcialni derivace (GUM), pokud byla spoctena.
        # Jinak fallback na statisticke u_A z per-radkovych vysledku.
        uc = getattr(self, "uc_propagated", None)
        if uc is not None and math.isfinite(uc):
            return uc
        if self._u_c is None:
            self._u_c = math.sqrt(self.u_A**2 + self.u_B**2)
        return self._u_c

    @property
    def u_A(self) -> float:
        if self._u_A is None:
            arr = np.asarray(self.values, dtype=np.float64)
            valid = arr[~np.isnan(arr)]
            n = len(valid)
            if n < 2:
                self._u_A = 0.0
            else:
                # Pouzij stat. mean z dat, ne propagovany (u_A je statistika z hodnot).
                stat_mean = float(np.mean(valid))
                odchylka = float(np.sum((valid - stat_mean) ** 2))
                self._u_A = math.sqrt(odchylka / (n * (n - 1)))
        return self._u_A
