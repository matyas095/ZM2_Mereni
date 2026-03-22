#!/bin/bash

EXE_NAME="statistika"
ICON_NAME="app_icon.ico"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -n "$1" ]; then
    VERSION="$1"
else
    LAST_VER=$(ls "$SCRIPT_DIR/release" 2>/dev/null | grep -oP 'v\d+\.\d+' | sort -V | tail -1)
    DEFAULT_VER=${LAST_VER:-"v0.1"}
    echo -n "🚀 Enter Build Version [Default $DEFAULT_VER]: "
    read USER_VER
    VERSION=${USER_VER:-$DEFAULT_VER}
fi

if [ "$EUID" -ne 0 ]; then
    # We pass $VERSION as an argument to the sudo call so it doesn't ask again
    sudo "$0" "$VERSION"
    exit $?
fi
# [ -n "$1" ] && VERSION="$1"

PFX_PATH="$PROJECT_ROOT/security/matyas095Gameing_PRIVATE.pfx"
CRT_PATH="$PROJECT_ROOT/security/matyas095Gameing_public.crt"
ICON_PATH="$SCRIPT_DIR/$ICON_NAME"

if [ -f "$PFX_PATH" ]; then
    echo -n "!!Enter PFX Password!!: "
    read -s PFX_PASS; echo ""
fi

if [ -f "$CRT_PATH" ]; then
    echo "Ensuring local trust for $VERSION..."
    cp "$CRT_PATH" /usr/local/share/ca-certificates/matyas095_build.crt
    update-ca-certificates --fresh > /dev/null
fi

mkdir -p "$SCRIPT_DIR/dist" "$SCRIPT_DIR/build" "$SCRIPT_DIR/release"

echo "--- 🐧 Building Linux Binary ($VERSION) ---"
"$PROJECT_ROOT/.venv/bin/python" -m PyInstaller --onefile --noconfirm \
--workpath "$SCRIPT_DIR/build" --distpath "$SCRIPT_DIR/dist" \
--name "${EXE_NAME}_${VERSION}_linux" \
--add-data "$PROJECT_ROOT/statisticke_vypracovani:statisticke_vypracovani" \
--hidden-import "numpy" "$PROJECT_ROOT/main.py"

echo "--- Building Windows EXE ($VERSION) ---"
if [ -f "$ICON_PATH" ]; then 
    cp "$ICON_PATH" "$PROJECT_ROOT/app_icon.ico"
    ICON_STR="--icon app_icon.ico"
fi

docker run --rm -v "$PROJECT_ROOT:/src" cdrx/pyinstaller-windows \
"pip install numpy requests && pyinstaller --onefile $ICON_STR --name ${EXE_NAME} --add-data 'statisticke_vypracovani;statisticke_vypracovani' main.py"

mv "$PROJECT_ROOT/dist/${EXE_NAME}.exe" "$SCRIPT_DIR/dist/" 2>/dev/null

if [ -f "$SCRIPT_DIR/dist/${EXE_NAME}.exe" ]; then
    echo "--- Signing & Verifying ---"
    SIGNED_EXE="$SCRIPT_DIR/dist/${EXE_NAME}_${VERSION}_signed.exe"
    osslsigncode sign -pkcs12 "$PFX_PATH" -pass "$PFX_PASS" \
    -n "Statistika Tool $VERSION" -t http://timestamp.digicert.com \
    -in "$SCRIPT_DIR/dist/${EXE_NAME}.exe" -out "$SIGNED_EXE"
    rm "$SCRIPT_DIR/dist/${EXE_NAME}.exe"
fi

echo "--- Creating Final Packages ---"
cp "$CRT_PATH" "$SCRIPT_DIR/dist/"
cat <<EOF > "$SCRIPT_DIR/dist/install_trust_windows.bat"
@echo off
net session >nul 2>&1 || (echo ❌ Please run as Administrator! & pause & exit)
certutil -addstore -f "Root" "$(basename "$CRT_PATH")"
echo ✅ Certificate installed.
pause
EOF

cat <<EOF > "$SCRIPT_DIR/dist/install_trust_linux.sh"
#!/bin/bash
if [ "\$EUID" -ne 0 ]; then
  echo "❌ Please run with sudo: sudo ./install_trust_linux.sh"
  exit 1
fi
# Copy to local share and update system store
cp "\$(ls *.crt | head -n 1)" /usr/local/share/ca-certificates/
update-ca-certificates
echo "✅ Trust installed successfully!"
EOF
chmod +x "$SCRIPT_DIR/dist/install_trust_linux.sh"

zip -j "$SCRIPT_DIR/release/${EXE_NAME}_${VERSION}_windows.zip" "$SCRIPT_DIR/dist/"*signed.exe "$SCRIPT_DIR/dist/"*.crt "$SCRIPT_DIR/dist/"*.bat
tar -czf "$SCRIPT_DIR/release/${EXE_NAME}_${VERSION}_linux.tar.gz" -C "$SCRIPT_DIR/dist" \
    "${EXE_NAME}_${VERSION}_linux" \
    "$(basename "$CRT_PATH")" \
    "install_trust_linux.sh"

echo "--- Final Cleanup ---"
rm -f "$PROJECT_ROOT/app_icon.ico"
rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist" "$PROJECT_ROOT"/*.spec
rm -rf "$SCRIPT_DIR/build" "$SCRIPT_DIR/dist" "$SCRIPT_DIR"/*.spec

if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER":"$SUDO_USER" "$SCRIPT_DIR"
fi
echo "Done! Release $VERSION is ready in builder/release/"