#!/usr/bin/env bash
# Builds "File Organizer Agent Setup.exe" via Inno Setup. Must run on
# Windows, after build_windows_exe.sh. Day 2 work.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v iscc >/dev/null 2>&1; then
  echo "Inno Setup's iscc.exe not found on PATH. Install Inno Setup: https://jrsoftware.org/isinfo.php" >&2
  exit 1
fi

iscc packaging/windows/installer.iss
echo "Built installer - see packaging/windows/ for output location."
