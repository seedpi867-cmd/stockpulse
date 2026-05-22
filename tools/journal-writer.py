#!/usr/bin/env python3
"""Write a structured journal entry each cycle with self-authored tags.

The LLM outputs a JOURNAL block with its own tags — the things it wants
future-self to find this entry by. The tags are what make collisions
discoverable: when two entries share a tag, they connect.

Tags are written by the agent, not by code. The agent decides what matters.
The routing tool finds entries by tag intersection.
"""
import json, os, re, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
JOURNAL = DATA / "journal"
JOURNAL.mkdir(parents=True, exist_ok=True)
INDEX = DATA / "journal-index.jsonl"

def load_json(path, default=None):
    if path.exists():
        try: return json.loads(path.read_text())
        except: pass
    return default or {}

def load_text(path):
    return path.read_text().strip() if path.exists() else ""

def extract_block(text, marker):
    """Extract everything after MARKER: until the next top-level marker."""
    pattern = r'^' + marker + r':\s*(.*?)(?=\n[A-Z_]+:|$)'
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""

def main():
    cycle_file = DATA / "cycle.txt"
    if not cycle_file.exists():
        return
    cycle = int(cycle_file.read_text().strip())

    journal_file = JOURNAL / "cycle-{:04d}.md".format(cycle)
    if journal_file.exists():
        print("[journal] Cycle {} already written".format(cycle))
        return

    log_file = DATA / "logs" / "cycle_{}.log".format(cycle)
    log_text = load_text(log_file)
    if not log_text:
        print("[journal] No log for cycle {}".format(cycle))
        return

    portfolio = load_json(DATA / "portfolio.json")
    performance = load_json(DATA / "performance.json")
    mood = load_json(DATA / "mood.json")

    # Extract the agent's self-authored tags and notes
    # The LLM writes: TAGS: breadth-divergence, narrow-rally, XLE-capitulation, ...
    # The LLM writes: NOTE_TO_FUTURE: <something it wants to remember>
    # The LLM writes: COLLISION: <pattern it noticed connecting to past knowledge>

    tags_raw = extract_block(log_text, "TAGS")
    tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

    note_to_future = extract_block(log_text, "NOTE_TO_FUTURE")
    collision = extract_block(log_text, "COLLISION")
    inner_voice = extract_block(log_text, "INNER_VOICE")
    watch = extract_block(log_text, "WATCH")
    memory_line = extract_block(log_text, "MEMORY")

    # Find trades and predictions this cycle
    trades = []
    if (DATA / "trades.jsonl").exists():
        for line in (DATA / "trades.jsonl").read_text().strip().splitlines():
            try:
                t = json.loads(line)
                if t.get("cycle") == cycle: trades.append(t)
            except: pass

    preds = []
    if (DATA / "predictions.jsonl").exists():
        for line in (DATA / "predictions.jsonl").read_text().strip().splitlines():
            try:
                p = json.loads(line)
                if p.get("cycle") == cycle: preds.append(p)
            except: pass

    # Auto-add ticker tags from trades/predictions
    for t in trades:
        ticker = t.get("ticker", "").lower()
        if ticker and ticker not in tags: tags.append(ticker)
        tags.append("trade")
    for p in preds:
        pred_text = p.get("prediction", "").lower()
        for sym in ["spy","qqq","iwm","nvda","aapl","msft","tsla","meta","googl","amzn","xle","xlk","xlf","dia","vix"]:
            if sym in pred_text and sym not in tags: tags.append(sym)
        tags.append("prediction")

    # Auto-tag mood extremes
    if mood.get("frustration", 0) > 0.5: tags.append("frustrated")
    if mood.get("confidence", 0) > 0.7: tags.append("high-confidence")
    if mood.get("caution", 0) > 0.7: tags.append("high-caution")
    if mood.get("curiosity", 0) > 0.8: tags.append("high-curiosity")

    tags = sorted(set(tags))

    # Get compact market snapshot
    prices = load_text(ROOT / "context" / "prices.md")
    key_lines = []
    for line in prices.split("\n"):
        if line.startswith("- ") and any(t in line for t in ["SPY","QQQ","IWM","VIX","NVDA","XLE"]):
            key_lines.append(line)

    # Build the journal entry
    now = datetime.now()
    lines = []
    lines.append("# Cycle {} — {}".format(cycle, now.strftime("%Y-%m-%d %H:%M")))
    lines.append("")
    lines.append("**Tags:** {}".format(", ".join("`{}`".format(t) for t in tags) if tags else "none"))
    lines.append("**Portfolio:** ${:,.0f} | Cash: ${:,.0f} | Positions: {}".format(
        performance.get("portfolio_value", 100000),
        portfolio.get("cash", 100000),
        len(portfolio.get("positions", []))))
    lines.append("")

    # Note to future self — the most important part
    if note_to_future:
        lines.append("## Note to Future Self")
        lines.append("")
        lines.append("> {}".format(note_to_future))
        lines.append("")

    # Collision — pattern the agent spotted connecting things
    if collision:
        lines.append("## Collision Detected")
        lines.append("")
        lines.append("{}".format(collision))
        lines.append("")

    # Thinking
    lines.append("## Thinking")
    lines.append("")
    lines.append(inner_voice if inner_voice else "No inner voice this cycle.")
    lines.append("")

    # Decisions
    if watch or trades or preds:
        lines.append("## Decisions")
        lines.append("")
        if watch:
            lines.append("**Watch:** {}".format(watch))
            lines.append("")
        for t in trades:
            lines.append("**{} {} {} @ ${}** (conv {}, stop {}, target {})".format(
                t["action"], t["ticker"], t["shares"], t["price"],
                t.get("conviction","?"), t.get("stop","?"), t.get("target","?")))
            lines.append("_{}_".format(t.get("reasoning","no reasoning")))
            lines.append("")
        for p in preds:
            lines.append("**Prediction:** {} (conv {}, by {})".format(
                p["prediction"], p.get("conviction","?"), p.get("deadline","?")))
            lines.append("_{}_".format(p.get("reasoning","no reasoning")))
            lines.append("")

    # Mood
    lines.append("## Mood")
    lines.append("")
    lines.append("conf={} conv={} curi={} caut={} frus={} satis={}".format(
        mood.get("confidence","?"), mood.get("conviction","?"),
        mood.get("curiosity","?"), mood.get("caution","?"),
        mood.get("frustration","?"), mood.get("satisfaction","?")))
    if mood.get("overall"):
        lines.append("")
        lines.append(mood["overall"])
    lines.append("")

    # Market snapshot
    if key_lines:
        lines.append("## Market Snapshot")
        lines.append("")
        for kl in key_lines:
            lines.append(kl)
        lines.append("")

    # Memory
    if memory_line:
        lines.append("## Summary")
        lines.append("")
        lines.append(memory_line)

    # Write journal file
    journal_file.write_text("\n".join(lines) + "\n")

    # Append to tag index — one JSON line per entry for fast search
    index_entry = {
        "cycle": cycle,
        "file": journal_file.name,
        "tags": tags,
        "timestamp": now.isoformat(),
        "note": note_to_future[:200] if note_to_future else "",
        "collision": collision[:200] if collision else "",
        "summary": memory_line[:200] if memory_line else ""
    }
    with open(str(INDEX), "a") as f:
        f.write(json.dumps(index_entry) + "\n")

    print("[journal] Cycle {} — {} tags, note={}, collision={}".format(
        cycle, len(tags),
        "yes" if note_to_future else "no",
        "yes" if collision else "no"))

if __name__ == "__main__":
    main()
