"""ZM2_Mereni — knihovní API pro statistické zpracování fyzikálních měření.

Příklad použití:
    >>> import zm2
    >>> result = zm2.aritmeticky_prumer("data.txt")
    >>> result = zm2.aritmeticky_prumer({"U": [1.0, 2.0, 3.0]})
    >>> result = zm2.aritmeticky_prumer("data.txt", typ_b={"R": 0.01}, outliers="iqr")
"""

from argparse import Namespace
from typing import Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from objects.measurement_set import MeasurementSet

__all__ = [
    "aritmeticky_prumer",
    "neprima_chyba",
    "vazeny_prumer",
    "derivace",
    "regrese",
    "graf",
    "graf_interval",
    "histogram",
    "format_table",
    "extract_table",
    "join_tables",
    "convert_soubor",
]


def _make_args(**kwargs) -> Namespace:
    ns = Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def aritmeticky_prumer(
    source: str | dict,
    typ_b: dict | None = None,
    outliers: str | None = None,
    si_normalize: bool = False,
    convert_units: dict | None = None,
) -> dict:
    """Aritmetický průměr + chyba. Vrátí dict {name: [mean, u_c]}."""
    from statisticke_vypracovani.aritmeticky_prumer.logic import AritmetickyPrumer

    m = AritmetickyPrumer()
    if isinstance(source, dict):
        return m.run(source, do_print=False)
    args = _make_args(
        input=source,
        latextable=None,
        typ_b=typ_b,
        outliers=outliers,
        caption=None,
        label=None,
        verbose=False,
        dry_run=False,
        export_csv=None,
        batch=None,
        si_normalize=si_normalize,
        convert_units=convert_units,
        quiet=True,
    )
    return m.run(args, do_print=False)


def neprima_chyba(
    source: str,
    rovnice: str | None = None,
    konstanty: dict | None = None,
    typ_b: dict | None = None,
) -> list:
    from statisticke_vypracovani.neprima_chyba.logic import NeprimaChyba

    m = NeprimaChyba()
    args = _make_args(input=source, rovnice=rovnice, konstanty=konstanty, typ_b=typ_b)
    return m.run(args, do_print=False)


def vazeny_prumer(values: list, uncertainties: list, name: str = "x") -> dict:
    from statisticke_vypracovani.vazeny_prumer.logic import VazenyPrumer

    m = VazenyPrumer()
    args = _make_args(
        values=",".join(str(v) for v in values),
        uncertainties=",".join(str(u) for u in uncertainties),
        name=name,
    )
    return m.run(args, do_print=False)


def derivace(source: str, x_col: str | None = None, y_col: str | None = None) -> dict:
    from statisticke_vypracovani.derivace.logic import Derivace

    m = Derivace()
    args = _make_args(input=source, x_col=x_col, y_col=y_col, output="der")
    return m.run(args, do_print=False)


def regrese(
    source: str, x_col: str | None = None, y_col: str | None = None, sigma: str | None = None
) -> dict:
    from statisticke_vypracovani.regrese.logic import Regrese

    m = Regrese()
    args = _make_args(input=source, x_col=x_col, y_col=y_col, sigma=sigma)
    return m.run(args, do_print=False)


def graf(
    source: str,
    name: str = "graf",
    rovnice: str | None = None,
    fit: str | None = None,
    chi2: bool = False,
    logaritmicky: bool = False,
    parametr: str | None = None,
    plot_outliers: str | None = None,
    custom_fit: str | None = None,
) -> dict:
    from statisticke_vypracovani.graf.logic import Graf

    m = Graf()
    args = _make_args(
        input=source,
        name=name,
        rovnice=rovnice,
        parametr=parametr,
        logaritmicky=logaritmicky,
        fit=fit,
        chi2=chi2,
        plot_outliers=plot_outliers,
        custom_fit=custom_fit,
    )
    return m.run(args, do_print=False)


def graf_interval(name: str, rovnice: str, interval: list) -> dict:
    from statisticke_vypracovani.graf_interval.logic import GrafInterval

    m = GrafInterval()
    args = _make_args(name=name, rovnice=rovnice, interval=interval)
    return m.run(args, do_print=False)


def histogram(
    source: str,
    name: str = "hist",
    column: str | None = None,
    bins: int | None = None,
    gauss: bool = False,
) -> dict:
    from statisticke_vypracovani.histogram.logic import Histogram

    m = Histogram()
    args = _make_args(input=source, name=name, column=column, bins=bins, gauss=gauss)
    return m.run(args, do_print=False)


def format_table(
    source: str,
    output: str = "formatted",
    si_normalize: bool = False,
    convert_units: dict | None = None,
    caption: str | None = None,
    label: str | None = None,
    precision: int | None = None,
    append_stats: bool = False,
    auto_scale: bool = False,
) -> dict:
    from statisticke_vypracovani.format_table.logic import FormatTable
    import json

    m = FormatTable()
    conv_str = json.dumps(convert_units) if convert_units else None
    args = _make_args(
        input=source,
        output=output,
        si_normalize=si_normalize,
        convert_units=conv_str,
        caption=caption,
        label=label,
        precision=precision,
        decimal_separator=",",
        rows_per_subtable=25,
        append_stats=append_stats,
        no_caption_stats=False,
        auto_scale=auto_scale,
        dry_run=False,
    )
    return m.run(args, do_print=False)


def extract_table(source: str, output: str = "extracted", keep_units: bool = False) -> dict:
    from statisticke_vypracovani.extract_table.logic import ExtractTable

    m = ExtractTable()
    args = _make_args(input=source, output=output, keep_units=keep_units)
    return m.run(args, do_print=False)


def join_tables(
    in1: str,
    in2: str,
    output: str = "joined",
    mode: str = "horizontal",
    si_normalize: bool = False,
    convert_units: dict | None = None,
) -> dict:
    from statisticke_vypracovani.join_tables.logic import JoinTables
    import json

    m = JoinTables()
    conv_str = json.dumps(convert_units) if convert_units else None
    args = _make_args(
        input=[in1, in2],
        output=output,
        mode=mode,
        si_normalize=si_normalize,
        convert_units=conv_str,
    )
    return m.run(args, do_print=False)


def convert_soubor(source: str, output: str = "output_convertor") -> "MeasurementSet":
    from statisticke_vypracovani.convert_soubor.logic import ConvertSoubor

    m = ConvertSoubor()
    args = _make_args(input=source, output=output)
    return m.run(args, return_file=True)
