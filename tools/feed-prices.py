#!/usr/bin/env python3
"""Fetch live stock prices from Yahoo Finance — global markets."""
import json, os, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)
CACHE = ROOT / "data" / "price_cache.json"

# Dynamic watchlist — agent adds tickers by editing data/watchlist.json
import json as _json

def load_watchlist():
    wl_path = ROOT / "data" / "watchlist.json"
    try:
        wl = _json.loads(wl_path.read_text())
        tickers = wl.get("tickers", [])
        added = wl.get("added_by_agent", [])
        # Flatten — agent sometimes writes dicts instead of strings
        result = []
        for t in tickers + added:
            if isinstance(t, str):
                result.append(t)
            elif isinstance(t, dict) and "ticker" in t:
                result.append(t["ticker"])
        return list(set(result))  # dedupe
    except:
        return []

# Static fallbacks + global indices (always tracked)
GLOBAL_INDICES = ["^GSPC", "^FTSE", "^N225", "^GDAXI", "^AXJO", "^HSI", "^STI"]
US_SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLP", "XLU", "XLRE", "XLC", "XLB", "XLY"]
COUNTRY_ETFS = ["EWA", "EWJ", "EWG", "EWU", "FXI", "INDA"]
FOREX = ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X"]
COMMODITIES = ["GC=F", "CL=F", "SI=F"]

# Merge dynamic watchlist with static infrastructure
_dynamic = load_watchlist()
US_INDICES = [t for t in ["SPY", "QQQ", "DIA", "IWM", "^VIX"] if t not in _dynamic]
US_WATCHLIST = _dynamic  # Agent controls this list
CRYPTO = [t for t in _dynamic if "-USD" in t] or ["BTC-USD", "ETH-USD"]

INDEX_NAMES = {
    "^GSPC": "S&P 500", "^FTSE": "FTSE 100", "^N225": "Nikkei 225",
    "^GDAXI": "DAX", "^AXJO": "ASX 200", "^HSI": "Hang Seng", "^STI": "Straits Times",
    "^VIX": "VIX"
}

COUNTRY_NAMES = {
    "EWA": "Australia", "EWJ": "Japan", "EWG": "Germany",
    "EWU": "UK", "FXI": "China", "INDA": "India"
}

FOREX_NAMES = {
    "EURUSD=X": "EUR/USD", "USDJPY=X": "USD/JPY",
    "GBPUSD=X": "GBP/USD", "AUDUSD=X": "AUD/USD"
}

COMMODITY_NAMES = {
    "GC=F": "Gold", "CL=F": "Crude Oil", "SI=F": "Silver"
}

def fetch_prices():
    import yfinance as yf
    all_tickers = US_INDICES + GLOBAL_INDICES + US_WATCHLIST + US_SECTORS + COUNTRY_ETFS + CRYPTO + FOREX + COMMODITIES
    data = yf.download(all_tickers, period="5d", group_by="ticker", progress=False, threads=True)
    results = {}
    for t in all_tickers:
        try:
            if len(all_tickers) == 1:
                df = data
            else:
                df = data[t] if t in data.columns.get_level_values(0) else None
            if df is None or df.empty:
                continue
            row = df.dropna().iloc[-1]
            prev = df.dropna().iloc[-2] if len(df.dropna()) > 1 else row
            price = float(row["Close"])
            prev_close = float(prev["Close"])
            change_pct = ((price - prev_close) / prev_close) * 100
            volume = int(row["Volume"]) if "Volume" in row and row["Volume"] > 0 else 0
            high_52w = float(df["Close"].max())
            low_52w = float(df["Close"].min())
            results[t] = {
                "price": round(price, 2),
                "change_pct": round(change_pct, 2),
                "volume": volume,
                "high_52w": round(high_52w, 2),
                "low_52w": round(low_52w, 2),
                "prev_close": round(prev_close, 2)
            }
        except Exception as e:
            print("Warning: {}: {}".format(t, e), file=sys.stderr)
    return results

def format_vol(v):
    if v >= 1_000_000_000: return "{:.1f}B".format(v / 1_000_000_000)
    if v >= 1_000_000: return "{:.1f}M".format(v / 1_000_000)
    if v >= 1_000: return "{:.0f}K".format(v / 1_000)
    return str(v)

def fmt(t, d, name=None):
    sign = "+" if d["change_pct"] >= 0 else ""
    label = name if name else t.replace("^", "")
    vol = " vol {}".format(format_vol(d["volume"])) if d["volume"] > 0 else ""
    rng = " | 52w: ${:.2f}-${:.2f}".format(d["low_52w"], d["high_52w"]) if d.get("high_52w") else ""
    return "- {}: ${:.2f} ({}{:.2f}%){}{}".format(label, d["price"], sign, d["change_pct"], vol, rng)

def write_output(results):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["# Market Prices — {}\n".format(now)]

    lines.append("## US Indices")
    for t in US_INDICES:
        if t in results:
            lines.append(fmt(t, results[t], INDEX_NAMES.get(t)))

    lines.append("\n## Global Indices")
    for t in GLOBAL_INDICES:
        if t in results:
            lines.append(fmt(t, results[t], INDEX_NAMES.get(t)))

    lines.append("\n## US Watchlist")
    for t in US_WATCHLIST:
        if t in results:
            lines.append(fmt(t, results[t]))

    lines.append("\n## US Sectors")
    for t in US_SECTORS:
        if t in results:
            lines.append(fmt(t, results[t]))

    lines.append("\n## Country ETFs")
    for t in COUNTRY_ETFS:
        if t in results:
            lines.append(fmt(t, results[t], COUNTRY_NAMES.get(t)))

    lines.append("\n## Crypto")
    for t in CRYPTO:
        if t in results:
            name = t.replace("-USD", "")
            lines.append(fmt(t, results[t], name))

    lines.append("\n## Forex")
    for t in FOREX:
        if t in results:
            lines.append(fmt(t, results[t], FOREX_NAMES.get(t)))

    lines.append("\n## Commodities")
    for t in COMMODITIES:
        if t in results:
            lines.append(fmt(t, results[t], COMMODITY_NAMES.get(t)))

    # Top movers across everything
    all_movers = {t: results[t] for t in results if t not in ["^VIX"]}
    if all_movers:
        sorted_by_change = sorted(all_movers.items(), key=lambda x: x[1]["change_pct"], reverse=True)
        lines.append("\n## Top Movers (Global)")
        for t, d in sorted_by_change[:5]:
            sign = "+" if d["change_pct"] >= 0 else ""
            name = INDEX_NAMES.get(t) or COUNTRY_NAMES.get(t) or FOREX_NAMES.get(t) or COMMODITY_NAMES.get(t) or t.replace("^","").replace("-USD","").replace("=X","").replace("=F","")
            lines.append("- UP: {} {}{:.2f}%".format(name, sign, d["change_pct"]))
        for t, d in sorted_by_change[-5:]:
            sign = "+" if d["change_pct"] >= 0 else ""
            name = INDEX_NAMES.get(t) or COUNTRY_NAMES.get(t) or FOREX_NAMES.get(t) or COMMODITY_NAMES.get(t) or t.replace("^","").replace("-USD","").replace("=X","").replace("=F","")
            lines.append("- DOWN: {} {}{:.2f}%".format(name, sign, d["change_pct"]))

    # Market session status
    from datetime import timezone, timedelta
    utc_now = datetime.now(timezone.utc)
    et = utc_now - timedelta(hours=4)  # rough ET
    jst = utc_now + timedelta(hours=9)
    gmt = utc_now
    aest = utc_now + timedelta(hours=10)

    lines.append("\n## Market Sessions")
    sessions = []
    # US: 9:30-16:00 ET, weekdays only
    if et.weekday() < 5 and (9 <= et.hour < 16 or (et.hour == 9 and et.minute >= 30)):
        sessions.append("US: OPEN")
    else:
        sessions.append("US: CLOSED")
    # Europe: 8:00-16:30 GMT, weekdays only
    if gmt.weekday() < 5 and 8 <= gmt.hour < 17:
        sessions.append("Europe: OPEN")
    else:
        sessions.append("Europe: CLOSED")
    # Asia/Tokyo: 9:00-15:00 JST, weekdays only
    if jst.weekday() < 5 and 9 <= jst.hour < 15:
        sessions.append("Tokyo: OPEN")
    else:
        sessions.append("Tokyo: CLOSED")
    # ASX: 10:00-16:00 AEST, weekdays only
    if aest.weekday() < 5 and 10 <= aest.hour < 16:
        sessions.append("ASX: OPEN")
    else:
        sessions.append("ASX: CLOSED")
    for s in sessions:
        lines.append("- {}".format(s))

    output = "\n".join(lines) + "\n"
    (CONTEXT / "prices.md").write_text(output)

    # Cache raw data
    cache_data = {t: d for t, d in results.items()}
    cache_data["_timestamp"] = datetime.now().isoformat()
    CACHE.write_text(json.dumps(cache_data, indent=2))

    print("[feed-prices] {} tickers written (global)".format(len(results)))

if __name__ == "__main__":
    try:
        results = fetch_prices()
        if results:
            write_output(results)
        else:
            print("[feed-prices] No data returned, keeping cached", file=sys.stderr)
    except Exception as e:
        print("[feed-prices] Error: {}".format(e), file=sys.stderr)
        if CACHE.exists():
            print("[feed-prices] Using cached data", file=sys.stderr)
