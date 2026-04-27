# Changelog

V tomto souboru dokumentujeme významné změny v projektu. Formát vychází z [Keep a Changelog](https://keepachangelog.com/cs/1.1.0/) a projekt dodržuje [Semantic Versioning](https://semver.org/lang/cs/).

## [Unreleased]

### Přidáno

**Distribuce**

- Docker image — automatický publish na `ghcr.io/matyas095/zm2_mereni` pro každý tag i merge do `main` (workflow `.github/workflows/docker.yml`).
- AppImage pro Linux — jediný spustitelný soubor `Statistika-*.AppImage`, není třeba rozbalovat.
- macOS build — nové buildy `statistika_*_macos.tar.gz` a `statistika_grafy_*_macos.tar.gz` (PyInstaller na `macos-latest`).

**Vstupní formáty**

- TOML rozpoznán napříč všemi metodami pracujícími se vstupním souborem (`ap`, `regrese`, `derivace`, `graf`, `histogram`, `integrace`, `nc`). Implementace: `InputParser.parse_toml` + dispatch v `InputParser.from_file` pro `.toml` extension. Schéma: `[veliciny.<nazev>]` s `hodnoty`, volitelně `unit` a `typ_b` (skalární přímý `u_B` nebo inline tabulka `{ a = ..., distribuce = ... }`). Pro `nc` se použije rozšířené schéma s `[funkce.<nazev>]` sekcemi.

**Vylepšení `neprima_chyba`**

- Nový vstupní formát `.toml` jako alternativa k indentovanému `.txt` (sekce `[veliciny.<nazev>]` a `[funkce.<nazev>]`, inline tabulka pro `typ_b`). Imunní vůči pasti desetinné/separátorové čárky a indentačním chybám, které trápily `.txt` parser. Stávající `.txt` a `.xlsx` formáty zachovány.
- Anotace `[jednotka]` na klíčích v `FUNKCE` (např. `u [g*mm**-3] = m/V`) — nástroj uloží jednotku, pokusí se ji převést na základní SI jednotky (gram → kg, mm → m, …) a v řádku `Výsledek` zobrazí převedenou formu, pokud splňuje pravidlo „bez `× 10^N` a nejvýš 2 desetinná místa". Hmotnostní jednotky se převádí na `kg` (v rozporu s `objects/units.parse_unit`, který používá `g` jako base).
- Nové výstupní řádky pro každou funkci: `LaTeX` (zdrojový tvar přes `sympy.latex`), `Hodnota` (střední hodnota), `Výsledek` (`(hodnota ± nejistota)` zaokrouhlené dle GUM §7.2.6 s **vždy 2 sig. cifry na nejistotě**), `Originál` (totéž v deklarované jednotce, pro konzistentní reportování napříč protokolem).
- **Auto-rescale jednoduchých jednotek** přes `utils.rescale_simple_unit` — pokud nejistota potřebuje > 2 desetinná místa, vybere se SI prefix (`m → mm/μm/…`, `g → mg/μg/…`) tak, aby výsledná nejistota měla 0–2 desetinná místa.
- Více funkcí najednou — TOML může obsahovat libovolný počet `[funkce.<jméno>]` sekcí, každá vypíše svůj propagovaný výsledek nezávisle. Vhodné pro zobrazení mezi-výpočtů (např. `m_lih = M_2 - M_1`, `m_voda = M_3 - M_1`, `rho = m_lih/m_voda * rho_v` v jednom běhu).
- Bugfix v `_derivace`: když funkce v `FUNKCE` používá jen podmnožinu proměnných z `ELEMENTY`, propagace správně vezme jen ty (dříve padalo `TypeError: takes N arguments but M were given`).
- Návratová hodnota metody rozšířena z 5-tice na 6-tici `(name, sigma, formatted_sigma, mean, latex_str, unit_str)`. Tester aktualizován + přidán `test_run_toml`.
- Nový řádek `Rel. nejistota` v každém výstupu (po `Výsledek`/`Originál`) — relativní nejistota `δ = σ/|μ| × 100 %`, formátovaná na 3 sig. cifry (přepíná se na scientific notation mimo rozsah `[0.001 %, 1000 %)`). Univerzální (bez ohledu na jednotku); umožňuje porovnávat precizionost napříč veličinami.

**Pomocné funkce v `utils.py`**

- `round_half_up(value, ndigits)` — školní zaokrouhlování (round half away from zero) přes `Decimal(repr(float(value))).quantize(..., ROUND_HALF_UP)`. Imunní vůči binární reprezentaci floatů (např. `33.05` se nyní zaokrouhlí na `33.1` namísto `33.0`) i vůči NumPy 2.x reprezentaci scalárů (`np.float64(33.05)` → `33.1`).
- `gum_round(value, uncertainty)` — vrací `(hodnota ± nejistota)` zaokrouhlené dle GUM §7.2.6: **vždy 2 sig. cifry** na nejistotě, hodnota na stejnou pozici. Plain notation pro `|val|` v rozsahu `[10⁻², 10⁸)`, jinak `× 10^N`.
- `parse_composite_unit(unit_str)` — parsuje složené jednotky `g*mm**-3`, `g/cm^3`, `m/s` a vrací `(faktor_do_si, si_jednotka)`. Hmotnost převádí na `kg`.
- `pick_display(orig, si, orig_unit, si_unit)` — vybere lepší z dvou zaokrouhlených zobrazení podle pravidla „bez `× 10^N` a ≤ 2 desetinná místa". SI forma se použije pouze pokud splňuje obě podmínky.
- `rescale_simple_unit(mean, sigma, unit)` — pro jednoduché SI base jednotky (`m`, `g`, `s`, `A`, …) vybere SI prefix tak, aby nejistota měla 0–2 desetinných míst. Krok prefixu je vždy násobek 3 (m → mm → μm → …, m → km → Mm → …).

**Vylepšení `aritmeticky_prumer`**

- Nový řádek `Relativní nejistota` v konzolovém výstupu (jak v základní variantě, tak s typem B) — `δ = σ/|μ| × 100 %`, formátovaná na 3 sig. cifry. Pro výstup s type B používá `u_c`, jinak `u_A`. Vrací `—` pokud `μ = 0` nebo není finite.
- Nový flag `-ru` / `--rel-uncertainty` pro `-lt` (LaTeX tabulky) — když je aktivní, ke každému řádku stats v captionu (`$X = (μ ± σ)\,\mathrm{unit}$`) se připojí `\quad(\delta_X = X.X\,\%)`. Předává se přes `MeasurementSet.to_latex_table(include_rel_uncertainty=True)`.

**Zaokrouhlování ve výstupu**

- `objects/measurement.py:142, 155` (`round_value`, `_fmt`) a `objects/measurement_set.py:112, 135–136` (LaTeX tabulka, caption stats) — všechny `round()` volání nahrazeny `round_half_up()`. Důsledek: hodnoty jako `33.05` se v konzolovém i LaTeX výstupu zobrazí jako `33.1`, ne `33.0`.

**CI/CD**

- Pin `ruff==0.15.12` a `mypy==1.20.2` v `.github/workflows/ci.yml`, aby verze odpovídaly `.pre-commit-config.yaml` a nedošlo k tichému driftu formátování.
- Bump GitHub Actions na verze podporující Node 24 (`actions/checkout@v5`, `actions/setup-python@v6`, `actions/upload-artifact@v6`, `actions/download-artifact@v7`, `docker/setup-buildx-action@v4`, `docker/login-action@v4`, `docker/metadata-action@v6`, `docker/build-push-action@v7`). Node 20 je v GitHub Actions deprecated od června 2026.

**Dokumentace**

- README oddíl 1.4 *Řešení potíží* — diagnostika a postup pro Windows binárku selhávající chybou `LoadLibrary: Invalid access to memory location` na Win 11 24H2+. Doplněn rozbor obou identifikovaných příčin (Python 3.12 bez `/CETCOMPAT` a PyInstaller `--strip` mažící CET bit z `python313.dll`) i postup nouzové opravy poškozené v0.4 binárky přepsáním `python313.dll` oficiální verzí z MSI instalátoru.
- README oddíl 5.2 *`neprima_chyba`* přepsán — popis nového čtyřřádkového výstupu (`LaTeX`/`Hodnota`/`Chyba`/`Výsledek`), anotace `[jednotka]`, automatický SI převod, TOML formát.

### Opraveno

- **Docker workflow padal s `tag is needed when pushing to registry`** při push tagu `vX.Y` (např. `v0.4`), protože `docker/metadata-action` měl jen `type=semver` vzory, které vyžadují strict semver `vX.Y.Z`. Doplněn `type=ref,event=tag`, který použije surový git tag jako docker tag — funguje i pro `vX.Y` konvenci, semver vzory zachovány pro budoucí přechod na `vX.Y.Z`.
- **`utils.return_Cislo_Krat_10_Na(0)` padal na `ValueError: math domain error`** (volá `math.log10(0)`). Přidána ochrana pro `x == 0` a non-finite (`inf`, `-inf`, `nan`) — vrátí `str(x)` místo crashe. Symptomatické u `nc` runs, kde nebyla zadaná žádná nejistota — `sig_R` vyšlo `0` a celý běh skončil tracebackem místo zobrazení nuly.
- **`deploy.sh` selhával na Windows Git Bash s `bash: python3: command not found`** — skript hardcodoval `python3`, který na Windows neexistuje (jen `python` nebo `py`). Přidána funkce `detect_python` zkoušející `python3 → python → py -3`. Zároveň opraven syntax-check loop, který kvůli pre-existující chybě v `if [ $? -eq 0 ]` po `for` smyčce maskoval chyby — nahrazeno akumulátorem `SYNTAX_OK=1`.
- **`ruff format --check`** v CI selhával na 56 souborech, které nikdy neprošly formaterem v0.4. Strom normalizován pomocí pinned `ruff==0.15.12`, samotná akce vrací green.
- **`utils.round_half_up` padal pod NumPy 2.x** s `decimal.InvalidOperation` při zpracování `numpy.float64` skalárů — NumPy 2.0 změnilo `repr(np.float64(x))` na `'np.float64(x)'`, což `Decimal` nedokáže parsovat. Helper nyní cast přes `float(value)` před `repr`. Symptom: `aritmeticky_prumer -lt` padal při generování LaTeX tabulky.
- **`_derivace` v `nc`** padalo `TypeError: takes N arguments but M were given`, když funkce v `FUNKCE` používala podmnožinu proměnných z `ELEMENTY`. Propagace nyní používá `chyby = list(variables)` místo `list(aritmety.keys())`.

#### Původní oprava CET / `--strip`

- **Windows binárka padala při startu na Windows 11 24H2+ s CPU podporujícím hardware CET** (Intel Tiger Lake+, AMD Zen 3+) chybou `[PYI-xxxx:ERROR] Failed to load Python DLL ... LoadLibrary: Invalid access to memory location.`. Identifikovány byly dvě nezávislé příčiny, obě bránily korektnímu loadu Python DLL kernel-vynuceným User Shadow Stackem:
    1. Knihovna `python312.dll` z Pythonu 3.12 nebyla zkompilována s flagem `/CETCOMPAT`. Build runner přepnut z Pythonu 3.12 na 3.13 — oficiální `python313.dll` má `IMAGE_DLLCHARACTERISTICS_EX_CET_COMPAT` nastaveno. Změna se promítla do workflow `release.yml`, `ci.yml` i do `Dockerfile` (`python:3.12-slim` → `python:3.13-slim`).
    2. Windows buildy předávaly PyInstalleru flag `--strip`, který spouští GNU `strip` nad bundlovanými binárkami. Na PE souborech `strip` maže rozšířené DLL characteristics včetně CET bitu, čímž rušil efekt opravy z bodu 1 — i v0.4 binárka s `python313.dll` proto stále padala. Flag `--strip` odstraněn ze všech tří Windows pipeline (`builder/build_statistika_windows.ps1`, `builder/build_grafy_windows.ps1`, `.github/workflows/release.yml` — joby `build-statistika-windows` a `build-grafy-windows`). Linuxové buildy `--strip` zachovávají, je tam korektní použití na ELF.

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
- Složka `examples/` s reálnými workflow pro konkrétní úlohy (rozpis úloh viz sekce *Dokumentace*).

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
