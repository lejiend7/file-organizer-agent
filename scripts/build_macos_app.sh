#!/usr/bin/env bash
# Builds File Organizer Agent.app via PyInstaller. Must run on macOS.
#
# Optional signing (never hardcoded, never committed):
#   APPLE_SIGNING_IDENTITY - codesign identity string
#   APPLE_TEAM_ID          - for notarization
#   APPLE_NOTARIZE         - set to "1" to notarize after signing
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ "$(uname)" != "Darwin" ]; then
  echo "This script must run on macOS (per docs/PRODUCT_SPEC.md packaging rules)." >&2
  exit 1
fi

if [ -d .venv ]; then source .venv/bin/activate; fi

pyinstaller \
  --name "File Organizer Agent" \
  --windowed \
  --add-data "organizer/ui/web:organizer/ui/web" \
  --paths . \
  organizer/ui/app.py

if [ -n "${APPLE_SIGNING_IDENTITY:-}" ]; then
  codesign --deep --force --options runtime --sign "$APPLE_SIGNING_IDENTITY" \
    "dist/File Organizer Agent.app"
fi

if [ "${APPLE_NOTARIZE:-0}" = "1" ]; then
  echo "Notarization requires an Apple Developer account configured via 'xcrun notarytool' credentials." >&2
  echo "Not run automatically - see Apple's notarytool docs and set up credentials first." >&2
fi

echo "Built: dist/File Organizer Agent.app"
