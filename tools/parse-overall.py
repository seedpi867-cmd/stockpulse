#!/usr/bin/env python3
"""Parse OVERALL: line and merge into mood.json."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOOD_FILE = ROOT / "data" / "mood.json"

overall = sys.argv[1] if len(sys.argv) > 1 else ""
if not overall:
    sys.exit(0)

try:
    d = json.loads(MOOD_FILE.read_text())
except Exception:
    d = {}

d["overall"] = overall
MOOD_FILE.write_text(json.dumps(d, indent=2))
