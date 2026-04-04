# ZM2_Mereni — Statistické zpracování dat (Základy měření 2)

CLI nástroj pro statistické zpracování fyzikálních laboratorních měření. Počítá aritmetické průměry, chyby měření, propagaci chyb přes parciální derivace a generuje grafy a LaTeX tabulky.

## Instalace

```bash
git clone git@github.com:matyas095/ZM2_Mereni.git
cd ZM2_Mereni
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Použití

```bash
# Spustit konkrétní metodu
python3 main.py <metoda> [argumenty]

# Interaktivní režim (bez argumentů — program se zeptá)
python3 main.py

# Výpis dostupných metod
python3 main.py -h

# Nápověda ke konkrétní metodě
python3 main.py <metoda> -h
```

## Dostupné metody

### `aritmeticky_prumer`
Aritmetický průměr + střední kvadratická chyba aritmetického průměru.

```bash
python3 main.py aritmeticky_prumer -i cesta/k/souboru.txt
python3 main.py aritmeticky_prumer -i cesta/k/souboru.txt -lt  # + LaTeX tabulka
```

**Vstupní formát** (`txt`):
```
VELIČINA1=1.23,4.56,7.89
VELIČINA2=2.34,5.67,8.90
```

**Výstup:**
```
VELIČINA
├──Aritmetický průměr = ČÍSLO
└──Chyba aritmetického průměru = ČÍSLO
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-lt`, `--latextable` | Exportovat do LaTeX tabulky |

---

### `neprima_chyba`
Nepřímá chyba měření — propagace chyby přes symbolické parciální derivace (SymPy).

```bash
python3 main.py neprima_chyba -i cesta/k/souboru.txt
python3 main.py neprima_chyba -i data.xlsx -r "R=U/I"
python3 main.py neprima_chyba -i data.xlsx -r "R=U/I" -k '{"C": 0.000000047}'
```

**Vstupní formát** (`txt` — indentovaný blokový formát):
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

Podporuje také `.xlsx` soubory (pandas).

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-r`, `--rovnice` | Rovnice ve formátu `VELIČINA=VZTAH` |
| `-k`, `--konstanty` | Konstanty jako JSON dict |

---

### `graf`
2D a 3D grafy s volitelným fitem a rovnicí. Výstup jako SVG.

```bash
python3 main.py graf_BROKEN -i data.txt -n "Můj graf"
python3 main.py graf_BROKEN -i data.txt -n "Graf" -r "Z=t*U" 
python3 main.py graf_BROKEN -i data.txt -n "Graf" -r "Z=t*U" -p t
python3 main.py graf_BROKEN -i data.txt -n "Graf" -f linearni
python3 main.py graf_BROKEN -i data.txt -n "Graf" -log -f exponencialni
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-n`, `--name` | Název grafu (povinný) |
| `-r`, `--rovnice` | Závislost — rovnice pro 3D/2D graf |
| `-p`, `--parametr` | Parametr pro 2D graf funkce f(x) |
| `-log`, `--logaritmicky` | Logaritmické měřítko y-osy |
| `-f`, `--fit` | Typ fitu: `linearni`, `kvadraticky`, `exponencialni`, `mocninny` |

---

### `graf_interval`
Graf jedné funkce na zadaném intervalu. Výstup jako SVG.

```bash
python3 main.py graf_interval -n "Funkce" -r "y=x**2+2*x" -i 0 100
```

| Argument | Popis |
|----------|-------|
| `-n`, `--name` | Název grafu (povinný) |
| `-r`, `--rovnice` | Funkce ve formátu `VELIČINA=VZTAH` (povinný) |
| `-i`, `--interval` | Počátek a konec intervalu, např. `-i 0 100` (povinný) |

---

### `convert_soubor`
Konverze tabulkového souboru (TSV s hlavičkou a jednotkami) do formátu `PROMĚNNÁ=data`.

```bash
python3 main.py convert_soubor -i tabulka.txt
python3 main.py convert_soubor -i tabulka.txt -o muj_vystup
```

**Vstupní formát:**
```
Sloupec1    Sloupec2    Sloupec3
m           A           s
0.1         1.5         2.3
0.2         1.6         2.4
```

**Výstupní formát:**
```
m=0.1,0.2
A=1.5,1.6
s=2.3,2.4
```

| Argument | Popis |
|----------|-------|
| `-i`, `--input` | Cesta ke vstupnímu souboru (povinný) |
| `-o`, `--output` | Název výstupního souboru bez přípony (výchozí: `output_convertor`) |

## Architektura

Projekt používá **plugin architekturu s OOP**. Každá statistická metoda je třída dědící z abstraktní bázové třídy `Method`:

```
main.py                              # CLIApp — discovery, argparse, spuštění
statisticke_vypracovani/
    base.py                          # Method (ABC) — rozhraní pro všechny metody
    aritmeticky_prumer/logic.py      # class AritmetickyPrumer(Method)
    neprima_chyba/logic.py           # class NeprimaChyba(Method)
    graf/logic.py                    # class Graf(Method)
    graf_interval/logic.py           # class GrafInterval(Method)
    convert_soubor/logic.py          # class ConvertSoubor(Method)
objects/
    elements/Element.py              # Obal pro jednu měřenou hodnotu
    elements/List.py                 # Kolekce měření s výpočty
    readable/TextFileToArray.py      # Parser vstupních souborů
utils.py                             # Pomocné funkce (barvy, konverze, regex)
```

### Jak přidat novou metodu

1. Vytvořte složku `statisticke_vypracovani/<nazev_metody>/`
2. V `logic.py` vytvořte třídu dědící z `Method`:
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
3. V `__init__.py` importujte třídu:
   ```python
   from .logic import MojeMetoda;
   ```
4. Hotovo — `CLIApp` ji automaticky najde.

## Konvence kódu

- Středníky na konci příkazů (záměrná volba stylu)
- Komentáře a UI řetězce v češtině
- Každá metoda musí implementovat `run(self, args)` a `get_args_info(self)`

## Závislosti

- numpy, scipy, matplotlib, sympy, pandas, scikit-learn, requests, openpyxl

## Licence

[MIT](LICENSE)
