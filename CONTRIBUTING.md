# Jak přispět (Contributing)

Děkujeme za zájem o přispění do ZM2_Mereni!

## Pravidla pro přispívání

### 1. Fork & Branch

1. Forkněte tento repozitář.
2. Vytvořte novou větev z `main`:
   ```bash
   git checkout -b feature/moje-zmena
   ```
3. Proveďte změny a commitněte.
4. Pushněte větev do svého forku:
   ```bash
   git push origin feature/moje-zmena
   ```
5. Otevřete **Pull Request** proti `main` větvi tohoto repozitáře.

### 2. Pull Request proces

- Každý PR musí být schválen správcem repozitáře (@matyas095) před mergem.
- Přímý push do `main` je zakázán pro všechny kromě správce.
- PR by měl obsahovat jasný popis změn a důvod.
- Pokud PR řeší existující issue, odkažte na něj (`Fixes #123`).

### 3. Konvence kódu

- Kód používá **středníky na konci příkazů** (záměrná volba stylu).
- UI řetězce a komentáře jsou v **češtině**.
- Každá nová statistická metoda patří do `statisticke_vypracovani/<nazev_metody>/logic.py`.
- Modul musí exportovat `run(args)` a volitelně `get_args_info()`.

### 4. Kontrola syntaxe

Před odesláním PR ověřte, že kód projde:
```bash
python3 -m py_compile statisticke_vypracovani/*/logic.py utils.py main.py
```

### 5. Hlášení chyb (Issues)

- Použijte šablonu issue (pokud je k dispozici).
- Popište problém, kroky k reprodukci a očekávané chování.
- Přiložte verzi Pythonu a OS.

## Otázky?

Otevřete issue nebo napište na matyas.kutaj@gmail.com.
