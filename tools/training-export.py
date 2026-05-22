#!/usr/bin/env python3
"""Training Data Export — filters and formats captured pairs for finetuning.

Reads:  data/training-pairs/pairs.jsonl
Writes: data/training-pairs/export_chatml.jsonl   (for DeepSeek/Qwen finetune)
        data/training-pairs/export_alpaca.jsonl    (for Llama finetune)
        data/training-pairs/stats.json             (dataset statistics)

Filters:
  - Drops fix-mode cycles (code debugging, not market thinking)
  - Drops responses under 100 chars (empty/error cycles)
  - Drops skip-mode cycles
  - Optionally filters by tag, action, or date range

Usage:
  python3 training-export.py                    # export all valid pairs
  python3 training-export.py --min-response 200 # only substantial responses
  python3 training-export.py --trades-only      # only cycles with trades
  python3 training-export.py --after 2026-05-01 # date filter
"""

import json, sys, argparse
from pathlib import Path
from datetime import datetime

ROOT = Path("/home/pi/stockpulse")
PAIRS_FILE = ROOT / "data/training-pairs/pairs.jsonl"
EXPORT_DIR = ROOT / "data/training-pairs"

def load_pairs():
    pairs = []
    if not PAIRS_FILE.exists():
        print("No training pairs found")
        return pairs
    for line in PAIRS_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                pairs.append(json.loads(line))
            except:
                pass
    return pairs

def filter_pairs(pairs, args):
    filtered = []
    for p in pairs:
        meta = p.get("metadata", {})

        # Skip fix cycles unless requested
        if meta.get("is_fix_cycle") and not args.include_fix:
            continue

        # Skip tiny responses
        if meta.get("response_bytes", 0) < args.min_response:
            continue

        # Skip skip-mode
        if meta.get("mode") == "skip":
            continue

        # Date filter
        if args.after:
            ts = meta.get("timestamp", "")
            if ts < args.after:
                continue

        # Trades only
        if args.trades_only and not meta.get("has_trade"):
            continue

        filtered.append(p)
    return filtered

def export_chatml(pairs, outpath):
    """ChatML format — native for DeepSeek finetuning."""
    with open(outpath, "w") as f:
        for p in pairs:
            convos = p["conversations"]
            entry = {"messages": [
                {"role": c["role"], "content": c["content"]}
                for c in convos
            ]}
            f.write(json.dumps(entry) + "\n")
    print(f"ChatML: {len(pairs)} pairs -> {outpath}")

def export_alpaca(pairs, outpath):
    """Alpaca format — instruction/input/output."""
    with open(outpath, "w") as f:
        for p in pairs:
            convos = p["conversations"]
            entry = {
                "instruction": convos[0]["content"],  # system prompt
                "input": convos[1]["content"],         # cycle prompt
                "output": convos[2]["content"]         # response
            }
            f.write(json.dumps(entry) + "\n")
    print(f"Alpaca: {len(pairs)} pairs -> {outpath}")

def compute_stats(pairs):
    total_prompt_bytes = sum(p["metadata"].get("prompt_bytes", 0) for p in pairs)
    total_response_bytes = sum(p["metadata"].get("response_bytes", 0) for p in pairs)
    modes = {}
    for p in pairs:
        m = p["metadata"].get("mode", "unknown")
        modes[m] = modes.get(m, 0) + 1
    trade_cycles = sum(1 for p in pairs if p["metadata"].get("has_trade"))
    pred_cycles = sum(1 for p in pairs if p["metadata"].get("has_prediction"))
    all_tags = {}
    for p in pairs:
        for t in p["metadata"].get("tags", []):
            all_tags[t] = all_tags.get(t, 0) + 1
    top_tags = sorted(all_tags.items(), key=lambda x: -x[1])[:20]

    return {
        "total_pairs": len(pairs),
        "total_prompt_mb": round(total_prompt_bytes / 1024 / 1024, 2),
        "total_response_mb": round(total_response_bytes / 1024 / 1024, 2),
        "total_training_mb": round((total_prompt_bytes + total_response_bytes) / 1024 / 1024, 2),
        "avg_prompt_bytes": round(total_prompt_bytes / len(pairs)) if pairs else 0,
        "avg_response_bytes": round(total_response_bytes / len(pairs)) if pairs else 0,
        "modes": modes,
        "trade_cycles": trade_cycles,
        "prediction_cycles": pred_cycles,
        "top_tags": top_tags
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-response", type=int, default=100)
    parser.add_argument("--trades-only", action="store_true")
    parser.add_argument("--include-fix", action="store_true")
    parser.add_argument("--after", type=str, default=None)
    args = parser.parse_args()

    pairs = load_pairs()
    print(f"Loaded {len(pairs)} raw pairs")

    filtered = filter_pairs(pairs, args)
    print(f"After filtering: {filtered and len(filtered) or 0} pairs")

    if not filtered:
        print("No pairs to export")
        return

    stats = compute_stats(filtered)
    print(json.dumps(stats, indent=2))

    export_chatml(filtered, EXPORT_DIR / "export_chatml.jsonl")
    export_alpaca(filtered, EXPORT_DIR / "export_alpaca.jsonl")

    (EXPORT_DIR / "stats.json").write_text(json.dumps(stats, indent=2))
    print("Done. Stats saved to stats.json")

if __name__ == "__main__":
    main()
