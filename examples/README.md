# Příklady použití

V této složce jsou reálné příklady workflow pro konkrétní úlohy ZM2 FJFI.

## 1 Struktura

```
examples/
├── termistor/          # Úloha #9 — závislost odporu termistoru na teplotě
├── ohmuv_zakon/        # Úloha #7 — U-I charakteristika rezistoru
├── wheatstone/         # Úloha #8 — Wheatstoneův můstek
├── kmity/              # Úloha #10 — harmonické kmity
└── ...
```

Každý adresář obsahuje:

- `README.md` — popis úlohy a workflow,
- `data/` — vstupní data,
- `commands.sh` — posloupnost příkazů pro kompletní zpracování.

## 2 Použití

Každý příklad obsahuje `commands.sh` s posloupností příkazů vedoucí ke kompletnímu zpracování dané úlohy. Stačí vstoupit do adresáře a skript spustit:

```bash
cd examples/termistor
bash commands.sh
```

Výstupy se ukládají do podsložek `latex_output/`, `outputs/` a `grafy_metoda_graf/`.
