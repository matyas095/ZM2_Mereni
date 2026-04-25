#!/bin/bash
# Příklad workflow: Závislost odporu termistoru na teplotě (ZM2, úloha #9)
set -e

cd "$(dirname "$0")"

# Cesta k main.py (relativně k tomuto skriptu)
MAIN=../../main.py

echo "=== 1. Načtení dat a výpočet statistik ==="
python3 $MAIN aritmeticky_prumer -i data/cassy.txt --verbose

echo ""
echo "=== 2. LaTeX tabulka s auto-statistikami v captionu ==="
python3 $MAIN aritmeticky_prumer -i data/cassy.txt -lt \
    --caption "Naměřené hodnoty závislosti odporu termistoru na teplotě" \
    --label "tab_termistor_data"

echo ""
echo "=== 3. Export do CSV pro další zpracování ==="
python3 $MAIN aritmeticky_prumer -i data/cassy.txt \
    --export-csv vysledky.csv -q

echo ""
echo "=== 4. Převod LaTeX tabulky na SI s přidáním statistik ==="
python3 $MAIN format_table \
    -i latex_output/table_t_T_URT_URN.tex \
    --append-stats \
    -o final_termistor

echo ""
echo "Hotovo. Výstupy:"
echo "  - latex_output/  (LaTeX tabulky)"
echo "  - outputs/       (CSV, extrahovaná data, finální tabulka)"
echo "  - vysledky.csv"
