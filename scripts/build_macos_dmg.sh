#!/usr/bin/env bash
# Packages File Organizer Agent.app into a .dmg. Must run on macOS, after
# build_macos_app.sh.
set -euo pipefail
cd "$(dirname "$0")/../.."

if [ "$(uname)" != "Darwin" ]; then
  echo "This script must run on macOS." >&2
  exit 1
fi

APP="dist/File Organizer Agent.app"
if [ ! -d "$APP" ]; then
  echo "Build the .app first: ./scripts/build_macos_app.sh" >&2
  exit 1
fi

hdiutil create -volname "File Organizer Agent" \
  -srcfolder "$APP" \
  -ov -format UDZO \
  "dist/File Organizer Agent.dmg"

echo "Built: dist/File Organizer Agent.dmg"
