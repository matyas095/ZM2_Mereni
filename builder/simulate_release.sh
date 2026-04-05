#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="${1:-v0.0-test}"
RELEASE_DIR="$SCRIPT_DIR/release_simulation"

cd "$PROJECT_DIR"

echo "========================================"
echo "  SIMULACE RELEASE $VERSION (Linux)"
echo "  Statistika + Grafy (nic online)"
echo "========================================"
echo ""

# Cleanup
rm -rf build dist *.spec "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# === 1. Syntax check ===
echo "=== [CI] Kontrola syntaxe ==="
.venv/bin/python3 -m py_compile main.py main_statistika.py main_grafy.py utils.py
for f in statisticke_vypracovani/*/logic.py; do .venv/bin/python3 -m py_compile "$f"; done
for f in objects/*.py; do .venv/bin/python3 -m py_compile "$f"; done
echo "Syntaxe OK"
echo ""

# === 2. Unit testy ===
echo "=== [CI] Unit testy ==="
.venv/bin/python3 -m unittest discover tests 2>&1 | tail -3
echo ""

UPX_FLAG=""
if command -v upx &>/dev/null; then
    UPX_FLAG="--upx-dir $(dirname $(which upx))"
fi

# === 3. Build Statistika ===
echo "=== [CI] Build Statistika ==="
.venv/bin/python3 -m PyInstaller --onedir --noconfirm --clean --strip \
    --name statistika_${VERSION}_linux \
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
    main_statistika.py 2>&1 | tail -3

if command -v upx &>/dev/null; then
    find dist/statistika_${VERSION}_linux -name "*.so*" | while read f; do
        upx -1 --quiet "$f" 2>/dev/null || true
    done
fi
find dist/ -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find dist/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

tar -czf "$RELEASE_DIR/statistika_${VERSION}_linux.tar.gz" -C dist .
STAT_SIZE=$(du -h "$RELEASE_DIR/statistika_${VERSION}_linux.tar.gz" | cut -f1)
echo "Statistika: $STAT_SIZE"
rm -rf build dist *.spec

echo ""

# === 4. Build Grafy ===
echo "=== [CI] Build Grafy ==="
.venv/bin/python3 -m PyInstaller --onedir --noconfirm --clean --strip \
    --name statistika_grafy_${VERSION}_linux \
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
    main_grafy.py 2>&1 | tail -3

if command -v upx &>/dev/null; then
    find dist/statistika_grafy_${VERSION}_linux -name "*.so*" | while read f; do
        upx -1 --quiet "$f" 2>/dev/null || true
    done
fi
find dist/ -name "*.dist-info" -type d -exec rm -rf {} + 2>/dev/null || true
find dist/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

tar -czf "$RELEASE_DIR/statistika_grafy_${VERSION}_linux.tar.gz" -C dist .
GRAF_SIZE=$(du -h "$RELEASE_DIR/statistika_grafy_${VERSION}_linux.tar.gz" | cut -f1)
echo "Grafy: $GRAF_SIZE"
rm -rf build dist *.spec

# === 5. Ověření ===
echo ""
echo "========================================"
echo "  VÝSLEDEK"
echo "========================================"
ls -lh "$RELEASE_DIR/"
echo ""
echo "Statistika tool: $STAT_SIZE"
echo "Grafy tool:      $GRAF_SIZE"
echo ""
echo "Vše lokální, nic online."
