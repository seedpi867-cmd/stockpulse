#!/usr/bin/env python3
"""Training Data Capture — saves each cycle's prompt+response as a training pair.

Format: ChatML-style JSONL (compatible with DeepSeek, Llama, Qwen finetuning)
Output: data/training-pairs/pairs.jsonl

Each line is a complete training example:
{
  "conversations": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "metadata": {
    "cycle": 370,
    "mode": "normal",
    "timestamp": "...",
    "prompt_bytes": 4500,
    "response_bytes": 3200,
    "tags": ["narrow-rally", "xle-distribution"],
    "actions": ["WATCH"],
    "has_trade": false,
    "has_prediction": false
  }
}
"""

import json, os, sys, re
from pathlib import Path
from datetime import datetime

ROOT = Path(os.environ.get("AGENT_ROOT", "/home/pi/stockpulse"))
DATA = ROOT / "data"
PAIRS_DIR = DATA / "training-pairs"
PAIRS_FILE = PAIRS_DIR / "pairs.jsonl"

def extract_tags(response):
    """Pull TAGS: line from response."""
    m = re.search(r'^TAGS:\s*(.+)$', response, re.MULTILINE)
    if m:
        return [t.strip() for t in m.group(1).split(',') if t.strip()]
    return []

def extract_actions(response):
    """Pull ACTION: lines from response."""
    actions = []
    for m in re.finditer(r'^ACTION:\s*(\w+)', response, re.MULTILINE):
        actions.append(m.group(1))
    return actions

def main():
    if len(sys.argv) < 4:
        print("Usage: training-capture.py <cycle> <mode> <prompt_file> [response_file]")
        sys.exit(1)

    cycle = int(sys.argv[1])
    mode = sys.argv[2]
    prompt_file = Path(sys.argv[3])
    response_file = Path(sys.argv[4]) if len(sys.argv) > 4 else None

    # Read prompt
    prompt_text = prompt_file.read_text() if prompt_file.exists() else ""
    if not prompt_text:
        print("[training-capture] Empty prompt, skipping")
        return

    # Read response
    if response_file and response_file.exists():
        response_text = response_file.read_text()
    else:
        # Try reading from stdin
        response_text = sys.stdin.read() if not sys.stdin.isatty() else ""

    if not response_text or len(response_text) < 20:
        print("[training-capture] Empty/tiny response, skipping")
        return

    # Skip fix-mode cycles — they're about code debugging, not market analysis
    # Still capture them but tag them so we can filter later
    is_fix = mode == "fix"

    # Read system prompt (AGENT.md + INSTRUCTIONS.md) — cached after first read
    system_cache = PAIRS_DIR / ".system_prompt_cache.txt"
    if system_cache.exists():
        system_prompt = system_cache.read_text()
    else:
        agent_md = (ROOT / "AGENT.md").read_text() if (ROOT / "AGENT.md").exists() else ""
        instructions_md = (ROOT / "INSTRUCTIONS.md").read_text() if (ROOT / "INSTRUCTIONS.md").exists() else ""
        system_prompt = agent_md + "\n\n" + instructions_md
        PAIRS_DIR.mkdir(parents=True, exist_ok=True)
        system_cache.write_text(system_prompt)

    # Extract metadata from response
    tags = extract_tags(response_text)
    actions = extract_actions(response_text)
    has_trade = any(a in actions for a in ["BUY", "SELL", "SHORT", "COVER"])
    has_prediction = "PREDICT" in actions or "PREDICTION:" in response_text

    pair = {
        "conversations": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_text},
            {"role": "assistant", "content": response_text}
        ],
        "metadata": {
            "cycle": cycle,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
            "prompt_bytes": len(prompt_text),
            "response_bytes": len(response_text),
            "tags": tags,
            "actions": actions,
            "has_trade": has_trade,
            "has_prediction": has_prediction,
            "is_fix_cycle": is_fix
        }
    }

    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    with open(PAIRS_FILE, "a") as f:
        f.write(json.dumps(pair) + "\n")

    print(f"[training-capture] Cycle {cycle} saved ({len(prompt_text)}B prompt, {len(response_text)}B response, tags={len(tags)}, actions={actions})")

if __name__ == "__main__":
    main()
