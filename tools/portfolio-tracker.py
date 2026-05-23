#!/usr/bin/env python3
"""Track portfolio P&L, check stops/targets, AUTO-TRAIL winners, auto-exit stale losers."""
import sys, json, os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

def load_json(path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    return default or {}

def save_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(str(tmp), str(path))

def get_current_price(ticker):
    cache = DATA / "price_cache.json"
    if cache.exists():
        data = json.loads(cache.read_text())
        if ticker in data:
            return data[ticker]["price"]
    return None

def main():
    portfolio = load_json(DATA / "portfolio.json")
    if not portfolio:
        return

    performance = load_json(DATA / "performance.json", {})
    cycle_file = DATA / "cycle.txt"
    cycle = int(cycle_file.read_text().strip()) if cycle_file.exists() else 0

    positions = portfolio.get("positions", [])
    cash = portfolio.get("cash", 100000)
    starting = portfolio.get("starting_capital", 100000)

    closed = []
    remaining = []
    for pos in positions:
        ticker = pos["ticker"]
        price = get_current_price(ticker)
        if price is None:
            remaining.append(pos)
            continue

        entry = pos["entry_price"]
        shares = pos["shares"]
        is_short = pos.get("direction") == "short"

        # P&L calculation
        if is_short:
            unrealized = (entry - price) * shares
        else:
            unrealized = (price - entry) * shares

        unrealized_pct = (unrealized / (entry * shares)) * 100 if entry else 0
        pos["current_price"] = price
        pos["unrealized_pnl"] = round(unrealized, 2)
        pos["unrealized_pnl_pct"] = round(unrealized_pct, 2)

        # ═══════════════════════════════════════════════════
        # AUTO-TRAILING STOPS — lock in profits automatically
        # ═══════════════════════════════════════════════════
        trail_pct = pos.get("trail_pct")

        # AUTO-SET trail if position is profitable and no trail exists
        if not trail_pct and unrealized_pct > 1.0:
            # Up 1-3%: set 3% trail
            if unrealized_pct < 3.0:
                trail_pct = 0.03
            # Up 3-5%: set 2% trail
            elif unrealized_pct < 5.0:
                trail_pct = 0.02
            # Up 5%+: set 1.5% trail
            else:
                trail_pct = 0.015
            pos["trail_pct"] = trail_pct
            print("[portfolio-tracker] AUTO-TRAIL {}: up {:.1f}%, set {:.1f}% trail".format(
                ticker, unrealized_pct, trail_pct * 100))

        # Tighten existing trail as profit grows
        if trail_pct and unrealized_pct > 5.0 and trail_pct > 0.015:
            pos["trail_pct"] = 0.015
            trail_pct = 0.015
            print("[portfolio-tracker] TIGHTEN TRAIL {}: up {:.1f}%, trail now 1.5%".format(
                ticker, unrealized_pct))
        elif trail_pct and unrealized_pct > 3.0 and trail_pct > 0.02:
            pos["trail_pct"] = 0.02
            trail_pct = 0.02
            print("[portfolio-tracker] TIGHTEN TRAIL {}: up {:.1f}%, trail now 2%".format(
                ticker, unrealized_pct))

        # Execute trailing stop logic
        if trail_pct and trail_pct > 0:
            if is_short:
                low = pos.get("low_since_entry", entry)
                if price < low:
                    pos["low_since_entry"] = price
                    low = price
                new_stop = round(low * (1 + trail_pct), 2)
                if pos.get("stop") and new_stop < pos["stop"]:
                    print("[portfolio-tracker] TRAIL SHORT {}: stop {} -> {}".format(ticker, pos["stop"], new_stop))
                    pos["stop"] = new_stop
            else:
                high = pos.get("high_since_entry", entry)
                if price > high:
                    pos["high_since_entry"] = price
                    high = price
                new_stop = round(high * (1 - trail_pct), 2)
                if pos.get("stop") and new_stop > pos["stop"]:
                    print("[portfolio-tracker] TRAIL LONG {}: stop {} -> {}".format(ticker, pos["stop"], new_stop))
                    pos["stop"] = new_stop

        # ═══════════════════════════════════════════════════
        # AUTO-EXIT stale losers — if underwater for too many cycles
        # ═══════════════════════════════════════════════════
        entry_cycle = pos.get("entry_cycle", cycle)
        cycles_held = cycle - entry_cycle

        # If down >2% after 6+ cycles (30 min), auto-exit — thesis failed
        if unrealized_pct < -2.0 and cycles_held >= 6:
            if is_short:
                pnl = (entry - price) * shares
                margin = shares * entry
                cash += margin + pnl
                action = "COVER"
            else:
                pnl = (price - entry) * shares
                cash += shares * price
                action = "SELL"

            record = {
                "cycle": cycle, "action": action, "ticker": ticker,
                "shares": shares, "price": price,
                "direction": "short" if is_short else "long",
                "conviction": pos.get("conviction", 0),
                "reasoning": "AUTO-EXIT: down {:.1f}% after {} cycles. Thesis failed.".format(unrealized_pct, cycles_held),
                "pnl": round(pnl, 2),
                "pnl_pct": round(unrealized_pct, 2),
                "entry_price": entry,
                "timestamp": datetime.now().isoformat(),
                "auto_close": "stale_loser"
            }
            with open(str(DATA / "trades.jsonl"), "a") as f:
                f.write(json.dumps(record) + "\n")
            closed.append(record)
            print("[portfolio-tracker] AUTO-EXIT: {} {} at ${:.2f} — down {:.1f}% for {} cycles (P&L: ${:.2f})".format(
                action, ticker, price, unrealized_pct, cycles_held, pnl))
            continue

        # Stop loss check
        if pos.get("stop"):
            stop_hit = False
            if is_short and price >= pos["stop"]:
                stop_hit = True
            elif not is_short and price <= pos["stop"]:
                stop_hit = True

            if stop_hit:
                if is_short:
                    pnl = (entry - pos["stop"]) * shares
                    margin = shares * entry
                    cash += margin + pnl
                    action = "COVER"
                else:
                    pnl = (pos["stop"] - entry) * shares
                    cash += shares * pos["stop"]
                    action = "SELL"

                record = {
                    "cycle": cycle, "action": action, "ticker": ticker,
                    "shares": shares, "price": pos["stop"],
                    "direction": "short" if is_short else "long",
                    "conviction": pos.get("conviction", 0),
                    "reasoning": "STOP LOSS HIT at ${:.2f}".format(pos["stop"]),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round((pnl / (entry * shares)) * 100, 2) if entry else 0,
                    "entry_price": entry,
                    "timestamp": datetime.now().isoformat(),
                    "auto_close": "stop"
                }
                with open(str(DATA / "trades.jsonl"), "a") as f:
                    f.write(json.dumps(record) + "\n")
                closed.append(record)
                print("[portfolio-tracker] STOP: {} {} at ${:.2f} (P&L: ${:.2f})".format(
                    action, ticker, pos["stop"], pnl))
                continue

        # Target check
        if pos.get("target"):
            target_hit = False
            if is_short and price <= pos["target"]:
                target_hit = True
            elif not is_short and price >= pos["target"]:
                target_hit = True

            if target_hit:
                if is_short:
                    pnl = (entry - pos["target"]) * shares
                    margin = shares * entry
                    cash += margin + pnl
                    action = "COVER"
                else:
                    pnl = (pos["target"] - entry) * shares
                    cash += shares * pos["target"]
                    action = "SELL"

                record = {
                    "cycle": cycle, "action": action, "ticker": ticker,
                    "shares": shares, "price": pos["target"],
                    "direction": "short" if is_short else "long",
                    "conviction": pos.get("conviction", 0),
                    "reasoning": "TARGET HIT at ${:.2f}".format(pos["target"]),
                    "pnl": round(pnl, 2),
                    "pnl_pct": round((pnl / (entry * shares)) * 100, 2) if entry else 0,
                    "entry_price": entry,
                    "timestamp": datetime.now().isoformat(),
                    "auto_close": "target"
                }
                with open(str(DATA / "trades.jsonl"), "a") as f:
                    f.write(json.dumps(record) + "\n")
                closed.append(record)
                print("[portfolio-tracker] TARGET: {} {} at ${:.2f} (P&L: ${:.2f})".format(
                    action, ticker, pos["target"], pnl))
                continue

        remaining.append(pos)

    portfolio["positions"] = remaining
    portfolio["cash"] = round(cash, 2)

    # Calculate total portfolio value
    portfolio_value = cash
    for pos in remaining:
        p = get_current_price(pos["ticker"])
        if p:
            if pos.get("direction") == "short":
                margin = pos["shares"] * pos["entry_price"]
                pnl = (pos["entry_price"] - p) * pos["shares"]
                portfolio_value += margin + pnl
            else:
                portfolio_value += pos["shares"] * p
    portfolio_value = round(portfolio_value, 2)

    hwm = portfolio.get("high_water_mark", starting)
    if portfolio_value > hwm:
        portfolio["high_water_mark"] = portfolio_value

    save_json(DATA / "portfolio.json", portfolio)

    # Update performance stats
    all_closed = []
    trades_file = DATA / "trades.jsonl"
    if trades_file.exists():
        for line in trades_file.read_text().strip().splitlines():
            try:
                t = json.loads(line)
                if t.get("pnl") is not None and t["action"] in ("SELL", "COVER"):
                    all_closed.append(t)
            except: pass

    total_pnl = sum(t["pnl"] for t in all_closed)
    wins = [t for t in all_closed if t["pnl"] > 0]
    losses = [t for t in all_closed if t["pnl"] <= 0]
    total_trades = len(all_closed)
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0

    streak = 0
    streak_type = None
    for t in reversed(all_closed):
        if streak == 0:
            streak_type = "win" if t["pnl"] > 0 else "loss"
            streak = 1
        elif (t["pnl"] > 0 and streak_type == "win") or (t["pnl"] <= 0 and streak_type == "loss"):
            streak += 1
        else:
            break

    current_dd = 0
    if portfolio_value < hwm:
        current_dd = round(((hwm - portfolio_value) / hwm) * 100, 2)

    # Sharpe estimate (annualized from daily P&L)
    sharpe = 0
    pnl_file = DATA / "daily-pnl.jsonl"
    if pnl_file.exists():
        daily_returns = []
        for line in pnl_file.read_text().strip().splitlines()[-30:]:
            try:
                d = json.loads(line)
                v = d.get("portfolio_value", starting)
                daily_returns.append((v - starting) / starting)
            except: pass
        if len(daily_returns) >= 5:
            avg_ret = sum(daily_returns) / len(daily_returns)
            std_ret = (sum((r - avg_ret) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
            if std_ret > 0:
                sharpe = round((avg_ret / std_ret) * (252 ** 0.5), 2)

    performance.update({
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(((portfolio_value - starting) / starting) * 100, 2),
        "total_trades": total_trades,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "avg_win": round(sum(t["pnl"] for t in wins) / len(wins), 2) if wins else 0,
        "avg_loss": round(sum(t["pnl"] for t in losses) / len(losses), 2) if losses else 0,
        "best_trade": max((t["pnl"] for t in all_closed), default=None),
        "worst_trade": min((t["pnl"] for t in all_closed), default=None),
        "max_drawdown": max(current_dd, performance.get("max_drawdown", 0)),
        "current_drawdown": current_dd,
        "sharpe_estimate": sharpe,
        "streak": streak,
        "streak_type": streak_type,
        "positions_open": len(remaining),
        "cash_available": round(cash, 2),
        "portfolio_value": portfolio_value,
        "cycles_run": cycle,
        "last_updated": datetime.now().isoformat()
    })

    save_json(DATA / "performance.json", performance)
    print("[portfolio-tracker] Val: ${:.0f} | P&L: ${:.2f} | WR: {:.0f}% | Pos: {} | Closed: {} | Sharpe: {:.2f}".format(
        portfolio_value, total_pnl, win_rate, len(remaining), len(closed), sharpe))

if __name__ == "__main__":
    main()
