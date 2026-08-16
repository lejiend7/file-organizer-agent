#!/usr/bin/env bash
# Removes build artifacts and caches. Never touches user data/config -
# only paths inside this repo checkout.
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
find . -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
echo "Cleaned."
