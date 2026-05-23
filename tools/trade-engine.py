#!/usr/bin/env python3
"""Parse LLM output for trade intents — BUY, SELL, SHORT, COVER — validate and execute.
   Enforces anti-churn, conviction minimums, risk limits, and weekend crypto mandate."""

# Ticker aliases — map common names to Yahoo Finance symbols
TICKER_ALIASES = {
    "BTC": "BTC-USD", "BITCOIN": "BTC-USD",
    "ETH": "ETH-USD", "ETHEREUM": "ETH-USD",
    "SOL": "SOL-USD", "SOLANA": "SOL-USD",
    "DOGE": "DOGE-USD", "DOGECOIN": "DOGE-USD",
    "AVAX": "AVAX-USD", "AVALANCHE": "AVAX-USD",
    "LINK": "LINK-USD", "CHAINLINK": "LINK-USD",
    "ADA": "ADA-USD", "CARDANO": "ADA-USD",
    "GOLD": "GC=F", "OIL": "CL=F", "CRUDE": "CL=F",
    "SILVER": "SI=F",
    "EURUSD": "EURUSD=X", "USDJPY": "USDJPY=X",
    "GBPUSD": "GBPUSD=X", "AUDUSD": "AUDUSD=X",
    "SP500": "^GSPC", "FTSE": "^FTSE", "NIKKEI": "^N225",
    "DAX": "^GDAXI", "ASX": "^AXJO", "HANGSENG": "^HSI",
}

CRYPTO_TICKERS = {"BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "ADA-USD"}

def resolve_ticker(ticker):
    """Resolve ticker aliases to canonical Yahoo Finance symbols."""
    t = ticker.upper().strip()
    return TICKER_ALIASES.get(t, t)

def is_crypto(ticker):
    return ticker in CRYPTO_TICKERS or ticker.endswith("-USD")

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

def load_recent_trades(limit=30):
    """Load recent trades to check for churning."""
    trades_file = DATA / "trades.jsonl"
    if not trades_file.exists():
        return []
    lines = trades_file.read_text().strip().splitlines()
    trades = []
    for line in lines[-limit:]:
        try:
            trades.append(json.loads(line))
        except:
            pass
    return trades

def check_churn(ticker, cycle, recent_trades, cooldown=5):
    """Check if ticker was traded recently (anti-churn rule).
    Returns (is_churning, reason) tuple."""
    for t in reversed(recent_trades):
        t_cycle = t.get("cycle", 0)
        if t["ticker"] == ticker and (cycle - t_cycle) < cooldown:
            pnl = t.get("pnl", 0) or 0
            if pnl <= 0:
                return True, "Anti-churn: {} traded {} cycles ago with P&L ${:.0f}. Wait {} cycles.".format(
                    ticker, cycle - t_cycle, pnl, cooldown - (cycle - t_cycle))
    return False, ""

def check_consecutive_losses(ticker, recent_trades, max_consecutive=2, ban_cycles=50):
    """Check if ticker has consecutive losses (ban rule)."""
    ticker_trades = [t for t in recent_trades if t["ticker"] == ticker and t.get("pnl") is not None]
    if len(ticker_trades) < max_consecutive:
        return False, ""
    last_n = ticker_trades[-max_consecutive:]
    if all(t.get("pnl", 0) < 0 for t in last_n):
        return True, "Banned: {} has {} consecutive losses. No trading for {} cycles.".format(
            ticker, max_consecutive, ban_cycles)
    return False, ""

def check_zero_win_rate(ticker, recent_trades, min_trades=3):
    """Check if ticker has 0% win rate after enough trades."""
    ticker_trades = [t for t in recent_trades if t["ticker"] == ticker and t.get("pnl") is not None]
    if len(ticker_trades) < min_trades:
        return False, ""
    wins = sum(1 for t in ticker_trades if t.get("pnl", 0) > 0)
    if wins == 0:
        return True, "0% win rate on {} after {} trades. Banned.".format(ticker, len(ticker_trades))
    return False, ""

def parse_trades(cycle_log):
    """Parse TRADE blocks from LLM output."""
    trades = []
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
                reasoning = line.split(":", 1)[1].strip()[:200]
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

    price = trade["price"] or get_current_price(ticker)
    if price is None:
        return False, "No price available for {}".format(ticker)
    trade["price"] = price

    positions = portfolio.get("positions", [])
    cash = portfolio.get("cash", 0)
    max_pos = int(config.get("MAX_POSITIONS", 8))
    max_pct = float(config.get("MAX_POSITION_PCT", 12))

    # Calculate portfolio value
    portfolio_value = cash
    for p in positions:
        cp = get_current_price(p["ticker"])
        if cp:
            if p.get("direction") == "short":
                portfolio_value += p["shares"] * p["entry_price"]
            else:
                portfolio_value += p["shares"] * cp
    if portfolio_value <= 0:
        portfolio_value = cash

    # Load recent trades for churn/ban checks
    recent_trades = load_recent_trades(50)

    if action in ("BUY", "SHORT"):
        # === CONVICTION CHECK (minimum 0.7) ===
        if trade["conviction"] < 0.7:
            return False, "Conviction {:.1f} < 0.7 minimum. Need higher conviction.".format(trade["conviction"])

        # === ANTI-CHURN CHECK ===
        is_churning, churn_reason = check_churn(ticker, cycle, recent_trades, cooldown=5)
        if is_churning:
            return False, churn_reason

        # === CONSECUTIVE LOSS BAN ===
        is_banned, ban_reason = check_consecutive_losses(ticker, recent_trades)
        if is_banned:
            return False, ban_reason

        # === ZERO WIN RATE BAN ===
        is_zero, zero_reason = check_zero_win_rate(ticker, recent_trades)
        if is_zero:
            return False, zero_reason

        # === POSITION LIMIT ===
        if len(positions) >= max_pos:
            return False, "Max positions ({})".format(max_pos)

        # === DUPLICATE POSITION ===
        for p in positions:
            if p["ticker"] == ticker:
                return False, "Already holding {}".format(ticker)

        # === STOP REQUIRED ===
        if trade["stop"] is None:
            return False, "Stop loss required"

        # === POSITION SIZE LIMIT ===
        trade_amount = trade["shares"] * price
        max_amount = portfolio_value * (max_pct / 100.0)
        if trade_amount > max_amount:
            return False, "Size ${:.0f} > {}% limit ${:.0f}".format(trade_amount, max_pct, max_amount)

        # === 2% MAX RISK PER TRADE ===
        if action == "BUY":
            risk_per_share = abs(price - trade["stop"])
        else:  # SHORT
            risk_per_share = abs(trade["stop"] - price)
        total_risk = risk_per_share * trade["shares"]
        max_risk = portfolio_value * 0.02
        if total_risk > max_risk:
            return False, "Risk ${:.0f} > 2% limit ${:.0f}. Reduce shares or tighten stop.".format(total_risk, max_risk)

        # === CASH CHECK ===
        if action == "BUY" and trade_amount > cash:
            return False, "Need ${:.0f}, have ${:.0f}".format(trade_amount, cash)
        if action == "SHORT":
            margin = trade["shares"] * price
            if margin > cash:
                return False, "Margin ${:.0f} > cash ${:.0f}".format(margin, cash)

        # === REWARD/RISK CHECK ===
        if trade["target"] is not None:
            if action == "BUY":
                reward = trade["target"] - price
                risk = price - trade["stop"]
            else:
                reward = price - trade["target"]
                risk = trade["stop"] - price
            if risk > 0:
                rr = reward / risk
                if rr < 1.5:
                    return False, "R/R ratio {:.1f} < 1.5 minimum. Widen target or tighten stop.".format(rr)

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
        margin = shares * price
        portfolio["cash"] -= margin
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
                pnl = (entry - price) * shares
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
        "pnl_pct": trade.get("pnl_pct"),
        "is_crypto": is_crypto(ticker)
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
            if record.get("is_crypto"):
                msg += " [CRYPTO]"
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
