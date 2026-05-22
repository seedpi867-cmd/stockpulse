#!/usr/bin/env python3
"""Self-review: analyze trading performance and evolve strategy."""
import sys, json, os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KNOWLEDGE = ROOT / "knowledge" / "lessons"
KNOWLEDGE.mkdir(parents=True, exist_ok=True)

def load_json(path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    return default or {}

def save_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(str(tmp), str(path))

def load_trades():
    trades_file = DATA / "trades.jsonl"
    if not trades_file.exists():
        return []
    trades = []
    for line in trades_file.read_text().strip().splitlines():
        try:
            trades.append(json.loads(line))
        except:
            pass
    return trades

def load_predictions():
    pred_file = DATA / "predictions.jsonl"
    if not pred_file.exists():
        return []
    preds = []
    for line in pred_file.read_text().strip().splitlines():
        try:
            preds.append(json.loads(line))
        except:
            pass
    return preds

def analyze(trades, predictions, strategy):
    """Perform deep self-analysis. Works with open positions + predictions, not just closed trades."""
    closed = [t for t in trades if t["action"] in ("SELL", "COVER") and t.get("pnl") is not None]
    opens = [t for t in trades if t["action"] in ("BUY", "SHORT") and t.get("pnl") is None]

    # Can review even with 0 closed trades if we have predictions or open positions
    if len(closed) < 1 and len(predictions) < 3 and len(opens) < 1:
        return None  # Not enough data

    analysis = {"generated": datetime.now().isoformat(), "trade_count": len(closed), "open_count": len(opens), "prediction_count": len(predictions)}

    # Open positions summary
    analysis["open_positions"] = []
    for t in opens:
        analysis["open_positions"].append({
            "ticker": t.get("ticker"), "action": t.get("action"),
            "entry_cycle": t.get("cycle"), "conviction": t.get("conviction")
        })

    # Prediction analysis
    resolved_preds = [p for p in predictions if p.get("outcome") is not None]
    correct_preds = [p for p in resolved_preds if p.get("was_correct")]
    open_preds = [p for p in predictions if p.get("outcome") is None]
    analysis["predictions_total"] = len(predictions)
    analysis["predictions_resolved"] = len(resolved_preds)
    analysis["predictions_correct"] = len(correct_preds)
    analysis["predictions_open"] = len(open_preds)
    analysis["prediction_accuracy"] = round(len(correct_preds) / len(resolved_preds) * 100, 1) if resolved_preds else None

    # Prediction conviction distribution
    if predictions:
        high_conv_preds = [p for p in predictions if (p.get("conviction") or 0) >= 0.7]
        low_conv_preds = [p for p in predictions if (p.get("conviction") or 0) < 0.7]
        analysis["high_conviction_predictions"] = len(high_conv_preds)
        analysis["low_conviction_predictions"] = len(low_conv_preds)

    # Direction bias
    long_preds = [p for p in predictions if p.get("direction") in ("long", "bullish")]
    short_preds = [p for p in predictions if p.get("direction") in ("short", "bearish")]
    analysis["direction_bias"] = "long" if len(long_preds) > len(short_preds) * 1.5 else "short" if len(short_preds) > len(long_preds) * 1.5 else "balanced"
    analysis["long_predictions"] = len(long_preds)
    analysis["short_predictions"] = len(short_preds)

    # Win rate (closed trades)
    wins = [t for t in closed if t["pnl"] > 0]
    losses = [t for t in closed if t["pnl"] <= 0]
    analysis["win_rate"] = round(len(wins) / len(closed) * 100, 1) if closed else 0

    # Conviction calibration
    high_conv = [t for t in closed if t.get("conviction", 0) >= 0.7]
    low_conv = [t for t in closed if t.get("conviction", 0) < 0.7]
    if high_conv:
        hc_wins = len([t for t in high_conv if t["pnl"] > 0])
        analysis["high_conviction_win_rate"] = round(hc_wins / len(high_conv) * 100, 1)
    if low_conv:
        lc_wins = len([t for t in low_conv if t["pnl"] > 0])
        analysis["low_conviction_win_rate"] = round(lc_wins / len(low_conv) * 100, 1)

    analysis["conviction_calibrated"] = (
        analysis.get("high_conviction_win_rate", 0) > analysis.get("low_conviction_win_rate", 0)
    )

    # Ticker performance
    by_ticker = defaultdict(list)
    for t in closed:
        by_ticker[t["ticker"]].append(t)
    analysis["ticker_performance"] = {}
    for ticker, ticker_trades in by_ticker.items():
        tw = len([t for t in ticker_trades if t["pnl"] > 0])
        analysis["ticker_performance"][ticker] = {
            "trades": len(ticker_trades),
            "wins": tw,
            "win_rate": round(tw / len(ticker_trades) * 100, 1),
            "total_pnl": round(sum(t["pnl"] for t in ticker_trades), 2)
        }

    # Stop loss analysis
    stop_outs = [t for t in closed if "STOP LOSS" in t.get("reasoning", "")]
    target_hits = [t for t in closed if "TARGET HIT" in t.get("reasoning", "")]
    analysis["stop_outs"] = len(stop_outs)
    analysis["target_hits"] = len(target_hits)

    # Average P&L
    analysis["avg_win"] = round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0
    analysis["avg_loss"] = round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0
    if analysis["avg_loss"] != 0:
        analysis["risk_reward_ratio"] = round(abs(analysis["avg_win"] / analysis["avg_loss"]), 2)
    else:
        analysis["risk_reward_ratio"] = float("inf")

    # Prediction accuracy
    resolved_preds = [p for p in predictions if p.get("outcome") is not None]
    correct_preds = [p for p in resolved_preds if p.get("was_correct")]
    analysis["prediction_accuracy"] = round(
        len(correct_preds) / len(resolved_preds) * 100, 1
    ) if resolved_preds else None

    return analysis

def generate_strategy_updates(analysis, current_strategy):
    """Generate concrete strategy changes based on analysis."""
    updates = {}
    evolved_rules = list(current_strategy.get("evolved_rules", []))

    # Conviction calibration
    if not analysis.get("conviction_calibrated", True):
        evolved_rules.append(
            "RULE: High conviction trades are not winning more than low conviction. "
            "Recalibrate — only mark 0.8+ conviction when 3+ signals align."
        )
        updates["position_sizing_note"] = "Reduce all position sizes to 5% until conviction calibrates"

    # Ticker-specific lessons
    best_ticker = None
    worst_ticker = None
    for ticker, perf in analysis.get("ticker_performance", {}).items():
        if perf["trades"] >= 2:
            if best_ticker is None or perf["win_rate"] > analysis["ticker_performance"][best_ticker]["win_rate"]:
                best_ticker = ticker
            if worst_ticker is None or perf["win_rate"] < analysis["ticker_performance"][worst_ticker]["win_rate"]:
                worst_ticker = ticker

    if best_ticker:
        focus = list(current_strategy.get("sector_focus", []))
        if best_ticker not in focus:
            focus.append(best_ticker)
        updates["sector_focus"] = focus

    if worst_ticker and analysis["ticker_performance"][worst_ticker]["win_rate"] < 33:
        avoid = list(current_strategy.get("sector_avoid", []))
        if worst_ticker not in avoid:
            avoid.append(worst_ticker)
        updates["sector_avoid"] = avoid
        evolved_rules.append(
            "RULE: {} win rate is {:.0f}%. Avoid until understanding improves.".format(
                worst_ticker, analysis["ticker_performance"][worst_ticker]["win_rate"])
        )

    # Risk/reward
    rr = analysis.get("risk_reward_ratio", 0)
    if rr < 1.5:
        evolved_rules.append(
            "RULE: Risk/reward ratio is {:.1f}. Need minimum 2:1. "
            "Widen targets or tighten stops.".format(rr)
        )

    # Stop loss pattern
    if analysis.get("stop_outs", 0) > analysis.get("target_hits", 0) * 2:
        evolved_rules.append(
            "RULE: Getting stopped out too often ({} stops vs {} targets). "
            "Either stops are too tight or entries are too early.".format(
                analysis["stop_outs"], analysis["target_hits"])
        )

    # Prediction-based insights
    if analysis.get("predictions_total", 0) > 5:
        bias = analysis.get("direction_bias", "balanced")
        if bias != "balanced":
            evolved_rules.append(
                "OBSERVATION: Direction bias is {} ({} long vs {} short predictions). Check if this matches the regime.".format(
                    bias, analysis.get("long_predictions", 0), analysis.get("short_predictions", 0)))

    # Open position assessment
    if analysis.get("open_count", 0) > 0:
        for pos in analysis.get("open_positions", []):
            evolved_rules.append(
                "POSITION REVIEW: {} {} from cycle {} (conv {}) — is the original thesis still intact?".format(
                    pos["action"], pos["ticker"], pos["entry_cycle"], pos["conviction"]))

    updates["evolved_rules"] = evolved_rules[-20:]

    # Build rating that reflects actual state
    closed_count = analysis.get("trade_count", 0)
    open_count = analysis.get("open_count", 0)
    pred_count = analysis.get("predictions_total", 0)
    wr = analysis.get("win_rate", 0)
    if closed_count > 0:
        updates["overall_rating"] = "active — {} closed ({:.0f}% win), {} open, {} predictions".format(
            closed_count, wr, open_count, pred_count)
    elif open_count > 0:
        updates["overall_rating"] = "deployed — {} open positions, {} predictions, building track record".format(
            open_count, pred_count)
    elif pred_count > 5:
        updates["overall_rating"] = "observing — {} predictions logged, building conviction before deploying capital".format(pred_count)
    else:
        updates["overall_rating"] = "newborn — not enough data"

    return updates

def write_lesson(analysis, cycle):
    """Write a permanent lesson file."""
    lesson_file = KNOWLEDGE / "review-cycle-{}.md".format(cycle)

    lines = ["# Self-Review — Cycle {}\n".format(cycle)]
    lines.append("Generated: {}\n".format(analysis["generated"]))

    lines.append("## Performance Summary")
    lines.append("- Total closed trades: {}".format(analysis["trade_count"]))
    lines.append("- Win rate: {}%".format(analysis.get("win_rate", "N/A")))
    lines.append("- Avg win: ${}".format(analysis.get("avg_win", 0)))
    lines.append("- Avg loss: ${}".format(analysis.get("avg_loss", 0)))
    lines.append("- Risk/Reward: {}".format(analysis.get("risk_reward_ratio", "N/A")))
    lines.append("- Stops hit: {} | Targets hit: {}".format(
        analysis.get("stop_outs", 0), analysis.get("target_hits", 0)))

    lines.append("\n## Predictions")
    lines.append("- Total predictions: {}".format(analysis.get("predictions_total", 0)))
    lines.append("- Resolved: {} | Correct: {} | Accuracy: {}%".format(
        analysis.get("predictions_resolved", 0), analysis.get("predictions_correct", 0),
        analysis.get("prediction_accuracy", "N/A")))
    lines.append("- Open: {}".format(analysis.get("predictions_open", 0)))
    lines.append("- Direction bias: {} ({} long, {} short)".format(
        analysis.get("direction_bias", "?"), analysis.get("long_predictions", 0), analysis.get("short_predictions", 0)))

    lines.append("\n## Open Positions")
    for pos in analysis.get("open_positions", []):
        lines.append("- {} {} from cycle {} (conviction {})".format(
            pos["action"], pos["ticker"], pos["entry_cycle"], pos["conviction"]))

    lines.append("\n## Conviction Calibration")
    lines.append("- High conviction (>=0.7) win rate: {}%".format(
        analysis.get("high_conviction_win_rate", "N/A")))
    lines.append("- Low conviction (<0.7) win rate: {}%".format(
        analysis.get("low_conviction_win_rate", "N/A")))
    lines.append("- Calibrated: {}".format(
        "YES" if analysis.get("conviction_calibrated") else "NO — conviction does not predict wins"))

    lines.append("\n## By Ticker")
    for ticker, perf in analysis.get("ticker_performance", {}).items():
        lines.append("- {}: {} trades, {}% win rate, P&L ${}".format(
            ticker, perf["trades"], perf["win_rate"], perf["total_pnl"]))

    if analysis.get("prediction_accuracy") is not None:
        lines.append("\n## Prediction Accuracy")
        lines.append("- {}% of predictions were correct".format(analysis["prediction_accuracy"]))

    lesson_file.write_text("\n".join(lines) + "\n")
    print("[self-review] Lesson written: {}".format(lesson_file.name))

def main():
    cycle_file = DATA / "cycle.txt"
    cycle = int(cycle_file.read_text().strip()) if cycle_file.exists() else 0

    trades = load_trades()
    predictions = load_predictions()
    strategy = load_json(DATA / "strategy.json", {})

    analysis = analyze(trades, predictions, strategy)
    if analysis is None:
        print("[self-review] Not enough trades to review yet")
        return

    # Generate strategy updates
    updates = generate_strategy_updates(analysis, strategy)

    # Update strategy
    strategy.update(updates)
    strategy["last_review_cycle"] = cycle
    strategy["lessons_count"] = strategy.get("lessons_count", 0) + 1
    save_json(DATA / "strategy.json", strategy)

    # Write permanent lesson
    write_lesson(analysis, cycle)

    print("[self-review] Review complete. Strategy updated. {} evolved rules.".format(
        len(strategy.get("evolved_rules", []))))

if __name__ == "__main__":
    main()
