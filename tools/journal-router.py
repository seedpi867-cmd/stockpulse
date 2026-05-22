#!/usr/bin/env python3
"""Route relevant past journal entries into the current cycle's context.

Reads the tag index, finds entries that share tags with the current market
conditions, and writes a PAST_INSIGHTS context file the agent reads each
cycle. This is how it finds collisions — when today's XLE capitulation
matches a pattern it tagged 40 cycles ago, that old entry surfaces.
"""
import json, os, re, sys
from datetime import datetime
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
JOURNAL = DATA / "journal"
INDEX = DATA / "journal-index.jsonl"
CONTEXT = ROOT / "context"

def load_index():
    if not INDEX.exists():
        return []
    entries = []
    for line in INDEX.read_text().strip().splitlines():
        try: entries.append(json.loads(line))
        except: pass
    return entries

def get_current_tags():
    """Build tags from current market conditions to match against past entries."""
    tags = set()

    # From prices — which tickers are moving
    prices_file = CONTEXT / "prices.md"
    if prices_file.exists():
        text = prices_file.read_text()
        # Find big movers (>2% either direction)
        for m in re.finditer(r'([A-Z]{2,5}).*?\(([+-]?\d+\.\d+)%\)', text):
            ticker = m.group(1).lower()
            change = float(m.group(2))
            if abs(change) > 2:
                tags.add(ticker)
                if change > 2: tags.add("rally")
                if change < -2: tags.add("selloff")

        # Check VIX
        vix_m = re.search(r'VIX.*?\$(\d+\.?\d*)', text)
        if vix_m:
            vix = float(vix_m.group(1))
            if vix > 25: tags.add("high-vix")
            if vix < 15: tags.add("low-vix")

    # From sentiment
    sent_file = CONTEXT / "sentiment.md"
    if sent_file.exists():
        text = sent_file.read_text()
        if "EXTREME FEAR" in text: tags.add("extreme-fear")
        if "EXTREME GREED" in text: tags.add("extreme-greed")
        pc_m = re.search(r'Equity P/C:\s*(\d+\.\d+)', text)
        if pc_m:
            pc = float(pc_m.group(1))
            if pc > 1.0: tags.add("bearish-positioning")
            if pc < 0.3: tags.add("bullish-positioning")

    # From recent predictions and mood
    mood = {}
    mood_file = DATA / "mood.json"
    if mood_file.exists():
        try: mood = json.loads(mood_file.read_text())
        except: pass
    if mood.get("frustration", 0) > 0.5: tags.add("frustrated")
    if mood.get("confidence", 0) > 0.7: tags.add("high-confidence")
    if mood.get("caution", 0) > 0.7: tags.add("high-caution")

    # From strategy — what setups are we looking for
    strat_file = DATA / "strategy.json"
    if strat_file.exists():
        try:
            strat = json.loads(strat_file.read_text())
            for setup in strat.get("preferred_setups", []):
                tags.add(setup.lower().replace(" ", "-"))
        except: pass

    return tags

def find_relevant(index, current_tags, current_cycle, max_results=5):
    """Find past journal entries with the most tag overlap to current conditions."""
    if not current_tags or not index:
        return []

    scored = []
    for entry in index:
        # Don't include the current or very recent cycles
        if entry["cycle"] >= current_cycle - 1:
            continue

        entry_tags = set(entry.get("tags", []))
        overlap = current_tags & entry_tags
        if not overlap:
            continue

        # Score: number of matching tags, boosted if there's a note or collision
        score = len(overlap)
        if entry.get("note"): score += 1
        if entry.get("collision"): score += 2

        scored.append((score, overlap, entry))

    scored.sort(key=lambda x: -x[0])
    return scored[:max_results]

def main():
    cycle_file = DATA / "cycle.txt"
    current_cycle = int(cycle_file.read_text().strip()) if cycle_file.exists() else 0

    index = load_index()
    if not index:
        print("[journal-router] No journal entries to route from")
        return

    current_tags = get_current_tags()
    if not current_tags:
        print("[journal-router] No current tags to match")
        return

    matches = find_relevant(index, current_tags, current_cycle)
    if not matches:
        print("[journal-router] No past entries match current tags: {}".format(
            ", ".join(sorted(current_tags))))
        # Clean up old insights
        insights_file = CONTEXT / "past-insights.md"
        if insights_file.exists():
            insights_file.write_text("# Past Insights\n\nNo matching past journal entries this cycle.\n")
        return

    # Build the context file
    lines = ["# Past Insights — Matching Journal Entries\n"]
    lines.append("Current tags: {}\n".format(", ".join("`{}`".format(t) for t in sorted(current_tags))))

    for score, overlap, entry in matches:
        lines.append("---")
        lines.append("")
        lines.append("## Cycle {} — matched on: {}".format(
            entry["cycle"],
            ", ".join("`{}`".format(t) for t in sorted(overlap))))

        # Load the actual journal file
        jfile = JOURNAL / entry["file"]
        if jfile.exists():
            content = jfile.read_text()
            # Extract the key sections: note to future, collision, thinking summary
            for section in ["Note to Future Self", "Collision Detected", "Summary"]:
                pattern = r'## {}\n\n(.*?)(?=\n## |\Z)'.format(re.escape(section))
                m = re.search(pattern, content, re.DOTALL)
                if m:
                    text = m.group(1).strip()
                    if text:
                        lines.append("")
                        lines.append("**{}:** {}".format(section, text[:300]))
        else:
            # Fallback to index data
            if entry.get("note"):
                lines.append("**Note:** {}".format(entry["note"]))
            if entry.get("collision"):
                lines.append("**Collision:** {}".format(entry["collision"]))
            if entry.get("summary"):
                lines.append("**Summary:** {}".format(entry["summary"]))

        lines.append("")

    output = "\n".join(lines) + "\n"
    (CONTEXT / "past-insights.md").write_text(output)

    print("[journal-router] {} matches surfaced from {} tags ({})".format(
        len(matches), len(current_tags),
        ", ".join(t for _, overlap, _ in matches for t in sorted(overlap))))

if __name__ == "__main__":
    main()
