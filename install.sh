#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if [[ -z "${TERMUX_VERSION:-}" ]]; then
  printf '%s\n' "This installer must be run in Termux (not inside a PRoot shell)." >&2
  exit 1
fi

pkg update -y
pkg install -y python clang make pkg-config libjpeg-turbo libpng cloudflared
python -m pip install --upgrade pip
python -m pip install termux-desk

printf '\nInstalled TermuxDesk. Start an X11 desktop, set DISPLAY, then run:\n'
printf '  termux-desk start\n'
