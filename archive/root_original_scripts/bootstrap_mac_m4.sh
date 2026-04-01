#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew is required. Install it first: https://brew.sh/"
  exit 1
fi

brew install pandoc openjdk uv tectonic

cd "${ROOT_DIR}"

if [ ! -d ".venv" ]; then
  uv venv --python 3.12 .venv
fi

uv sync --extra dev

echo
echo "Bootstrap complete."
echo "Run: uv run doc-shape-shifter doctor"
