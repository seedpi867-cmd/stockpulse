#!/usr/bin/env python3
"""Fetch compact equity fundamentals for watched stocks.

This fills the gap between price/news feeds and trade reasoning: the agent gets
valuation, earnings timing, profitability, leverage, and analyst target context
for individual equities without wasting calls on ETFs, futures, crypto, or forex.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)

SKIP_PREFIXES = ("^",)
SKIP_CONTAINS = ("=", "-USD")
ETF_LIKE = {
    "SPY", "QQQ", "DIA", "IWM", "XLK", "XLF", "XLE", "XLV", "XLI", "XLP",
    "XLU", "XLRE", "XLC", "XLB", "XLY", "SH", "SQQQ", "UVXY", "TLT", "GLD",
    "SLV", "GDX", "USO", "CPER", "SIL", "PPLT", "PALL", "JETS", "DBA", "INDA",
    "EWA", "EWJ", "EWG", "EWU", "FXI", "IYT",
}

def load_equity_tickers():
    wl_path = ROOT / "data" / "watchlist.json"
    if not wl_path.exists():
        return []
    try:
        wl = json.loads(wl_path.read_text())
    except Exception:
        return []

    tickers = []
    for item in wl.get("tickers", []) + wl.get("added_by_agent", []):
        ticker = item.get("ticker") if isinstance(item, dict) else item
        if not isinstance(ticker, str):
            continue
        ticker = ticker.strip().upper()
        if not ticker or ticker in ETF_LIKE:
            continue
        if ticker.startswith(SKIP_PREFIXES) or any(part in ticker for part in SKIP_CONTAINS):
            continue
        if ticker not in tickers:
            tickers.append(ticker)
    return tickers[:35]

def fmt_num(value, suffix=""):
    if value is None:
        return "n/a"
    try:
        value = float(value)
    except Exception:
        return "n/a"
    return "{:.2f}{}".format(value, suffix)

def fmt_money(value):
    if value is None:
        return "n/a"
    try:
        return "${:.2f}".format(float(value))
    except Exception:
        return "n/a"

def fmt_market_cap(value):
    if value is None:
        return "n/a"
    try:
        value = float(value)
    except Exception:
        return "n/a"
    if value >= 1_000_000_000_000:
        return "${:.2f}T".format(value / 1_000_000_000_000)
    if value >= 1_000_000_000:
        return "${:.1f}B".format(value / 1_000_000_000)
    if value >= 1_000_000:
        return "${:.1f}M".format(value / 1_000_000)
    return "${:.0f}".format(value)

def normalize_date(value):
    if value is None:
        return None
    if isinstance(value, (list, tuple)) and value:
        value = value[0]
    if hasattr(value, "date"):
        return str(value.date())
    if isinstance(value, str):
        return value[:10]
    return None

def next_earnings_date(ticker_obj):
    try:
        cal = ticker_obj.calendar
        if isinstance(cal, dict):
            for key in ("Earnings Date", "EarningsDate"):
                date = normalize_date(cal.get(key))
                if date:
                    return date
        elif hasattr(cal, "empty") and not cal.empty:
            for key in ("Earnings Date", "EarningsDate"):
                if key in cal.index:
                    date = normalize_date(cal.loc[key].iloc[0])
                    if date:
                        return date
    except Exception:
        pass

    try:
        dates = ticker_obj.get_earnings_dates(limit=4)
        if dates is not None and not dates.empty:
            today = datetime.utcnow().date()
            for idx in dates.index:
                d = idx.date() if hasattr(idx, "date") else None
                if d and d >= today - timedelta(days=1):
                    return str(d)
    except Exception:
        pass
    return None

def fetch_one(ticker):
    import yfinance as yf

    t = yf.Ticker(ticker)
    info = {}
    try:
        info = t.get_info() or {}
    except Exception as e:
        print("[feed-fundamentals] {} info unavailable: {}".format(ticker, e), file=sys.stderr)

    fast = {}
    try:
        fi = t.fast_info
        fast = {
            "last_price": getattr(fi, "last_price", None),
            "market_cap": getattr(fi, "market_cap", None),
        }
    except Exception:
        pass

    return {
        "ticker": ticker,
        "name": info.get("shortName") or info.get("longName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap") or fast.get("market_cap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_sales": info.get("priceToSalesTrailing12Months"),
        "gross_margin": info.get("grossMargins"),
        "operating_margin": info.get("operatingMargins"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "debt_to_equity": info.get("debtToEquity"),
        "target_mean": info.get("targetMeanPrice"),
        "recommendation": info.get("recommendationKey"),
        "next_earnings": next_earnings_date(t),
    }

def write_output(rows):
    now = datetime.now().strftime("%Y-%m-%d %H:%M EST")
    lines = ["# Equity Fundamentals — {}\n".format(now)]

    if not rows:
        lines.append("No single-stock fundamentals available from the current watchlist.")
    else:
        lines.append("## Watchlist Snapshot")
        for r in rows:
            parts = [
                "{} ({})".format(r["ticker"], r["name"][:40]),
                "sector {}".format(r["sector"] or "n/a"),
                "cap {}".format(fmt_market_cap(r["market_cap"])),
                "P/E ttm {} fwd {}".format(fmt_num(r["trailing_pe"]), fmt_num(r["forward_pe"])),
                "P/S {}".format(fmt_num(r["price_to_sales"])),
                "rev growth {}".format(fmt_num((r["revenue_growth"] or 0) * 100, "%") if r["revenue_growth"] is not None else "n/a"),
                "op margin {}".format(fmt_num((r["operating_margin"] or 0) * 100, "%") if r["operating_margin"] is not None else "n/a"),
                "debt/equity {}".format(fmt_num(r["debt_to_equity"])),
                "target {}".format(fmt_money(r["target_mean"])),
                "rating {}".format(r["recommendation"] or "n/a"),
                "earnings {}".format(r["next_earnings"] or "n/a"),
            ]
            lines.append("- " + " | ".join(parts))

    (CONTEXT / "fundamentals.md").write_text("\n".join(lines) + "\n")
    print("[feed-fundamentals] {} equities written".format(len(rows)))

def main():
    tickers = load_equity_tickers()
    rows = []
    for ticker in tickers:
        try:
            rows.append(fetch_one(ticker))
        except Exception as e:
            print("[feed-fundamentals] {} failed: {}".format(ticker, e), file=sys.stderr)
    write_output(rows)

if __name__ == "__main__":
    main()
