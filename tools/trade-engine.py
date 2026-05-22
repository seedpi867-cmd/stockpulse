#!/usr/bin/env python3
"""Parse LLM output for trade intents — BUY, SELL, SHORT, COVER — validate and execute."""

# Ticker aliases — map common names to Yahoo Finance symbols
TICKER_ALIASES = {
    "BTC": "BTC-USD", "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD", "ETHEREUM": "ETH-USD",
    "GOLD": "GC=F", "OIL": "CL=F", "CRUDE": "CL=F",
    "SILVER": "SI=F",
    "EURUSD": "EURUSD=X", "USDJPY": "USDJPY=X",
    "GBPUSD": "GBPUSD=X", "AUDUSD": "AUDUSD=X",
    "SP500": "^GSPC", "FTSE": "^FTSE", "NIKKEI": "^N225",
    "DAX": "^GDAXI", "ASX": "^AXJO", "HANGSENG": "^HSI",
}

def resolve_ticker(ticker):
    """Resolve ticker aliases to canonical Yahoo Finance symbols."""
    t = ticker.upper().strip()
    return TICKER_ALIASES.get(t, t)

import sys, json, re, os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTEXT = ROOT / "context"

def load_json(path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    return default or {}

def save_json(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(str(tmp), str(path))

def load_config():
    config = {}
    cfg_path = ROOT / "config.sh"
    if cfg_path.exists():
        for line in cfg_path.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                # Strip inline comments
                if "#" in val:
                    val = val[:val.index("#")].strip()
                config[key.strip()] = val
    return config

def get_current_price(ticker):
    cache = DATA / "price_cache.json"
    if cache.exists():
        data = json.loads(cache.read_text())
        if ticker in data:
            return data[ticker]["price"]
    return None

def parse_trades(cycle_log):
    """Parse TRADE blocks from LLM output. Supports BUY, SELL, SHORT, COVER."""
    trades = []
    # Match: TRADE: BUY/SELL/SHORT/COVER TICKER SHARES shares @ PRICE
    # Shares may be fractional (e.g. 0.01 BTC). Ticker may include hyphen (BTC-USD).
    pattern = r'TRADE:\s*(BUY|SELL|SHORT|COVER)\s+([\w\-^=]+)\s+(\d+(?:\.\d+)?)\s+shares?\s*@?\s*\$?([\d.]+)?'
    for match in re.finditer(pattern, cycle_log, re.IGNORECASE):
        action = match.group(1).upper()
        ticker = resolve_ticker(match.group(2).upper())
        shares_str = match.group(3)
        shares = float(shares_str) if "." in shares_str else int(shares_str)
        price = float(match.group(4)) if match.group(4) else None

        block_start = match.start()
        block_end = cycle_log.find("\n\n", block_start)
        if block_end == -1:
            block_end = len(cycle_log)
        block = cycle_log[block_start:block_end]

        conviction = 0.5
        stop = None
        target = None
        reasoning = ""
        timeframe = ""

        for line in block.splitlines():
            line = line.strip()
            if line.startswith("CONVICTION:"):
                try: conviction = float(re.search(r'[\d.]+', line.split(":")[1]).group())
                except: pass
            elif line.startswith("STOP:"):
                try: stop = float(re.search(r'[\d.]+', line.split(":")[1]).group())
                except: pass
            elif line.startswith("TARGET:"):
                try: target = float(re.search(r'[\d.]+', line.split(":")[1]).group())
                except: pass
            elif line.startswith("REASONING:"):
                reasoning = line.split(":", 1)[1].strip()[:150]
            elif line.startswith("TIMEFRAME:"):
                timeframe = line.split(":", 1)[1].strip()

        trades.append({
            "action": action,
            "ticker": ticker,
            "shares": shares,
            "price": price,
            "conviction": conviction,
            "stop": stop,
            "target": target,
            "reasoning": reasoning,
            "timeframe": timeframe
        })
    return trades

def validate_trade(trade, portfolio, config, cycle):
    """Validate trade against risk rules. Returns (ok, reason)."""
    ticker = trade["ticker"]
    action = trade["action"]
    watchlist = [t.strip() for t in config.get("WATCHLIST", "").split(",")]

    # Watchlist check removed — agent can trade anything
    # return False, "Ticker {} not in watchlist".format(ticker)

    price = trade["price"] or get_current_price(ticker)
    if price is None:
        return False, "No price available for {}".format(ticker)
    trade["price"] = price

    positions = portfolio.get("positions", [])
    cash = portfolio.get("cash", 0)
    max_pos = int(config.get("MAX_POSITIONS", 5))
    max_pct = float(config.get("MAX_POSITION_PCT", 10))

    # Calculate portfolio value
    portfolio_value = cash
    for p in positions:
        cp = get_current_price(p["ticker"])
        if cp:
            if p.get("direction") == "short":
                portfolio_value += p["shares"] * p["entry_price"]  # margin held
            else:
                portfolio_value += p["shares"] * cp
    if portfolio_value <= 0:
        portfolio_value = cash

    if action == "BUY":
        if len(positions) >= max_pos:
            return False, "Max positions ({})".format(max_pos)
        trade_amount = trade["shares"] * price
        max_amount = portfolio_value * (max_pct / 100.0)
        if trade_amount > max_amount:
            return False, "Size ${:.0f} > {}% limit ${:.0f}".format(trade_amount, max_pct, max_amount)
        if trade_amount > cash:
            return False, "Need ${:.0f}, have ${:.0f}".format(trade_amount, cash)
        if trade["stop"] is None:
            return False, "Stop loss required"
        for p in positions:
            if p["ticker"] == ticker:
                return False, "Already holding {}".format(ticker)

    elif action == "SHORT":
        if len(positions) >= max_pos:
            return False, "Max positions ({})".format(max_pos)
        # Short selling: margin requirement = position value
        margin = trade["shares"] * price
        max_amount = portfolio_value * (max_pct / 100.0)
        if margin > max_amount:
            return False, "Short size ${:.0f} > {}% limit ${:.0f}".format(margin, max_pct, max_amount)
        if margin > cash:
            return False, "Margin ${:.0f} > cash ${:.0f}".format(margin, cash)
        if trade["stop"] is None:
            return False, "Stop loss required for shorts"
        # Stop must be ABOVE entry for shorts
        if trade["stop"] <= price:
            # Auto-fix: agent might have set stop wrong direction
            pass  # Allow it, the agent should learn
        for p in positions:
            if p["ticker"] == ticker:
                return False, "Already positioned in {}".format(ticker)

    elif action == "SELL":
        held = None
        for p in positions:
            if p["ticker"] == ticker and p.get("direction", "long") == "long":
                held = p
                break
        if held is None:
            return False, "Not holding {} long".format(ticker)
        if trade["shares"] > held["shares"]:
            return False, "Selling {} but only hold {}".format(trade["shares"], held["shares"])

    elif action == "COVER":
        held = None
        for p in positions:
            if p["ticker"] == ticker and p.get("direction") == "short":
                held = p
                break
        if held is None:
            return False, "No short position in {} to cover".format(ticker)
        if trade["shares"] > held["shares"]:
            return False, "Covering {} but only short {}".format(trade["shares"], held["shares"])

    return True, "OK"

def execute_trade(trade, portfolio, cycle):
    """Execute a validated trade."""
    ticker = trade["ticker"]
    price = trade["price"]
    shares = trade["shares"]
    now = datetime.now().isoformat()

    if trade["action"] == "BUY":
        cost = shares * price
        portfolio["cash"] -= cost
        portfolio["positions"].append({
            "ticker": ticker,
            "shares": shares,
            "entry_price": price,
            "direction": "long",
            "entry_cycle": cycle,
            "entry_time": now,
            "stop": trade["stop"],
            "target": trade["target"],
            "conviction": trade["conviction"],
            "reasoning": trade["reasoning"]
        })

    elif trade["action"] == "SHORT":
        # Short: we receive cash from selling borrowed shares, but hold margin
        margin = shares * price
        portfolio["cash"] -= margin  # margin held
        portfolio["positions"].append({
            "ticker": ticker,
            "shares": shares,
            "entry_price": price,
            "direction": "short",
            "entry_cycle": cycle,
            "entry_time": now,
            "stop": trade["stop"],
            "target": trade["target"],
            "conviction": trade["conviction"],
            "reasoning": trade["reasoning"]
        })

    elif trade["action"] == "SELL":
        for i, p in enumerate(portfolio["positions"]):
            if p["ticker"] == ticker and p.get("direction", "long") == "long":
                entry = p["entry_price"]
                pnl = (price - entry) * shares
                portfolio["cash"] += shares * price
                trade["pnl"] = round(pnl, 2)
                trade["pnl_pct"] = round(((price - entry) / entry) * 100, 2)
                trade["entry_price"] = entry
                portfolio["positions"].pop(i)
                break

    elif trade["action"] == "COVER":
        for i, p in enumerate(portfolio["positions"]):
            if p["ticker"] == ticker and p.get("direction") == "short":
                entry = p["entry_price"]
                # Short P&L: profit when price drops (entry - cover price)
                pnl = (entry - price) * shares
                # Return margin + P&L
                margin = shares * entry
                portfolio["cash"] += margin + pnl
                trade["pnl"] = round(pnl, 2)
                trade["pnl_pct"] = round(((entry - price) / entry) * 100, 2)
                trade["entry_price"] = entry
                portfolio["positions"].pop(i)
                break

    # Append to trades.jsonl
    record = {
        "cycle": cycle,
        "action": trade["action"],
        "ticker": ticker,
        "shares": shares,
        "price": price,
        "direction": "short" if trade["action"] in ("SHORT", "COVER") else "long",
        "conviction": trade["conviction"],
        "stop": trade["stop"],
        "target": trade["target"],
        "reasoning": trade["reasoning"],
        "timeframe": trade.get("timeframe", ""),
        "timestamp": now,
        "pnl": trade.get("pnl"),
        "pnl_pct": trade.get("pnl_pct")
    }
    with open(str(DATA / "trades.jsonl"), "a") as f:
        f.write(json.dumps(record) + "\n")

    save_json(DATA / "portfolio.json", portfolio)
    return record

def parse_predictions(cycle_log, cycle):
    """Parse PREDICTION blocks."""
    predictions = []
    pattern = r'PREDICTION:\s*(.+?)(?:\n|$)'
    for match in re.finditer(pattern, cycle_log):
        block_start = match.start()
        block_end = cycle_log.find("\n\n", block_start)
        if block_end == -1:
            block_end = len(cycle_log)
        block = cycle_log[block_start:block_end]

        pred = {
            "cycle": cycle,
            "prediction": match.group(1).strip(),
            "direction": "unknown",
            "conviction": 0.5,
            "reasoning": "",
            "deadline": "",
            "outcome": None,
            "resolved_at": None,
            "was_correct": None,
            "post_mortem": None,
            "timestamp": datetime.now().isoformat()
        }

        for line in block.splitlines():
            line = line.strip()
            if line.startswith("DIRECTION:"):
                pred["direction"] = line.split(":")[1].strip().lower()
            elif line.startswith("CONVICTION:"):
                try: pred["conviction"] = float(re.search(r'[\d.]+', line.split(":")[1]).group())
                except: pass
            elif line.startswith("REASONING:"):
                pred["reasoning"] = line.split(":", 1)[1].strip()
            elif line.startswith("DEADLINE:"):
                pred["deadline"] = line.split(":", 1)[1].strip()

        predictions.append(pred)
    return predictions

def main():
    cycle_file = DATA / "cycle.txt"
    if not cycle_file.exists():
        print("[trade-engine] No cycle.txt")
        return

    cycle = int(cycle_file.read_text().strip())
    log_file = DATA / "logs" / "cycle_{}.log".format(cycle)
    if not log_file.exists():
        print("[trade-engine] No log for cycle {}".format(cycle))
        return

    cycle_log = log_file.read_text()
    config = load_config()
    portfolio = load_json(DATA / "portfolio.json", {
        "cash": 100000, "positions": [], "started_at": "2026-05-08",
        "starting_capital": 100000, "high_water_mark": 100000
    })

    # Process trades
    trades = parse_trades(cycle_log)
    status_lines = []

    for trade in trades:
        ok, reason = validate_trade(trade, portfolio, config, cycle)
        if ok:
            record = execute_trade(trade, portfolio, cycle)
            msg = "EXECUTED: {} {} {} shares @ ${:.2f}".format(
                record["action"], record["ticker"], record["shares"], record["price"])
            if record.get("pnl") is not None:
                msg += " (P&L: ${:.2f})".format(record["pnl"])
            status_lines.append(msg)
            print("[trade-engine] {}".format(msg))
        else:
            status_lines.append("REJECTED: {} {} — {}".format(trade["action"], trade["ticker"], reason))
            print("[trade-engine] REJECTED: {} {} — {}".format(trade["action"], trade["ticker"], reason))

    # Process predictions
    predictions = parse_predictions(cycle_log, cycle)
    for pred in predictions:
        with open(str(DATA / "predictions.jsonl"), "a") as f:
            f.write(json.dumps(pred) + "\n")
        status_lines.append("PREDICTION: {}".format(pred["prediction"][:80]))
        print("[trade-engine] Prediction: {}".format(pred["prediction"][:80]))

    # Write status for next cycle
    if status_lines:
        status = "# Trade Status — Cycle {}\n\n".format(cycle)
        for line in status_lines:
            status += "- {}\n".format(line)
        (CONTEXT / "trade-status.md").write_text(status)

    if not trades and not predictions:
        print("[trade-engine] No trades or predictions in cycle {}".format(cycle))

if __name__ == "__main__":
    main()
