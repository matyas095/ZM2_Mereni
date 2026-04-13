#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== BUILD: Grafy (Linux) ==="
echo "Metody: graf, graf_interval, histogram"
echo ""

echo "=== Kontrola syntaxe ==="
python3 -m py_compile main.py main_grafy.py utils.py
for f in statisticke_vypracovani/*/logic.py; do python3 -m py_compile "$f"; done
echo "OK"

UPX_FLAG=""
if command -v upx &>/dev/null; then UPX_FLAG="--upx-dir $(dirname $(which upx))"; fi

echo ""
echo "=== PyInstaller ==="
python3 -m PyInstaller --onedir --noconfirm --clean --strip \
    --name statistika_grafy \
    $UPX_FLAG \
    --add-data 'statisticke_vypracovani:statisticke_vypracovani' \
    --add-data 'objects:objects' \
    --add-data 'utils.py:.' \
    --add-data 'main.py:.' \
    --exclude-module IPython --exclude-module notebook \
    --exclude-module test --exclude-module tests \
    --exclude-module sklearn --exclude-module scikit-learn \
    --exclude-module pyarrow \
    --exclude-module pandas --exclude-module openpyxl \
    --exclude-module matplotlib.tests --exclude-module scipy.tests \
    --exclude-module sympy.testing --exclude-module sympy.benchmarks \
    --collect-submodules sympy \
    --collect-submodules scipy \
    --collect-submodules matplotlib \
    --hidden-import sympy.parsing.latex \
    --hidden-import sympy.parsing.sympy_parser \
    --hidden-import scipy.optimize \
    --hidden-import scipy.stats \
    --hidden-import scipy.linalg \
    --hidden-import matplotlib \
    --hidden-import matplotlib.pyplot \
    --hidden-import matplotlib.backends.backend_agg \
    --hidden-import matplotlib.backends.backend_tkagg \
    --hidden-import PIL._tkinter_finder \
    --hidden-import tkinter \
    --hidden-import statisticke_vypracovani.base \
    --hidden-import objects.measurement \
    --hidden-import objects.measurement_set \
    --hidden-import objects.input_parser \
    --hidden-import objects.config \
    --hidden-import objects.units \
    --hidden-import objects.logger \
    main_grafy.py

# Cleanup
find dist/ -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find dist/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf dist/statistika_grafy/_internal/pandas 2>/dev/null || true

# UPX
if command -v upx &>/dev/null; then
    echo ""
    echo "=== UPX ==="
    find dist/statistika_grafy -name "*.so" -o -name "*.so.*" | while read f; do upx -1 --quiet "$f" 2>/dev/null || true; done
    echo "OK"
fi

# Balení
echo ""
echo "=== Balení ==="
mkdir -p "$SCRIPT_DIR/compiled"
tar -czf "$SCRIPT_DIR/compiled/statistika_grafy_linux.tar.gz" -C dist statistika_grafy
rm -rf "$SCRIPT_DIR/compiled/statistika_grafy"
mv dist/statistika_grafy "$SCRIPT_DIR/compiled/statistika_grafy"
rm -rf build dist *.spec

TAR_SIZE=$(du -h "$SCRIPT_DIR/compiled/statistika_grafy_linux.tar.gz" | cut -f1)
echo "=== Hotovo: $TAR_SIZE ==="
echo "Test: ./builder/compiled/statistika_grafy/statistika_grafy -h"
