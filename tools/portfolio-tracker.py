#!/usr/bin/env python3
"""Track portfolio P&L, check stops/targets for both long and short positions."""
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
            unrealized = (entry - price) * shares  # profit when price drops
        else:
            unrealized = (price - entry) * shares

        unrealized_pct = (unrealized / (entry * shares)) * 100 if entry else 0
        pos["current_price"] = price
        pos["unrealized_pnl"] = round(unrealized, 2)
        pos["unrealized_pnl_pct"] = round(unrealized_pct, 2)

        # Stop loss check
        if pos.get("stop"):
            stop_hit = False
            if is_short and price >= pos["stop"]:
                stop_hit = True  # short stop = price went UP past stop
            elif not is_short and price <= pos["stop"]:
                stop_hit = True  # long stop = price went DOWN past stop

            if stop_hit:
                if is_short:
                    pnl = (entry - pos["stop"]) * shares
                    margin = shares * entry
                    cash += margin + pnl  # return margin + P&L
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
                target_hit = True  # short target = price dropped to target
            elif not is_short and price >= pos["target"]:
                target_hit = True  # long target = price rose to target

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
                # Short: margin held + unrealized P&L
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
        "streak": streak,
        "streak_type": streak_type,
        "positions_open": len(remaining),
        "cash_available": round(cash, 2),
        "portfolio_value": portfolio_value,
        "cycles_run": cycle,
        "last_updated": datetime.now().isoformat()
    })

    save_json(DATA / "performance.json", performance)
    print("[portfolio-tracker] Val: ${:.0f} | P&L: ${:.2f} | Pos: {} ({} short) | Closed: {}".format(
        portfolio_value, total_pnl, len(remaining),
        sum(1 for p in remaining if p.get("direction") == "short"),
        len(closed)))

if __name__ == "__main__":
    main()
