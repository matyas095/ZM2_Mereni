# Příklady použití

V této složce jsou reálné příklady workflow nástroje ZM2_Mereni pro jednotlivé úlohy ZM2.

## Struktura příkladů

```
examples/
├── termistor/          # Protokol #9 — závislost odporu termistoru na teplotě
│   ├── README.md       # Popis úlohy
│   ├── data/           # Vstupní data (CASSY export)
│   └── commands.sh     # Kompletní workflow
└── ...
```

## Jak používat

Každý příklad obsahuje `commands.sh` s posloupností příkazů, které vedou ke kompletnímu zpracování dané úlohy. Stačí vstoupit do adresáře a skript spustit:

```bash
cd examples/termistor
bash commands.sh
```

Výstupy se uloží do podsložek `latex_output/`, `outputs/`, `grafy_metoda_graf/`.
