#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Virtual environment not found. Run ./setup.sh first."
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python generate_nametags.py
