# Příklad: Harmonické kmity

Úloha ZM2 č. 10 (FJFI).

## 1 Zadání

Studium tlumených harmonických kmitů. Ze záznamu polohy $x(t)$ určujeme úhlovou frekvenci a tlumící koeficient fitem.

## 2 Vstupní data

V `data/kmity.txt` je časový záznam polohy.

## 3 Workflow

Viz `commands.sh`:

1. Histogram rozdělení pro ověření.
2. Numerická derivace pro získání rychlosti.
3. Custom fit harmonickou funkcí s tlumením.
