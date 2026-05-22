#!/usr/bin/env python3
"""Fetch sector performance data."""
import sys, json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = ROOT / "context"
CONTEXT.mkdir(exist_ok=True)

SECTOR_MAP = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication Services",
    "XLB": "Materials",
    "XLY": "Consumer Discretionary"
}

def get_sector_data():
    """Read from price cache (populated by feed-prices.py)."""
    cache = ROOT / "data" / "price_cache.json"
    if not cache.exists():
        return {}
    data = json.loads(cache.read_text())
    sectors = {}
    for etf, name in SECTOR_MAP.items():
        if etf in data:
            sectors[etf] = {
                "name": name,
                "price": data[etf]["price"],
                "change_pct": data[etf]["change_pct"],
                "volume": data[etf]["volume"]
            }
    return sectors

def format_vol(v):
    if v >= 1_000_000: return "{:.1f}M".format(v / 1_000_000)
    if v >= 1_000: return "{:.0f}K".format(v / 1_000)
    return str(v)

def write_output(sectors):
    now = datetime.now().strftime("%Y-%m-%d %H:%M EST")
    lines = ["# Sector Performance — {}\n".format(now)]

    if not sectors:
        lines.append("No sector data available — run feed-prices.py first.")
        (CONTEXT / "sectors.md").write_text("\n".join(lines) + "\n")
        return

    # Sort by performance
    sorted_sectors = sorted(sectors.items(), key=lambda x: x[1]["change_pct"], reverse=True)

    lines.append("## Today's Rotation (best to worst)")
    for etf, d in sorted_sectors:
        sign = "+" if d["change_pct"] >= 0 else ""
        bar = "█" * max(1, int(abs(d["change_pct"]) * 5))
        direction = "▲" if d["change_pct"] >= 0 else "▼"
        lines.append("- {} {} {}: ${:.2f} ({}{}%) vol {} {}".format(
            direction, etf, d["name"], d["price"],
            sign, d["change_pct"], format_vol(d["volume"]), bar))

    # Rotation analysis
    top3 = [s for s in sorted_sectors[:3]]
    bot3 = [s for s in sorted_sectors[-3:]]

    lines.append("\n## Rotation Signal")
    defensive = {"XLU", "XLP", "XLV", "XLRE"}
    cyclical = {"XLK", "XLY", "XLI", "XLF", "XLB", "XLE"}

    top_etfs = set(e for e, _ in top3)
    if top_etfs & defensive and not (top_etfs & cyclical):
        lines.append("- **RISK-OFF**: Defensive sectors leading. Money moving to safety.")
    elif top_etfs & cyclical and not (top_etfs & defensive):
        lines.append("- **RISK-ON**: Cyclical sectors leading. Growth appetite strong.")
    else:
        lines.append("- **MIXED**: No clear rotation signal. Watch for sector leadership to clarify.")

    lines.append("\n## Leaders")
    for etf, d in top3:
        lines.append("- {} ({}): {}{}%".format(etf, d["name"], "+" if d["change_pct"] >= 0 else "", d["change_pct"]))

    lines.append("\n## Laggards")
    for etf, d in bot3:
        lines.append("- {} ({}): {}{}%".format(etf, d["name"], "+" if d["change_pct"] >= 0 else "", d["change_pct"]))

    output = "\n".join(lines) + "\n"
    (CONTEXT / "sectors.md").write_text(output)
    print("[feed-sectors] {} sectors written".format(len(sectors)))

if __name__ == "__main__":
    try:
        sectors = get_sector_data()
        write_output(sectors)
    except Exception as e:
        print("[feed-sectors] Error: {}".format(e), file=sys.stderr)
