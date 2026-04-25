# Changelog

V tomto souboru dokumentujeme významné změny v projektu. Formát vychází z [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/) a projekt dodržuje [Semantic Versioning](https://semver.org/lang/cs/).

## [Unreleased]

### Přidáno

**Distribuce**

- Docker image — automatický publish na `ghcr.io/matyas095/zm2_mereni` pro každý tag i merge do `main` (workflow `.github/workflows/docker.yml`).
- AppImage pro Linux — jediný spustitelný `.AppImage` soubor, není třeba rozbalovat.
- macOS build — nové artefakty `statistika_*_macos.tar.gz` a `statistika_grafy_*_macos.tar.gz` (PyInstaller na `macos-latest`).

**Nová metoda**

- `integrace` (alias `int`) — numerická integrace kumulativní lichoběžníkovou metodou (`scipy.integrate.cumulative_trapezoid`) jako párová metoda k `derivace`.

**Kvalita kódu**

- `pyproject.toml` — centrální konfigurace pro ruff, mypy, coverage.
- Ruff lint + format v CI a pre-commit hooku.
- Mypy type-check v CI a pre-commit hooku (lenientní baseline).
- Coverage badge v README + Codecov upload v CI.
- Refactor `_interactive_handler` v `main.py` na samostatné helpery (`_resolve_method`, `_prompt_file`, `_prompt_bool`, `_prompt_value`, `_fill_method_args`, `_check_input_files_exist`).

**UX vylepšení**

- Did-you-mean návrhy přes `difflib.get_close_matches` pro překlepy v názvu metody (`reggrese` → „Měli jste na mysli: regrese, reg?").
- TTY guard v interaktivním handleru — žádný `EOFError` při neinteraktivním stdin.
- Tkinter import s `try/except` fallbackem — binárka bez tkinteru funguje, padá rovnou do textového promptu.
- `--typ-b` jako opakovatelný flag s jednoduchou syntaxí: `-tb U=0.05:rovnomerne -tb t=0.5` (zachována zpětná kompatibilita s JSON).

**Robustnost**

- `utils.locked_open` — `fcntl.flock` (Linux/Mac) + `msvcrt.locking` (Windows) fallback. Aplikováno ve všech zápisech do `outputs/` a `latex_output/`.
- Numerická stabilita — Python `sum()` → `np.sum()` v `objects/measurement.py`, `format_table`, `neprima_chyba`.
- `neprima_chyba` — čitelná `ValueError` při kolizi názvů proměnných se SymPy reserved symboly (`I, E, pi, oo, S, N, O, Q, C`) místo neinformativního `Can't calculate derivative wrt I`.

**Build a velikost**

- Vyřazení nepotřebných balíků z PyInstaller buildu (`sphinx`, `babel`, `docutils`, `alabaster`, `jinja2`, `markupsafe`) — úspora ~49 MB instalovaných.

## [v0.4] - 2026-04-25

### Přidáno

**Nové metody**

- `vazeny_prumer` — vážený průměr z hodnot naměřených s rozdílnou přesností.
- `join_tables` — horizontální spojení dvou LaTeX tabulek (módy `horizontal` a `match`).
- `histogram` — histogram rozdělení s volitelným proložením Gaussovkou.
- `derivace` — numerická derivace metodou centrálních diferencí.
- `regrese` — lineární regrese bez grafu; vrací koeficienty, kovarianci a chi-squared.
- `extract_table` — extrakce dat z LaTeX tabulky zpět do formátu `VELIČINA=data` (inverze `format_table`).
- `format_table` — úprava existující LaTeX tabulky; podporuje:
  - `--si-normalize` / `--convert-units` — převod jednotek v hlavičkách i hodnotách,
  - `--caption` / `--label` — nahrazení popisku a návěští,
  - `--precision N` / `--decimal-separator` — přeformátování čísel,
  - `--rows-per-subtable N` — rozdělení nebo sloučení subtables,
  - `--append-stats` — doplnění průměru a chyby pro každý sloupec do captionu ve formátu `$VELIČINA = (průměr \pm chyba)\,\mathrm{jednotka}$`,
  - `--no-caption-stats` — vypnutí auto-statistik (přepisuje nastavení z configu),
  - `--auto-scale` — automatický výběr vhodného SI prefixu podle velikosti hodnot,
  - `--interactive` — interaktivní režim pro postupnou úpravu parametrů,
  - `--dry-run` — náhled bez zápisu.

**Programatické API a architektura**

- Nový modul `zm2/__init__.py` — knihovní API pro volání z jiného skriptu nebo Jupyter notebooku.
- Sjednocené signatury všech metod: `run(args, do_print: bool = True) -> dict`.
- Metoda `validate(args)` v každé metodě — odchytává chyby předem (chybějící soubory, nesprávné argumenty) místo hluboko ve výpočtech.
- Oddělený `compute()` v bázové třídě pro čistý výpočet bez I/O.
- Python logging (`objects/logger.py`) — nahrazuje `print()` s verbose/quiet úrovněmi.
- Type hints v klíčových souborech (`base.py`, `measurement.py`, `zm2/`).

**CLI vylepšení**

- Aliasy metod: `ap`, `nc`, `vp`, `der`, `reg`, `cs`, `jt`, `ft`, `et`, `g`, `gi`, `hist`.
- Custom fit funkce v `graf` (`--custom-fit "a*sin(b*x+c)"`) přes SymPy parser.
- Progress bar pro batch režim (tqdm s fallbackem).

**Dokumentace**

- Sphinx scaffold v `docs/` pro generování HTML dokumentace z docstringů.
- Rozšíření `examples/` o úlohy `ohmuv_zakon/`, `wheatstone/` a `kmity/`.

**Infrastruktura**

- Pre-commit hooky v `.pre-commit-config.yaml` — syntax check + testy před commitem.
- Coverage enforcement v CI (`--fail-under=55`) — PR neprojde při poklesu pokrytí.
- Integration testy v `tests/integration/test_api.py` pro programatické API.

**Vylepšení `aritmeticky_prumer`**

- Nejistota typu B (`--typ-b`) s podporou rovnoměrného, trojúhelníkového a normálního rozdělení.
- Detekce outlierů (`--outliers`): 3σ, 2σ, N-σ, IQR.
- Export do CSV (`--export-csv`).
- Vlastní LaTeX caption a label (`--caption`, `--label`).
- Automatické generování labelu z názvu vstupního souboru.
- Převod jednotek: `--si-normalize` (např. mA → A) a `--convert-units` (JSON mapování).
- Podpora všech SI prefixů (y až Y, 10⁻²⁴ až 10²⁴).
- Batch režim (`--batch GLOB`) pro hromadné zpracování více souborů.
- Jednotka v konzolovém výstupu (`U = 0.256 (0.3) V`).

**Vylepšení `graf`**

- Chi-squared statistika s p-hodnotou a nejistotami parametrů fitu (`--chi2`).
- Dvoupanelový graf s panelem reziduí.
- Zvýraznění outlierů v grafu (`--plot-outliers`).

**Vylepšení `neprima_chyba`**

- Nejistota typu B (`--typ-b`) — propagujeme kombinovanou nejistotu u_c namísto pouze u_A.

**Ostatní**

- CASSY parser — autodetekce formátu s desetinnou čárkou a hlavičkou s jednotkami.
- Převod jednotek v `join_tables` (`--si-normalize`, `--convert-units`) s varováním při nálezu převáděné jednotky v captionu.
- JSON výstup (`--output-format json`) na všech metodách.
- Konfigurační soubor `.zm2rc` pro výchozí hodnoty (`decimal_separator`, `color_scheme`, `default_outliers`).
- Barevné schéma s režimy auto/none (respektuje proměnné prostředí `NO_COLOR` a `ZM2_COLORS`).
- Verbose mode (`--verbose`) pro výpis ladicích informací.
- Dry-run mode (`--dry-run`) pro náhled změn bez zápisu.
- Globální přepínače `--no-color` a `-q`/`--quiet` dostupné pro každou metodu.
- Přehled podporovaných SI jednotek a prefixů pomocí `--list-units`.
- Validace konfiguračního souboru `.zm2rc` — varování při neznámých klíčích.
- Shell completion pro bash/zsh prostřednictvím knihovny `argcomplete`.
- Integrační testy ve složce `tests/integration/`.
- Coverage report pomocí `coverage.py` v CI workflow.
- Složka `examples/` s reálnými workflow pro konkrétní úlohy (rozpis v sekci *Dokumentace*).

**LaTeX tabulky**

- Auto-caption s názvem souboru a hodnotami ve formátu `$X = (mean \pm err)$`.
- Rozdělení do subtables při počtu řádků > 20 (2/3/4 podtabulky vedle sebe).
- Automatické vyvažování `$...$` a `{...}` v captionu.
- Desetinná čárka namísto tečky.
- Zaokrouhlení dle přesnosti určené z chyby (maximálně 2 desetinná místa).

### Změněno

- OOP refaktoring — všechny metody jsou třídy dědící z abstraktní třídy `Method`.
- Rozdělené buildy — balík **Statistika** (cca 75 MB) a balík **Grafy** (cca 96 MB) namísto jednoho monolitu.
- Objektový model `Measurement`, `MeasurementSet`, `InputParser` nahrazuje dřívější procedurální kód.
- Rozšíření testů ze 3 na 159+ jednotkových testů.
- CI workflow spouští testy na každém pull requestu, repozitář má nastavenou branch protection.
- Metoda `graf_BROKEN` přejmenována na `graf`.

### Opraveno

- `EOFError` ve frozen módu (`.exe`) při chybějícím TTY.
- Vyvážení `$..$` v LaTeX captionu.
- Vyvážení `{..}` v LaTeX math módu.
- Lichý počet `$` se automaticky opravuje.
- Parsing `\caption{...}` a `\label{...}` — nyní správně zpracujeme vnořené závorky (např. `\mathrm{s}` v captionu).
- Funkce `convert_str_value` zachovává počet desetinných míst ze vstupu (`0,00 × 1000 = 0,00`, nikoli `0`).

### Odstraněno

- Staré složky `objects/elements/` a `objects/readable/` (nahrazeny novým objektovým modelem).
- Funkce `get_Promeny()` z `utils.py` (nahrazena třídou `InputParser`).
- Závislost na knihovně `sklearn` — `r2_score` implementujeme vlastní funkcí (úspora cca 25 MB v buildu).
- Závislost na knihovně `pyarrow` z buildu (úspora cca 80 MB).

## [v0.2] - 2026-04-04

### Přidáno

- Aritmetický průměr s chybou.
- Nepřímá chyba měření (propagace přes parciální derivace).
- 2D a 3D grafy s volitelným fitem.
- Graf funkce na zadaném intervalu.
- Konverze tabulkových souborů.
- Build pro Linux a Windows pomocí PyInstalleru.
