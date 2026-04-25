# Jak přispět

Děkuji za zájem o přispění do ZM2_Mereni.

## 1 Pravidla

### 1.1 Fork a větev

1. Forkni repozitář.
2. Vytvoř novou větev z `main`:
   ```bash
   git checkout -b feature/moje-zmena
   ```
3. Proveď změny a commitni.
4. Pushni větev do svého forku:
   ```bash
   git push origin feature/moje-zmena
   ```
5. Otevři **Pull Request** proti `main`.

### 1.2 Pull Request

- Každý PR vyžaduje schválení správcem repozitáře (@matyas095) před mergem.
- Přímý push do `main` je zakázán pro všechny kromě správce.
- PR má obsahovat jasný popis změn a důvodu.
- Pokud PR řeší existující issue, odkaž na ni (`Fixes #123`).
- CI workflow spouští syntax check a všechny testy — PR neprojde pokud testy neprojdou.

## 2 Konvence kódu

- Středníky na konci příkazů (záměrná stylová volba).
- Komentáře a UI řetězce v češtině.
- Každá nová metoda patří do `statisticke_vypracovani/<nazev_metody>/logic.py`.
- Každá metoda musí být třídou dědící z `Method` a implementovat `run(self, args)` a `get_args_info(self)`.

## 3 Kontrola před odesláním PR

```bash
# Syntax check
python3 -m py_compile main.py main_statistika.py main_grafy.py utils.py
for f in statisticke_vypracovani/*/logic.py; do python3 -m py_compile "$f"; done
for f in objects/*.py zm2/*.py; do python3 -m py_compile "$f"; done

# Testy
python3 -m unittest discover tests
```

### 3.1 Pre-commit hooky

Pro automatické spouštění kontrol před každým commitem:

```bash
pip install pre-commit
pre-commit install
```

Od teď se před `git commit` spustí syntax check a testy; commit neprojde při chybě.

## 4 Přidání metody

1. Vytvoř složku `statisticke_vypracovani/<nazev>/`.
2. V `logic.py` definuj třídu dědící z `Method`:

   ```python
   from statisticke_vypracovani.base import Method

   class MojeMetoda(Method):
       name = "nazev"
       description = "Popis"

       def get_args_info(self) -> list:
           return [{"flags": ["-i"], ...}]

       def validate(self, args) -> None:
           # chytej chyby předem
           pass

       def run(self, args, do_print: bool = True) -> dict:
           # hlavní logika
           return {}
   ```

3. V `__init__.py` importuj třídu: `from .logic import MojeMetoda`.
4. Napiš testy do `tests/test_<nazev>.py`.
5. Pokud má být v binárce, přidej název do `main_statistika.py` nebo `main_grafy.py`.
6. Přidej wrapper do `zm2/__init__.py` pro programatické volání.
7. Přidej alias do `_METHOD_ALIASES` v `main.py`.

## 5 Hlášení chyb

- Použij šablonu issue (bug_report / feature_request).
- Popiš problém, kroky k reprodukci a očekávané chování.
- Přilož verzi Pythonu, OS a konkrétní příkaz.

## 6 Kontakt

Otevři issue nebo napiš na matyas.kutaj@gmail.com.
