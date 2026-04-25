# Příklad: Závislost odporu termistoru na teplotě

Úloha ZM2 č. 9 (FJFI).

## 1 Zadání

Měříme závislost odporu termistoru na teplotě v rozsahu 20–60 °C. Z naměřených dat extrapolujeme hodnotu odporu při 0 °C a počítáme konstanty B a R∞ ze vztahu:

```
R(T) = R∞ · exp(B/T)
```

## 2 Vstupní data

V adresáři `data/` je CASSY export, který obsahuje:

- `t [s]` — čas měření,
- `T [K]` — teplota termistoru,
- `URT [V]` — napětí na termistoru,
- `URN [V]` — napětí na kalibračním rezistoru.

## 3 Workflow

Kompletní posloupnost příkazů je v souboru `commands.sh`. Postup:

1. Načtení dat z CASSY exportu a výpočet statistik.
2. Export do LaTeX tabulky pro protokol (s auto-statistikami v captionu).
3. Export výsledků do CSV pro další zpracování.
4. Úprava LaTeX tabulky — doplnění průměrů a chyb do captionu.
