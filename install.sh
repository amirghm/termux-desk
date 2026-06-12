#!/usr/bin/env bash
set -euo pipefail

echo "=== TermuxDesk Installer ==="
echo ""

# Detect environment
if command -v pkg >/dev/null 2>&1 && [[ -n "${TERMUX_VERSION:-}" ]]; then
    echo "[Termux detected]"
    pkg update -y
    pkg install -y python clang make pkg-config libjpeg-turbo libpng curl
    python -m pip install --upgrade pip --break-system-packages 2>/dev/null || python -m pip install --upgrade pip
    python -m pip install termux-desk --break-system-packages 2>/dev/null || python -m pip install termux-desk
elif command -v apt >/dev/null 2>&1; then
    echo "[Debian/Ubuntu PRoot detected]"
    if python3 -m venv ~/venv --clear 2>/dev/null; then
        echo "Using virtual environment..."
        source ~/venv/bin/activate
        pip install termux-desk
        echo ""
        echo "To run TermuxDesk, first activate the venv:"
        echo "  source ~/venv/bin/activate"
        echo "  termux-desk start --tunnel"
    else
        echo "venv not available, installing system-wide..."
        pip install termux-desk --break-system-packages
    fi
else
    echo "[Generic Linux]"
    pip install termux-desk --break-system-packages 2>/dev/null || pip install termux-desk
fi

echo ""
echo "=== Done! ==="
echo ""
echo "Start your X11 desktop, then run:"
echo "  export DISPLAY=:0"
echo "  termux-desk start --tunnel"
echo ""
