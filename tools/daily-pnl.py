"""Daily P&L snapshot tool for Stockpulse. Runs each cycle, writes one entry per day."""
import json, os
from pathlib import Path
from datetime import datetime

ROOT = Path("/home/pi/stockpulse")
DATA = ROOT / "data"
SNAP_FILE = DATA / "daily-pnl.jsonl"

def main():
    portfolio = json.loads((DATA / "portfolio.json").read_text())
    perf = json.loads((DATA / "performance.json").read_text())
    cycle = int((DATA / "cycle.txt").read_text().strip())

    today = datetime.now().strftime("%Y-%m-%d")
    day_name = datetime.now().strftime("%A")

    # Calculate position values
    cache = {}
    try:
        cache = json.loads((DATA / "price_cache.json").read_text())
    except: pass

    positions = portfolio.get("positions", [])
    pos_value = 0
    pos_summary = []
    for p in positions:
        ticker = p["ticker"]
        price = cache.get(ticker, {}).get("price", p.get("current_price", p["entry_price"]))
        if p["direction"] == "short":
            pnl = (p["entry_price"] - price) * p["shares"]
            val = p["shares"] * p["entry_price"]
        else:
            pnl = (price - p["entry_price"]) * p["shares"]
            val = p["shares"] * price
        pos_value += val
        pos_summary.append({"ticker": ticker, "direction": p["direction"], "pnl": round(pnl, 2)})

    total_value = portfolio.get("cash", 0) + pos_value
    starting = portfolio.get("starting_capital", 100000)
    total_pnl = total_value - starting

    snap = {
        "date": today,
        "day": day_name,
        "cycle": cycle,
        "portfolio_value": round(total_value, 2),
        "cash": round(portfolio.get("cash", 0), 2),
        "total_pnl": round(total_pnl, 2),
        "positions": len(positions),
        "position_pnl": pos_summary,
        "closed_trades": perf.get("total_trades", 0),
        "realized_pnl": perf.get("total_pnl", 0),
    }

    # Check if we already have an entry for today — update it
    existing = []
    if SNAP_FILE.exists():
        for line in SNAP_FILE.read_text().strip().splitlines():
            try:
                entry = json.loads(line)
                if entry.get("date") != today:
                    existing.append(line)
            except:
                existing.append(line)

    existing.append(json.dumps(snap))

    SNAP_FILE.write_text("\n".join(existing) + "\n")
    print("[daily-pnl] %s C%d: $%.0f (PnL $%.2f)" % (today, cycle, total_value, total_pnl))

if __name__ == "__main__":
    main()
