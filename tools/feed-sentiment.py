#!/usr/bin/env python3
"""Fetch market sentiment indicators — VIX, Fear & Greed, Put/Call, bond yields, DXY."""
import sys, json, re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)

def get_vix():
    cache = ROOT / "data" / "price_cache.json"
    if cache.exists():
        data = json.loads(cache.read_text())
        vix = data.get("^VIX", {})
        return vix.get("price", None), vix.get("change_pct", None)
    return None, None

def get_fear_greed():
    import requests
    for url in [
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        "https://production.dataviz.cnn.io/index/fearandgreed/current",
    ]:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux aarch64)"}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                fg = data.get("fear_and_greed", data)
                score = fg.get("score", None)
                rating = fg.get("rating", None)
                if score is not None:
                    return float(score), rating
        except:
            continue
    return None, None

def get_put_call_and_yields():
    """Get P/C ratio and Treasury yields from yfinance — reliable source."""
    pc_ratio = None
    yields = {}
    try:
        import yfinance as yf
        # Put/Call — use CBOE total P/C index if available, else compute from SPY options
        try:
            spy = yf.Ticker("SPY")
            # Get nearest expiry options
            dates = spy.options
            if dates:
                chain = spy.option_chain(dates[0])
                put_vol = chain.puts["volume"].sum()
                call_vol = chain.calls["volume"].sum()
                if call_vol > 0:
                    pc_ratio = round(put_vol / call_vol, 2)
        except Exception as e:
            print("[feed-sentiment] SPY P/C failed: {}".format(e), file=sys.stderr)

        # Treasury yields
        yield_tickers = {
            "^TNX": "10Y",
            "^FVX": "5Y",
            "^TYX": "30Y",
            "^IRX": "3M",
        }
        for ticker, label in yield_tickers.items():
            try:
                t = yf.Ticker(ticker)
                info = t.fast_info
                price = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
                if price:
                    yields[label] = round(price, 3)
            except:
                pass

        # DXY (Dollar Index)
        try:
            dxy = yf.Ticker("DX-Y.NYB")
            info = dxy.fast_info
            price = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
            if price:
                yields["DXY"] = round(price, 2)
        except:
            pass

    except Exception as e:
        print("[feed-sentiment] yfinance block failed: {}".format(e), file=sys.stderr)

    return pc_ratio, yields

def write_output(vix_price, vix_change, fg_score, fg_rating, pc_ratio, yields):
    now = datetime.now().strftime("%Y-%m-%d %H:%M EST")
    lines = ["# Market Sentiment — {}\n".format(now)]

    # Fear & Greed
    lines.append("## Fear & Greed Index")
    if fg_score is not None:
        lines.append("- Score: {:.0f}/100 ({})".format(fg_score, fg_rating or "unknown"))
        if fg_score <= 25:
            lines.append("- **EXTREME FEAR** — historically a contrarian buy signal")
        elif fg_score <= 40:
            lines.append("- **FEAR** — market is nervous")
        elif fg_score <= 60:
            lines.append("- **NEUTRAL**")
        elif fg_score <= 75:
            lines.append("- **GREED** — watch for complacency")
        else:
            lines.append("- **EXTREME GREED** — historically a contrarian sell signal")
    else:
        lines.append("- Score: unavailable")

    # VIX
    lines.append("\n## VIX (Fear Index)")
    if vix_price is not None:
        lines.append("- VIX: {:.2f} ({}{:.2f}%)".format(
            vix_price, "+" if vix_change >= 0 else "", vix_change))
        if vix_price < 15:
            lines.append("- **LOW VOLATILITY** — complacency, watch for vol expansion")
        elif vix_price < 20:
            lines.append("- **NORMAL**")
        elif vix_price < 30:
            lines.append("- **ELEVATED** — market stress")
        else:
            lines.append("- **HIGH FEAR** — potential capitulation")
    else:
        lines.append("- VIX: unavailable")

    # Put/Call
    lines.append("\n## Put/Call Ratio (SPY nearest expiry)")
    if pc_ratio is not None:
        lines.append("- Equity P/C: {:.2f}".format(pc_ratio))
        if pc_ratio > 1.0:
            lines.append("- **BEARISH POSITIONING** — more puts than calls, contrarian bullish")
        elif pc_ratio > 0.7:
            lines.append("- **NEUTRAL** — balanced options flow")
        elif pc_ratio > 0.4:
            lines.append("- **BULLISH POSITIONING** — heavy call buying, contrarian bearish")
        else:
            lines.append("- **EXTREME CALL BUYING** — very one-sided, contrarian bearish")
    else:
        lines.append("- Put/Call ratio: unavailable")

    # Treasury Yields
    if yields:
        lines.append("\n## Treasury Yields")
        for label in ["3M", "5Y", "10Y", "30Y"]:
            if label in yields:
                lines.append("- {} Treasury: {:.3f}%".format(label, yields[label]))
        # Yield curve
        if "10Y" in yields and "3M" in yields:
            spread = yields["10Y"] - yields["3M"]
            lines.append("- 10Y-3M Spread: {:.3f}% {}".format(
                spread, "(**INVERTED** — recession signal)" if spread < 0 else "(normal)"))
        if "10Y" in yields and "5Y" in yields:
            spread_5_10 = yields["10Y"] - yields["5Y"]
            lines.append("- 10Y-5Y Spread: {:.3f}%".format(spread_5_10))

    # Dollar Index
    if "DXY" in yields:
        lines.append("\n## US Dollar Index")
        lines.append("- DXY: {:.2f}".format(yields["DXY"]))
        if yields["DXY"] > 105:
            lines.append("- **STRONG DOLLAR** — headwind for commodities and EM")
        elif yields["DXY"] < 100:
            lines.append("- **WEAK DOLLAR** — tailwind for commodities and gold")
        else:
            lines.append("- **NEUTRAL RANGE**")

    output = "\n".join(lines) + "\n"
    (CONTEXT / "sentiment.md").write_text(output)
    print("[feed-sentiment] written (P/C={}, yields={}, DXY={})".format(
        pc_ratio, len([k for k in yields if k != "DXY"]), "DXY" in yields))

if __name__ == "__main__":
    try:
        vix_price, vix_change = get_vix()
        fg_score, fg_rating = get_fear_greed()
        pc_ratio, yields = get_put_call_and_yields()
        write_output(vix_price, vix_change, fg_score, fg_rating, pc_ratio, yields)
    except Exception as e:
        print("[feed-sentiment] Error: {}".format(e), file=sys.stderr)
