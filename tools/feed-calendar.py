#!/usr/bin/env python3
"""Fetch economic calendar — live events + earnings this week."""
import sys, json, re
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)

def fetch_calendar_rss():
    import feedparser
    events = []
    feeds = [
        "https://www.investing.com/rss/economic_calendar.rss",
        "https://rsshub.app/investing/economic-calendar",
    ]
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:
                title = entry.get("title", "").strip()
                if title:
                    events.append({
                        "title": title,
                        "date": entry.get("published", ""),
                        "summary": re.sub(r'<[^>]+>', '', entry.get("summary", ""))[:150]
                    })
            if events:
                break
        except:
            continue
    return events

def fetch_earnings():
    """Get this week's notable earnings from yfinance."""
    earnings = []
    try:
        import yfinance as yf
        # Check earnings for major tickers the agent watches
        watchlist_path = ROOT / "data" / "watchlist.json"
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META",
                   "JPM", "BAC", "GS", "WMT", "HD", "DIS", "NFLX", "AMD",
                   "CRM", "ORCL", "INTC", "BA", "CAT", "XOM", "CVX"]
        if watchlist_path.exists():
            wl = json.loads(watchlist_path.read_text())
            for t in wl.get("tickers", []) + wl.get("added_by_agent", []):
                if isinstance(t, str) and t not in tickers and "-" not in t and "=" not in t:
                    tickers.append(t)

        today = datetime.now()
        week_end = today + timedelta(days=7)

        skip = {
            "SPY", "QQQ", "DIA", "IWM", "XLK", "XLF", "XLE", "XLV", "XLI",
            "XLP", "XLU", "XLRE", "XLC", "XLB", "XLY", "SH", "SQQQ",
            "UVXY", "TLT", "GLD", "SLV", "GDX", "USO", "CPER", "SIL",
            "PPLT", "PALL", "JETS", "DBA", "INDA", "EWA", "EWJ", "EWG",
            "EWU", "FXI", "IYT",
        }
        equities = [
            t for t in tickers
            if t not in skip and "-" not in t and "=" not in t and not t.startswith("^")
        ]

        for ticker in equities[:30]:  # cap to avoid slow fetch
            try:
                t = yf.Ticker(ticker)
                cal = t.calendar
                if cal is not None and not (hasattr(cal, 'empty') and cal.empty):
                    if isinstance(cal, dict):
                        ed = cal.get("Earnings Date", None)
                        if ed:
                            # Can be a list of dates
                            dates = ed if isinstance(ed, list) else [ed]
                            for d in dates:
                                if hasattr(d, 'date'):
                                    d = d.date()
                                if isinstance(d, str):
                                    from datetime import date as dt_date
                                    d = datetime.strptime(d[:10], "%Y-%m-%d").date()
                                if today.date() <= d <= week_end.date():
                                    earnings.append({"ticker": ticker, "date": str(d)})
            except:
                continue
    except Exception as e:
        print("[feed-calendar] earnings fetch error: {}".format(e), file=sys.stderr)
    return earnings

def get_known_events():
    """Hard-coded known upcoming events — updated by the news feeder context."""
    events = []
    today = datetime.now()

    # Key known events — these are derived from news context
    known = [
        {"title": "US CPI Release (April)", "date": "2026-05-13", "impact": "HIGH",
         "note": "Core CPI consensus ~3.5%. Hot print = hawkish Fed, dollar up, gold/bonds down. Cool = dovish, risk-on."},
        {"title": "FOMC Minutes", "date": "2026-05-14", "impact": "MEDIUM",
         "note": "Watch for language on rate path and tariff inflation pass-through."},
    ]
    for k in known:
        try:
            d = datetime.strptime(k["date"], "%Y-%m-%d")
            if d >= today - timedelta(days=1):
                days_away = (d - today).days
                k["days_away"] = days_away
                events.append(k)
        except:
            continue
    return events

def write_output(rss_events, earnings, known_events):
    now = datetime.now().strftime("%Y-%m-%d %H:%M EST")
    lines = ["# Economic Calendar — {}\n".format(now)]

    # Known high-impact events first
    if known_events:
        lines.append("## Key Events This Week")
        for e in sorted(known_events, key=lambda x: x.get("days_away", 99)):
            days = e.get("days_away", "?")
            marker = "**TODAY**" if days == 0 else "**TOMORROW**" if days == 1 else "in {} days".format(days)
            lines.append("- [{}] **{}** — {} ({})".format(e["impact"], e["title"], e["date"], marker))
            if e.get("note"):
                lines.append("  {}".format(e["note"]))
        lines.append("")

    # Earnings
    if earnings:
        lines.append("## Earnings This Week")
        by_date = {}
        for e in earnings:
            by_date.setdefault(e["date"], []).append(e["ticker"])
        for date in sorted(by_date.keys()):
            lines.append("- **{}**: {}".format(date, ", ".join(by_date[date])))
        lines.append("")

    # RSS events
    if rss_events:
        lines.append("## Economic Releases")
        for e in rss_events[:15]:
            lines.append("- **{}** — {}".format(e["title"], e["date"]))
        lines.append("")

    # Standing reminders
    lines.append("## Standing Events to Track")
    standing = [
        "FOMC Rate Decision — watch for hawkish/dovish language shifts",
        "CPI Release — inflation trend is the dominant macro signal",
        "Non-Farm Payrolls — labor market strength/weakness",
        "Jobless Claims (weekly) — leading indicator",
        "PCE Price Index — Fed preferred inflation gauge",
        "ISM Manufacturing — expansion/contraction signal",
    ]
    for s in standing:
        lines.append("- {}".format(s))

    output = "\n".join(lines) + "\n"
    (CONTEXT / "calendar.md").write_text(output)
    print("[feed-calendar] {} rss + {} earnings + {} known events".format(
        len(rss_events), len(earnings), len(known_events)))

if __name__ == "__main__":
    try:
        rss_events = fetch_calendar_rss()
        earnings = fetch_earnings()
        known_events = get_known_events()
        write_output(rss_events, earnings, known_events)
    except Exception as e:
        print("[feed-calendar] Error: {}".format(e), file=sys.stderr)
