# Vstupní formáty

Tento dokument popisuje všechny formáty vstupních souborů akceptované jednotlivými metodami nástroje. Pro každý formát uvádíme schema, příklad a metody, které jej akceptují.

Pro programovou validaci vstupů (line:col chyb) je v repu skript [`validate_inputs.py`](../validate_inputs.py).

## Obsah

1. [Přehled — která metoda žere jaký formát](#1-přehled)
2. [Sdílené formáty](#2-sdílené-formáty) — `.txt`, `.xlsx`, `.toml`
3. [Speciální formáty per metoda](#3-speciální-formáty-per-metoda) — `nc`, `derivace` (symbolický), `tabulka`, `vp`, `gi`, `cs`, `jt`/`ft`/`et`
4. [Příklady end-to-end](#4-příklady-end-to-end)
5. [Validace](#5-validace)

---

## 1 Přehled

| Metoda | Alias | Vstupní formáty | Specifikum |
|---|---|---|---|
| `aritmeticky_prumer` | `ap` | `.txt`, `.xlsx`, `.toml` | TOML podporuje `[vypocty]` |
| `neprima_chyba` | `nc` | `.txt` (indentovaný), `.xlsx`, `.toml` (rozšířené) | Vlastní schema |
| `vazeny_prumer` | `vp` | žádný — argumenty na CLI | `-v`, `-u`, `-n` |
| `regrese` | `reg` | `.txt`, `.xlsx`, `.toml` | |
| `derivace` | `der` | `.txt`, `.xlsx`, `.toml` | `.txt`/`.xlsx` → numerická; `.toml` → symbolická (sdílené schema s `nc`) |
| `integrace` | `integrace` | `.txt`, `.xlsx`, `.toml` | |
| `histogram` | `hist` | `.txt`, `.xlsx`, `.toml` | |
| `graf` | `g` | `.txt`, `.xlsx`, `.toml` | |
| `graf_interval` | `gi` | žádný — argumenty na CLI | `-r`, `-i` |
| `tabulka` | `tab` | `.toml` | Sdílené schema s `nc`; `[funkce.*]` se vyhodnocuje po řádcích (1-na-1) |
| `convert_soubor` | `cs` | `.txt`/`.csv`/`.tsv` (CASSY auto-detect) | Konvertuje na standardní formát |
| `join_tables` | `jt` | dva `.tex` soubory | LaTeX tabulky |
| `format_table` | `ft` | jeden `.tex` soubor | LaTeX tabulka |
| `extract_table` | `et` | jeden `.tex` soubor | LaTeX tabulka |

---

## 2 Sdílené formáty

Tyto tři formáty žerou všechny metody, které berou `-i SOUBOR`: `ap`, `reg`, `der`, `integrace`, `hist`, `g`. Detekce proběhne podle přípony (`.xlsx`, `.toml`) nebo obsahu (CASSY auto-detekce z druhého řádku `.txt`).

### 2.1 `.txt` — standardní formát

Schema: každý řádek je `VELIČINA = v1, v2, v3, ...`

- Desetinný oddělovač je **tečka** (`3.14`).
- Hodnoty oddělujeme čárkou.
- Jméno veličiny může mít jednotku v hranatých závorkách: `t [s]`, `U [V]`, `T [K]`.
- Prázdné řádky ignorujeme.

Příklad (`kmity.txt`):

```
t [s]=0.0,0.1,0.2,0.3,0.4,0.5
x [m]=0.00,0.29,0.48,0.52,0.38,0.12
```

Nejistotu typu B lze nastavit jen z CLI:

```bash
python3 main.py ap -i kmity.txt --typ-b '{"x": [0.005, "rovnomerne"]}'
```

### 2.2 `.txt` — CASSY auto-detekce

Pokud druhý řádek `.txt` souboru obsahuje hlavičku s jednotkami v závorkách (`(...)`), parser ho rozezná jako export z měřicího systému CASSY. Schema:

- Řádek 1: hlavička s názvem souboru / běhu (ignoruje se).
- Řádek 2: jména veličin s jednotkami v závorkách, oddělené tabulátorem nebo dvojicí mezer.
- Řádky 3+: hodnoty v tabulkové podobě (sloupce odděleny `\t` nebo `  +`).
- Desetinný oddělovač: **čárka** (lokalizovaný export).

Příklad (`cassy.txt`):

```
E, Run #1
t (s)	T (K)	URT (V)	URN (V)
0,0	296,45	-0,40	0,80
30,0	296,45	-0,39	0,81
60,0	296,55	-0,39	0,81
```

Detekce je automatická — stačí `python3 main.py ap -i cassy.txt`.

### 2.3 `.xlsx` — Excel

Schema:

- Hlavička v prvním řádku — názvy sloupců odpovídají veličinám (s jednotkami: `U [V]`).
- Hodnoty číselné, prázdné buňky a sloupce `Unnamed:*` se ignorují.
- Desetinný oddělovač podle Excelu (oba akceptováno).

Žádný textový vzor — ukázka je v `examples/`.

Limit: nepodporuje `typ_b` přímo v souboru (jen z CLI přes `--typ-b`).

### 2.4 `.toml` — strukturovaný formát

**Nejvíc preferovaný formát.** Zbavuje uživatele dvou pastí (záměny `,` jako des. oddělovače vs. oddělovače hodnot, chyb v indentaci) a umožňuje deklarovat `typ_b` přímo v souboru.

Schema:

```toml
[veliciny.<jméno>]
unit = "<SI jednotka>"      # volitelné — přidá se do názvu jako "<jméno> [<unit>]"
hodnoty = [v1, v2, v3, ...]

# Nejistota typu B (volitelné). Tři podoby:
typ_b = 0.01                                                   # přímý u_B
typ_b = { a = 0.005, distribuce = "rovnomerne" }               # polovina intervalu + rozdělení
typ_b = { a = 10, unit = "um", distribuce = "rovnomerne" }     # chyba v jiné jednotce — přepočet
```

Rozdělení pro `typ_b`:

| `distribuce` | Vzorec | Použití |
|---|---|---|
| `rovnomerne` | `u_B = a / √3` | rozlišení digitálního přístroje |
| `trojuhelnikove` | `u_B = a / √6` | dva nezávislé zdroje, překrývající se intervaly |
| `normalni` | `u_B = a / 2` | kalibrační certifikát s `k=2` |

#### Derivované sloupce — `[vypocty.<jméno>]`

Spočte odvozený sloupec per řádek dosazením do vzorce:

```toml
[veliciny.U]
unit = "V"
hodnoty = [1.20, 1.21, 1.19, 1.22]

[veliciny.I]
unit = "A"
hodnoty = [0.50, 0.51, 0.49, 0.52]

[vypocty.R]
unit = "Ohm"
vzorec = "U / I"

[vypocty.P]
unit = "W"
vzorec = "U * I"
```

Volitelný klíč `konstanty` umožňuje ve vzorci použít pevné hodnoty, které nejsou veličiny:

```toml
[vypocty.R_corr]
unit = "Ohm"
vzorec = "U / I + R_0"
konstanty = { R_0 = 0.05 }

[vypocty.x]
unit = "m"
vzorec = "v_0 * t + 0.5 * g * t**2"
konstanty = { v_0 = 5.0, g = 9.81 }
```

- Konstanty jsou jen číselné hodnoty (int/float). Substituují se před vyhodnocením, takže ve výsledné tabulce se neobjeví jako sloupec.
- Jméno konstanty nesmí kolidovat s jménem veličiny (`[veliciny.R_0]` + `konstanty.R_0` → chyba).
- Vzorec musí obsahovat aspoň jednu skutečnou veličinu — vzorec čistě z konstant by spočítal jedno číslo, ne sloupec.

- Vzorec parsuje SymPy. Seznam podporovaných funkcí viz [§ 3.5 Funkce ve vzorcích](#35-funkce-ve-vzorcích).
- Identifikátory ve vzorci musí odpovídat jménům veličin (bez jednotky).
- Při dělení nulou nebo mimo definiční obor je výsledek `NaN`, v LaTeX tabulce se zobrazí jako `-`, a po výstupu se na `stderr` vypíše seznam problematických řádků.
- Nejistoty se u derivovaných veličin **nepropagují** — pro to slouží metoda `nc`/`neprima_chyba`.

---

## 3 Speciální formáty per metoda

### 3.1 `neprima_chyba` (`nc`)

Tato metoda počítá nepřímou chybu měření propagací přes parciální derivace. Vyžaduje **dva typy vstupu**: měřená data (elementy) + funkční vztah (vzorec). Tři podporované formáty:

#### 3.1.1 `.txt` — indentovaný

Dvě sekce: `ELEMENTY` (data) a `FUNKCE` (vzorec). Indentace 4 mezery.

```
ELEMENTY
    R_1=100.2, 100.1, 100.3, 100.2, 100.1
    R_2=220.5, 220.3, 220.4, 220.6, 220.5
    R_3=330.8, 330.7, 330.9, 330.6, 330.8

FUNKCE
    R_x=R_2 * R_1 / R_3
```

#### 3.1.2 `.toml` — rozšířené schema

```toml
[veliciny.t]
hodnoty = [10.0, 10.1, 9.9]
typ_b = 0.5

[veliciny.U]
hodnoty = [3.0, 3.0, 3.0]
typ_b = 1.0

[funkce.R]
vzorec = "t / log(U_0 / U)"
unit = "Ohm"                      # volitelné — aktivuje SI převod výsledku
konstanty = { U_0 = 300, C = 4.7e-8 }     # volitelné, včetně pi/e/...
```

Klíče v `[funkce.<jméno>]`:
- `vzorec` (povinné) — formula s identifikátory odpovídajícími veličinám (a konstantám).
- `unit` (volitelné) — výsledná jednotka. Pokud je složená (`g*mm**-3`), tool ji rozparsuje a převede na základní SI (např. `kg*m^-3`).
- `konstanty` (volitelné) — slovník konstant, které ve vzorci vystupují (např. `pi`, `e`, ale i `U_0`, `C`).

Rozdíl proti TOMLu pro `ap`:
- `[veliciny]` může — ale nemusí — mít `unit`. Při propagaci nejistot se `unit` nepoužívá.
- `[funkce]` je **povinná** sekce.
- `[vypocty]` se v `nc` **nepoužívá** (parser pro nc ignoruje, použít pro per-row výpočty bez propagace nejistot — to je `ap`).

#### 3.1.3 `.xlsx`

Stejné schema jako u `ap` (sloupce = veličiny). Funkční vztah se zadává přes CLI:

```bash
python3 main.py nc -i data.xlsx -r "R=U/I" -k '{"C": 4.7e-8}'
```

#### 3.1.4 Sdílení TOML s `derivace` a `tabulka`

Stejný TOML soubor (`[veliciny.*]` + `[funkce.*]`) lze pustit přes tři metody bez úprav:

| Metoda | Co spočte |
|---|---|
| `nc` | propagace nejistoty (numericky), výstup `(mean ± u_c)` per funkce |
| `derivace` (s `.toml`) | symbolické parciální derivace `∂f/∂x` per veličina (sympy + LaTeX) |
| `tabulka` | LaTeX tabulka: sloupce = veličiny + per-řádkové vyhodnocení vzorců |

Veličiny bez `hodnoty`/`typ_b` jsou pro `derivace` v pořádku (potřebuje jen seznam jmen); pro `nc` a `tabulka` se hodnoty vyžadují. Klíče `unit`, `typ_b` a `konstanty` mají v každé metodě jiný význam:

| Klíč | `nc` | `derivace` | `tabulka` |
|---|---|---|---|
| `veliciny.X.hodnoty` | povinné | ignoruje | povinné |
| `veliciny.X.typ_b` | použito (u_B) | ignoruje | ignoruje |
| `veliciny.X.unit` | informativní | ignoruje | hlavička sloupce |
| `funkce.Y.vzorec` | povinné | povinné | volitelné (přidá sloupec) |
| `funkce.Y.unit` | aktivuje SI rescale | ignoruje | hlavička sloupce |
| `funkce.Y.konstanty` | dosadí při výpočtu | nederivuje se podle nich | dosadí při výpočtu po řádcích |

### 3.1bis `tabulka` (`tab`) — `.toml` schema

```toml
[veliciny.t]
hodnoty = [10.0, 10.1, 9.9]
unit = "s"

[veliciny.U]
hodnoty = [3.0, 3.05, 2.98]
unit = "V"

[funkce.R]                              # volitelné
vzorec = "t / log(U_0 / U)"
unit = "Ohm"
konstanty = { U_0 = 300 }
```

Pravidla:

- Každá `[veliciny.X]` se stane jedním sloupcem v tabulce. `hodnoty` jsou povinné, `unit` je volitelná (vykreslí se v hlavičce jako `\mathrm{unit}`).
- Pro každou `[funkce.Y]` se vzorec dosadí **po řádcích** (1-na-1 pairing): i-tá hodnota každé veličiny → i-tý řádek funkce. Konstanty z `konstanty = { … }` se dosazují předem.
- Pokud má vzorec proměnnou, která není ani ve `[veliciny.*]` ani v `konstanty`, parser hlásí chybu.
- Bez přepínače `-lt` produkuje jen tabulku hodnot. S `-lt` přidá do popisku `$X = (mean \pm u_c)\,\mathrm{unit}$` per sloupec — chování ekvivalentní `aritmeticky_prumer -lt`.

### 3.1ter `derivace` (`der`) — `.toml` (symbolický režim)

Stejné schema jako `nc`. `derivace` ze schématu vyžaduje jen jména veličin (z `[veliciny.*]`) a vzorec(e) z `[funkce.*]`; `hodnoty`, `typ_b` a `unit` ignoruje. Pro každou funkci spočte parciální derivace podle všech veličin, které se ve vzorci vyskytují a nejsou v `konstanty`. Pokud `[veliciny.*]` chybí, derivuje podle všech proměnných ve vzorci, které nejsou konstantami.

### 3.2 `vazeny_prumer` (`vp`) — bez souboru

Argumenty se předávají na CLI:

```bash
python3 main.py vp \
    -v "10.2,10.3,10.1,10.25" \
    -u "0.1,0.05,0.2,0.08" \
    -n "x [mm]"
```

| Flag | Popis |
|---|---|
| `-v`, `--values` | Naměřené hodnoty oddělené čárkou |
| `-u`, `--uncertainties` | Nejistoty jednotlivých měření, stejný počet jako `-v` |
| `-n`, `--name` | Název veličiny (s jednotkou nebo bez) |

### 3.3 `graf_interval` (`gi`) — bez souboru

Vykreslí funkci na zadaném intervalu, žádná data nečte.

```bash
python3 main.py gi \
    -n "kvadrat" \
    -r "y = x**2" \
    -i 0 10
```

| Flag | Popis |
|---|---|
| `-n`, `--name` | Název grafu (jméno výstupního SVG) |
| `-r`, `--rovnice` | Funkční závislost ve formátu `VELIČINA=VZTAH`. Musí mít právě jednu proměnnou. Akceptuje Python (`x**2`) i LaTeX (`\frac{x}{2}`). |
| `-i`, `--interval` | Dvě čísla — meze intervalu (např. `-i 0 10`). |

### 3.4 `convert_soubor` (`cs`) — žere libovolné .txt/.csv/.tsv

Konvertuje různé tabulkové vstupy (CASSY exporty, Excel-export-jako-CSV, TSV s desetinnou čárkou) do standardního formátu `VELIČINA=v1,v2,...` použitelného ostatními metodami.

```bash
python3 main.py cs -i raw_export.txt -o clean
# vytvoří clean.txt v standardním formátu
```

Žádné fixní schema — heuristicky detekuje:
- desetinný oddělovač (tečka vs. čárka),
- oddělovač sloupců (tab, dvojí mezera, středník, jednoduchá čárka),
- hlavičku s jednotkami v závorkách.

### 3.5 Funkce ve vzorcích

Vzorce v `[vypocty.<X>]` (metoda `ap`) i `[funkce.<X>]` (metoda `nc`) se parsují přes SymPy. Identifikátory ve vzorci jsou buď názvy veličin (musí existovat sekce `[veliciny.<jméno>]`), konstanty (uvedené v `konstanty = {...}` u `nc`), nebo matematické funkce z následujícího seznamu.

#### Trigonometrické funkce

| Funkce | Popis |
|---|---|
| `sin(x)` | sinus |
| `cos(x)` | kosinus |
| `tan(x)` | tangens |
| `cot(x)` | kotangens |
| `sec(x)` | sekans (`1/cos`) |
| `csc(x)` | kosekans (`1/sin`) |

Argumenty se předpokládají v **radiánech**.

#### Inverzní trigonometrické funkce — dvě notace

Tool akceptuje dvě ekvivalentní notace; vyber si tu, která ti je bližší:

| Python-style | Fyzikální alias | Popis |
|---|---|---|
| `asin(x)` | `arcsin(x)` | arkussinus |
| `acos(x)` | `arccos(x)` | arkuskosinus |
| `atan(x)` | `arctan(x)` | arkustangens |
| `acot(x)` | — | arkuskotangens |
| `asec(x)` | — | arkussekans |
| `acsc(x)` | — | arkuskosekans |
| `atan2(y, x)` | — | dvouargumentový arkustangens — vrací úhel správného kvadrantu |

Výsledek je v **radiánech**. Pokud chceš stupně, máš dvě možnosti:

1. **Násob v vzorci** — `vzorec = "atan(h/l) * 180 / pi"`, `unit = "deg"`.
2. **Nastavit `unit = "rad"` a převést přes `--convert-units`** — `--convert-units '{"theta":"deg"}'`. Tool zná převod `rad ↔ deg` automaticky (`deg` = π/180 rad), funguje i s prefixy (`mrad`, `mdeg`, ...).

#### Hyperbolické a inverzní hyperbolické

| Hyperbolické | Inverzní (Python) | Inverzní (alias) |
|---|---|---|
| `sinh(x)` | `asinh(x)` | `arcsinh(x)` |
| `cosh(x)` | `acosh(x)` | `arccosh(x)` |
| `tanh(x)` | `atanh(x)` | `arctanh(x)` |
| `coth(x)` | `acoth(x)` | — |
| `sech(x)` | `asech(x)` | — |
| `csch(x)` | `acsch(x)` | — |

#### Exponenciální, logaritmické, mocninné

| Funkce | Popis |
|---|---|
| `exp(x)` | e^x |
| `log(x)` | **přirozený** logaritmus (== `ln`) — pozor, není dekadický! |
| `ln(x)` | přirozený logaritmus (alias `log`) |
| `log(x, base)` | logaritmus o základu `base` (např. `log(x, 10)` = dekadický) |
| `sqrt(x)` | druhá odmocnina (== `x**0.5`) |
| `x**y` | mocnina |

#### Ostatní

| Funkce | Popis |
|---|---|
| `Abs(x)` / `abs(x)` | absolutní hodnota |
| `floor(x)` | dolní celá část |
| `ceiling(x)` | horní celá část |
| `Min(a, b, ...)` | minimum |
| `Max(a, b, ...)` | maximum |

#### Konstanty

| Konstanta | Hodnota |
|---|---|
| `pi` | π = 3,141592… |
| `e` | Eulerovo číslo = 2,71828… (pozor: `E` je běžný symbol, ne konstanta) |
| `I` | imaginární jednotka (jen pro `nc`, kde se může objevit ve výpočtech) |

#### Příklady

```toml
# Úhel z arkustangens — obě varianty stejně
[vypocty.theta_python]
unit = "rad"
vzorec = "atan(h / l)"

[vypocty.theta_fyz]
unit = "rad"
vzorec = "arctan(h / l)"

# Stupně místo radiánů
[vypocty.theta_deg]
unit = "deg"
vzorec = "atan(h / l) * 180 / pi"

# Snellův zákon — index lomu z úhlů
[vypocty.n]
unit = "-"
vzorec = "sin(theta_i) / sin(theta_r)"

# Logaritmický článek (např. R z τ = R*C*ln(U₀/U))
[vypocty.R]
unit = "Ohm"
vzorec = "tau / (C * log(U_0 / U))"

# Kombinace — eulerova metoda pro pohyb v gravitaci
[vypocty.dosah]
unit = "m"
vzorec = "v_0**2 * sin(2 * theta) / g"

# Hypotenuza s ošetřenou doménou
[vypocty.c]
unit = "mm"
vzorec = "sqrt(a**2 + b**2)"
```

#### Co **nejde**

| Co | Proč | Jak místo toho |
|---|---|---|
| `\arcsin{x}` (LaTeX) | TOML parser je SymPy, ne LaTeX. | Použij `arcsin(x)` nebo `asin(x)`. Pro LaTeX vzorce slouží metody `g`/`gi` přes flag `--rovnice`. |
| `sin^{-1}(x)` | Není ani Python ani SymPy syntax. | `asin(x)` nebo `arcsin(x)`. |
| `log_{10}(x)` | LaTeX subscript notace. | `log(x, 10)`. |
| `x^2` | `^` je v Pythonu XOR, ne mocnina. | `x**2`. |
| `xy` (implicitní násobení dvou identifikátorů) | Tool nepoužívá `split_symbols`, takže `xy` je jeden symbol, ne `x*y`. Schválně — kdyby mohl, kolize s `R_0`/`theta` by byly noční můrou. | `x*y`. |

### Co naopak **funguje**

| Zápis | Výsledek |
|---|---|
| `2l` | `2*l` (číslo + identifikátor) |
| `2(x + y)` | `2*(x+y)` (číslo + závorka) |
| `2pi` | `2*pi` |
| `atan(n / (2l))` | identické s `atan(n / (2*l))` |

---

### 3.6 `join_tables`, `format_table`, `extract_table` — `.tex` vstupy

Tyto tři metody pracují **nad existujícími LaTeX tabulkami**, ne nad surovými daty.

| Metoda | Vstup | Co dělá |
|---|---|---|
| `jt` | `-i SOUBOR1.tex SOUBOR2.tex` (dva) | Spojí dvě tabulky vedle sebe (mód `horizontal`) nebo s match po klíči |
| `ft` | `-i SOUBOR.tex` (jeden) | Mění jednotky, caption, label, precision, počet subtables, doplní statistiky |
| `et` | `-i SOUBOR.tex` (jeden) | Vytáhne data z LaTeX tabulky zpět do formátu `VELIČINA=...` (inverze `format_table`) |

Schema vstupu: standardní `\begin{table}...\begin{tabular}{...}...\end{tabular}...\end{table}` blok s `\caption{...}` a `\label{tab:...}`. Tool rozumí `\toprule`/`\midrule`/`\bottomrule` (booktabs) a běžným hlavičkám typu `$U \, [\mathrm{V}]$`.

---

## 4 Příklady end-to-end

### 4.1 Aritmetický průměr s typ B v jiné jednotce, derivovaný sloupec

`mereni.toml`:

```toml
[veliciny.U]
unit = "V"
hodnoty = [1.205, 1.213, 1.198, 1.225]
typ_b = { a = 5, unit = "mV", distribuce = "rovnomerne" }   # 5 mV = 0,005 V

[veliciny.I]
unit = "A"
hodnoty = [0.502, 0.511, 0.494, 0.520]
typ_b = 0.001

[vypocty.R]
unit = "Ohm"
vzorec = "U / I"
```

```bash
python3 main.py ap -i mereni.toml -lt --round-by u_b
```

### 4.2 Nepřímá chyba, TOML

`hustota.toml`:

```toml
[veliciny.m]
hodnoty = [12.34, 12.35, 12.33]
typ_b = 0.01

[veliciny.d]
hodnoty = [3.42, 3.41, 3.43]
typ_b = 0.005

[funkce.rho]
vzorec = "6 * m / (pi * d**3)"
unit = "g*mm**-3"
konstanty = { pi = 3.14159265358979 }
```

```bash
python3 main.py nc -i hustota.toml
```

### 4.3 Vážený průměr — bez souboru

```bash
python3 main.py vp -v "9.81,9.78,9.83" -u "0.05,0.02,0.10" -n "g [m/s^2]"
```

### 4.4 Histogram z Excelu

```bash
python3 main.py hist -i mereni.xlsx --bins 20 --gauss
```

### 4.5 CASSY soubor → graf

```bash
# CASSY auto-detekce funguje v jednom kroku
python3 main.py g -i cassy.txt -x "t (s)" -y "T (K)" --fit-type poly1
```

### 4.6 Spojení dvou LaTeX tabulek

```bash
python3 main.py jt -i tab_pred.tex tab_po.tex --mode horizontal
```

---

## 5 Validace

Pro hromadnou kontrolu syntaxe vstupních souborů (TOML i TXT/XLSX) je v repu skript:

```bash
# Jeden soubor
python3 validate_inputs.py inputfiles/2_uloha.toml

# Glob
python3 validate_inputs.py 'inputfiles/*.toml'

# Rekurzivně přes celý strom
python3 validate_inputs.py 'examples/**/*'

# CI / log (bez barev)
NO_COLOR=1 python3 validate_inputs.py 'inputfiles/*'
```

Výstup pro běžné chyby (line:col, kde to jde):

```
OK    /tmp/clean.toml
FAIL  /tmp/syntax.toml:4:9: TOML syntax: Invalid value (at line 4, column 9)
FAIL  /tmp/semantic.toml:4:35: ValueError: Velicina 'd': nezname rozlozeni 'rovomerne'.
FAIL  /tmp/missing.toml:1:11: ValueError: Velicina 'x' nema klic 'hodnoty'
FAIL  /tmp/unitmismatch.toml:1:11: ValueError: Velicina 't': typ_b.unit nelze prevest na jednotku veliciny — ...
FAIL  /tmp/bad_formula.toml:7:15: ValueError: Vypocet 'R': v setu chybi promenne ['Q']

1 OK, 5 FAIL
```

Exit kód: `0` pokud vše OK, `1` pokud aspoň jeden FAIL.

Skript chytá:

| Typ chyby | Lokalizace |
|---|---|
| TOML syntax (chybějící čárka, dvojí klíč, ...) | přesná `line:col` |
| Chybějící povinný klíč (`hodnoty`, `vzorec`) | line jména veličiny |
| Neznámé `distribuce` v `typ_b` | line+col špatné hodnoty |
| Nesourodé jednotky v `typ_b.unit` | line jména veličiny |
| Neparsovatelný vzorec v `[vypocty]`/`[funkce]` | line+col bad symbolu |
| Vstupy s různým počtem hodnot | line jména veličiny |
| Špatný formát TXT | jen typ chyby (TXT nemá strukturu pro line tracking) |
| XLSX corrupted / chybí list | jen typ chyby |

Známá omezení:

1. Validátor nepoznává `nc` formát automaticky — jednoduché TOMLy s `[funkce]` interpretuje jako `ap` formát, který `[funkce]` ignoruje (false-positive OK). Pro pořádnou validaci `nc` souboru ho spusť jako `python3 main.py nc -i FILE --dry-run`.
2. `.txt` soubory pro `nc` (s `ELEMENTY`/`FUNKCE`) projdou skriptem jako `IndexError`, protože parser pro `ap` formát se nedokáže k tomu schematu vrátit. Pro tyhle soubory použij `--dry-run` přes vlastní metodu.
