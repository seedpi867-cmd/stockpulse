#!/usr/bin/env python3
"""Detect whether market data moved since last cycle — GLOBAL markets.

Writes context/data-freshness.md so the next cycle knows what changed.
Checks ALL global market sessions, not just US.
"""
import json
from datetime import datetime, time, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "price_cache.json"
SNAP = ROOT / "data" / "price_cache_snapshot.json"
OUT = ROOT / "context" / "data-freshness.md"

def market_sessions(now_utc):
    """Return which global market sessions are currently open."""
    sessions = []

    # US: 9:30-16:00 ET (UTC-4 EDT / UTC-5 EST)
    et = now_utc - timedelta(hours=4)
    if et.weekday() < 5:
        t = et.time()
        if time(9, 30) <= t <= time(16, 0):
            sessions.append("US (NYSE/NASDAQ)")
        elif time(4, 0) <= t < time(9, 30):
            sessions.append("US Pre-Market")
        elif time(16, 0) < t <= time(20, 0):
            sessions.append("US After-Hours")

    # Europe: 8:00-16:30 GMT (London)
    gmt = now_utc
    if gmt.weekday() < 5:
        t = gmt.time()
        if time(8, 0) <= t <= time(16, 30):
            sessions.append("Europe (FTSE/DAX)")

    # Tokyo: 9:00-15:00 JST (UTC+9)
    jst = now_utc + timedelta(hours=9)
    if jst.weekday() < 5:
        t = jst.time()
        if time(9, 0) <= t <= time(15, 0):
            sessions.append("Tokyo (Nikkei)")

    # Hong Kong: 9:30-16:00 HKT (UTC+8)
    hkt = now_utc + timedelta(hours=8)
    if hkt.weekday() < 5:
        t = hkt.time()
        if time(9, 30) <= t <= time(16, 0):
            sessions.append("Hong Kong (HSI)")

    # ASX: 10:00-16:00 AEST (UTC+10)
    aest = now_utc + timedelta(hours=10)
    if aest.weekday() < 5:
        t = aest.time()
        if time(10, 0) <= t <= time(16, 0):
            sessions.append("Australia (ASX)")

    # Crypto/Forex: always
    sessions.append("Crypto/Forex (24/7)")

    return sessions

def signature(cache):
    sig = {}
    for k, v in cache.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        sig[k] = (v.get("price"), v.get("volume"))
    return sig

def main():
    if not CACHE.exists():
        OUT.write_text("# Data Freshness\n\nNo price_cache.json yet.\n")
        return

    cur = json.loads(CACHE.read_text())
    cur_sig = signature(cur)

    prev_sig = {}
    prev_ts = None
    if SNAP.exists():
        prev = json.loads(SNAP.read_text())
        prev_sig = prev.get("_signature", {})
        prev_ts = prev.get("_snapshot_ts")

    changed = [t for t in cur_sig if list(cur_sig[t]) != list(prev_sig.get(t, []))]
    total = len(cur_sig)
    now_utc = datetime.now(timezone.utc)
    sessions = market_sessions(now_utc)
    any_equity_open = any(s for s in sessions if "Crypto" not in s)

    et = now_utc - timedelta(hours=4)
    aest = now_utc + timedelta(hours=10)

    lines = ["# Data Freshness\n"]
    lines.append("- snapshot now (UTC): {}".format(now_utc.isoformat(timespec="seconds")))
    lines.append("- snapshot now (US/Eastern): {}".format(et.isoformat(timespec="seconds")))
    lines.append("- snapshot now (AEST): {}".format(aest.isoformat(timespec="seconds")))
    lines.append("- snapshot prev (UTC): {}".format(prev_ts or "none"))
    lines.append("- tickers changed vs last snapshot: **{}/{}**".format(len(changed), total))
    if changed:
        lines.append("- changed: {}".format(", ".join(sorted(changed))))
    else:
        lines.append("- changed: none since last snapshot")

    lines.append("")
    lines.append("## Market Sessions Currently Open")
    for s in sessions:
        lines.append("- {}".format(s))

    if any_equity_open:
        lines.append("")
        lines.append("**LIVE SESSION.** Equity markets are open. Fresh price data expected.")
    elif changed:
        lines.append("")
        lines.append("**DATA MOVED.** No equity session open but tickers changed (crypto/forex/futures). Analyze the moves.")
    else:
        lines.append("")
        lines.append("**RESEARCH WINDOW.** All equity markets closed, no price changes.")
        lines.append("Use this time productively:")
        lines.append("- Search the web for overnight news, earnings, economic data, geopolitical events")
        lines.append("- Build or refine watchlists for the next session open")
        lines.append("- Study knowledge files to deepen pattern understanding")
        lines.append("- Review past trades and predictions — write detailed post-mortems")
        lines.append("- Analyze correlations between global markets (Asia->Europe->US flow)")
        lines.append("- Prepare theses for tomorrow based on tonight's data")
        lines.append("- Add new tickers to config.sh if you discover something worth tracking")
        lines.append("- You can ALWAYS search the web for news regardless of market hours")

    OUT.write_text("\n".join(lines) + "\n")

    SNAP.write_text(json.dumps({
        "_snapshot_ts": now_utc.isoformat(timespec="seconds"),
        "_signature": {k: list(v) for k, v in cur_sig.items()},
    }, indent=2))

    print("[data-freshness] {}/{} tickers changed; sessions={}".format(
        len(changed), total, len(sessions)))

if __name__ == "__main__":
    main()
