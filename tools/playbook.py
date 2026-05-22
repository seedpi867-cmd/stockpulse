#!/usr/bin/env python3
"""Playbook runner — executes structured actions from LLM output.

The LLM writes ACTION lines. This script parses and executes them.
No regex gymnastics. Simple, deterministic.

Supported actions:
  ACTION: BUY <ticker> <shares> <stop> <target>
  ACTION: SELL <ticker>
  ACTION: SHORT <ticker> <shares> <stop> <target>
  ACTION: COVER <ticker>
  ACTION: WATCH <ticker> <reason>
  ACTION: ADD_WATCHLIST <ticker>
  ACTION: PREDICT <direction> <ticker> <deadline> <conviction>
"""
import json, sys, re, os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTEXT = ROOT / "context"

TICKER_ALIASES = {
    "BTC": "BTC-USD", "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD", "ETHEREUM": "ETH-USD",
    "GOLD": "GC=F", "OIL": "CL=F", "CRUDE": "CL=F",
    "SILVER": "SI=F",
    "EURUSD": "EURUSD=X", "USDJPY": "USDJPY=X",
    "GBPUSD": "GBPUSD=X", "AUDUSD": "AUDUSD=X",
}

def resolve(ticker):
    return TICKER_ALIASES.get(ticker.upper(), ticker.upper())

def load_json(path, default=None):
    try: return json.loads(path.read_text())
    except: return default or {}

def save_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(str(tmp), str(path))

def get_price(ticker):
    cache = load_json(DATA / "price_cache.json")
    t = resolve(ticker)
    if t in cache and isinstance(cache[t], dict):
        return cache[t].get("price")
    return None

def execute_buy(ticker, shares, stop, target, portfolio, reasoning=""):
    t = resolve(ticker)
    price = get_price(t)
    if not price:
        return False, "No price for %s" % t

    cost = shares * price
    if cost > portfolio.get("cash", 0):
        return False, "Need $%.0f, have $%.0f" % (cost, portfolio.get("cash", 0))

    if not stop:
        return False, "Stop required"

    # Check if already holding — add to position instead of rejecting
    for p in portfolio.get("positions", []):
        if p["ticker"] == t and p["direction"] == "long":
            # Average in: weighted average entry price
            old_cost = p["shares"] * p["entry_price"]
            new_cost = shares * price
            total_shares = p["shares"] + shares
            if new_cost > portfolio.get("cash", 0):
                return False, "Need $%.0f to add, have $%.0f" % (new_cost, portfolio.get("cash", 0))
            p["entry_price"] = round((old_cost + new_cost) / total_shares, 2)
            p["shares"] = total_shares
            p["stop"] = stop
            p["target"] = target
            p["current_price"] = price
            p["unrealized_pnl"] = round((price - p["entry_price"]) * total_shares, 2)
            p["unrealized_pnl_pct"] = round((price - p["entry_price"]) / p["entry_price"] * 100, 2)
            portfolio["cash"] -= new_cost

            trade = {"cycle": int((DATA / "cycle.txt").read_text().strip()), "action": "ADD", "ticker": t,
                     "shares": shares, "total_shares": total_shares, "price": price, "direction": "long",
                     "stop": stop, "target": target, "avg_entry": p["entry_price"],
                     "reasoning": reasoning[:300], "timestamp": datetime.now().isoformat(), "pnl": None}
            with open(str(DATA / "trades.jsonl"), "a") as f:
                f.write(json.dumps(trade) + "\n")

            save_json(DATA / "portfolio.json", portfolio)
            return True, "ADDED %s %.0f @ $%.2f (now %.0f shares, avg $%.2f, stop $%.2f, target $%.2f)" % (
                t, shares, price, total_shares, p["entry_price"], stop, target)

    # New position
    portfolio["cash"] -= cost
    portfolio.setdefault("positions", []).append({
        "ticker": t,
        "shares": shares,
        "entry_price": price,
        "direction": "long",
        "entry_cycle": int((DATA / "cycle.txt").read_text().strip()),
        "entry_time": datetime.now().isoformat(),
        "stop": stop,
        "target": target,
        "conviction": 0.6,
        "reasoning": reasoning[:300],
        "current_price": price,
        "unrealized_pnl": 0,
        "unrealized_pnl_pct": 0,
    })

    # Log trade
    trade = {"cycle": int((DATA / "cycle.txt").read_text().strip()), "action": "BUY", "ticker": t,
             "shares": shares, "price": price, "direction": "long", "stop": stop, "target": target,
             "reasoning": reasoning[:300], "timestamp": datetime.now().isoformat(), "pnl": None}
    with open(str(DATA / "trades.jsonl"), "a") as f:
        f.write(json.dumps(trade) + "\n")

    save_json(DATA / "portfolio.json", portfolio)
    return True, "BOUGHT %s %.4f @ $%.2f (stop $%.2f, target $%.2f)" % (t, shares, price, stop, target)

def execute_sell(ticker, portfolio, reasoning=""):
    t = resolve(ticker)
    positions = portfolio.get("positions", [])
    for i, p in enumerate(positions):
        if p["ticker"] == t and p["direction"] == "long":
            price = get_price(t) or p["entry_price"]
            pnl = (price - p["entry_price"]) * p["shares"]
            portfolio["cash"] += p["shares"] * price
            positions.pop(i)

            trade = {"cycle": int((DATA / "cycle.txt").read_text().strip()), "action": "SELL", "ticker": t,
                     "shares": p["shares"], "price": price, "direction": "long",
                     "reasoning": reasoning[:300], "timestamp": datetime.now().isoformat(),
                     "pnl": round(pnl, 2), "pnl_pct": round(pnl / (p["entry_price"] * p["shares"]) * 100, 2)}
            with open(str(DATA / "trades.jsonl"), "a") as f:
                f.write(json.dumps(trade) + "\n")

            save_json(DATA / "portfolio.json", portfolio)
            return True, "SOLD %s %.4f @ $%.2f (P&L $%.2f)" % (t, p["shares"], price, pnl)
    return False, "No long position in %s" % t

def execute_short(ticker, shares, stop, target, portfolio, reasoning=""):
    t = resolve(ticker)
    price = get_price(t)
    if not price:
        return False, "No price for %s" % t
    if not stop:
        return False, "Stop required"

    # Check if already holding short — add to position
    for p in portfolio.get("positions", []):
        if p["ticker"] == t and p["direction"] == "short":
            old_margin = p["shares"] * p["entry_price"]
            new_margin = shares * price
            total_shares = p["shares"] + shares
            if new_margin > portfolio.get("cash", 0):
                return False, "Need $%.0f margin to add, have $%.0f" % (new_margin, portfolio.get("cash", 0))
            p["entry_price"] = round((old_margin + new_margin) / total_shares, 2)
            p["shares"] = total_shares
            p["stop"] = stop
            p["target"] = target
            p["current_price"] = price
            p["unrealized_pnl"] = round((p["entry_price"] - price) * total_shares, 2)
            p["unrealized_pnl_pct"] = round((p["entry_price"] - price) / p["entry_price"] * 100, 2)
            portfolio["cash"] -= new_margin

            trade = {"cycle": int((DATA / "cycle.txt").read_text().strip()), "action": "ADD_SHORT", "ticker": t,
                     "shares": shares, "total_shares": total_shares, "price": price, "direction": "short",
                     "stop": stop, "target": target, "avg_entry": p["entry_price"],
                     "reasoning": reasoning[:300], "timestamp": datetime.now().isoformat(), "pnl": None}
            with open(str(DATA / "trades.jsonl"), "a") as f:
                f.write(json.dumps(trade) + "\n")

            save_json(DATA / "portfolio.json", portfolio)
            return True, "ADDED SHORT %s %.0f @ $%.2f (now %.0f shares, avg $%.2f, stop $%.2f, target $%.2f)" % (
                t, shares, price, total_shares, p["entry_price"], stop, target)

    # New short position
    margin = shares * price
    if margin > portfolio.get("cash", 0):
        return False, "Need $%.0f margin, have $%.0f" % (margin, portfolio.get("cash", 0))

    portfolio["cash"] -= margin
    portfolio.setdefault("positions", []).append({
        "ticker": t, "shares": shares, "entry_price": price, "direction": "short",
        "entry_cycle": int((DATA / "cycle.txt").read_text().strip()),
        "entry_time": datetime.now().isoformat(),
        "stop": stop, "target": target, "conviction": 0.6, "reasoning": reasoning[:300],
        "current_price": price, "unrealized_pnl": 0, "unrealized_pnl_pct": 0,
    })

    trade = {"cycle": int((DATA / "cycle.txt").read_text().strip()), "action": "SHORT", "ticker": t,
             "shares": shares, "price": price, "direction": "short", "stop": stop, "target": target,
             "reasoning": reasoning[:300], "timestamp": datetime.now().isoformat(), "pnl": None}
    with open(str(DATA / "trades.jsonl"), "a") as f:
        f.write(json.dumps(trade) + "\n")

    save_json(DATA / "portfolio.json", portfolio)
    return True, "SHORTED %s %.4f @ $%.2f (stop $%.2f, target $%.2f)" % (t, shares, price, stop, target)

def execute_cover(ticker, portfolio, reasoning=""):
    t = resolve(ticker)
    positions = portfolio.get("positions", [])
    for i, p in enumerate(positions):
        if p["ticker"] == t and p["direction"] == "short":
            price = get_price(t) or p["entry_price"]
            pnl = (p["entry_price"] - price) * p["shares"]
            portfolio["cash"] += p["shares"] * p["entry_price"] + pnl
            positions.pop(i)

            trade = {"cycle": int((DATA / "cycle.txt").read_text().strip()), "action": "COVER", "ticker": t,
                     "shares": p["shares"], "price": price, "direction": "short",
                     "reasoning": reasoning[:300], "timestamp": datetime.now().isoformat(),
                     "pnl": round(pnl, 2)}
            with open(str(DATA / "trades.jsonl"), "a") as f:
                f.write(json.dumps(trade) + "\n")

            save_json(DATA / "portfolio.json", portfolio)
            return True, "COVERED %s %.4f @ $%.2f (P&L $%.2f)" % (t, p["shares"], price, pnl)
    return False, "No short position in %s" % t

def execute_add_watchlist(ticker):
    t = resolve(ticker)
    wl = load_json(DATA / "watchlist.json", {"tickers": [], "added_by_agent": []})
    added = wl.get("added_by_agent", [])
    if t not in added and t not in wl.get("tickers", []):
        added.append(t)
        wl["added_by_agent"] = added
        save_json(DATA / "watchlist.json", wl)
        return True, "Added %s to watchlist" % t
    return True, "%s already in watchlist" % t

def execute_predict(direction, ticker, deadline, conviction, reasoning=""):
    t = resolve(ticker)
    ref_price = get_price(t)
    pred = {
        "prediction": "%s %s by %s" % (t, "up" if direction == "long" else "down", deadline),
        "direction": direction, "ticker": t, "conviction": conviction,
        "deadline": deadline, "reasoning": reasoning[:300],
        "cycle": int((DATA / "cycle.txt").read_text().strip()),
        "timestamp": datetime.now().isoformat(),
        "was_correct": None,
        "reference_price": ref_price,
    }
    with open(str(DATA / "predictions.jsonl"), "a") as f:
        f.write(json.dumps(pred) + "\n")
    return True, "PREDICTED: %s" % pred["prediction"]

def parse_action_line(line, portfolio):
    """Parse any ACTION line format the LLM might produce.

    Handles:
      Clean:      BUY FCX 246 57.80 65.50
      Labeled:    BUY FCX 246 stop 57.80 target 65.50
      Dollar:     BUY FCX 246 stop $57.80 target $65.50
      Percent:    BUY FCX allocation=15% stop=-5% target=+7.5%
      Mixed:      BUY FCX 180 shares stop -6.0% target +9.5%

    Returns (cmd, ticker, shares, stop, target) or None if unparseable.
    shares/stop/target are absolute dollar values (percentages resolved).
    """
    raw = line[7:].strip() if line.startswith("ACTION:") else line.strip()
    parts = raw.split()
    if len(parts) < 2:
        return None

    cmd = parts[0].upper()
    ticker = parts[1].upper()
    rest = raw[len(parts[0]):].strip()
    rest = rest[len(parts[1]):].strip()  # everything after ticker

    # For SELL/COVER/WATCH/ADD_WATCHLIST — no numbers needed
    if cmd in ("SELL", "COVER", "WATCH", "ADD_WATCHLIST"):
        return (cmd, ticker, 0, 0, 0)

    # For PREDICT — special format
    if cmd == "PREDICT":
        return (cmd, ticker, 0, 0, 0)

    # Need price for percentage resolution
    price = get_price(resolve(ticker))
    cash = portfolio.get("cash", 0)

    # Extract key=value pairs (allocation=15%, stop=-5%, target=+7.5%)
    kv = {}
    for m in re.finditer(r'(allocation|stop|target|shares|entry|size)\s*[=:]\s*([+\-]?[$]?[\d.]+%?)', rest, re.IGNORECASE):
        kv[m.group(1).lower()] = m.group(2)

    # Also look for "stop X%" or "stop $X" or "stop -X%" patterns without = sign
    for m in re.finditer(r'\b(stop|target)\s+([+\-]?[$]?[\d.]+%?)', rest, re.IGNORECASE):
        key = m.group(1).lower()
        if key not in kv:
            kv[key] = m.group(2)

    # Also look for "X% allocation" pattern
    alloc_m = re.search(r'(\d+(?:\.\d+)?)\s*%\s*allocation', rest, re.IGNORECASE)
    if alloc_m and 'allocation' not in kv:
        kv['allocation'] = alloc_m.group(1) + '%'

    # Extract all plain numbers from the rest (stripping $, commas, %)
    nums = []
    for p in parts[2:]:
        clean = p.replace("$", "").replace(",", "").rstrip("%")
        # Skip if it's a label word
        try:
            nums.append(float(clean))
        except ValueError:
            continue

    def resolve_value(val_str, is_pct_relative_to_price=True):
        """Turn a string like '-5%', '$57.80', '+7.5%', '57.80' into a dollar value."""
        if val_str is None:
            return None
        s = val_str.replace("$", "").replace(",", "").strip()
        if s.endswith("%"):
            pct = float(s.rstrip("%")) / 100.0
            if price and is_pct_relative_to_price:
                if cmd == "SHORT":
                    # For shorts: stop above, target below
                    return round(price * (1 + pct), 2) if pct > 0 else round(price * (1 + pct), 2)
                return round(price * (1 + pct), 2)
            return None
        return float(s)

    # Resolve shares
    shares = None
    if "allocation" in kv or "size" in kv:
        alloc_str = kv.get("allocation") or kv.get("size")
        alloc_val = alloc_str.replace("$", "").replace(",", "").strip()
        if alloc_val.endswith("%") and price:
            pct = float(alloc_val.rstrip("%")) / 100.0
            shares = int((cash * pct) / price)
        else:
            try:
                shares = float(alloc_val)
            except ValueError:
                pass
    if "shares" in kv and shares is None:
        try:
            shares = float(kv["shares"].replace("$", "").rstrip("%"))
        except ValueError:
            pass

    # Resolve stop and target
    stop = resolve_value(kv.get("stop"))
    target = resolve_value(kv.get("target"))

    # If kv parsing didn't get everything, fall back to positional numbers
    if nums:
        # First number is shares if we don't have it yet
        if shares is None and nums:
            # If allocation was found via kv, shares is already set above
            # Otherwise check if number looks like share count or percentage
            if nums[0] >= 1 and (not price or nums[0] > 100 or nums[0] * price > cash * 0.005):
                # Looks like an actual share count
                shares = nums[0]
            elif price:
                # Small number — likely percentage allocation
                shares = int((cash * nums[0] / 100.0) / price)

        # Remaining numbers after shares for stop/target
        remaining = nums[1:] if (shares is not None and len(nums) > 0 and nums[0] == shares) else nums
        if stop is None and len(remaining) >= 1:
            val = remaining[0]
            # Is it a percentage (small abs value) or a dollar price?
            if abs(val) <= 20 and price and price > 20:
                # Percentage — negative means below price for BUY stop
                stop = round(price * (1 + val / 100.0), 2)
            else:
                stop = abs(val)
        if target is None and len(remaining) >= 2:
            val = remaining[1]
            if abs(val) <= 20 and price and price > 20:
                target = round(price * (1 + val / 100.0), 2)
            else:
                target = abs(val)

    # Default target if we have stop but no target
    if stop and not target and price:
        if cmd == "SHORT":
            risk = stop - price
            target = round(price - risk * 1.5, 2)
        else:
            risk = price - stop
            target = round(price + risk * 1.5, 2)

    # Default shares if we have price but no shares — use 10% of cash
    if shares is None and price:
        shares = int((cash * 0.10) / price)

    if not shares or shares <= 0:
        return None
    if not stop:
        return None

    return (cmd, ticker, float(int(shares)), stop, target or stop)


def run(cycle_log):
    """Parse ACTION lines from cycle log and execute them."""
    portfolio = load_json(DATA / "portfolio.json", {"cash": 100000, "positions": []})
    results = []

    for line in cycle_log.split("\n"):
        line = line.strip()
        if not line.startswith("ACTION:"):
            continue

        # Skip template/example/echoed lines
        if any(c in line for c in ['<', '>', '←', '→', '|']):
            continue
        if 'example' in line.lower() or 'format' in line.lower():
            continue
        parts = line[7:].strip().split()
        if len(parts) < 2:
            continue
        cmd = parts[0].upper()
        ticker = parts[1].upper() if len(parts) > 1 else ""
        if cmd == "VERB" or ticker == "TICKER":
            continue

        # Get reasoning from the next REASONING: line
        idx = cycle_log.find(line)
        reasoning = ""
        after = cycle_log[idx:idx+500]
        rm = re.search(r"REASONING:\s*(.+)", after)
        if rm:
            reasoning = rm.group(1).strip()

        parsed = parse_action_line(line, portfolio)
        if parsed is None:
            print("[playbook] SKIP: could not parse: %s" % line[:100])
            results.append("[playbook] SKIP: unparseable: %s" % line[:80])
            continue

        cmd, ticker, shares, stop, target = parsed

        if cmd == "BUY":
            ok, msg = execute_buy(ticker, shares, stop, target, portfolio, reasoning)
        elif cmd == "SELL":
            ok, msg = execute_sell(ticker, portfolio, reasoning)
        elif cmd == "SHORT":
            ok, msg = execute_short(ticker, shares, stop, target, portfolio, reasoning)
        elif cmd == "COVER":
            ok, msg = execute_cover(ticker, portfolio, reasoning)
        elif cmd == "WATCH":
            msg = "WATCHING: %s" % ticker
            ok = True
        elif cmd == "ADD_WATCHLIST":
            ok, msg = execute_add_watchlist(ticker)
        elif cmd == "PREDICT" and len(parts) >= 4:
            direction = parts[1].lower()
            pticker = parts[2]
            deadline = parts[3]
            conv = float(parts[4]) if len(parts) > 4 else 0.5
            ok, msg = execute_predict(direction, pticker, deadline, conv, reasoning)
        else:
            msg = "UNKNOWN: %s" % line[:80]
            ok = False

        status = "OK" if ok else "FAIL"
        results.append("[playbook] %s: %s" % (status, msg))
        print("[playbook] %s: %s" % (status, msg))

    # Write status
    if results:
        status_text = "# Playbook Results — Cycle\n\n" + "\n".join("- %s" % r for r in results)
        (CONTEXT / "trade-status.md").write_text(status_text + "\n")

    return results

if __name__ == "__main__":
    cycle = int((DATA / "cycle.txt").read_text().strip())
    # Prefer cleaned output (instruction echo + dedup already stripped)
    clean_file = DATA / "last-output.txt"
    if clean_file.exists() and clean_file.stat().st_size > 10:
        run(clean_file.read_text())
    else:
        log_file = DATA / "logs" / ("cycle_%d.log" % cycle)
        if log_file.exists():
            run(log_file.read_text())
        else:
            print("[playbook] No log for cycle %d" % cycle)
