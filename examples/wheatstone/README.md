# Příklad: Wheatstoneův můstek

Úloha ZM2 č. 8 (FJFI).

## 1 Zadání

Měřením neznámého odporu $R_x$ pomocí Wheatstoneova můstku. Vzorec:

```
R_x = R_2 · (R_1 / R_3)
```

## 2 Vstupní data

V `data/mereni.txt` jsou referenční odpory $R_1$, $R_2$, $R_3$ a jejich nejistoty.

## 3 Workflow

Viz `commands.sh`:

1. Aritmetický průměr jednotlivých odporů s chybou typu B z manuálu multimetru.
2. Propagace chyby přes `neprima_chyba` se vzorcem $R_x = R_2 \cdot R_1 / R_3$.
