#!/usr/bin/env bash
# Sets up a local development environment. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,content]"

echo "Done. Activate with: source .venv/bin/activate"
