#!/usr/bin/env bash
set -euo pipefail
echo "📦 Installing TermuxDesk..."
pip install termux-desk --break-system-packages -q 2>/dev/null || pip install termux-desk -q
echo "🚀 Starting TermuxDesk..."
export DISPLAY="${DISPLAY:-:0}"
exec "$(which termux-desk)" start --tunnel
