#!/bin/bash
# Příklad: Harmonické kmity — fit s tlumením
set -e
cd "$(dirname "$0")"
MAIN=../../main.py

echo "=== 1. Statistiky ==="
python3 $MAIN ap -i data/kmity.txt

echo ""
echo "=== 2. Numerická derivace (rychlost z polohy) ==="
python3 $MAIN der -i data/kmity.txt -x "t [s]" -y "x [m]" -o rychlost

echo ""
echo "=== 3. Custom fit — tlumený harmonický oscilátor ==="
python3 $MAIN graf -i data/kmity.txt -n "kmity_fit" \
    --custom-fit "a*exp(-b*x)*sin(c*x+d)"

echo ""
echo "Hotovo."
