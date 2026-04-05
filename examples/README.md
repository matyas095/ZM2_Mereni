# Příklady použití

V této složce jsou reálné příklady workflow pro konkrétní úlohy ZM2 FJFI.

## 1 Struktura

```
examples/
├── termistor/          # Úloha #9 — závislost odporu termistoru na teplotě
│   ├── README.md       # Popis úlohy
│   ├── data/           # Vstupní data (CASSY export)
│   └── commands.sh     # Workflow — posloupnost příkazů
└── ...
```

## 2 Použití

Každý příklad obsahuje `commands.sh` s posloupností příkazů vedoucí ke kompletnímu zpracování dané úlohy. Stačí vstoupit do adresáře a skript spustit:

```bash
cd examples/termistor
bash commands.sh
```

Výstupy se ukládají do podsložek `latex_output/`, `outputs/` a `grafy_metoda_graf/`.
