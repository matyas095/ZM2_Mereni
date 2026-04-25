# ZM2_Mereni — Statistické zpracování dat (Základy měření 2)

[![CI](https://github.com/matyas095/ZM2_Mereni/actions/workflows/ci.yml/badge.svg)](https://github.com/matyas095/ZM2_Mereni/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/matyas095/ZM2_Mereni/branch/main/graph/badge.svg)](https://codecov.io/gh/matyas095/ZM2_Mereni)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Nástroj pro statistické zpracování fyzikálních laboratorních měření. Počítá aritmetické průměry, chyby typu A i B, propagaci chyb přes parciální derivace, vážené průměry a generuje grafy spolu s LaTeX tabulkami vhodnými přímo do protokolu.

Distribuujeme jej ve dvou samostatných balících — **Statistika** (výpočty) a **Grafy** (vizualizace).

## 1 Instalace

### 1.1 Ze zdrojového kódu

```bash
git clone git@github.com:matyas095/ZM2_Mereni.git
cd ZM2_Mereni
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.2 Binární distribuce

Na stránce [Releases](https://github.com/matyas095/ZM2_Mereni/releases) stáhneme balík odpovídající platformě:

| Balík | Linux | Windows | macOS |
|-------|-------|---------|-------|
| **Statistika** (výpočty) | `statistika_*_linux.tar.gz` + `Statistika-*.AppImage` | `statistika_*_windows.zip` | `statistika_*_macos.tar.gz` |
| **Grafy** (vizualizace) | `statistika_grafy_*_linux.tar.gz` | `statistika_grafy_*_windows.zip` | `statistika_grafy_*_macos.tar.gz` |

```bash
# Linux (tar.gz)
tar -xzf statistika_v0.4_linux.tar.gz
./statistika_v0.4_linux/statistika -h

# Linux (AppImage — jeden spustitelný soubor)
chmod +x Statistika-v0.4-x86_64.AppImage
./Statistika-v0.4-x86_64.AppImage -h

# macOS
tar -xzf statistika_v0.4_macos.tar.gz
./statistika_v0.4_macos/statistika -h

# Windows
.\statistika\statistika.exe -h
```

### 1.3 Docker

```bash
# Spuštění z GHCR (data jsou v aktuálním adresáři)
docker run --rm -v "$PWD:/data" ghcr.io/matyas095/zm2_mereni:latest ap -i mereni.txt

# Konkrétní verze
docker run --rm -v "$PWD:/data" ghcr.io/matyas095/zm2_mereni:v0.4 reg -i data.txt -x U -y I

# Lokální build z repozitáře
docker build -t zm2 .
docker run --rm -v "$PWD:/data" zm2 --list-units
```

## 2 Použití

```bash
# Spuštění konkrétní metody
python3 main.py <metoda> [argumenty]

# Pouze výpočetní metody
python3 main_statistika.py <metoda> [argumenty]

# Pouze grafové metody
python3 main_grafy.py <metoda> [argumenty]

# Interaktivní režim (bez argumentů — program se dotáže)
python3 main.py

# Strojově čitelný výstup
python3 main.py <metoda> [argumenty] --output-format json

# Seznam podporovaných SI jednotek a prefixů
python3 main.py --list-units
```

### 2.1 Aliasy metod

Každá metoda má krátký alias pro rychlejší psaní:

| Metoda | Alias |
|--------|-------|
| `aritmeticky_prumer` | `ap` |
| `neprima_chyba` | `nc` |
| `vazeny_prumer` | `vp` |
| `derivace` | `der` |
| `integrace` | `int` |
| `regrese` | `reg` |
| `convert_soubor` | `cs` |
| `join_tables` | `jt` |
| `format_table` | `ft` |
| `extract_table` | `et` |
| `graf` | `g` |
| `graf_interval` | `gi` |
| `histogram` | `hist` |

Příklad: `python3 main.py ap -i data.txt` místo `python3 main.py aritmeticky_prumer -i data.txt`.

### 2.2 Programatické API

Nástroj je zároveň Python knihovnou — lze volat z jiného skriptu nebo Jupyter notebooku:

```python
import zm2

# Z dictu
result = zm2.aritmeticky_prumer({"U": [1.0, 2.0, 3.0]})
# → {'U': [2.0, 0.5773]}

# Ze souboru
result = zm2.aritmeticky_prumer("data.txt", typ_b={"R": 0.01}, outliers="iqr")

# Regrese
r = zm2.regrese("data.txt")
# → {'a': [2.0, 0.03], 'b': [0.05, 0.1], 'R2': 0.999, ...}

# Graf
zm2.graf("data.txt", name="Fit", fit="linearni", chi2=True)
```

Globální přepínače jsou dostupné pro každou metodu:

| Přepínač | Popis |
|----------|-------|
| `--no-color` | Vypne barevný výstup |
| `-q`, `--quiet` | Minimální výstup (bez dekorací, pro scripty) |
| `--output-format json` | JSON výstup |

## 3 Konfigurace

Pro výchozí hodnoty vytvoříme soubor `.zm2rc` v aktuálním adresáři, případně v `~/.zm2rc`:

```json
{
  "decimal_separator": ",",
  "default_outliers": "iqr",
  "default_output_format": "text",
  "color_scheme": "auto",
  "verbose": false
}
```

| Klíč | Hodnoty | Popis |
|------|---------|-------|
| `decimal_separator` | `","` / `"."` | Separátor v LaTeX tabulkách |
| `default_outliers` | `"3sigma"` / `"iqr"` / `null` | Automaticky odstranit outliery |
| `color_scheme` | `"auto"` / `"none"` | Barevný výstup |
| `verbose` | `true` / `false` | Debug výpisy |

Nástroj respektuje proměnné prostředí `NO_COLOR` a `ZM2_COLORS`.

## 4 Příklady použití

Aritmetický průměr s chybou z naměřených hodnot napětí a proudu:
```bash
python3 main.py aritmeticky_prumer -i mereni.txt
```

LaTeX tabulka pro protokol s vlastním popiskem:
```bash
python3 main.py aritmeticky_prumer -i mereni.txt -lt \
    --caption "Změřené hodnoty R pro vozíček 1" \
    --label "tab_vozicek_1"
```

Automatické odstranění outlierů (IQR):
```bash
python3 main.py aritmeticky_prumer -i mereni.txt --outliers iqr
```

Náhled výstupu před uložením:
```bash
python3 main.py aritmeticky_prumer -i mereni.txt -lt --dry-run --verbose
```

Export výsledků do CSV:
```bash
python3 main.py aritmeticky_prumer -i mereni.txt --export-csv vysledky.csv
```

Nejistota typu B z manuálu multimetru (±1%, rovnoměrné rozdělení):
```bash
python3 main.py aritmeticky_prumer -i mereni.txt --typ-b '{"U": [0.01, "rovnomerne"]}'
```

Vážený průměr tří měření s rozdílnou přesností:
```bash
python3 main.py vazeny_prumer -v "10.2,10.3,10.1" -u "0.1,0.05,0.2" -n "R"
```

Lineární fit s chi-squared analýzou a panelem reziduí:
```bash
python3 main.py graf -i data.txt -n "Fit" -f linearni --chi2
```

Numerická derivace polohy podle času:
```bash
python3 main.py derivace -i poloha.txt -x t -y x -o rychlost
```

Histogram s proloženou Gaussovkou:
```bash
python3 main.py histogram -i mereni.txt -c U --gauss -b 15
```

Spojení dvou LaTeX tabulek párováním podle prvního sloupce:
```bash
python3 main.py join_tables -i U_t.tex I_t.tex -o UI_t.tex -m match
```

Úprava existující LaTeX tabulky (převod jednotek a doplnění statistik):
```bash
python3 main.py format_table -i mereni.tex --si-normalize --append-stats -o final
```

Spojení tabulek s převodem jednotek na SI:
```bash
python3 main.py join_tables -i t1.tex t2.tex -o spojeno --si-normalize -m match
```

## 5 Statistické metody

### 5.1 `aritmeticky_prumer`

Výpočet aritmetického průměru a střední kvadratické chyby aritmetického průměru. Nástroj podporuje nejistotu typu A i typu B a jejich kombinovanou nejistotu dle GUM.

```bash
# Základní výpočet (pouze typ A)
python3 main.py aritmeticky_prumer -i data.txt

# Export do LaTeX tabulky
python3 main.py aritmeticky_prumer -i data.txt -lt

# Nejistota typu B zadaná přímou hodnotou
python3 main.py aritmeticky_prumer -i data.txt --typ-b '{"R_i": 50000000}'

# Nejistota typu B z poloviny intervalu a rozdělení
python3 main.py aritmeticky_prumer -i data.txt --typ-b '{"R_i": [50000000, "rovnomerne"]}'

# JSON výstup
python3 main.py aritmeticky_prumer -i data.txt --output-format json
```

Vstupní formát souboru `.txt`:
```
VELIČINA1=1.23,4.56,7.89
VELIČINA2=2.34,5.67,8.90
```

Výstup bez typu B:
```
VELIČINA
├──Aritmetický průměr = ČÍSLO
└──Chyba aritmetického průměru = ČÍSLO
```

Výstup s typem B:
```
VELIČINA
├──Aritmetický průměr = ČÍSLO
├──Nejistota typu A = ČÍSLO
├──Nejistota typu B = ČÍSLO
├──Kombinovaná nejistota = ČÍSLO
└──Rozšířená nejistota (k=2) = ČÍSLO
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-lt`, `--latextable` | Exportovat do LaTeX tabulky |
| `-tb`, `--typ-b` | Nejistota typu B jako JSON (viz příklady) |
| `-ol`, `--outliers` | Odstranit outliery: `3sigma`, `2sigma`, `iqr` |
| `--caption` | Vlastní LaTeX caption (jinak auto-generace) |
| `--label` | Vlastní LaTeX label (jinak z názvu souboru) |
| `--export-csv` | Exportovat výsledky do CSV souboru |
| `--batch GLOB` | Zpracuje více souborů najednou (např. `'input/*.txt'`) |
| `--verbose` | Debug výpisy (parsování, precision, ...) |
| `--dry-run` | Neukládat soubory, jen ukázat co by se stalo |
| `--si-normalize` | Převede jednotky na základní SI (mA → A, kV → V, MΩ → Ω) |
| `--convert-units` | Převede jednotky dle JSON: `'{"I":"A","U":"mV"}'` |
| `--output-format` | `text` (výchozí) nebo `json` |

Podporované SI prefixy: y, z, a, f, p, n, μ, u, m, c, d, da, h, k, M, G, T, P, E, Z, Y.

Rozdělení pro nejistotu typu B jsou uvedena v Tabulce 1.

| Rozdělení | Vzorec | Použití |
|-----------|--------|---------|
| `rovnomerne` | u_B = a / √3 | Rozlišení digitálního přístroje |
| `trojuhelnikove` | u_B = a / √6 | Dva překrývající se zdroje nejistoty |
| `normalni` | u_B = a / 2 | Kalibrační certifikát (k=2) |

*Tab. 1: Rozdělení pro výpočet nejistoty typu B z poloviny intervalu a.*

---

### 5.2 `neprima_chyba`

Výpočet nepřímé chyby měření propagací přes parciální derivace. Parciální derivace počítáme symbolicky pomocí knihovny SymPy. Při zadání nejistoty typu B propagujeme kombinovanou nejistotu u_c namísto pouze u_A.

```bash
# Pouze typ A
python3 main.py neprima_chyba -i cesta/k/souboru.txt

# S nejistotou typu B
python3 main.py neprima_chyba -i cesta/k/souboru.txt --typ-b '{"t": 0.5, "U": 1}'

# Vstup ve formátu .xlsx
python3 main.py neprima_chyba -i data.xlsx -r "R=U/I"
python3 main.py neprima_chyba -i data.xlsx -r "R=U/I" -k '{"C": 0.000000047}'
```

Vstupní formát souboru `.txt` (indentovaný blokový zápis):
```
ELEMENTY
    t=0, 600, 1200, 1800
    U=300, 297, 291, 287

FUNKCE
    R=t / (C * ln(U_0 / U))
        FUNC_KONSTANTY
            U_0=300
            C=0.000000047
```

Nástroj podporuje i vstup ve formátu `.xlsx` (skrze knihovnu `pandas`).

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-r`, `--rovnice` | Rovnice ve formátu `VELIČINA=VZTAH` |
| `-k`, `--konstanty` | Konstanty jako JSON dict |
| `-tb`, `--typ-b` | Nejistota typu B jako JSON (stejný formát jako u aritmeticky_prumer) |

---

### 5.3 `vazeny_prumer`

Výpočet váženého průměru z hodnot naměřených s rozdílnou nejistotou (např. různými přístroji). Váha každé hodnoty je dána převrácenou hodnotou čtverce její nejistoty.

```bash
python3 main.py vazeny_prumer -v "10.2,10.3,10.1" -u "0.1,0.05,0.2"
python3 main.py vazeny_prumer -v "10.2,10.3,10.1" -u "0.1,0.05,0.2" -n "R"
```

Výstup:
```
R
├──Vážený průměr = 10.271428571428574
├──Nejistota = 0.04364357804719848
├──Počet měření = 3
└──Výsledek = 10.2714 ± 0.0436436
```

| Argument | Popis |
|----------|-------|
| `-v`, `--values` | Naměřené hodnoty oddělené čárkou (povinný) |
| `-u`, `--uncertainties` | Nejistoty jednotlivých měření (povinný) |
| `-n`, `--name` | Název veličiny (výchozí: `x`) |

---

### 5.4 `regrese`

Lineární regrese bez grafického výstupu. Vhodná pro situace kdy potřebujeme jen koeficienty ± nejistoty a kovarianční matici, nikoli graf.

```bash
python3 main.py regrese -i data.txt
python3 main.py regrese -i data.txt -x "U [V]" -y "I [mA]"
python3 main.py regrese -i data.txt -s sigma  # s nejistotami pro chi-squared
```

**Výstup:**
```
Lineární regrese: y = a·x + b
├──a = (2.00 ± 0.03)
├──b = (0.05 ± 0.10)
├──R² = 0.999319
├──Cov(a,b) = -0.0027
├──χ² = 5.23
├──χ²_red = 1.05 (ν = 3)
└──p-hodnota = 0.389
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-x`, `--x-col` | Sloupec nezávislé proměnné (výchozí: první) |
| `-y`, `--y-col` | Sloupec závislé proměnné (výchozí: druhý) |
| `-s`, `--sigma` | Sloupec s nejistotami y (pro chi-squared) |

---

### 5.5 `derivace`

Numerická derivace dat metodou centrálních diferencí (funkce `numpy.gradient`). Užitečné například pro výpočet rychlosti ze záznamu polohy.

```bash
python3 main.py derivace -i poloha.txt
python3 main.py derivace -i data.txt -x t -y x -o rychlost
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-x`, `--x-col` | Nezávislá proměnná (výchozí: první sloupec) |
| `-y`, `--y-col` | Závislá proměnná (výchozí: druhý sloupec) |
| `-o`, `--output` | Výstupní soubor bez přípony |

Výstupní soubor je ve formátu `VELIČINA=data` a ukládá se do adresáře `outputs/`.

---

### 5.6 `join_tables`

Spojení dvou LaTeX tabulek (`.tex`) do jedné. Metoda pracuje i s tabulkami rozdělenými do subtables (např. vygenerovanými metodou `aritmeticky_prumer -lt` nad velkými soubory).

```bash
# Horizontální spojení
python3 main.py join_tables -i tab1.tex tab2.tex -o spojena

# Párování podle prvního sloupce
python3 main.py join_tables -i mereni_U.tex mereni_I.tex -o spojena -m match
```

Mód `horizontal` (výchozí) umístí obě tabulky vedle sebe jako nezávislé sloupce. Kratší tabulku doplníme hodnotou `-`:

```
IN1: t|U    IN2: t|I     →   t|U|t|I
     0|300       0|1.5           0|300|0|1.5
     1|297       1|1.6           1|297|1|1.6
     2|291       5|2.0           2|291|5|2.0
```

Mód `match` páruje řádky podle prvního sloupce, který musí mít v obou tabulkách shodný header. Z druhé tabulky přidáváme jen zbývající sloupce:

```
IN1: t|U    IN2: t|I     →   t|U|I
     0|300       0|1.5           0|300|1.5
     1|297       1|1.6           1|297|1.6
     2|291       5|2.0           2|291|-       (t=2 není v IN2)
     3|287                       3|287|-
```

Výstupní soubor `outputs/<name>.tex` obsahuje:
- spojené sloupce (column spec se upraví podle jejich počtu),
- caption ve tvaru `IN1_caption \\ IN2_caption` (na novém řádku v LaTeXu),
- label ve tvaru `tab:IN1_label_IN2_label`.

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Dva `.tex` soubory (povinný, nargs=2) |
| `-o`, `--output` | Název výstupu bez přípony (výchozí: `joined_table`) |
| `-m`, `--mode` | `horizontal` (výchozí) nebo `match` |
| `--si-normalize` | Převede jednotky v tabulkách na SI |
| `--convert-units` | Převede jednotky dle JSON |

---

### 5.7 `format_table`

Úprava existující LaTeX tabulky. Metoda umožňuje převod jednotek, změnu captionu a labelu, přeformátování čísel, rozdělení či sloučení subtables a doplnění statistik z dat.

```bash
# Převod jednotek na SI
python3 main.py format_table -i mereni.tex --si-normalize

# Manuální převod s novým captionem
python3 main.py format_table -i mereni.tex --convert-units '{"I":"A"}' \
    --caption "Převedeno na SI"

# Přeformátování čísel
python3 main.py format_table -i mereni.tex --precision 3 --decimal-separator "."

# Rozdělení do subtables
python3 main.py format_table -i velka.tex --rows-per-subtable 30

# Doplnění statistik do captionu
python3 main.py format_table -i mereni.tex --append-stats --caption "Měření"

# Kombinace více úprav
python3 main.py format_table -i in.tex \
    --si-normalize --precision 2 --append-stats \
    --caption "Final" --label "final_tab" -o final
```

Přepínač `--append-stats` dopočítá z dat aritmetický průměr a střední kvadratickou chybu každého sloupce a vloží je do captionu ve formátu `$VELIČINA = (PRŮMĚR \pm CHYBA)\,\mathrm{JEDNOTKA}$`:

```latex
\caption{Test \\
    $t = (4900 \pm 286)\,\mathrm{ms}$ \\
    $T = (0,03 \pm 0,00)\,\mathrm{J}$ \\
    $U = (0,08 \pm 0,01)\,\mathrm{J}$ \\
    $E = (0,11 \pm 0,01)\,\mathrm{J}$}
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Vstupní `.tex` soubor (povinný) |
| `-o`, `--output` | Výstupní soubor bez přípony |
| `--si-normalize` | Převede jednotky na základní SI |
| `--convert-units` | JSON: `{"I":"A"}` |
| `--caption` | Nahradí caption |
| `--label` | Nahradí label |
| `--precision N` | Zaokrouhlit čísla na N des. míst |
| `--decimal-separator` | `","` nebo `"."` |
| `--rows-per-subtable N` | Split do subtables (0 = jedna tabulka) |
| `--append-stats` | Přidá aritmetický průměr ± chybu do captionu |
| `--no-caption-stats` | Vynutí vypnutí auto-statistik (pokud jsou v configu) |
| `--auto-scale` | Automaticky zvolí vhodný SI prefix pro každý sloupec |
| `--interactive` | Interaktivní režim pro postupnou úpravu parametrů |
| `--dry-run` | Neukládat, jen zobrazit |

---

### 5.8 `extract_table`

Inverze metody `format_table` — extrahuje data z LaTeX tabulky zpět do formátu `VELIČINA=data`. Užitečné pokud potřebujeme s tabulkou dále pracovat (nový průměr, jiný graf).

```bash
python3 main.py extract_table -i mereni.tex -o data
python3 main.py extract_table -i mereni.tex -o data --keep-units
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Vstupní `.tex` soubor (povinný) |
| `-o`, `--output` | Výstupní soubor bez přípony |
| `--keep-units` | Zachová jednotku v názvu sloupce (`X [s]=...`) |

---

### 5.9 `convert_soubor`

Konverze tabulkového souboru (TSV s hlavičkou a jednotkami) do formátu `PROMĚNNÁ=data`.

```bash
python3 main.py convert_soubor -i tabulka.txt
python3 main.py convert_soubor -i tabulka.txt -o muj_vystup
```

Vstupní formát:
```
Sloupec1    Sloupec2    Sloupec3
m           A           s
0.1         1.5         2.3
0.2         1.6         2.4
```

Výstupní formát:
```
m=0.1,0.2
A=1.5,1.6
s=2.3,2.4
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-o`, `--output` | Název výstupního souboru bez přípony (výchozí: `output_convertor`) |

## 6 Grafové metody

### 6.1 `graf`

2D a 3D grafy s volitelným fitem, chi-squared statistikou a panelem reziduí. Výstupem je soubor `.svg`.

```bash
# Základní graf
python3 main.py graf -i data.txt -n "Můj graf"

# S rovnicí (3D)
python3 main.py graf -i data.txt -n "Graf" -r "Z=t*U"

# 2D graf funkce přes parametr
python3 main.py graf -i data.txt -n "Graf" -r "Z=t*U" -p t

# S fitem
python3 main.py graf -i data.txt -n "Graf" -f linearni

# S fitem + chi-squared statistika + panel reziduí
python3 main.py graf -i data.txt -n "Graf" -f linearni --chi2

# Logaritmické měřítko + fit
python3 main.py graf -i data.txt -n "Graf" -log -f exponencialni
```

Výstup s přepínačem `--chi2`:
```
Fit: linearni
├──a = 1.234 * 10^0 ± 5.600 * 10^-2
├──b = -1.200 * 10^0 ± 3.000 * 10^-1
├──R² = 0.998700
├──χ² = 5.2300
├──χ²_red = 1.0460  (ν = 5)
└──p-hodnota = 0.3890
```

Hodnotu redukovaného χ² interpretujeme dle Tabulky 2.

| χ²_red | Interpretace |
|--------|-------------|
| ≈ 1 | Fit odpovídá datům, nejistoty jsou konzistentní |
| >> 1 | Fit neodpovídá datům, případně jsou nejistoty podhodnocené |
| << 1 | Nejistoty jsou nadhodnocené |

*Tab. 2: Interpretace redukovaného chi-squared.*

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-n`, `--name` | Název grafu (povinný) |
| `-r`, `--rovnice` | Závislost — rovnice pro 3D/2D graf |
| `-p`, `--parametr` | Parametr pro 2D graf funkce f(x) |
| `-log`, `--logaritmicky` | Logaritmické měřítko y-osy |
| `-f`, `--fit` | Typ fitu: `linearni`, `kvadraticky`, `exponencialni`, `mocninny` |
| `--chi2` | Zobrazí chi-squared statistiku a panel reziduí |
| `--plot-outliers` | Zvýrazní outliery červeně: `3sigma`, `iqr` atd. |
| `--custom-fit` | Vlastní fit funkce (SymPy): `'a*sin(b*x+c)'` |

---

### 6.2 `histogram`

Histogram rozdělení dat s volitelným proložením Gaussovkou. Užitečné zejména pro ověření normality rozdělení naměřených hodnot. Výstupem je soubor `.svg`.

```bash
python3 main.py histogram -i data.txt --gauss
python3 main.py histogram -i data.txt -c U --bins 20 -n "Rozdeleni_U"
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-c`, `--column` | Sloupec pro histogram (výchozí: první) |
| `-b`, `--bins` | Počet binů (výchozí: √n) |
| `-n`, `--name` | Název výstupního grafu |
| `--gauss` | Překryje Gaussovkou (pro ověření normality) |

---

### 6.3 `graf_interval`

Graf jedné funkce na zadaném intervalu. Výstupem je soubor `.svg`.

```bash
python3 main.py graf_interval -n "Funkce" -r "y=x**2+2*x" -i 0 100
```

| Argument | Popis |
|----------|-------|
| `-n`, `--name` | Název grafu (povinný) |
| `-r`, `--rovnice` | Funkce ve formátu `VELIČINA=VZTAH` (povinný) |
| `-i`, `--interval` | Počátek a konec intervalu, např. `-i 0 100` (povinný) |

## 7 Architektura

Projekt je postaven na plugin architektuře v OOP. Každá metoda je třída dědící z abstraktní bázové třídy `Method`. Data jsou zpracovávána prostřednictvím objektového modelu (`Measurement`, `MeasurementSet`, `InputParser`).

```
main.py                              # CLIApp — discovery, argparse, spuštění (všechny metody)
main_statistika.py                   # CLIApp — jen výpočetní metody
main_grafy.py                        # CLIApp — jen grafové metody
statisticke_vypracovani/
    base.py                          # Method (ABC) — rozhraní pro všechny metody
    aritmeticky_prumer/logic.py      # class AritmetickyPrumer(Method)
    neprima_chyba/logic.py           # class NeprimaChyba(Method)
    vazeny_prumer/logic.py           # class VazenyPrumer(Method)
    join_tables/logic.py             # class JoinTables(Method) — spojování .tex tabulek
    derivace/logic.py                # class Derivace(Method) — numerická derivace
    format_table/logic.py            # class FormatTable(Method) — úprava .tex tabulky
    regrese/logic.py                 # class Regrese(Method) — lineární regrese
    extract_table/logic.py           # class ExtractTable(Method) — extrakce dat z .tex zpět
    histogram/logic.py               # class Histogram(Method) — histogram + Gaussovka
    graf/logic.py             # class Graf(Method) + chi-squared
    graf_interval/logic.py           # class GrafInterval(Method)
    convert_soubor/logic.py          # class ConvertSoubor(Method)
objects/
    measurement.py                   # Measurement — jedna veličina (mean, u_A, u_B, u_c)
    measurement_set.py               # MeasurementSet — kolekce měření + LaTeX/JSON export
    input_parser.py                  # InputParser — parsování txt, xlsx, indent formátu, CASSY
    config.py                        # Config loader pro .zm2rc
utils.py                             # Sdílené funkce (smart_parse, clean_latex, r2_score...)
tests/                               # 159+ unit testů (+ integration/)
docs/                                # Sphinx dokumentace (make html)
zm2/                                 # Programatické API
examples/                            # Příklady workflow pro konkrétní úlohy
```

### 7.1 Postup přidání nové metody

1. Vytvoříme složku `statisticke_vypracovani/<nazev_metody>/`.
2. V souboru `logic.py` definujeme třídu dědící z `Method`:
   ```python
   from statisticke_vypracovani.base import Method;

   class MojeMetoda(Method):
       name = "nazev_metody";
       description = "Popis metody";

       def get_args_info(self):
           return [ ... ];  # definice CLI argumentů

       def run(self, args):
           ...  # hlavní logika
   ```
3. V souboru `__init__.py` importujeme třídu:
   ```python
   from .logic import MojeMetoda;
   ```
4. `CLIApp` metodu automaticky vyhledá při spuštění.
5. Pro zařazení do binárního balíku přidáme název metody do `main_statistika.py` nebo `main_grafy.py`.

## 8 Lokální build

```bash
# Výpočetní tool (bez matplotlib — cca 75 MB)
bash builder/build_statistika_linux.sh

# Grafový tool (včetně matplotlib — cca 96 MB)
bash builder/build_grafy_linux.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File builder\build_statistika_windows.ps1
powershell -ExecutionPolicy Bypass -File builder\build_grafy_windows.ps1

# Simulace release procesu lokálně
bash builder/simulate_release.sh v0.4-test
```

## 9 Konvence kódu

- Středníky na konci příkazů (záměrná stylová volba).
- Komentáře a UI řetězce v češtině.
- Každá metoda musí implementovat `run(self, args)` a `get_args_info(self)`.

## 10 Shell completion

Nástroj podporuje tab-completion v bashi i zsh prostřednictvím knihovny `argcomplete`:

```bash
pip install argcomplete
eval "$(register-python-argcomplete main.py)"
```

Podrobný návod v [docs/shell_completion.md](docs/shell_completion.md).

## 11 Příklady

Reálné příklady workflow najdeme ve složce [`examples/`](examples/). Každá úloha obsahuje popis, vstupní data a `commands.sh` s kompletní posloupností příkazů:

- `termistor/` — Úloha #9, závislost odporu na teplotě
- `ohmuv_zakon/` — Úloha #7, U-I charakteristika rezistoru
- `wheatstone/` — Úloha #8, Wheatstoneův můstek
- `kmity/` — Úloha #10, tlumené harmonické kmity

## 12 Dokumentace (Sphinx)

Projekt má scaffold pro generování HTML dokumentace z docstringů pomocí Sphinxu.

```bash
pip install sphinx
cd docs
make html
# výstup v docs/_build/html/index.html
```

## 13 Závislosti

- numpy, scipy, sympy, requests — jádro,
- matplotlib, Pillow — grafy,
- pandas, openpyxl — vstup ve formátu `.xlsx`.

## 14 Historie změn

Přehled změn je uveden v souboru [CHANGELOG.md](CHANGELOG.md).

## 15 Licence

Projekt je distribuován pod licencí [MIT](LICENSE).
