#!/usr/bin/env python3
"""Track and resolve predictions using actual price data."""
import sys, json, re
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTEXT = ROOT / "context"

STALE_DAYS = 14  # auto-expire predictions with no deadline after this many days


def get_current_price(ticker):
    cache = DATA / "price_cache.json"
    if not cache.exists():
        return None
    data = json.loads(cache.read_text())
    if ticker in data and isinstance(data[ticker], dict):
        return data[ticker].get("price")
    return None


def parse_reference_price(text):
    """Try to extract a dollar amount from prediction text like 'below $733.30'."""
    m = re.search(r"\$(\d+\.?\d*)", text)
    if m:
        return float(m.group(1))
    return None


def check_direction(pred, current_price):
    """Check if prediction direction was correct given current price.
    Returns True (correct), False (wrong), or None (can't determine).
    """
    direction = pred.get("direction", "").lower()
    ref = pred.get("reference_price")
    if ref is None:
        ref = parse_reference_price(pred.get("prediction", ""))
    if ref is None or current_price is None:
        return None

    if direction in ("long", "bullish", "up"):
        return current_price > ref
    elif direction in ("short", "bearish", "down"):
        return current_price < ref
    return None


def main():
    pred_file = DATA / "predictions.jsonl"
    if not pred_file.exists():
        print("[prediction-tracker] No predictions file")
        return

    lines = pred_file.read_text().strip().splitlines()
    if not lines:
        print("[prediction-tracker] No predictions to check")
        return

    today = date.today()
    now = datetime.now()
    updated = []
    resolved_this_cycle = []

    for line in lines:
        try:
            pred = json.loads(line)
        except Exception:
            continue  # drop unparseable lines

        # Already resolved — keep as-is
        if pred.get("outcome") is not None:
            updated.append(json.dumps(pred))
            continue

        # Determine deadline
        deadline = None
        deadline_str = pred.get("deadline", "").strip()
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            except ValueError:
                pass

        # No deadline — auto-expire after STALE_DAYS from timestamp
        if deadline is None:
            ts = pred.get("timestamp", "")
            if ts:
                try:
                    created = datetime.fromisoformat(ts).date()
                    if (today - created).days > STALE_DAYS:
                        deadline = today - timedelta(days=1)  # force expired
                except (ValueError, TypeError):
                    pass

        # Not yet expired — keep open
        if deadline is None or today <= deadline:
            updated.append(json.dumps(pred))
            continue

        # Deadline has passed — try to resolve with price data
        ticker = pred.get("ticker", "")
        current_price = get_current_price(ticker) if ticker else None
        direction_correct = check_direction(pred, current_price)

        if direction_correct is True:
            pred["outcome"] = "correct"
            pred["was_correct"] = True
        elif direction_correct is False:
            pred["outcome"] = "wrong"
            pred["was_correct"] = False
        else:
            # Can't determine — default to expired/unknown
            pred["outcome"] = "expired"
            pred["was_correct"] = False

        pred["resolved_at"] = now.isoformat()
        if current_price is not None:
            pred["resolved_price"] = current_price
        resolved_this_cycle.append(pred)
        updated.append(json.dumps(pred))

    # Write updated predictions
    pred_file.write_text("\n".join(updated) + "\n" if updated else "")

    # Write resolution context for the agent
    if resolved_this_cycle:
        parts = ["# Prediction Resolutions\n"]
        for p in resolved_this_cycle[:10]:  # cap at 10 per cycle
            parts.append("## {}".format(p["prediction"][:80]))
            parts.append("- Outcome: {} | Direction: {} | Conviction: {}".format(
                p["outcome"], p.get("direction", "?"), p.get("conviction", "?")))
            ref = p.get("reference_price") or parse_reference_price(p.get("prediction", ""))
            rp = p.get("resolved_price")
            if ref and rp:
                parts.append("- Reference: ${:.2f} → Resolved: ${:.2f}".format(ref, rp))
            parts.append("")
        (CONTEXT / "prediction-resolutions.md").write_text("\n".join(parts))

    # Summary
    all_preds = []
    for line in updated:
        try:
            all_preds.append(json.loads(line))
        except Exception:
            pass

    open_preds = [p for p in all_preds if p.get("outcome") is None]
    correct = [p for p in all_preds if p.get("was_correct") is True]
    incorrect = [p for p in all_preds if p.get("was_correct") is False]
    total_resolved = len(correct) + len(incorrect)
    acc = round(len(correct) / total_resolved * 100, 1) if total_resolved > 0 else "N/A"

    print("[prediction-tracker] Open: {} | Correct: {} | Incorrect: {} | Accuracy: {}%".format(
        len(open_preds), len(correct), len(incorrect), acc))
    if resolved_this_cycle:
        print("[prediction-tracker] Resolved this cycle: {}".format(len(resolved_this_cycle)))


if __name__ == "__main__":
    main()
