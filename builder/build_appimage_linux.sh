#!/bin/bash
# Vytvoří AppImage z PyInstaller --onedir výstupu.
# Předpoklady:
#   1) builder/compiled/statistika/ existuje (běžel build_statistika_linux.sh)
#   2) appimagetool je v PATH (https://github.com/AppImage/AppImageKit/releases)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SRC="$SCRIPT_DIR/compiled/statistika"
APPDIR="$PROJECT_DIR/build/Statistika.AppDir"

if [ ! -d "$SRC" ]; then
    echo "Chybí $SRC — spusť nejprve builder/build_statistika_linux.sh"
    exit 1
fi

if ! command -v appimagetool &>/dev/null; then
    echo "appimagetool nenalezen v PATH."
    echo "Stáhni z: https://github.com/AppImage/AppImageKit/releases"
    echo "  wget -O ~/.local/bin/appimagetool https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "  chmod +x ~/.local/bin/appimagetool"
    exit 1
fi

echo "=== Příprava AppDir ==="
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp -a "$SRC"/* "$APPDIR/usr/bin/"

# AppRun (entry point)
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/statistika" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Desktop file
cat > "$APPDIR/statistika.desktop" <<'EOF'
[Desktop Entry]
Name=Statistika ZM2
Comment=Statistické zpracování dat (Základy měření 2)
Exec=statistika
Icon=statistika
Type=Application
Terminal=true
Categories=Science;Education;
EOF

# Ikona (PyInstaller už má app_icon.ico — převedeme nebo použijeme placeholder)
if command -v convert &>/dev/null && [ -f "$SCRIPT_DIR/app_icon.ico" ]; then
    convert "$SCRIPT_DIR/app_icon.ico[0]" "$APPDIR/statistika.png"
else
    # 1×1 placeholder (validní PNG)
    printf '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xcf\xc0\x00\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82' > "$APPDIR/statistika.png"
fi

echo "=== Build AppImage ==="
mkdir -p "$SCRIPT_DIR/compiled"
ARCH=x86_64 appimagetool "$APPDIR" "$SCRIPT_DIR/compiled/Statistika-x86_64.AppImage" 2>&1 | tail -5

if [ -f "$SCRIPT_DIR/compiled/Statistika-x86_64.AppImage" ]; then
    SIZE=$(du -h "$SCRIPT_DIR/compiled/Statistika-x86_64.AppImage" | cut -f1)
    echo "=== Hotovo: $SIZE ==="
    echo "Test: ./builder/compiled/Statistika-x86_64.AppImage --help"
else
    echo "Build selhal."
    exit 1
fi
