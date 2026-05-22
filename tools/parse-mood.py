#!/usr/bin/env python3
"""Parse MOOD: line into mood.json."""
import json, re, sys
from datetime import datetime

line = sys.argv[1] if len(sys.argv) > 1 else ""
mood = {}
for key in ["confidence", "conviction", "frustration", "satisfaction", "curiosity", "caution"]:
    m = re.search(key + r"=([0-9.]+)", line)
    if m:
        mood[key] = float(m.group(1))
mood["overall"] = ""
mood["last_updated"] = datetime.now().isoformat()
print(json.dumps(mood, indent=2))
