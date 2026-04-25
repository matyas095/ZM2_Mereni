#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== BUILD: Statistika (Linux) ==="
echo "Metody: aritmeticky_prumer, neprima_chyba, convert_soubor, vazeny_prumer,"
echo "        join_tables, derivace, format_table, extract_table"
echo ""

echo "=== Kontrola syntaxe ==="
python3 -m py_compile main.py main_statistika.py utils.py
for f in statisticke_vypracovani/*/logic.py; do python3 -m py_compile "$f"; done
echo "OK"

UPX_FLAG=""
if command -v upx &>/dev/null; then UPX_FLAG="--upx-dir $(dirname $(which upx))"; fi

echo ""
echo "=== PyInstaller ==="
python3 -m PyInstaller --onedir --noconfirm --clean --strip \
    --name statistika \
    $UPX_FLAG \
    --add-data 'statisticke_vypracovani:statisticke_vypracovani' \
    --add-data 'objects:objects' \
    --add-data 'utils.py:.' \
    --add-data 'main.py:.' \
    --exclude-module IPython --exclude-module notebook \
    --exclude-module test --exclude-module tests \
    --exclude-module sklearn --exclude-module scikit-learn \
    --exclude-module pyarrow \
    --exclude-module matplotlib --exclude-module mpl_toolkits \
    --exclude-module PIL --exclude-module Pillow --exclude-module pillow \
    --exclude-module tkinter --exclude-module _tkinter \
    --exclude-module pandas --exclude-module openpyxl \
    --exclude-module fontTools --exclude-module contourpy --exclude-module kiwisolver \
    --exclude-module scipy.tests --exclude-module sympy.testing --exclude-module sympy.benchmarks \
    --collect-submodules sympy \
    --collect-submodules scipy \
    --hidden-import sympy.parsing.latex \
    --hidden-import sympy.parsing.sympy_parser \
    --hidden-import scipy.optimize \
    --hidden-import scipy.stats \
    --hidden-import scipy.linalg \
    --hidden-import statisticke_vypracovani.base \
    --hidden-import objects.measurement \
    --hidden-import objects.measurement_set \
    --hidden-import objects.input_parser \
    --hidden-import objects.config \
    --hidden-import objects.units \
    --hidden-import objects.logger \
    main_statistika.py

# Cleanup
find dist/ -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find dist/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf dist/statistika/_internal/matplotlib 2>/dev/null || true
rm -rf dist/statistika/_internal/PIL 2>/dev/null || true
rm -rf dist/statistika/_internal/pillow* 2>/dev/null || true
rm -rf dist/statistika/_internal/pandas 2>/dev/null || true
rm -rf dist/statistika/_internal/_tcl_data 2>/dev/null || true
rm -rf dist/statistika/_internal/_tk_data 2>/dev/null || true
rm -f dist/statistika/_internal/libBLT* dist/statistika/_internal/libtk* dist/statistika/_internal/libtcl* 2>/dev/null || true
rm -f dist/statistika/_internal/lib*jpeg* dist/statistika/_internal/lib*png16* dist/statistika/_internal/lib*tiff* 2>/dev/null || true
rm -f dist/statistika/_internal/lib*webp* dist/statistika/_internal/lib*avif* dist/statistika/_internal/lib*openjp* 2>/dev/null || true

# UPX
if command -v upx &>/dev/null; then
    echo ""
    echo "=== UPX ==="
    find dist/statistika -name "*.so" -o -name "*.so.*" | while read f; do upx -1 --quiet "$f" 2>/dev/null || true; done
    echo "OK"
fi

# Balení
echo ""
echo "=== Balení ==="
mkdir -p "$SCRIPT_DIR/compiled"
tar -czf "$SCRIPT_DIR/compiled/statistika_linux.tar.gz" -C dist statistika
rm -rf "$SCRIPT_DIR/compiled/statistika"
mv dist/statistika "$SCRIPT_DIR/compiled/statistika"
rm -rf build dist *.spec

TAR_SIZE=$(du -h "$SCRIPT_DIR/compiled/statistika_linux.tar.gz" | cut -f1)
echo "=== Hotovo: $TAR_SIZE ==="
echo "Test: ./builder/compiled/statistika/statistika -h"
