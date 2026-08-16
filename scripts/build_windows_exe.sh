#!/usr/bin/env bash
# Builds File Organizer Agent.exe via PyInstaller. Must run on Windows
# (e.g. in Git Bash / WSL invoking the Windows Python, or a plain .bat
# equivalent - PyInstaller does not support cross-compiling from macOS/Linux
# to Windows). Day 2 work - see docs/IMPLEMENTATION_PLAN.md.
set -euo pipefail
cd "$(dirname "$0")/../.."

case "$(uname -s 2>/dev/null || echo unknown)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *)
    echo "This script must run on Windows (per docs/PRODUCT_SPEC.md packaging rules)." >&2
    exit 1
    ;;
esac

if [ -d .venv ]; then source .venv/Scripts/activate; fi

pyinstaller \
  --name "File Organizer Agent" \
  --windowed \
  --add-data "organizer/ui/web;organizer/ui/web" \
  --paths . \
  organizer/ui/app.py

echo "Built: dist/File Organizer Agent/File Organizer Agent.exe"
