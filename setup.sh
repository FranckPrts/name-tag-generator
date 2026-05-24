#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python - <<'PY'
import config
from pathlib import Path

Path(config.CSV).write_text(config.EXAMPLE_CSV, encoding="utf-8")

if not Path(config.TEMPLATE).exists():
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(config.TEMPLATE, pagesize=(612, 792))
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.7, 0.7, 0.7)
    c.drawCentredString(306, 396, "Replace nametag_template.pdf with your name tag template")
    c.save()
    print(f"Created placeholder {config.TEMPLATE}")
PY

echo ""
echo "Setup complete. Run:"
echo "  ./run.sh"
