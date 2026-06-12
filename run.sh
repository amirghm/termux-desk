#!/usr/bin/env bash
# TermuxDesk — one-line installer & runner
# Works on: Termux, PRoot Ubuntu/Debian/Arch, any Linux
set -euo pipefail

echo "╔══════════════════════════════════╗"
echo "║        TermuxDesk Installer      ║"
echo "╚══════════════════════════════════╝"
echo ""

# Step 1: Install termux-desk
echo "📦 Installing termux-desk..."
if pip install termux-desk --break-system-packages -q 2>/dev/null; then
    echo "   ✅ Installed via pip (--break-system-packages)"
elif pip install termux-desk -q 2>/dev/null; then
    echo "   ✅ Installed via pip"
elif python3 -m pip install termux-desk --break-system-packages -q 2>/dev/null; then
    echo "   ✅ Installed via python3 -m pip"
else
    echo "   ❌ pip install failed. Try manually:"
    echo "      pkg install python && pip install termux-desk"
    exit 1
fi

# Step 2: Find the binary
TERMUX_DESK_BIN="$(which termux-desk 2>/dev/null || true)"
if [ -z "$TERMUX_DESK_BIN" ]; then
    echo "   ⚠️  termux-desk not in PATH, using python module directly"
    TERMUX_DESK_BIN="python3 -m termux_desk.cli"
fi

# Step 3: Ensure cloudflared is available
if ! command -v cloudflared >/dev/null 2>&1; then
    echo "📥 Downloading cloudflared..."
    ARCH="$(uname -m)"
    case "$ARCH" in
        aarch64) CF_ARCH="arm64" ;;
        armv7l)  CF_ARCH="arm" ;;
        x86_64)  CF_ARCH="amd64" ;;
        i686)    CF_ARCH="386" ;;
        *)       CF_ARCH="$ARCH" ;;
    esac
    mkdir -p ~/.local/bin
    curl -fsSL -o ~/.local/bin/cloudflared \
        "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}"
    chmod +x ~/.local/bin/cloudflared
    export PATH="$HOME/.local/bin:$PATH"
    echo "   ✅ cloudflared downloaded"
fi

# Step 4: Set display
export DISPLAY="${DISPLAY:-:0}"

# Step 5: Run
echo ""
echo "🚀 Starting TermuxDesk..."
echo "   Display: $DISPLAY"
echo "   URL will appear below (Ctrl+C to stop)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

exec $TERMUX_DESK_BIN start --tunnel
