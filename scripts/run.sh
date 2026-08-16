#!/usr/bin/env bash
# Runs the app locally (unpackaged), from source.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -d .venv ]; then source .venv/bin/activate; fi
python3 -m organizer.ui.app
