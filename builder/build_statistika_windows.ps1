$ErrorActionPreference = "Stop"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_DIR = Split-Path -Parent $SCRIPT_DIR
Set-Location $PROJECT_DIR

Write-Host "=== BUILD: Statistika (Windows) ===" -ForegroundColor Cyan
Write-Host "Metody: aritmeticky_prumer, neprima_chyba, convert_soubor, vazeny_prumer, join_tables, derivace, format_table, extract_table"

python -m py_compile main.py
python -m py_compile main_statistika.py
python -m py_compile utils.py

python -m PyInstaller --onedir --noconfirm --clean --strip `
    --name statistika --icon builder/app_icon.ico `
    --add-data "statisticke_vypracovani;statisticke_vypracovani" `
    --add-data "objects;objects" `
    --add-data "utils.py;." `
    --add-data "main.py;." `
    --exclude-module IPython --exclude-module notebook `
    --exclude-module test --exclude-module tests `
    --exclude-module sklearn --exclude-module scikit-learn `
    --exclude-module pyarrow `
    --exclude-module matplotlib --exclude-module mpl_toolkits `
    --exclude-module PIL --exclude-module Pillow --exclude-module pillow `
    --exclude-module tkinter --exclude-module _tkinter `
    --exclude-module pandas --exclude-module openpyxl `
    --exclude-module fontTools --exclude-module contourpy --exclude-module kiwisolver `
    --exclude-module scipy.tests --exclude-module sympy.testing --exclude-module sympy.benchmarks `
    --collect-submodules sympy `
    --collect-submodules scipy `
    --hidden-import sympy.parsing.latex `
    --hidden-import sympy.parsing.sympy_parser `
    --hidden-import scipy.optimize `
    --hidden-import scipy.stats `
    --hidden-import scipy.linalg `
    --hidden-import statisticke_vypracovani.base `
    --hidden-import objects.measurement `
    --hidden-import objects.measurement_set `
    --hidden-import objects.input_parser `
    --hidden-import objects.config `
    --hidden-import objects.units `
    --hidden-import objects.logger `
    main_statistika.py

Get-ChildItem -Path "dist/statistika/_internal" -Filter "*.dist-info" -Directory -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "dist/statistika/_internal" -Filter "__pycache__" -Directory -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

$compiledDir = Join-Path $SCRIPT_DIR "compiled"
New-Item -ItemType Directory -Force -Path $compiledDir | Out-Null
$zipPath = Join-Path $compiledDir "statistika_windows.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath }
Compress-Archive -Path "dist/statistika" -DestinationPath $zipPath
Remove-Item -Recurse -Force build, dist, statistika.spec -ErrorAction SilentlyContinue

$zipSize = "{0:N0} MB" -f ((Get-Item $zipPath).Length / 1MB)
Write-Host "=== Hotovo: $zipSize ===" -ForegroundColor Green
Write-Host "Test: .\builder\compiled\statistika\statistika.exe -h"
