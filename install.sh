#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[performance,mcp]'
echo
echo 'Core installed. External local engines are intentionally not vendored.'
echo 'Run: performance-film doctor'
