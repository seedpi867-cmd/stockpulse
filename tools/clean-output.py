#!/usr/bin/env python3
"""Filter LLM output: keep only structured markers, reject templates, dedup by marker."""
import sys, re

MARKERS = {"ACTION", "WATCH", "TAGS", "COLLISION", "INNER_VOICE", "THOUGHTS",
           "MOOD", "OVERALL", "MEMORY", "TRADE", "PREDICTION", "NOTE_TO_FUTURE",
           "REASONING", "NOTE_TO_SELF"}

# Patterns that indicate template/instruction echo rather than real output
TEMPLATE_PATTERNS = [
    r"BUY\|SELL\|SHORT\|COVER",
    r"confidence=X",
    r"One line,",                      # "One line, max..." or "One line, C{cycle}..."
    r"C\{cycle\}",                     # literal {cycle} format-string marker
    r"\{ticker\}",                     # literal {ticker}
    r"\{direction\}",                  # literal {direction}
    r"Comma-separated lowercase",
    r"4-8 sentences",                  # inner voice template
    r"1-2 sentences max",             # thoughts template
    r"1-2 sentences first person",    # thoughts template variant
    r"first person\. What",
    r"One standalone",
    r"One sentence on current",
    r"One sentence market read",
    r"entering/modifying",
    r"A lesson or warning",
    r"2\+ signals connect",
    r"Why you took the action",
    r"lowercase comma-separated tags",
    r"key facts about what you did",  # the exact template text GPT echoes
    r"correlations, knowledge connections, opportunities",
]

text = sys.stdin.read() if not sys.argv[1:] else open(sys.argv[1]).read()

# Collect last occurrence of each marker (later turns override earlier)
last_by_marker = {}
order = []
for line in text.splitlines():
    line = line.strip()
    if not line:
        continue
    match = re.match(r"^([A-Z_]+): ", line)
    if not match:
        continue
    marker = match.group(1)
    if marker not in MARKERS:
        continue
    # Skip template lines
    if any(re.search(p, line) for p in TEMPLATE_PATTERNS):
        continue
    # Skip very short lines (likely template fragments)
    if len(line) < 20:
        continue
    last_by_marker[marker] = line
    if marker not in order:
        order.append(marker)

for marker in order:
    if marker in last_by_marker:
        print(last_by_marker[marker])
