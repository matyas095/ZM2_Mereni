#!/bin/bash
# Příklad: Wheatstoneův můstek — nepřímé měření odporu
set -e
cd "$(dirname "$0")"
MAIN=../../main.py

echo "=== 1. Výpočet nepřímé chyby pomocí parciálních derivací ==="
python3 $MAIN nc -i data/mereni.txt

echo ""
echo "=== 2. Výpočet nepřímé chyby s nejistotou typu B ==="
python3 $MAIN nc -i data/mereni.txt --typ-b '{"R_1": 0.5, "R_2": 0.5, "R_3": 0.5}'

echo ""
echo "Hotovo."
