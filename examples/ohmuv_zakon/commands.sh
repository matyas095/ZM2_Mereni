#!/bin/bash
# Příklad: Ohmův zákon — U-I charakteristika rezistoru
set -e
cd "$(dirname "$0")"
MAIN=../../main.py

echo "=== 1. Průměr a chyba naměřených hodnot ==="
python3 $MAIN ap -i data/mereni.txt

echo ""
echo "=== 2. Lineární regrese (odpor ze směrnice) ==="
python3 $MAIN regrese -i data/mereni.txt -x "U [V]" -y "I [mA]"

echo ""
echo "=== 3. Graf s fitem a chi-squared ==="
python3 $MAIN graf -i data/mereni.txt -n "ohm_fit" -f linearni --chi2

echo ""
echo "=== 4. LaTeX tabulka s statistikami v captionu ==="
python3 $MAIN ap -i data/mereni.txt -lt \
    --caption "Voltampérová charakteristika rezistoru" \
    --label "tab_ohm"

echo ""
echo "Hotovo. Výstupy v latex_output/, grafy_metoda_graf/"
