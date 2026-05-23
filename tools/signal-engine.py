#!/usr/bin/env python3
"""Signal Engine v2 — Pre-computes technical indicators, predictive signals, and setup scoring.

Runs BEFORE the LLM call. Outputs context/signals.md with:
- RSI-14, MACD, Bollinger Bands, ATR for all watchlist tickers
- Support/resistance levels from price history
- Momentum acceleration (2nd derivative — sees moves before they happen)
- Volume-price divergence detection (smart money tells)
- Cross-market leading indicators (BTC→altcoins, sector rotation)
- Correlation break detection (pairs that normally move together diverge)
- Market regime (trending/ranging/volatile)
- Scored and ranked trade setups (0-100)
- Anti-churn warnings (recent losers)
- Weekend crypto opportunities

This is the EDGE. The LLM sees pre-analyzed data instead of raw prices.
"""

import json, sys, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)

def load_json(path, default=None):
    try: return json.loads(path.read_text())
    except: return default or {}

def load_recent_trades(limit=50):
    trades_file = DATA / "trades.jsonl"
    if not trades_file.exists():
        return []
    lines = trades_file.read_text().strip().splitlines()
    trades = []
    for line in lines[-limit:]:
        try: trades.append(json.loads(line))
        except: pass
    return trades

def ticker_win_rate(ticker, trades):
    """Calculate win rate for a specific ticker from trade history."""
    closed = [t for t in trades if t.get("ticker") == ticker and t.get("pnl") is not None]
    if not closed:
        return None, 0
    wins = sum(1 for t in closed if t["pnl"] > 0)
    return round(wins / len(closed) * 100, 1), len(closed)

def recent_ticker_trades(ticker, trades, lookback=10):
    """Get recent trades on this ticker."""
    return [t for t in trades[-lookback:] if t.get("ticker") == ticker]

def is_weekend():
    utc = datetime.now(timezone.utc)
    et = utc - timedelta(hours=4)
    return et.weekday() >= 5 or (et.weekday() == 4 and et.hour >= 16)

def is_market_open():
    utc = datetime.now(timezone.utc)
    et = utc - timedelta(hours=4)
    if et.weekday() >= 5:
        return False
    return (et.hour > 9 or (et.hour == 9 and et.minute >= 30)) and et.hour < 16

def compute_rsi(closes, period=14):
    """Compute RSI from a list of closing prices."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [-min(d, 0) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 1)

def compute_ema(values, period):
    """Compute EMA from a list of values."""
    if len(values) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for val in values[period:]:
        ema = (val - ema) * multiplier + ema
    return ema

def compute_macd(closes):
    """Compute MACD line, signal line, and histogram."""
    if len(closes) < 26:
        return None, None, None
    ema12 = compute_ema(closes, 12)
    ema26 = compute_ema(closes, 26)
    if ema12 is None or ema26 is None:
        return None, None, None
    macd_line = ema12 - ema26
    macd_values = []
    for i in range(len(closes) - 26):
        subset = closes[:26 + i + 1]
        e12 = compute_ema(subset, 12)
        e26 = compute_ema(subset, 26)
        if e12 and e26:
            macd_values.append(e12 - e26)
    signal = compute_ema(macd_values, 9) if len(macd_values) >= 9 else None
    histogram = round(macd_line - signal, 4) if signal else None
    return round(macd_line, 4), round(signal, 4) if signal else None, histogram

def compute_bollinger(closes, period=20, std_mult=2):
    """Compute Bollinger Band position (0=lower band, 0.5=middle, 1=upper)."""
    if len(closes) < period:
        return None
    recent = closes[-period:]
    mean = sum(recent) / period
    variance = sum((x - mean) ** 2 for x in recent) / period
    std = variance ** 0.5
    if std == 0:
        return 0.5
    price = closes[-1]
    lower = mean - std_mult * std
    upper = mean + std_mult * std
    position = (price - lower) / (upper - lower) if upper != lower else 0.5
    return round(max(0, min(1, position)), 2)

# ═══════════════════════════════════════════════════
# ATR — Average True Range (volatility-based stops)
# ═══════════════════════════════════════════════════
def compute_atr(highs, lows, closes, period=14):
    """Compute ATR — the mathematically correct stop distance.
    Uses True Range = max(H-L, abs(H-prevC), abs(L-prevC))."""
    if len(closes) < period + 1 or len(highs) < period + 1:
        return None
    true_ranges = []
    for i in range(1, len(closes)):
        h = highs[i] if i < len(highs) else closes[i]
        l = lows[i] if i < len(lows) else closes[i]
        prev_c = closes[i - 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        true_ranges.append(tr)
    if len(true_ranges) < period:
        return None
    atr = sum(true_ranges[-period:]) / period
    return round(atr, 4)

def atr_stop_distance(price, atr, multiplier=2.0):
    """Calculate optimal stop distance using ATR.
    2x ATR = standard, 1.5x = tight for high-conviction, 3x = loose for volatile."""
    if atr is None or price == 0:
        return None, None
    stop_long = round(price - atr * multiplier, 2)
    stop_short = round(price + atr * multiplier, 2)
    return stop_long, stop_short

# ═══════════════════════════════════════════════════
# Support/Resistance from price history
# ═══════════════════════════════════════════════════
def compute_support_resistance(highs, lows, closes, num_levels=3):
    """Find key support/resistance levels from recent price pivots."""
    if len(closes) < 10:
        return [], []
    pivots_high = []
    pivots_low = []
    for i in range(2, len(closes) - 2):
        h = highs[i] if i < len(highs) else closes[i]
        l = lows[i] if i < len(lows) else closes[i]
        neighbors_h = [highs[j] if j < len(highs) else closes[j] for j in range(i-2, i+3) if j != i]
        neighbors_l = [lows[j] if j < len(lows) else closes[j] for j in range(i-2, i+3) if j != i]
        if h >= max(neighbors_h):
            pivots_high.append(h)
        if l <= min(neighbors_l):
            pivots_low.append(l)

    def cluster(levels, threshold_pct=0.5):
        if not levels:
            return []
        levels = sorted(levels)
        clusters = [[levels[0]]]
        for lv in levels[1:]:
            if abs(lv - clusters[-1][-1]) / clusters[-1][-1] * 100 < threshold_pct:
                clusters[-1].append(lv)
            else:
                clusters.append([lv])
        result = []
        for c in clusters:
            avg = sum(c) / len(c)
            result.append((round(avg, 2), len(c)))
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:num_levels]

    resistance = cluster(pivots_high)
    support = cluster(pivots_low)
    return support, resistance

# ═══════════════════════════════════════════════════
# Momentum Acceleration (2nd derivative)
# ═══════════════════════════════════════════════════
def compute_momentum_accel(closes, period=5):
    """Compute rate-of-change of rate-of-change.
    Positive accel = move is accelerating (getting stronger).
    Negative accel = move is decelerating (about to reverse).
    This sees turns BEFORE they happen in the price."""
    if len(closes) < period * 2 + 1:
        return None, None
    roc = []
    for i in range(period, len(closes)):
        roc.append((closes[i] - closes[i - period]) / closes[i - period] * 100)
    if len(roc) < period + 1:
        return None, None
    accel = []
    for i in range(1, len(roc)):
        accel.append(roc[i] - roc[i - 1])
    current_roc = round(roc[-1], 3)
    current_accel = round(accel[-1], 3) if accel else None
    return current_roc, current_accel

# ═══════════════════════════════════════════════════
# Volume-Price Divergence (smart money tells)
# ═══════════════════════════════════════════════════
def detect_volume_price_divergence(closes, volumes, lookback=5):
    """Detect when price and volume disagree — a leading reversal signal.
    - Price up + volume down = weak rally, likely to fail
    - Price down + volume down = weak selloff, likely to bounce
    - Price up + volume up = strong move, likely to continue
    - Price down + volume up = capitulation or accumulation"""
    if len(closes) < lookback + 1 or len(volumes) < lookback + 1:
        return None
    price_change = (closes[-1] - closes[-lookback]) / closes[-lookback] * 100
    vol_recent = sum(volumes[-lookback:]) / lookback
    vol_prior = sum(volumes[-(lookback*2):-lookback]) / lookback if len(volumes) >= lookback * 2 else vol_recent
    vol_change = (vol_recent - vol_prior) / vol_prior * 100 if vol_prior > 0 else 0

    if price_change > 0.5 and vol_change < -15:
        return "BEARISH_DIVERGENCE"
    elif price_change < -0.5 and vol_change < -15:
        return "BULLISH_DIVERGENCE"
    elif price_change > 0.5 and vol_change > 15:
        return "STRONG_BULLISH"
    elif price_change < -0.5 and vol_change > 15:
        return "CAPITULATION"
    return None

# ═══════════════════════════════════════════════════
# Cross-Market Leading Indicators
# ═══════════════════════════════════════════════════
LEAD_LAG_PAIRS = {
    "BTC-USD": ["ETH-USD", "SOL-USD", "DOGE-USD", "AVAX-USD", "LINK-USD", "ADA-USD"],
    "SPY": ["QQQ", "IWM"],
    "^VIX": ["SPY"],
}

def compute_cross_market_signals(signals_dict, cache):
    """Compute leading indicator signals from cross-market relationships."""
    cross_signals = {}
    for leader, followers in LEAD_LAG_PAIRS.items():
        leader_data = signals_dict.get(leader) or {}
        leader_roc = leader_data.get("momentum_roc")
        leader_accel = leader_data.get("momentum_accel")
        leader_change = leader_data.get("day_change", 0)

        if leader_roc is None:
            continue

        for follower in followers:
            if follower not in signals_dict:
                continue
            follower_change = signals_dict[follower].get("day_change", 0)

            if leader == "^VIX":
                if leader_change > 2 and follower_change > -0.5:
                    cross_signals[follower] = "VIX_SPIKE_INCOMING — VIX up %.1f%%, %s hasn't dropped yet" % (leader_change, follower)
                elif leader_change < -2 and follower_change < 0.5:
                    cross_signals[follower] = "VIX_CRUSH_BUY — VIX down %.1f%%, %s hasn't rallied yet" % (leader_change, follower)
            else:
                if leader_change > 1.5 and follower_change < 0.5:
                    cross_signals[follower] = "LEADER_BULLISH — %s up %.1f%%, %s lagging (BUY)" % (leader, leader_change, follower)
                elif leader_change < -1.5 and follower_change > -0.5:
                    cross_signals[follower] = "LEADER_BEARISH — %s down %.1f%%, %s lagging (SHORT)" % (leader, leader_change, follower)

    return cross_signals

# ═══════════════════════════════════════════════════
# Correlation Break Detection
# ═══════════════════════════════════════════════════
CORRELATED_PAIRS = [
    ("SPY", "QQQ"),
    ("BTC-USD", "ETH-USD"),
    ("SOL-USD", "ETH-USD"),
    ("AAPL", "QQQ"),
    ("NVDA", "QQQ"),
    ("TSLA", "QQQ"),
    ("AMD", "NVDA"),
]

def detect_correlation_breaks(signals_dict, threshold=2.0):
    """Detect when normally correlated assets diverge — mean reversion opportunity."""
    breaks = []
    for a, b in CORRELATED_PAIRS:
        if a not in signals_dict or b not in signals_dict:
            continue
        change_a = signals_dict[a].get("week_change", 0)
        change_b = signals_dict[b].get("week_change", 0)
        divergence = abs(change_a - change_b)
        if divergence > threshold:
            if change_a > change_b:
                breaks.append({
                    "pair": (a, b),
                    "leader": a, "laggard": b,
                    "divergence": round(divergence, 1),
                    "signal": "BUY %s — lagging %s by %.1f%%" % (b, a, divergence)
                })
            else:
                breaks.append({
                    "pair": (a, b),
                    "leader": b, "laggard": a,
                    "divergence": round(divergence, 1),
                    "signal": "BUY %s — lagging %s by %.1f%%" % (a, b, divergence)
                })
    return breaks


def detect_regime(vix_data, spy_data):
    """Detect market regime from VIX level and SPY trend."""
    regime = "UNKNOWN"
    vix_level = None
    spy_trend = None

    if vix_data and "price" in vix_data:
        vix_level = vix_data["price"]
        if vix_level > 30:
            regime = "HIGH_VOLATILITY"
        elif vix_level > 20:
            regime = "ELEVATED_VOL"
        elif vix_level < 14:
            regime = "LOW_VOL_COMPLACENT"
        else:
            regime = "NORMAL"

    if spy_data:
        change = spy_data.get("change_pct", 0)
        if change > 1:
            spy_trend = "STRONG_UP"
        elif change > 0.3:
            spy_trend = "UP"
        elif change < -1:
            spy_trend = "STRONG_DOWN"
        elif change < -0.3:
            spy_trend = "DOWN"
        else:
            spy_trend = "FLAT"

    return regime, vix_level, spy_trend

def score_setup(ticker, data, rsi, macd_hist, bb_pos, volume_ratio, regime, win_rate_info,
                recent_trades_on_ticker, portfolio_tickers, atr_val, price,
                momentum_accel, vol_price_div, cross_signal, corr_break):
    """Score a potential trade setup 0-100. Higher = stronger signal."""
    score = 50

    # RSI signals
    if rsi is not None:
        if rsi < 30:
            score += 15
        elif rsi < 40:
            score += 8
        elif rsi > 70:
            score += 12
        elif rsi > 60:
            score += 5
        else:
            score -= 5

    # MACD signals
    if macd_hist is not None:
        if macd_hist > 0 and macd_hist > 0.01:
            score += 10
        elif macd_hist < 0 and macd_hist < -0.01:
            score += 8
        else:
            score -= 3

    # Bollinger Band position
    if bb_pos is not None:
        if bb_pos < 0.1:
            score += 12
        elif bb_pos > 0.9:
            score += 8
        elif 0.4 < bb_pos < 0.6:
            score -= 5

    # Volume anomaly
    if volume_ratio is not None:
        if volume_ratio > 2.0:
            score += 15
        elif volume_ratio > 1.5:
            score += 10
        elif volume_ratio < 0.5:
            score -= 10

    # Trend strength
    change = data.get("change_pct", 0) if data else 0
    if abs(change) > 3:
        score += 10
    elif abs(change) > 1.5:
        score += 5

    # ═══ PREDICTIVE SIGNALS ═══

    # Momentum acceleration
    if momentum_accel is not None:
        if abs(momentum_accel) > 1.5:
            score += 12
        elif abs(momentum_accel) > 0.5:
            score += 6
        if momentum_accel < -0.5 and change > 1:
            score -= 8  # rally decelerating

    # Volume-price divergence
    if vol_price_div:
        if vol_price_div == "STRONG_BULLISH":
            score += 12
        elif vol_price_div == "BEARISH_DIVERGENCE":
            score += 8
        elif vol_price_div == "BULLISH_DIVERGENCE":
            score += 10
        elif vol_price_div == "CAPITULATION":
            score += 6

    # Cross-market leading signal
    if cross_signal:
        score += 10

    # Correlation break
    if corr_break:
        score += 8

    # ATR-adjusted
    if atr_val and price:
        atr_pct = (atr_val / price) * 100
        if 1.0 < atr_pct < 4.0:
            score += 5
        elif atr_pct > 6:
            score -= 5

    # ═══ EXISTING FILTERS ═══

    # Anti-churn penalty
    if recent_trades_on_ticker:
        last_trade = recent_trades_on_ticker[-1]
        last_pnl = last_trade.get("pnl", 0) or 0
        if last_pnl <= 0:
            score -= 20
        elif last_pnl > 0:
            score += 5

    # Win rate on this ticker
    wr, count = win_rate_info
    if count >= 3 and wr is not None:
        if wr == 0:
            score -= 30
        elif wr < 30:
            score -= 15
        elif wr > 60:
            score += 10

    # Already holding penalty
    if ticker in portfolio_tickers:
        score -= 25

    # Regime bonus
    if regime == "HIGH_VOLATILITY":
        score += 5

    return max(0, min(100, score))


def main():
    try:
        import yfinance as yf
    except ImportError:
        print("[signal-engine] yfinance not installed, skipping", file=sys.stderr)
        return

    # Load watchlist
    wl = load_json(DATA / "watchlist.json", {"tickers": []})
    all_tickers = list(set(wl.get("tickers", []) + wl.get("added_by_agent", []) + wl.get("crypto", [])))
    crypto_tickers = set(wl.get("crypto", ["BTC-USD", "ETH-USD"]))

    # Load portfolio
    portfolio = load_json(DATA / "portfolio.json", {"positions": [], "cash": 100000})
    portfolio_tickers = set(p["ticker"] for p in portfolio.get("positions", []))
    cash = portfolio.get("cash", 0)

    # Load cached prices
    cache = load_json(DATA / "price_cache.json", {})

    # Load trade history
    trades = load_recent_trades(100)

    # Fetch 30-day history for indicator computation
    analysis_tickers = [t for t in all_tickers if not t.startswith("^") and "=X" not in t and "=F" not in t]
    fetch_list = list(set(analysis_tickers + ["SPY", "^VIX"]))

    print("[signal-engine] Fetching history for %d tickers..." % len(fetch_list), file=sys.stderr)
    try:
        hist = yf.download(fetch_list, period="1mo", group_by="ticker", progress=False, threads=True)
    except Exception as e:
        print("[signal-engine] yfinance download failed: %s" % e, file=sys.stderr)
        return

    # Compute indicators for each ticker
    signals = {}
    for ticker in analysis_tickers:
        try:
            if len(fetch_list) == 1:
                df = hist
            else:
                df = hist[ticker] if ticker in hist.columns.get_level_values(0) else None
            if df is None or df.empty:
                continue

            closes = df["Close"].dropna().tolist()
            highs = df["High"].dropna().tolist() if "High" in df.columns else closes
            lows = df["Low"].dropna().tolist() if "Low" in df.columns else closes
            volumes = df["Volume"].dropna().tolist() if "Volume" in df.columns else []

            if len(closes) < 5:
                continue

            price = closes[-1]
            rsi = compute_rsi(closes)
            macd_line, macd_signal, macd_hist = compute_macd(closes)
            bb_pos = compute_bollinger(closes)

            # ATR
            atr = compute_atr(highs, lows, closes)
            stop_long, stop_short = atr_stop_distance(price, atr)
            atr_pct = round((atr / price) * 100, 2) if atr and price else None

            # Support/Resistance
            support, resistance = compute_support_resistance(highs, lows, closes)

            # Momentum acceleration
            mom_roc, mom_accel = compute_momentum_accel(closes)

            # Volume-price divergence
            vpd = detect_volume_price_divergence(closes, volumes)

            # Volume analysis
            volume_ratio = None
            if len(volumes) >= 5 and volumes[-1] > 0:
                avg_vol = sum(volumes[-20:]) / len(volumes[-20:]) if len(volumes) >= 20 else sum(volumes) / len(volumes)
                volume_ratio = round(volumes[-1] / avg_vol, 2) if avg_vol > 0 else None

            # Price vs moving averages
            sma_20 = round(sum(closes[-20:]) / 20, 2) if len(closes) >= 20 else None
            sma_5 = round(sum(closes[-5:]) / 5, 2) if len(closes) >= 5 else None
            above_sma20 = price > sma_20 if sma_20 else None

            # Recent change
            day_change = round((closes[-1] - closes[-2]) / closes[-2] * 100, 2) if len(closes) >= 2 else 0
            week_change = round((closes[-1] - closes[-5]) / closes[-5] * 100, 2) if len(closes) >= 5 else 0

            # Win rate on this ticker
            wr_info = ticker_win_rate(ticker, trades)
            recent_on_ticker = recent_ticker_trades(ticker, trades)

            signals[ticker] = {
                "price": round(price, 2),
                "rsi": rsi,
                "macd_line": macd_line,
                "macd_signal": macd_signal,
                "macd_hist": macd_hist,
                "macd_cross": "BULLISH" if (macd_hist and macd_hist > 0) else ("BEARISH" if (macd_hist and macd_hist < 0) else "NEUTRAL"),
                "bb_position": bb_pos,
                "volume_ratio": volume_ratio,
                "sma_20": sma_20,
                "sma_5": sma_5,
                "above_sma20": above_sma20,
                "day_change": day_change,
                "week_change": week_change,
                "is_crypto": ticker in crypto_tickers,
                "ticker_win_rate": wr_info[0],
                "ticker_trade_count": wr_info[1],
                "in_portfolio": ticker in portfolio_tickers,
                "atr": atr,
                "atr_pct": atr_pct,
                "atr_stop_long": stop_long,
                "atr_stop_short": stop_short,
                "support": support,
                "resistance": resistance,
                "momentum_roc": mom_roc,
                "momentum_accel": mom_accel,
                "vol_price_div": vpd,
            }
        except Exception as e:
            print("[signal-engine] %s error: %s" % (ticker, e), file=sys.stderr)

    # Regime detection
    vix_data = cache.get("^VIX", {})
    spy_data = cache.get("SPY", {})
    regime, vix_level, spy_trend = detect_regime(vix_data, spy_data)

    # Cross-market leading indicators
    cross_signals = compute_cross_market_signals(signals, cache)

    # Correlation break detection
    corr_breaks = detect_correlation_breaks(signals)
    corr_break_tickers = set()
    for b in corr_breaks:
        corr_break_tickers.add(b["laggard"])

    # Score all setups
    for ticker, sig in signals.items():
        wr_info = (sig["ticker_win_rate"], sig["ticker_trade_count"])
        recent = recent_ticker_trades(ticker, trades)
        sig["cross_signal"] = cross_signals.get(ticker)
        sig["corr_break"] = ticker in corr_break_tickers
        sig["score"] = score_setup(
            ticker, cache.get(ticker), sig["rsi"], sig["macd_hist"],
            sig["bb_position"], sig["volume_ratio"], regime,
            wr_info, recent, portfolio_tickers,
            sig["atr"], sig["price"],
            sig["momentum_accel"], sig["vol_price_div"],
            sig.get("cross_signal"), sig.get("corr_break")
        )

    # Sort by score
    ranked = sorted(signals.items(), key=lambda x: x[1]["score"], reverse=True)

    # Calculate rolling win rate
    recent_closed = [t for t in trades if t.get("pnl") is not None][-20:]
    rolling_wr = round(sum(1 for t in recent_closed if t["pnl"] > 0) / len(recent_closed) * 100, 1) if recent_closed else 0
    total_closed = [t for t in trades if t.get("pnl") is not None]
    overall_wr = round(sum(1 for t in total_closed if t["pnl"] > 0) / len(total_closed) * 100, 1) if total_closed else 0

    # Loss streak
    streak = 0
    for t in reversed(total_closed):
        if t.get("pnl", 0) <= 0:
            streak += 1
        else:
            break

    # Weekend detection
    weekend = is_weekend()
    market_open = is_market_open()

    # ═══════════════════════════════════════════════════
    # Write output (context/signals.md)
    # ═══════════════════════════════════════════════════
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["# Signal Analysis — %s\n" % now]

    # Regime
    lines.append("## Market Regime")
    lines.append("- Regime: **%s**" % regime)
    if vix_level:
        lines.append("- VIX: %.1f" % vix_level)
    if spy_trend:
        lines.append("- SPY Trend: %s" % spy_trend)
    lines.append("- Market: %s" % ("OPEN" if market_open else "CLOSED"))
    if weekend:
        lines.append("- **WEEKEND MODE — CRYPTO TRADING ACTIVE**")
    lines.append("")

    # Win rate accountability
    lines.append("## Your Performance")
    lines.append("- Rolling 20-trade win rate: **%.1f%%** (target: 65%%)" % rolling_wr)
    lines.append("- Overall win rate: **%.1f%%**" % overall_wr)
    if streak > 0:
        lines.append("- Current loss streak: **%d**" % streak)
    if rolling_wr < 55:
        lines.append("- **WARNING: Win rate below 55%%. Be MORE selective. Only trade score 75+.**")
    if streak >= 3:
        lines.append("- **WARNING: %d-loss streak. Reduce position sizes to 5%% until 2 consecutive wins.**" % streak)
    lines.append("- Cash available: $%.0f" % cash)
    lines.append("")

    # Predictive Alerts
    alerts = []
    for ticker, sig in ranked:
        if sig.get("momentum_accel") is not None and abs(sig["momentum_accel"]) > 1.0:
            direction = "ACCELERATING UP" if sig["momentum_accel"] > 0 else "ACCELERATING DOWN"
            alerts.append("**%s** %s (accel: %.2f) — move is building" % (ticker, direction, sig["momentum_accel"]))
        if sig.get("vol_price_div"):
            alerts.append("**%s** %s — smart money signal" % (ticker, sig["vol_price_div"]))
        if sig.get("cross_signal"):
            alerts.append("**%s** %s" % (ticker, sig["cross_signal"]))

    if alerts:
        lines.append("## PREDICTIVE ALERTS — See moves before they happen")
        for a in alerts[:10]:
            lines.append("- %s" % a)
        lines.append("")

    # Correlation break alerts
    if corr_breaks:
        lines.append("## CORRELATION BREAKS — Mean reversion opportunities")
        for b in corr_breaks:
            lines.append("- %s (divergence: %.1f%%)" % (b["signal"], b["divergence"]))
        lines.append("")

    # Top setups
    lines.append("## Top Setups (Score 70+)")
    top_count = 0
    for ticker, sig in ranked:
        if sig["score"] >= 70 and not sig["in_portfolio"]:
            top_count += 1
            direction = "BUY" if sig.get("rsi", 50) < 50 or sig.get("macd_cross") == "BULLISH" else "SHORT"
            rsi_str = "RSI %.0f" % sig["rsi"] if sig["rsi"] else "RSI n/a"
            vol_str = "vol %.1fx" % sig["volume_ratio"] if sig["volume_ratio"] else ""
            macd_str = sig["macd_cross"]
            bb_str = "BB %.0f%%" % (sig["bb_position"] * 100) if sig["bb_position"] is not None else ""
            wr_str = "WR %.0f%%(%d)" % (sig["ticker_win_rate"], sig["ticker_trade_count"]) if sig["ticker_win_rate"] is not None else "WR n/a"
            crypto_str = " [CRYPTO 24/7]" if sig["is_crypto"] else ""
            atr_str = ""
            if sig.get("atr"):
                if direction == "BUY":
                    atr_str = " | ATR-stop: $%.2f" % sig["atr_stop_long"] if sig["atr_stop_long"] else ""
                else:
                    atr_str = " | ATR-stop: $%.2f" % sig["atr_stop_short"] if sig["atr_stop_short"] else ""
            accel_str = ""
            if sig.get("momentum_accel") is not None:
                accel_str = " | accel:%.2f" % sig["momentum_accel"]
            sr_str = ""
            if sig.get("support"):
                nearest_sup = min(sig["support"], key=lambda x: abs(x[0] - sig["price"]))
                sr_str = " | sup:$%.2f(%dx)" % (nearest_sup[0], nearest_sup[1])
            if sig.get("resistance"):
                nearest_res = min(sig["resistance"], key=lambda x: abs(x[0] - sig["price"]))
                sr_str += " | res:$%.2f(%dx)" % (nearest_res[0], nearest_res[1])

            lines.append("- **%s %s** Score:%d | %s | MACD:%s | %s | %s | %s | day:%.1f%% wk:%.1f%%%s%s%s%s" % (
                direction, ticker, sig["score"], rsi_str, macd_str, bb_str, vol_str, wr_str,
                sig["day_change"], sig["week_change"], crypto_str, atr_str, accel_str, sr_str
            ))

    if top_count == 0:
        lines.append("- No setups above score 70. Consider WATCH this cycle.")
    lines.append("")

    # Moderate setups
    lines.append("## Moderate Setups (Score 50-69)")
    for ticker, sig in ranked:
        if 50 <= sig["score"] < 70 and not sig["in_portfolio"]:
            rsi_str = "RSI %.0f" % sig["rsi"] if sig["rsi"] else ""
            crypto_str = " [CRYPTO]" if sig["is_crypto"] else ""
            accel_str = " accel:%.2f" % sig["momentum_accel"] if sig.get("momentum_accel") is not None else ""
            lines.append("- %s Score:%d | %s | MACD:%s | day:%.1f%%%s%s" % (
                ticker, sig["score"], rsi_str, sig["macd_cross"], sig["day_change"], crypto_str, accel_str
            ))
    lines.append("")

    # Avoid list
    lines.append("## AVOID (Score < 40 or flagged)")
    for ticker, sig in ranked:
        if sig["score"] < 40 or (sig["ticker_win_rate"] is not None and sig["ticker_win_rate"] == 0 and sig["ticker_trade_count"] >= 3):
            reason = []
            if sig["ticker_win_rate"] == 0 and sig["ticker_trade_count"] >= 3:
                reason.append("0%% WR after %d trades" % sig["ticker_trade_count"])
            if sig["score"] < 30:
                reason.append("score %d" % sig["score"])
            recent = recent_ticker_trades(ticker, trades)
            if recent and (recent[-1].get("pnl", 0) or 0) <= 0:
                reason.append("recent loser")
            if reason:
                lines.append("- %s: %s" % (ticker, ", ".join(reason)))
    lines.append("")

    # Current positions analysis
    lines.append("## Position Health Check")
    for pos in portfolio.get("positions", []):
        t = pos["ticker"]
        sig = signals.get(t, {})
        rsi_str = "RSI %.0f" % sig["rsi"] if sig.get("rsi") else "RSI n/a"
        pnl = pos.get("unrealized_pnl", 0)
        pnl_pct = pos.get("unrealized_pnl_pct", 0)
        entry_cycles_ago = 0
        cycle_file = DATA / "cycle.txt"
        if cycle_file.exists():
            current_cycle = int(cycle_file.read_text().strip())
            entry_cycles_ago = current_cycle - pos.get("entry_cycle", current_cycle)

        status = "HOLD"
        if pnl_pct < -1.5 and entry_cycles_ago >= 2:
            status = "**EXIT — underwater >1.5%% for %d cycles**" % entry_cycles_ago
        elif pnl_pct > 1 and not pos.get("trail_pct"):
            status = "**SET TRAIL — up %.1f%%, lock in gains**" % pnl_pct
        elif pnl_pct > 3:
            status = "**TIGHTEN TRAIL to 2%%**"

        atr_note = ""
        if sig.get("atr"):
            if pos.get("stop"):
                stop_dist = abs(pos.get("current_price", pos["entry_price"]) - pos["stop"])
                if stop_dist > 0 and stop_dist < sig["atr"] * 0.5:
                    atr_note = " | **STOP TOO TIGHT** (< 0.5x ATR)"
                elif stop_dist > sig["atr"] * 3:
                    atr_note = " | stop too wide (> 3x ATR)"
        mom_note = ""
        if sig.get("momentum_accel") is not None:
            if pos.get("direction") == "long" and sig["momentum_accel"] < -1.0:
                mom_note = " | **DECEL WARNING** — momentum fading"
            elif pos.get("direction") == "short" and sig["momentum_accel"] > 1.0:
                mom_note = " | **DECEL WARNING** — bounce building"

        lines.append("- %s: %s $%.2f (P&L: $%.0f / %.1f%%) | %s | Action: %s%s%s" % (
            t, pos.get("direction", "long"), pos.get("current_price", pos["entry_price"]),
            pnl, pnl_pct, rsi_str, status, atr_note, mom_note
        ))
    lines.append("")

    # Weekend crypto spotlight
    if weekend:
        lines.append("## WEEKEND CRYPTO OPPORTUNITIES")
        lines.append("Markets are closed. Your capital should be in crypto.")
        crypto_ranked = [(t, s) for t, s in ranked if s["is_crypto"]]
        if crypto_ranked:
            for ticker, sig in crypto_ranked[:5]:
                rsi_str = "RSI %.0f" % sig["rsi"] if sig["rsi"] else ""
                accel_str = " | accel:%.2f" % sig["momentum_accel"] if sig.get("momentum_accel") is not None else ""
                atr_str = " | ATR:$%.2f (%.1f%%)" % (sig["atr"], sig["atr_pct"]) if sig.get("atr") else ""
                lines.append("- **%s** Score:%d | $%.2f | %s | MACD:%s | day:%.1f%% | wk:%.1f%%%s%s" % (
                    ticker, sig["score"], sig["price"], rsi_str, sig["macd_cross"],
                    sig["day_change"], sig["week_change"], accel_str, atr_str
                ))
        else:
            lines.append("- No crypto data available. Check watchlist.")
        lines.append("")

    # ATR Stop Guide
    lines.append("## ATR Stop Guide (mathematically optimal stops)")
    for ticker, sig in ranked[:15]:
        if sig.get("atr") and not sig["in_portfolio"]:
            lines.append("- %s: ATR $%.2f (%.1f%%) | BUY stop: $%.2f | SHORT stop: $%.2f" % (
                ticker, sig["atr"], sig["atr_pct"],
                sig["atr_stop_long"] or 0, sig["atr_stop_short"] or 0
            ))
    lines.append("")

    output = "\n".join(lines) + "\n"
    (CONTEXT / "signals.md").write_text(output)

    # Save raw signals as JSON for other tools
    (DATA / "signals.json").write_text(json.dumps({
        "regime": regime, "vix": vix_level, "spy_trend": spy_trend,
        "rolling_wr": rolling_wr, "overall_wr": overall_wr, "loss_streak": streak,
        "weekend": weekend, "market_open": market_open,
        "cross_signals": cross_signals,
        "correlation_breaks": [{"pair": list(b["pair"]), "signal": b["signal"], "divergence": b["divergence"]} for b in corr_breaks],
        "top_setups": [{"ticker": t, "score": s["score"], "rsi": s["rsi"], "macd": s["macd_cross"],
                        "atr": s.get("atr"), "momentum_accel": s.get("momentum_accel"),
                        "vol_price_div": s.get("vol_price_div")}
                       for t, s in ranked if s["score"] >= 70][:10],
        "timestamp": now,
    }, indent=2))

    predictive_count = sum(1 for _, s in signals.items()
                          if s.get("momentum_accel") is not None and abs(s["momentum_accel"]) > 0.5)
    print("[signal-engine] Analyzed %d tickers, %d scored 70+ | Regime: %s | WR: %.0f%% | %d predictive alerts | %d corr breaks" % (
        len(signals), sum(1 for _, s in ranked if s["score"] >= 70), regime, rolling_wr,
        predictive_count, len(corr_breaks)))


if __name__ == "__main__":
    main()
