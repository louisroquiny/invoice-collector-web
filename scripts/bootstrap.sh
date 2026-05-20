#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
if [ ! -f config.yaml ]; then
  cp config.example.yaml config.yaml
fi
invoice-collector init-profiles
