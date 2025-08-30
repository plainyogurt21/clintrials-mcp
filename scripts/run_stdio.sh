#!/usr/bin/env bash
set -euo pipefail

unset TRANSPORT

if [ ! -x ".venv/bin/python" ]; then
  echo ".venv/bin/python not found. Please create the venv and install requirements."
  echo "python -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

exec .venv/bin/python mcp_server.py

