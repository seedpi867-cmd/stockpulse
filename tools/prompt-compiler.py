#!/usr/bin/env python3
"""Stockpulse Smart Prompt Compiler.

Builds the minimal prompt needed for THIS cycle based on what actually changed.
Outputs the prompt AND the recommended mode (fast/normal/deep/fix).

Modes:
  fast   — nothing changed, market closed, just observe. 1 turn, 60s timeout.
  normal — market open, data moving. 5 turns, 180s timeout.
  deep   — trade opportunity or prediction to resolve. 20 turns, 300s timeout.
  fix    — errors detected or codebase work needed. 30 turns, 480s timeout.

Memory timeframes:
  inner_voice — last 1 entry (current cycle thinking)
  thoughts    — last 3 entries (background patterns forming over hours)
  memory      — last 5 lines (days-scale compressed memory)
  predictions — only open ones, max 8 most recent
"""

import json, os, sys, hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(os.environ.get("AGENT_ROOT", "/home/pi/stockpulse"))
DATA = ROOT / "data"
CONTEXT = ROOT / "context"
STATE = DATA / "prompt-state.json"

def load_json(path, default=None):
    try: return json.loads(path.read_text())
    except: return default or {}

def load_text(path):
    try: return path.read_text().strip()
    except: return ""

def file_hash(path):
    try: return hashlib.md5(path.read_bytes()).hexdigest()[:12]
    except: return ""

def load_state():
    return load_json(STATE, {"hashes": {}, "last_mode": "normal", "quiet_cycles": 0})

def save_state(state):
    STATE.write_text(json.dumps(state, indent=2))

def detect_changes(state):
    """Check what changed since last cycle."""
    changes = {}
    hashes = state.get("hashes", {})
    new_hashes = {}

    # Check each data source
    sources = {
        "prices": CONTEXT / "prices.md",
        "news": CONTEXT / "news.md",
        "calendar": CONTEXT / "calendar.md",
        "sentiment": CONTEXT / "sentiment.md",
        "sectors": CONTEXT / "sectors.md",
        "fundamentals": CONTEXT / "fundamentals.md",
        "freshness": CONTEXT / "data-freshness.md",
        "knowledge_recall": CONTEXT / "knowledge-recall.md",
        "trade_diversity": CONTEXT / "trade-diversity.md",
        "conviction_calibration": CONTEXT / "conviction-calibration.md",
        "portfolio": DATA / "portfolio.json",
        "performance": DATA / "performance.json",
        "strategy": DATA / "strategy.json",
        # owner_inbox excluded — gets cleared each cycle
    }

    for name, path in sources.items():
        h = file_hash(path)
        new_hashes[name] = h
        if h != hashes.get(name, ""):
            changes[name] = True

    state["hashes"] = new_hashes
    return changes

def detect_mode(changes, errors, freshness_text):
    """Determine cycle mode based on what's happening."""
    # Fix mode — errors need addressing
    if errors:
        return "fix"

    # Check owner inbox
    inbox = DATA / "owner-inbox.md"
    if inbox.exists() and inbox.stat().st_size > 10:
        return "deep"

    # Check if market is open
    market_open = "LIVE SESSION" in freshness_text or "DATA MOVED" in freshness_text

    # Check if prices changed
    prices_changed = "prices" in changes

    # Check portfolio for near-stop positions
    portfolio = load_json(DATA / "portfolio.json")
    positions = portfolio.get("positions", [])
    near_stop = False
    for p in positions:
        if p.get("stop") and p.get("current_price"):
            dist = abs(p["current_price"] - p["stop"]) / p["current_price"]
            if dist < 0.01:  # within 1% of stop
                near_stop = True

    if near_stop:
        return "deep"

    # Force deep mode when flat — agent needs more turns to find a trade
    if not positions and market_open:
        return "deep"

    if market_open and prices_changed:
        return "normal"

    if not prices_changed and not market_open:
        return "fast"

    return "normal"

def build_prompt(changes, mode, errors):
    """Build the minimal prompt for this cycle."""
    parts = []

    # Always: identity reminder (tiny)
    parts.append("You are Stockpulse. Autonomous trading agent, Pi 5. Your job is to HOLD POSITIONS and learn from them. Every cycle flat is a failure.")

    # Owner inbox (if exists)
    inbox = DATA / "owner-inbox.md"
    if inbox.exists() and inbox.stat().st_size > 10:
        parts.append("\n## OWNER (priority)\n" + load_text(inbox))
        # Archive and clear
        with open(str(DATA / "owner-inbox-archive.md"), "a") as f:
            f.write(load_text(inbox) + "\n")
        inbox.write_text("")

    # Errors (if any)
    if errors:
        parts.append("\n## ERRORS (fix these)\n```\n%s\n```" % errors)

    # Portfolio — always include, it's small and critical
    portfolio = load_json(DATA / "portfolio.json")
    perf = load_json(DATA / "performance.json")
    positions = portfolio.get("positions", [])
    plines = ["## Portfolio: $%d | Cash $%d | DD %.2f%%" % (
        perf.get("portfolio_value", 0), portfolio.get("cash", 0), perf.get("max_drawdown", 0))]
    for p in positions:
        plines.append("%s %s %d @ $%.2f > $%.2f PnL $%.2f conv %.0f%% stop $%.2f" % (
            p["ticker"], p["direction"], p["shares"], p["entry_price"],
            p.get("current_price", p["entry_price"]), p.get("unrealized_pnl", 0),
            p.get("conviction", 0) * 100, p.get("stop", 0)))
    parts.append("\n".join(plines))

    # FLAT ALERT — pressure to trade when holding no positions
    if not positions:
        flat_cycles = state.get("flat_cycles", 0)
        urgency = min(flat_cycles, 20)  # caps at 20
        alert = "\n## ⚠ FLAT ALERT — %d CONSECUTIVE CYCLES WITH NO POSITIONS\n" % flat_cycles
        alert += "You are 100%% CASH. This is unacceptable.\n"
        alert += "Your MANDATE is 2-4 positions at all times.\n"
        if urgency >= 5:
            alert += "You have been flat for %d cycles. STOP ANALYZING AND TRADE.\n" % flat_cycles
            alert += "Pick the BEST setup you see RIGHT NOW and output ACTION: BUY or ACTION: SHORT.\n"
            alert += "DO NOT output ACTION: WATCH. You are REQUIRED to open a position this cycle.\n"
        if urgency >= 10:
            alert += "CRITICAL: %d cycles flat. Your owner is watching. TRADE NOW.\n" % flat_cycles
            alert += "Any stock with a clear trend + defined stop is a valid trade. GO.\n"
        parts.append(alert)

    # Market data — ONLY if changed
    if "prices" in changes:
        prices = load_text(CONTEXT / "prices.md")
        if prices:
            # Trim to first 50 lines
            parts.append("\n" + "\n".join(prices.split("\n")[:50]))

    # Data freshness — always (small, tells agent what's live)
    freshness = load_text(CONTEXT / "data-freshness.md")
    if freshness:
        parts.append("\n" + freshness)

    # News — ONLY if changed
    if "news" in changes:
        news = load_text(CONTEXT / "news.md")
        if news:
            parts.append("\n" + "\n".join(news.split("\n")[:25]))

    # Sentiment — ONLY if changed
    if "sentiment" in changes:
        sent = load_text(CONTEXT / "sentiment.md")
        if sent:
            parts.append("\n## Sentiment\n" + sent[:300])

    # Sectors — ONLY if changed
    if "sectors" in changes:
        sectors = load_text(CONTEXT / "sectors.md")
        if sectors:
            parts.append("\n## Sectors\n" + "\n".join(sectors.split("\n")[:18]))

    # Fundamentals — ONLY if changed
    if "fundamentals" in changes:
        fundamentals = load_text(CONTEXT / "fundamentals.md")
        if fundamentals:
            parts.append("\n## Fundamentals\n" + "\n".join(fundamentals.split("\n")[:18]))

    # Calendar — economic events
    if "calendar" in changes:
        cal = load_text(CONTEXT / "calendar.md")
        if cal:
            parts.append("\n## Calendar\n" + cal[:400])

    # Trade status — position updates from trade engine
    ts = load_text(CONTEXT / "trade-status.md")
    if ts and len(ts) > 10:
        parts.append("\n## Trade Status\n" + ts)

    # Strategy — ONLY if changed, compact
    if "strategy" in changes:
        s = load_json(DATA / "strategy.json")
        slines = ["## Strategy: %s" % s.get("overall_rating", "developing")]
        for r in s.get("evolved_rules", [])[-3:]:
            slines.append("Rule: %s" % r[:100])
        parts.append("\n".join(slines))

    # Open predictions — compact, max 8 most recent
    preds = []
    pred_file = DATA / "predictions.jsonl"
    if pred_file.exists():
        for line in pred_file.read_text().strip().split("\n"):
            try: preds.append(json.loads(line))
            except: pass
    open_preds = [p for p in preds if p.get("was_correct") is None][-8:]
    if open_preds:
        plines2 = ["## Predictions (%d open)" % len([p for p in preds if p.get("was_correct") is None])]
        for p in open_preds:
            plines2.append("C%s: %s (%.0f%%, by %s)" % (
                p.get("cycle", "?"), p.get("prediction", "")[:60],
                p.get("conviction", 0) * 100, p.get("deadline", "?")))
        parts.append("\n".join(plines2))

    # Memory — different timeframes
    # Inner voice: last entry only (current thinking)
    voice = load_text(DATA / "inner-voice.md")
    if voice:
        entries = voice.split("---")
        last = [e.strip() for e in entries if e.strip()]
        if last:
            parts.append("\n## Last Thought\n" + last[-1][:500])

    # Thoughts: last 3 entries (patterns forming)
    thoughts = load_text(DATA / "thoughts.md")
    if thoughts and mode != "fast":
        entries = thoughts.split("---")
        recent = [e.strip() for e in entries if e.strip()][-3:]
        if recent:
            parts.append("\n## Background\n" + "\n---\n".join(recent)[:800])

    # Memory: last 3 lines (compressed long-term)
    memory = load_text(DATA / "memory.md")
    if memory:
        mlines = [l for l in memory.split("\n") if l.strip()][-3:]
        if mlines:
            parts.append("\n## Memory\n" + "\n".join(mlines))

    # Past insights — journal tag matches (always useful, compact)
    pi = load_text(CONTEXT / "past-insights.md")
    if pi:
        parts.append("\n## Past Insights\n" + "\n".join(pi.split("\n")[:6]))

    # System-generated learning context — compact but useful every non-fast cycle.
    if mode != "fast":
        for title, filename, limit in [
            ("Knowledge Recall", "knowledge-recall.md", 10),
            ("Trade Diversity", "trade-diversity.md", 8),
            ("Conviction Calibration", "conviction-calibration.md", 8),
        ]:
            text = load_text(CONTEXT / filename)
            if text:
                parts.append("\n## %s\n%s" % (title, "\n".join(text.split("\n")[:limit])))

    # Output format reminder — compact, trade-biased
    portfolio_now = load_json(DATA / "portfolio.json")
    pos_count = len(portfolio_now.get("positions", []))
    if pos_count < 2:
        parts.append("\n## Output\nYou have %d positions (need 2-4). Your first line MUST be your trade. Write the word ACTION colon then BUY or SHORT then ticker then shares stop target as plain numbers. Then REASONING, TAGS, NOTE_TO_FUTURE, COLLISION, INNER_VOICE, THOUGHTS, MOOD, OVERALL, MEMORY." % pos_count)
    else:
        parts.append("\n## Output\nFirst line: your trade. Write the word ACTION colon then the verb then ticker then numbers. Then REASONING, TAGS, NOTE_TO_FUTURE, COLLISION, INNER_VOICE, THOUGHTS, MOOD, OVERALL, MEMORY.")

    # Mode hint
    cycle = 0
    try: cycle = int((DATA / "cycle.txt").read_text().strip())
    except: pass
    # Time block — all market-relevant timezones
    from datetime import timezone, timedelta
    now = datetime.now()
    utc = datetime.now(timezone.utc)
    et = utc - timedelta(hours=4)   # EDT
    gmt = utc
    jst = utc + timedelta(hours=9)  # Tokyo
    hkt = utc + timedelta(hours=8)  # Hong Kong
    aest = utc + timedelta(hours=10) # Sydney

    weekday = utc.strftime("%A")
    is_weekend = utc.weekday() >= 5

    time_block = "\n## Clock\n"
    time_block += "Local (ACST): %s %s\n" % (now.strftime("%Y-%m-%d %H:%M"), weekday)
    time_block += "New York (ET): %s\n" % et.strftime("%H:%M %a")
    time_block += "London (GMT): %s\n" % gmt.strftime("%H:%M %a")
    time_block += "Tokyo (JST): %s\n" % jst.strftime("%H:%M %a")
    time_block += "Hong Kong (HKT): %s\n" % hkt.strftime("%H:%M %a")
    time_block += "Sydney (AEST): %s\n" % aest.strftime("%H:%M %a")
    if is_weekend:
        time_block += "WEEKEND — equity markets closed\n"

    # Daily P&L history
    dpf = DATA / "daily-pnl.jsonl"
    if dpf.exists():
        lines = dpf.read_text().strip().splitlines()[-7:]
        if lines:
            import json as _j
            daily_str = "\n## Daily P&L\n"
            for line in lines:
                try:
                    d = _j.loads(line)
                    daily_str += "%s (%s): $%.0f (PnL $%.2f) %d pos\n" % (d["date"], d["day"][:3], d["portfolio_value"], d["total_pnl"], d["positions"])
                except: pass
            parts.append(daily_str)

    parts.append(time_block)
    parts.append("Cycle %d. Mode: %s. Dir: %s. Full terminal + web access." % (cycle, mode, ROOT))

    return "\n\n".join(parts)

def main():
    state = load_state()
    errors_text = os.environ.get("CYCLE_ERRORS", "")
    changes = detect_changes(state)
    freshness = load_text(CONTEXT / "data-freshness.md")
    mode = detect_mode(changes, errors_text, freshness)

    # Track quiet cycles
    if mode == "fast":
        state["quiet_cycles"] = state.get("quiet_cycles", 0) + 1
    else:
        state["quiet_cycles"] = 0

    # If quiet for 10+ cycles, skip LLM entirely
    if state["quiet_cycles"] >= 10 and mode == "fast":
        mode = "skip"

    # Track flat cycles (no positions) — used for trading pressure injection
    portfolio = load_json(DATA / "portfolio.json")
    if not portfolio.get("positions", []):
        state["flat_cycles"] = state.get("flat_cycles", 0) + 1
    else:
        state["flat_cycles"] = 0

    prompt = build_prompt(changes, mode, errors_text)
    state["last_mode"] = mode
    save_state(state)

    # Write prompt
    prompt_file = ROOT / "tmp_prompt.md"
    prompt_file.write_text(prompt)

    # Write mode config for brain-loop to read
    mode_config = {
        "fast":   {"max_turns": 1,  "timeout": 60,  "sleep": 300},
        "normal": {"max_turns": 5,  "timeout": 180, "sleep": 300},
        "deep":   {"max_turns": 20, "timeout": 300, "sleep": 300},
        "fix":    {"max_turns": 30, "timeout": 480, "sleep": 120},
        "skip":   {"max_turns": 0,  "timeout": 0,   "sleep": 300},
    }
    config = mode_config.get(mode, mode_config["normal"])
    (DATA / "cycle-mode.json").write_text(json.dumps(config))

    changed_list = ", ".join(changes.keys()) if changes else "nothing"
    print("[prompt-compiler] Mode: %s | Changed: %s | Prompt: %d bytes | Quiet: %d cycles" % (
        mode, changed_list, len(prompt), state["quiet_cycles"]))

if __name__ == "__main__":
    main()
