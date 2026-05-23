import re
#!/usr/bin/env python3
"""Compile all agent data into a single JSON for the dashboard."""
import sys, json, os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTEXT = ROOT / "context"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

def load_json(path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            pass
    return default or {}

def load_jsonl(path, limit=50):
    if not path.exists():
        return []
    items = []
    for line in path.read_text().strip().splitlines():
        try:
            items.append(json.loads(line))
        except:
            pass
    return items[-limit:]

def load_text(path, limit_lines=50):
    if not path.exists():
        return ""
    lines = path.read_text().strip().splitlines()
    return "\n".join(lines[-limit_lines:])


def parse_entries(text):
    """Parse ---\nCycle N (HH:MM):\ntext entries into structured list."""
    if not text:
        return []
    entries = []
    for block in text.split("---"):
        block = block.strip()
        if not block:
            continue
        m = re.match(r'Cycle\s+(\d+)\s*\(([^)]+)\):\s*([\s\S]*)', block)
        if m:
            entries.append({
                "cycle": int(m.group(1)),
                "time": m.group(2).strip(),
                "text": m.group(3).strip()
            })
    return sorted(entries, key=lambda x: x["cycle"], reverse=True)

def main():
    portfolio = load_json(DATA / "portfolio.json")
    performance = load_json(DATA / "performance.json")
    mood = load_json(DATA / "mood.json")
    strategy = load_json(DATA / "strategy.json")

    trades = load_jsonl(DATA / "trades.jsonl", 100)
    predictions = load_jsonl(DATA / "predictions.jsonl", 20)

    inner_voice_raw = load_text(DATA / "inner-voice.md", 50)
    inner_voice = parse_entries(inner_voice_raw)
    memory = load_text(DATA / "memory.md", 10)
    thoughts_raw = load_text(DATA / "thoughts.md", 30)
    thoughts = parse_entries(thoughts_raw)

    # Load context files
    market = {}
    for name in [
        "prices",
        "news",
        "sentiment",
        "sectors",
        "calendar",
        "knowledge-recall",
        "trade-diversity",
        "conviction-calibration",
        "data-freshness",
        "trade-status",
        "past-insights",
        "prediction-resolutions",
    ]:
        path = CONTEXT / "{}.md".format(name)
        if path.exists():
            market[name] = path.read_text()

    # Load latest lessons
    lessons_dir = ROOT / "knowledge" / "lessons"
    lessons = []
    if lessons_dir.exists():
        lesson_files = sorted(lessons_dir.glob("review-cycle-*.md"), reverse=True)
        for lf in lesson_files[:3]:
            lessons.append({"file": lf.name, "content": lf.read_text()[:500]})

    # Cycle info
    cycle = 0
    cycle_file = DATA / "cycle.txt"
    if cycle_file.exists():
        try:
            cycle = int(cycle_file.read_text().strip())
        except:
            pass

    # Prediction stats
    pred_open = len([p for p in predictions if p.get("was_correct") is None])
    pred_correct = len([p for p in predictions if p.get("was_correct") is True])
    pred_wrong = len([p for p in predictions if p.get("was_correct") is False])
    pred_total = len(predictions)

    # Extract recent notes-to-future and collisions from journal
    notes = []
    collisions = []
    journal_dir = DATA / "journal"
    if journal_dir.exists():
        for jf in sorted(journal_dir.glob("cycle-*.md"), reverse=True)[:30]:
            text = jf.read_text()
            cycle_num = jf.stem.replace("cycle-","").lstrip("0") or "0"
            # Parse sections by ## headers
            sections = text.split("## ")
            for sec in sections:
                if sec.startswith("Note to Future") and len(notes) < 8:
                    body = sec.split("\n", 1)[1].strip().strip("> ").replace("\n> ", " ").replace("\n", " ")[:400]
                    if body:
                        notes.append({"cycle": cycle_num, "text": body})
                elif sec.startswith("Collision") and len(collisions) < 8:
                    body = sec.split("\n", 1)[1].strip().replace("\n", " ")[:400]
                    if body:
                        collisions.append({"cycle": cycle_num, "text": body})

    # Active positions as theses
    theses = []
    for pos in portfolio.get("positions", []):
        theses.append({
            "ticker": pos["ticker"],
            "direction": pos.get("direction", "long"),
            "entry": pos.get("entry_price", 0),
            "conviction": pos.get("conviction", 0),
            "reasoning": pos.get("reasoning", "")[:200],
            "cycle": pos.get("entry_cycle", 0)
        })

    dashboard_data = {
        "cycle": cycle,
        "timestamp": datetime.now().isoformat(),
        "portfolio": portfolio,
        "performance": performance,
        "mood": mood,
        "strategy": {
            "preferred_setups": strategy.get("preferred_setups", []),
            "avoid_setups": strategy.get("avoid_setups", []),
            "evolved_rules": strategy.get("evolved_rules", [])[-5:],
            "overall_rating": strategy.get("overall_rating", "unknown"),
            "hypotheses": strategy.get("hypotheses", []),
            "active_experiments": strategy.get("active_experiments", []),
            "position_sizing_note": strategy.get("position_sizing_note", ""),
            "risk_reward_target": strategy.get("risk_reward_target", 2.0),
            "conviction_calibration": strategy.get("conviction_calibration", "untested"),
            "holding_period_target": strategy.get("holding_period_target", "unknown"),
            "sector_focus": strategy.get("sector_focus", []),
            "sector_avoid": strategy.get("sector_avoid", [])
        },
        "prediction_stats": {
            "total": pred_total,
            "open": pred_open,
            "correct": pred_correct,
            "wrong": pred_wrong,
            "accuracy": round(pred_correct / (pred_correct + pred_wrong) * 100, 1) if (pred_correct + pred_wrong) > 0 else None
        },
        "notes_to_future": notes,
        "collisions": collisions,
        "active_theses": theses,
        "trades": trades,
        "predictions": predictions,
        "inner_voice": inner_voice,
        "thoughts": thoughts,
        "memory": memory,
        "market": market,
        "lessons": lessons
    }

    # Atomic write
    out_path = OUTPUT / "dashboard-data.json"
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(dashboard_data, indent=2))
    os.replace(str(tmp), str(out_path))

    print("[update-dashboard] Dashboard data compiled — cycle {}".format(cycle))

if __name__ == "__main__":
    main()
