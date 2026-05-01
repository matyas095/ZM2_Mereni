#!/usr/bin/env python3
"""Validace vstupnich souboru pro ZM2_Mereni.

Pro kazdy zadany soubor (nebo glob) zkontroluje:
- TOML: syntaxi pres tomllib (line:col z chyboveho hlaseni)
        a semantiku pres InputParser.parse_toml (chybejici klice,
        nezname rozdeleni typ_b, nesourode jednotky typ_b.unit, ...).
- TXT/CSV/TSV: parsovani pres InputParser.from_file.
- XLSX: parsovani pres InputParser.parse_xlsx.

Pouziti:
    python3 validate_inputs.py inputfiles/*.toml
    python3 validate_inputs.py 'inputfiles/**/*' file.txt
    python3 validate_inputs.py inputfiles/2_uloha.toml inputfiles/koule.xlsx

Exit kod: 0 pokud vse OK, 1 pokud aspon jeden FAIL.
"""

from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
GREEN = "\033[32m" if USE_COLOR else ""
RED = "\033[31m" if USE_COLOR else ""
YELLOW = "\033[33m" if USE_COLOR else ""
BOLD = "\033[1m" if USE_COLOR else ""
RESET = "\033[0m" if USE_COLOR else ""

LINE_COL_RE = re.compile(r"line\s+(\d+),\s*column\s+(\d+)", re.IGNORECASE)
QUOTED_RE = re.compile(r"'([^']+)'")


def _find_in_source(path: Path, needle: str) -> tuple[int, int] | None:
    """Best-effort: najde retezec v souboru, vrati (radek, sloupec) 1-indexovane."""
    try:
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            col = line.find(needle)
            if col >= 0:
                return (i, col + 1)
    except Exception:
        return None
    return None


def _validate_toml(path: Path) -> str | None:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]
    try:
        with open(path, "rb") as f:
            tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        msg = str(e)
        m = LINE_COL_RE.search(msg)
        loc = f":{m.group(1)}:{m.group(2)}" if m else ""
        return f"{path}{loc}: TOML syntax: {msg}"
    except Exception as e:
        return f"{path}: {type(e).__name__}: {e}"

    try:
        from objects.input_parser import InputParser

        InputParser.parse_toml(str(path))
    except Exception as e:
        msg = str(e)
        loc = ""
        # Pozdejsi citaty v hlasce byvaji specifictejsi (nazev klice, spatna hodnota)
        # nez prvni (typicky nazev veliciny v hlavicce sekce).
        for needle in reversed(QUOTED_RE.findall(msg)):
            line_col = _find_in_source(path, needle)
            if line_col:
                loc = f":{line_col[0]}:{line_col[1]}"
                break
        return f"{path}{loc}: {type(e).__name__}: {msg}"
    return None


def _validate_txt_like(path: Path) -> str | None:
    try:
        from objects.input_parser import InputParser

        InputParser.from_file(str(path))
    except Exception as e:
        return f"{path}: {type(e).__name__}: {e}"
    return None


def _expand(args: list[str]) -> list[Path]:
    paths: list[Path] = []
    for arg in args:
        matched = glob.glob(arg, recursive=True)
        if not matched and Path(arg).exists():
            matched = [arg]
        if not matched:
            print(f"{YELLOW}WARN{RESET}  no files match {arg!r}", file=sys.stderr)
            continue
        paths.extend(Path(p) for p in matched)
    return sorted({p for p in paths if p.is_file()})


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv and argv[0] in ("-h", "--help") else 2

    sys.path.insert(0, str(Path(__file__).resolve().parent))

    paths = _expand(argv)
    if not paths:
        print(f"{YELLOW}WARN{RESET}  zadne soubory k validaci", file=sys.stderr)
        return 2

    n_ok = n_fail = n_skip = 0
    for path in paths:
        ext = path.suffix.lower()
        if ext == ".toml":
            err = _validate_toml(path)
        elif ext in (".txt", ".csv", ".tsv", ".xlsx"):
            err = _validate_txt_like(path)
        else:
            print(f"{YELLOW}SKIP{RESET}  {path} (neznama pripona)")
            n_skip += 1
            continue
        if err:
            print(f"{RED}FAIL{RESET}  {err}")
            n_fail += 1
        else:
            print(f"{GREEN}OK{RESET}    {path}")
            n_ok += 1

    summary = f"{n_ok} OK, {n_fail} FAIL"
    if n_skip:
        summary += f", {n_skip} SKIP"
    color = GREEN if n_fail == 0 else RED
    print(f"\n{BOLD}{color}{summary}{RESET}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
