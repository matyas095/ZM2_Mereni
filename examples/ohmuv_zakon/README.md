# Příklad: Ohmův zákon (U–I charakteristika)

Úloha ZM2 č. 7 (FJFI).

## 1 Zadání

Měříme voltampérovou charakteristiku rezistoru, z lineárního fitu získáme jeho odpor. Ze směrnice přímky dopočítáme odpor $R$ včetně nejistoty.

## 2 Vstupní data

V souboru `data/mereni.txt` jsou hodnoty:

- `U [V]` — napětí na rezistoru,
- `I [mA]` — proud rezistorem.

## 3 Workflow

Kompletní posloupnost příkazů je v `commands.sh`:

1. Načtení dat a výpis statistik.
2. Lineární regrese se získáním směrnice a průsečíku.
3. Graf s fitem, chi-squared a panelem reziduí.
4. Export LaTeX tabulky pro protokol.
