#!/usr/bin/env bash
# Runs the pytest suite.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -d .venv ]; then source .venv/bin/activate; fi
pytest tests/ -v "$@"
