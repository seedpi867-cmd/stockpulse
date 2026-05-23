#!/usr/bin/env python3
"""
StockPulse Email Report Tool — Premium Edition
Generates and sends professional HTML email reports for the StockPulse trading agent.

Usage:
    python3 stockpulse-email.py --type weekly
    python3 stockpulse-email.py --type trade --summary "BUY NVDA 50 @ 142.50"
    python3 stockpulse-email.py --type signal --message "UVXY approaching target $40"
    python3 stockpulse-email.py --type stop --summary "UVXY stopped out at $35.40"
"""

import argparse
import json
import os
import sys
import smtplib
import tempfile
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path

# ---------- CONFIG ----------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "seedpi867@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
FROM_NAME = "StockPulse"
TO_EMAIL = "leighmcmillan20@gmail.com"

BASE_DIR = Path("/home/piagent/edge-agent")
DATA_DIR = BASE_DIR / "data"

MAX_EMAILS_PER_DAY = 10

# ---------- COLORS ----------
BG_DARK = "#0f1923"
BG_CARD = "#172a3a"
BG_CARD_ALT = "#1a3045"
BG_HEADER = "#0a1218"
ACCENT = "#00d4aa"
RED = "#ff4757"
GOLD = "#ffa502"
SIGNAL = "#7c5cff"
TEXT_PRIMARY = "#e8edf2"
TEXT_SECONDARY = "#8a9bb5"
TEXT_MUTED = "#5a6d84"
BORDER = "#1e3a50"

# ---------- DATA LOADERS ----------

def load_json(filename, default=None):
    path = DATA_DIR / filename
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}

def load_jsonl(filename):
    path = DATA_DIR / filename
    lines = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return lines

def load_text(filename):
    path = DATA_DIR / filename
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def parse_last_output(text):
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        for key in ["INNER_VOICE", "THOUGHTS", "MOOD", "TAGS", "ACTION",
                     "REASONING", "COLLISION", "NOTE_TO_FUTURE", "OVERALL", "MEMORY"]:
            if line.startswith(key + ":"):
                result[key] = line[len(key)+1:].strip()
                break
    return result

# ---------- RATE LIMIT ----------

def check_rate_limit():
    sent_log = load_jsonl("email-sent.jsonl")
    today = date.today().isoformat()
    today_count = sum(1 for e in sent_log if e.get("date", "").startswith(today))
    if today_count >= MAX_EMAILS_PER_DAY:
        print(f"Rate limit reached: {today_count}/{MAX_EMAILS_PER_DAY} emails sent today")
        sys.exit(1)
    return today_count

def log_sent(email_type, subject, summary=""):
    path = DATA_DIR / "email-sent.jsonl"
    entry = {
        "date": datetime.now().isoformat(),
        "type": email_type,
        "subject": subject,
        "summary": summary,
        "to": TO_EMAIL
    }
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ---------- CHART GENERATION ----------

def generate_chart():
    """Generate portfolio value + daily P&L chart, return PNG bytes or None."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.ticker import FuncFormatter
    except ImportError:
        print("Warning: matplotlib not available, skipping chart")
        return None

    records = load_jsonl("daily-pnl.jsonl")
    if len(records) < 2:
        return None

    # Deduplicate by date (keep last entry per date)
    by_date = {}
    for r in records:
        d = r.get("date")
        if d:
            by_date[d] = r
    records = [by_date[d] for d in sorted(by_date.keys())]

    dates = []
    values = []
    pnls = []
    for r in records:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d")
            dates.append(d)
            values.append(r.get("portfolio_value", 100000))
            pnls.append(r.get("total_pnl", 0))
        except (KeyError, ValueError):
            pass

    if len(dates) < 2:
        return None

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), gridspec_kw={"height_ratios": [2.5, 1]})
    fig.patch.set_facecolor(BG_DARK)

    for ax in (ax1, ax2):
        ax.set_facecolor(BG_DARK)
        ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(BORDER)
        ax.spines["bottom"].set_color(BORDER)
        ax.yaxis.label.set_color(TEXT_SECONDARY)

    # Portfolio value line
    ax1.plot(dates, values, color=ACCENT, linewidth=2.5, solid_capstyle="round")
    ax1.fill_between(dates, values, min(values) - 50, alpha=0.1, color=ACCENT)
    ax1.set_ylabel("Portfolio Value", fontsize=10, color=TEXT_SECONDARY)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax1.axhline(y=100000, color=TEXT_MUTED, linestyle="--", linewidth=0.8, alpha=0.5)

    # Highlight current value
    if values:
        last_val = values[-1]
        clr = ACCENT if last_val >= 100000 else RED
        ax1.scatter([dates[-1]], [last_val], color=clr, s=60, zorder=5)
        ax1.annotate(f"${last_val:,.2f}", (dates[-1], last_val),
                     textcoords="offset points", xytext=(-65, 12),
                     fontsize=10, fontweight="bold", color=clr)

    # Daily P&L bars
    bar_colors = [ACCENT if p >= 0 else RED for p in pnls]
    ax2.bar(dates, pnls, color=bar_colors, width=0.6, alpha=0.85)
    ax2.set_ylabel("Total P&L", fontsize=10, color=TEXT_SECONDARY)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:+,.0f}"))
    ax2.axhline(y=0, color=TEXT_MUTED, linewidth=0.8)

    for ax in (ax1, ax2):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha="center")

    fig.suptitle("STOCKPULSE  PERFORMANCE", fontsize=12, fontweight="bold",
                 color=TEXT_PRIMARY, y=0.98, fontfamily="monospace")

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=150, facecolor=BG_DARK, bbox_inches="tight",
                pad_inches=0.3)
    plt.close(fig)

    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)
    return data

# ---------- HTML HELPERS ----------

# Shared font stacks
F_MONO = "'Courier New', Courier, monospace"
F_BODY = "Georgia, 'Times New Roman', serif"
F_SYS = "Arial, Helvetica, sans-serif"

def esc(text):
    """Basic HTML escape."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def pnl_color(val):
    try:
        v = float(val)
        if v > 0: return ACCENT
        elif v < 0: return RED
        return TEXT_SECONDARY
    except (ValueError, TypeError):
        return TEXT_SECONDARY

def pnl_prefix(val):
    try:
        v = float(val)
        return "+" if v > 0 else ""
    except (ValueError, TypeError):
        return ""

def mood_bar_html(label, value):
    """Build a single mood bar row for the mood section."""
    pct = max(0, min(100, int(float(value) * 100)))
    # Color logic
    if label.lower() in ("frustration", "caution"):
        bar_color = RED if pct > 60 else (GOLD if pct > 35 else ACCENT)
    else:
        bar_color = ACCENT if pct > 70 else (GOLD if pct < 30 else ACCENT)
        if pct < 30:
            bar_color = RED
    right_radius = "border-radius:4px;" if pct >= 100 else ""
    return f'''<tr>
<td style="padding:6px 14px 6px 0;color:{TEXT_SECONDARY};font-size:14px;font-family:{F_MONO};text-transform:uppercase;letter-spacing:1px;width:130px;vertical-align:middle;">{esc(label)}</td>
<td style="padding:6px 0;width:100%;vertical-align:middle;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr>
<td style="background:{bar_color};height:10px;width:{pct}%;border-radius:5px 0 0 5px;{right_radius}"></td>
<td style="background:{BG_DARK};height:10px;width:{100-pct}%;border-radius:0 5px 5px 0;"></td>
</tr>
</table>
</td>
<td style="padding:6px 0 6px 12px;color:{bar_color};font-size:14px;font-family:{F_MONO};font-weight:bold;white-space:nowrap;vertical-align:middle;">{pct}%</td>
</tr>'''

def tag_pill(tag):
    return f'<span style="display:inline-block;background:{BG_DARK};color:{ACCENT};border:1px solid {ACCENT}44;padding:5px 14px;border-radius:14px;font-size:13px;font-family:{F_MONO};margin:3px 4px;letter-spacing:0.5px;">{esc(tag)}</span>'

# ---------- SECTION BUILDERS ----------

def section_header(title):
    """Section header label: small uppercase."""
    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr><td style="padding:0 0 12px 0;">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:3px;text-transform:uppercase;font-weight:bold;">{esc(title)}</span>
</td></tr></table>'''

def build_header(cycle, date_str, time_str, badge_color, badge_text):
    """Top brand header bar."""
    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr>
<td style="padding:32px 0 16px 0;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr>
<td style="vertical-align:middle;">
<span style="font-size:28px;color:{ACCENT};font-family:{F_MONO};font-weight:bold;letter-spacing:6px;">&#9670; STOCKPULSE</span>
</td>
<td style="text-align:right;vertical-align:middle;">
<span style="display:inline-block;background:{badge_color};color:{BG_DARK};font-size:12px;font-family:{F_MONO};font-weight:bold;padding:6px 16px;border-radius:4px;letter-spacing:2px;">{esc(badge_text)}</span>
</td>
</tr>
</table>
</td>
</tr>
<tr>
<td style="padding:0 0 20px 0;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr>
<td>
<span style="font-size:14px;color:{TEXT_SECONDARY};font-family:{F_SYS};line-height:1.6;">{esc(date_str)}</span>
<span style="font-size:14px;color:{TEXT_MUTED};font-family:{F_SYS};margin-left:8px;">&bull; {esc(time_str)}</span>
</td>
<td style="text-align:right;">
<span style="display:inline-block;background:{ACCENT}15;border:1px solid {ACCENT}33;color:{ACCENT};font-size:12px;font-family:{F_MONO};padding:5px 14px;border-radius:20px;letter-spacing:1.5px;">CYCLE {esc(str(cycle))}</span>
</td>
</tr>
</table>
</td>
</tr>
<tr><td style="border-bottom:1px solid {BORDER};height:1px;"></td></tr>
</table>'''

def build_action_box(badge_color, badge_text, action_text, reasoning_text=""):
    """Colored left-border action/signal box."""
    reasoning_html = ""
    if reasoning_text:
        # Truncate reasoning at 600 chars
        r = reasoning_text[:600] + ("..." if len(reasoning_text) > 600 else "")
        reasoning_html = f'''<tr><td style="padding-top:12px;border-top:1px solid {BORDER};">
<p style="margin:0;font-size:15px;color:{TEXT_SECONDARY};font-family:{F_BODY};line-height:1.7;">{esc(r)}</p>
</td></tr>'''

    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin:24px 0;">
<tr><td style="background:{BG_CARD};border-left:5px solid {badge_color};border-radius:0 8px 8px 0;padding:24px 28px;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr><td style="padding-bottom:10px;">
<span style="font-size:12px;color:{badge_color};font-family:{F_MONO};letter-spacing:2.5px;text-transform:uppercase;font-weight:bold;">{esc(badge_text)}</span>
</td></tr>
<tr><td style="padding-bottom:8px;">
<span style="font-size:18px;color:{TEXT_PRIMARY};font-family:{F_BODY};font-weight:bold;line-height:1.6;">{esc(action_text)}</span>
</td></tr>
{reasoning_html}
</table>
</td></tr></table>'''

def build_portfolio_cards(port_value, total_pnl, total_pnl_pct, cash):
    """Three big-number metric cards."""
    pnl_c = pnl_color(total_pnl)
    pnl_sign = pnl_prefix(total_pnl)

    def card(label, value_html, subtitle_html=""):
        sub = f'<tr><td style="padding-top:4px;">{subtitle_html}</td></tr>' if subtitle_html else ""
        return f'''<td style="padding:0 6px;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr><td style="background:{BG_CARD};border-radius:8px;padding:22px 18px;text-align:center;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr><td style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2.5px;text-transform:uppercase;padding-bottom:10px;font-weight:bold;">{label}</td></tr>
<tr><td>{value_html}</td></tr>
{sub}
</table>
</td></tr></table>
</td>'''

    val_card = card("PORTFOLIO",
        f'<span style="font-size:28px;color:{TEXT_PRIMARY};font-family:{F_MONO};font-weight:bold;">${port_value:,.2f}</span>')

    pnl_card = card("TOTAL P&amp;L",
        f'<span style="font-size:28px;color:{pnl_c};font-family:{F_MONO};font-weight:bold;">{pnl_sign}${total_pnl:,.2f}</span>',
        f'<span style="font-size:14px;color:{pnl_c};font-family:{F_MONO};">{pnl_sign}{total_pnl_pct:.2f}%</span>')

    cash_card = card("CASH",
        f'<span style="font-size:28px;color:{TEXT_PRIMARY};font-family:{F_MONO};font-weight:bold;">${cash:,.2f}</span>')

    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;">
<tr>{val_card}{pnl_card}{cash_card}</tr>
</table>'''

def build_stats_row(perf):
    """Single-row stats strip: trades, win rate, W/L, best, worst, max DD, streak."""
    total_trades = perf.get("total_trades", 0)
    win_rate = perf.get("win_rate", 0)
    wins = perf.get("wins", 0)
    losses = perf.get("losses", 0)
    best_trade = perf.get("best_trade", 0)
    worst_trade = perf.get("worst_trade", 0)
    max_dd = perf.get("max_drawdown", 0)
    streak = perf.get("streak", 0)
    streak_type = perf.get("streak_type", "")
    streak_str = f"{streak}{'W' if streak_type == 'win' else 'L'}" if streak else "-"

    def stat_cell(label, value, color=TEXT_PRIMARY):
        return f'''<td style="text-align:center;padding:6px 10px;">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:1.5px;text-transform:uppercase;font-weight:bold;">{label}</span><br/>
<span style="font-size:16px;color:{color};font-family:{F_MONO};font-weight:bold;line-height:2;">{value}</span>
</td>'''

    wr_color = ACCENT if win_rate >= 50 else RED
    sk_color = ACCENT if streak_type == "win" else RED

    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;">
<tr><td style="background:{BG_CARD};border-radius:8px;padding:16px 12px;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr>
{stat_cell("TRADES", total_trades)}
{stat_cell("WIN RATE", f"{win_rate:.0f}%", wr_color)}
{stat_cell("W / L", f"{wins}/{losses}")}
{stat_cell("BEST", f"${best_trade:+,.2f}", ACCENT)}
{stat_cell("WORST", f"${worst_trade:,.2f}", RED)}
{stat_cell("MAX DD", f"-${max_dd:,.2f}", RED)}
{stat_cell("STREAK", streak_str, sk_color)}
</tr>
</table>
</td></tr></table>'''

def build_chart_section(chart_cid):
    if not chart_cid:
        return ""
    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;">
<tr><td style="background:{BG_CARD};border-radius:8px;padding:18px;text-align:center;">
<img src="cid:{chart_cid}" alt="Performance Chart" style="max-width:100%;height:auto;border-radius:6px;" />
</td></tr></table>'''

def build_positions_table(positions):
    """Open positions table with readable 15px cells."""
    if not positions:
        return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;">
<tr><td style="background:{BG_CARD};border-radius:8px;padding:24px;text-align:center;">
<span style="font-size:16px;color:{TEXT_MUTED};font-family:{F_MONO};">No open positions &mdash; 100% cash</span>
</td></tr></table>'''

    rows = ""
    for i, pos in enumerate(positions):
        ticker = pos.get("ticker", "?")
        shares = pos.get("shares", 0)
        entry = pos.get("entry_price", 0)
        current = pos.get("current_price", 0)
        upnl = pos.get("unrealized_pnl", 0)
        upnl_pct = pos.get("unrealized_pnl_pct", 0)
        stop = pos.get("stop", 0)
        target = pos.get("target", 0)
        direction = pos.get("direction", "long")
        conviction = pos.get("conviction", 0)

        row_bg = BG_CARD if i % 2 == 0 else BG_CARD_ALT
        upnl_c = pnl_color(upnl)
        dir_icon = "&#9650;" if direction == "long" else "&#9660;"
        dir_color = ACCENT if direction == "long" else RED

        conv_pct = int(float(conviction or 0) * 100)
        conv_color = ACCENT if conv_pct >= 60 else (GOLD if conv_pct >= 40 else TEXT_MUTED)

        rows += f'''<tr style="background:{row_bg};">
<td style="padding:14px 16px;font-family:{F_MONO};font-size:15px;font-weight:bold;color:{TEXT_PRIMARY};border-bottom:1px solid {BORDER};">
<span style="color:{dir_color};font-size:12px;">{dir_icon}</span> {esc(ticker)}
</td>
<td style="padding:14px 12px;font-family:{F_MONO};font-size:15px;color:{TEXT_SECONDARY};border-bottom:1px solid {BORDER};text-align:center;">{shares}</td>
<td style="padding:14px 12px;font-family:{F_MONO};font-size:15px;color:{TEXT_SECONDARY};border-bottom:1px solid {BORDER};text-align:center;">${entry:,.2f}</td>
<td style="padding:14px 12px;font-family:{F_MONO};font-size:15px;color:{TEXT_PRIMARY};font-weight:bold;border-bottom:1px solid {BORDER};text-align:center;">${current:,.2f}</td>
<td style="padding:14px 12px;font-family:{F_MONO};font-size:15px;color:{upnl_c};font-weight:bold;border-bottom:1px solid {BORDER};text-align:center;">
{pnl_prefix(upnl)}${upnl:,.2f}<br/>
<span style="font-size:13px;">{pnl_prefix(upnl_pct)}{upnl_pct:.2f}%</span>
</td>
<td style="padding:14px 12px;font-family:{F_MONO};font-size:15px;color:{RED};border-bottom:1px solid {BORDER};text-align:center;">${stop:,.2f}</td>
<td style="padding:14px 12px;font-family:{F_MONO};font-size:15px;color:{ACCENT};border-bottom:1px solid {BORDER};text-align:center;">${target:,.2f}</td>
<td style="padding:14px 12px;border-bottom:1px solid {BORDER};text-align:center;">
<table cellpadding="0" cellspacing="0" border="0" width="60" style="border-collapse:collapse;display:inline-table;">
<tr>
<td style="background:{conv_color};height:6px;width:{conv_pct}%;border-radius:3px 0 0 3px;"></td>
<td style="background:{BG_DARK};height:6px;width:{100-conv_pct}%;border-radius:0 3px 3px 0;"></td>
</tr>
</table>
<br/><span style="font-size:13px;color:{conv_color};font-family:{F_MONO};">{conviction:.0%}</span>
</td>
</tr>'''

    th_style = f"padding:12px 12px;font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;border-bottom:2px solid {ACCENT}44;font-weight:bold;"

    return f'''{section_header("OPEN POSITIONS")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;border-radius:8px;overflow:hidden;">
<tr style="background:{BG_HEADER};">
<td style="{th_style}text-align:left;padding-left:16px;">TICKER</td>
<td style="{th_style}text-align:center;">QTY</td>
<td style="{th_style}text-align:center;">ENTRY</td>
<td style="{th_style}text-align:center;">CURRENT</td>
<td style="{th_style}text-align:center;">P&amp;L</td>
<td style="{th_style}text-align:center;">STOP</td>
<td style="{th_style}text-align:center;">TARGET</td>
<td style="{th_style}text-align:center;">CONV</td>
</tr>
{rows}
</table>'''

def build_trade_detail(summary, trades_data=None):
    """Trade detail box for trade-type emails."""
    # Parse summary: e.g. "BUY NVDA 50 @ 142.50"
    parts = summary.split() if summary else []
    action_word = parts[0] if len(parts) > 0 else "TRADE"
    ticker = parts[1] if len(parts) > 1 else ""
    detail = " ".join(parts[2:]) if len(parts) > 2 else ""

    action_color = ACCENT if action_word.upper() in ("BUY", "LONG") else RED

    # Try to find matching trade in trades data for reasoning
    reasoning = ""
    if trades_data and ticker:
        for t in reversed(trades_data):
            if t.get("ticker", "").upper() == ticker.upper():
                reasoning = t.get("reasoning", "")
                break

    reasoning_html = ""
    if reasoning:
        r = reasoning[:500] + ("..." if len(reasoning) > 500 else "")
        reasoning_html = f'''<tr><td colspan="2" style="padding:16px 0 0 0;border-top:1px solid {BORDER};">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;font-weight:bold;">REASONING</span>
<p style="margin:8px 0 0 0;font-size:15px;color:{TEXT_SECONDARY};font-family:{F_BODY};line-height:1.7;">{esc(r)}</p>
</td></tr>'''

    return f'''{section_header("TRADE DETAIL")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;background:{BG_CARD};border-radius:8px;border-left:5px solid {action_color};">
<tr><td style="padding:24px 28px;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr>
<td style="vertical-align:top;">
<span style="font-size:26px;color:{action_color};font-family:{F_MONO};font-weight:bold;">{esc(action_word)}</span>
<span style="font-size:26px;color:{TEXT_PRIMARY};font-family:{F_MONO};font-weight:bold;margin-left:8px;">{esc(ticker)}</span>
</td>
<td style="text-align:right;vertical-align:top;">
<span style="font-size:16px;color:{TEXT_SECONDARY};font-family:{F_MONO};">{esc(detail)}</span>
</td>
</tr>
{reasoning_html}
</table>
</td></tr></table>'''

def build_signal_detail(message):
    """Signal description box for signal-type emails."""
    return f'''{section_header("SIGNAL DETECTED")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;background:{BG_CARD};border-radius:8px;border-left:5px solid {SIGNAL};">
<tr><td style="padding:24px 28px;">
<span style="font-size:12px;color:{SIGNAL};font-family:{F_MONO};letter-spacing:2.5px;text-transform:uppercase;font-weight:bold;">&#9670; SIGNAL</span>
<p style="margin:12px 0 0 0;font-size:18px;color:{TEXT_PRIMARY};font-family:{F_BODY};font-weight:bold;line-height:1.6;">{esc(message)}</p>
</td></tr></table>'''

def build_stop_detail(summary, trades_data=None):
    """Stop detail box with P&L for stop-type emails."""
    parts = summary.split() if summary else []
    ticker = parts[0] if len(parts) > 0 else ""
    detail = " ".join(parts[1:]) if len(parts) > 1 else summary

    # Find the closed trade
    pnl_val = None
    reasoning = ""
    if trades_data and ticker:
        for t in reversed(trades_data):
            if t.get("ticker", "").upper() == ticker.upper() and t.get("pnl") is not None:
                pnl_val = t.get("pnl", 0)
                reasoning = t.get("reasoning", "")
                break

    pnl_html = ""
    if pnl_val is not None:
        pc = pnl_color(pnl_val)
        pnl_html = f'''<tr><td style="padding-top:12px;">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;font-weight:bold;">REALIZED P&amp;L</span><br/>
<span style="font-size:26px;color:{pc};font-family:{F_MONO};font-weight:bold;">{pnl_prefix(pnl_val)}${pnl_val:,.2f}</span>
</td></tr>'''

    reasoning_html = ""
    if reasoning:
        r = reasoning[:500] + ("..." if len(reasoning) > 500 else "")
        reasoning_html = f'''<tr><td style="padding-top:14px;border-top:1px solid {BORDER};">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;font-weight:bold;">POST-MORTEM</span>
<p style="margin:8px 0 0 0;font-size:15px;color:{TEXT_SECONDARY};font-family:{F_BODY};line-height:1.7;">{esc(r)}</p>
</td></tr>'''

    return f'''{section_header("STOP TRIGGERED")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;background:{BG_CARD};border-radius:8px;border-left:5px solid {RED};">
<tr><td style="padding:24px 28px;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr><td>
<span style="font-size:12px;color:{RED};font-family:{F_MONO};letter-spacing:2.5px;text-transform:uppercase;font-weight:bold;">&#9670; STOPPED OUT</span>
<p style="margin:12px 0 0 0;font-size:18px;color:{TEXT_PRIMARY};font-family:{F_BODY};font-weight:bold;line-height:1.6;">{esc(summary)}</p>
</td></tr>
{pnl_html}
{reasoning_html}
</table>
</td></tr></table>'''

def build_weekly_pnl_summary(pnl_records):
    """Week's P&L summary for weekly emails."""
    if not pnl_records:
        return ""
    # Get last 7 days
    today = date.today()
    week_ago = today - timedelta(days=7)
    week_records = []
    for r in pnl_records:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d").date()
            if d >= week_ago:
                week_records.append(r)
        except (KeyError, ValueError):
            pass

    if not week_records:
        return ""

    # Deduplicate by date
    by_date = {}
    for r in week_records:
        by_date[r["date"]] = r
    week_records = [by_date[d] for d in sorted(by_date.keys())]

    if len(week_records) >= 2:
        start_val = week_records[0].get("portfolio_value", 100000)
        end_val = week_records[-1].get("portfolio_value", 100000)
        week_change = end_val - start_val
        week_pct = ((end_val / start_val) - 1) * 100 if start_val else 0
    else:
        week_change = 0
        week_pct = 0

    wc = pnl_color(week_change)
    ws = pnl_prefix(week_change)

    rows = ""
    for r in week_records:
        d = r.get("date", "")
        day = r.get("day", "")[:3]
        pv = r.get("portfolio_value", 0)
        tp = r.get("total_pnl", 0)
        pc = pnl_color(tp)
        ps = pnl_prefix(tp)
        npos = r.get("positions", 0)
        rows += f'''<tr>
<td style="padding:10px 14px;font-size:15px;color:{TEXT_SECONDARY};font-family:{F_MONO};border-bottom:1px solid {BORDER};">{esc(day)} {esc(d)}</td>
<td style="padding:10px 14px;font-size:15px;color:{TEXT_PRIMARY};font-family:{F_MONO};border-bottom:1px solid {BORDER};text-align:right;font-weight:bold;">${pv:,.2f}</td>
<td style="padding:10px 14px;font-size:15px;color:{pc};font-family:{F_MONO};border-bottom:1px solid {BORDER};text-align:right;font-weight:bold;">{ps}${tp:,.2f}</td>
<td style="padding:10px 14px;font-size:15px;color:{TEXT_MUTED};font-family:{F_MONO};border-bottom:1px solid {BORDER};text-align:center;">{npos}</td>
</tr>'''

    return f'''{section_header("WEEK PERFORMANCE")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:8px;">
<tr><td style="background:{BG_CARD};border-radius:8px;padding:22px 24px;text-align:center;">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2.5px;font-weight:bold;">WEEK CHANGE</span><br/>
<span style="font-size:30px;color:{wc};font-family:{F_MONO};font-weight:bold;line-height:2;">{ws}${week_change:,.2f}</span>
<span style="font-size:16px;color:{wc};font-family:{F_MONO};margin-left:8px;">({ws}{week_pct:.2f}%)</span>
</td></tr></table>
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;border-radius:8px;overflow:hidden;">
<tr style="background:{BG_HEADER};">
<td style="padding:10px 14px;font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;border-bottom:2px solid {ACCENT}44;font-weight:bold;">DATE</td>
<td style="padding:10px 14px;font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;border-bottom:2px solid {ACCENT}44;text-align:right;font-weight:bold;">VALUE</td>
<td style="padding:10px 14px;font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;border-bottom:2px solid {ACCENT}44;text-align:right;font-weight:bold;">P&amp;L</td>
<td style="padding:10px 14px;font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;border-bottom:2px solid {ACCENT}44;text-align:center;font-weight:bold;">POS</td>
</tr>
{rows}
</table>'''

def build_weekly_trades(trades_data):
    """List of all trades this week for weekly emails."""
    today = date.today()
    week_ago = today - timedelta(days=7)
    week_trades = []
    for t in trades_data:
        ts = t.get("timestamp", "")
        try:
            td = datetime.fromisoformat(ts).date()
            if td >= week_ago:
                week_trades.append(t)
        except (ValueError, TypeError):
            pass

    if not week_trades:
        return ""

    rows = ""
    for t in week_trades:
        action = t.get("action", "?")
        ticker = t.get("ticker", "?")
        shares = t.get("shares", 0)
        price = t.get("price", 0)
        pnl = t.get("pnl")
        ts = t.get("timestamp", "")
        try:
            td = datetime.fromisoformat(ts)
            date_str = td.strftime("%b %d")
        except (ValueError, TypeError):
            date_str = "?"

        act_color = ACCENT if action.upper() in ("BUY", "LONG") else RED
        pnl_html = ""
        if pnl is not None:
            pc = pnl_color(pnl)
            pnl_html = f'<span style="color:{pc};font-weight:bold;">{pnl_prefix(pnl)}${pnl:,.2f}</span>'
        else:
            pnl_html = f'<span style="color:{TEXT_MUTED};">open</span>'

        rows += f'''<tr style="background:{BG_CARD};">
<td style="padding:12px 14px;font-size:15px;color:{TEXT_MUTED};font-family:{F_MONO};border-bottom:1px solid {BORDER};">{esc(date_str)}</td>
<td style="padding:12px 14px;font-size:15px;color:{act_color};font-family:{F_MONO};font-weight:bold;border-bottom:1px solid {BORDER};">{esc(action)}</td>
<td style="padding:12px 14px;font-size:15px;color:{TEXT_PRIMARY};font-family:{F_MONO};font-weight:bold;border-bottom:1px solid {BORDER};">{esc(ticker)}</td>
<td style="padding:12px 14px;font-size:15px;color:{TEXT_SECONDARY};font-family:{F_MONO};border-bottom:1px solid {BORDER};text-align:center;">{shares}</td>
<td style="padding:12px 14px;font-size:15px;color:{TEXT_SECONDARY};font-family:{F_MONO};border-bottom:1px solid {BORDER};text-align:right;">${price:,.2f}</td>
<td style="padding:12px 14px;font-size:15px;font-family:{F_MONO};border-bottom:1px solid {BORDER};text-align:right;">{pnl_html}</td>
</tr>'''

    th_style = f"padding:10px 14px;font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;border-bottom:2px solid {ACCENT}44;font-weight:bold;"

    return f'''{section_header("TRADES THIS WEEK")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;border-radius:8px;overflow:hidden;">
<tr style="background:{BG_HEADER};">
<td style="{th_style}">DATE</td>
<td style="{th_style}">ACTION</td>
<td style="{th_style}">TICKER</td>
<td style="{th_style}text-align:center;">QTY</td>
<td style="{th_style}text-align:right;">PRICE</td>
<td style="{th_style}text-align:right;">P&amp;L</td>
</tr>
{rows}
</table>'''

def build_mind_section(last_output):
    """Agent mind: inner voice, collision, thoughts, note to future."""
    inner_voice = last_output.get("INNER_VOICE", "")
    collision = last_output.get("COLLISION", "")
    thoughts = last_output.get("THOUGHTS", "")
    note_future = last_output.get("NOTE_TO_FUTURE", "")

    if not any([inner_voice, collision, thoughts, note_future]):
        return ""

    mind_rows = ""
    if inner_voice:
        mind_rows += f'''<tr><td style="padding:18px 22px;border-bottom:1px solid {BORDER};">
<span style="font-size:12px;color:{ACCENT};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;font-weight:bold;">INNER VOICE</span>
<p style="margin:10px 0 0 0;font-size:16px;color:{TEXT_PRIMARY};font-family:{F_BODY};line-height:1.7;font-style:italic;">
&ldquo;{esc(inner_voice)}&rdquo;
</p>
</td></tr>'''

    if collision:
        mind_rows += f'''<tr><td style="padding:18px 22px;border-bottom:1px solid {BORDER};">
<span style="font-size:12px;color:{GOLD};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;font-weight:bold;">&#9889; SIGNAL COLLISION</span>
<p style="margin:10px 0 0 0;font-size:16px;color:{TEXT_SECONDARY};font-family:{F_BODY};line-height:1.7;">
{esc(collision)}
</p>
</td></tr>'''

    if thoughts:
        mind_rows += f'''<tr><td style="padding:18px 22px;border-bottom:1px solid {BORDER};">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;font-weight:bold;">THOUGHTS</span>
<p style="margin:10px 0 0 0;font-size:16px;color:{TEXT_SECONDARY};font-family:{F_BODY};line-height:1.7;">
{esc(thoughts)}
</p>
</td></tr>'''

    if note_future:
        mind_rows += f'''<tr><td style="padding:18px 22px;">
<span style="font-size:12px;color:{SIGNAL};font-family:{F_MONO};letter-spacing:2px;text-transform:uppercase;font-weight:bold;">&#128337; NOTE TO FUTURE SELF</span>
<p style="margin:10px 0 0 0;font-size:16px;color:{TEXT_SECONDARY};font-family:{F_BODY};line-height:1.7;">
{esc(note_future)}
</p>
</td></tr>'''

    return f'''{section_header("AGENT MIND")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;background:{BG_CARD};border-radius:8px;overflow:hidden;">
{mind_rows}
</table>'''

def build_mood_section(mood):
    """Mood state bars + overall text."""
    mood_metrics = [
        ("Confidence", mood.get("confidence", 0)),
        ("Conviction", mood.get("conviction", 0)),
        ("Satisfaction", mood.get("satisfaction", 0)),
        ("Curiosity", mood.get("curiosity", 0)),
        ("Caution", mood.get("caution", 0)),
        ("Frustration", mood.get("frustration", 0)),
    ]
    bars = "".join(mood_bar_html(label, val) for label, val in mood_metrics)

    overall_text = mood.get("overall", "")
    overall_html = ""
    if overall_text:
        overall_html = f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-top:14px;border-top:1px solid {BORDER};">
<tr><td style="padding-top:14px;">
<p style="margin:0;font-size:15px;color:{TEXT_SECONDARY};font-family:{F_BODY};line-height:1.6;font-style:italic;">{esc(overall_text)}</p>
</td></tr></table>'''

    return f'''{section_header("AGENT MOOD")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;">
<tr><td style="background:{BG_CARD};border-radius:8px;padding:22px 24px;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
{bars}
</table>
{overall_html}
</td></tr></table>'''

def build_tags_section(tags_text):
    """Focus tags cloud."""
    if not tags_text:
        return ""
    tags = [t.strip() for t in tags_text.split(",") if t.strip()]
    if not tags:
        return ""
    pills = " ".join(tag_pill(t) for t in tags)
    return f'''{section_header("FOCUS TAGS")}
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;">
<tr><td style="background:{BG_CARD};border-radius:8px;padding:18px 20px;">
{pills}
</td></tr></table>'''

def build_strategy_section(strategy):
    """Strategy evolution — deduplicated rules."""
    evolved = strategy.get("evolved_rules", [])
    lessons = strategy.get("lessons_count", 0)
    rating = strategy.get("overall_rating", "")

    if not evolved:
        return ""

    # Deduplicate and get latest 5 unique rules
    seen = set()
    unique_rules = []
    for r in reversed(evolved):
        if r not in seen:
            seen.add(r)
            unique_rules.append(r)
        if len(unique_rules) >= 5:
            break
    unique_rules.reverse()

    rules_html = ""
    for rule in unique_rules:
        is_review = rule.startswith("POSITION REVIEW:")
        icon_color = GOLD if is_review else ACCENT
        icon = "&#128270;" if is_review else "&#9889;"
        rules_html += f'''<tr><td style="padding:12px 18px;border-bottom:1px solid {BORDER};">
<span style="font-size:14px;color:{icon_color};font-family:{F_MONO};">{icon}</span>
<span style="font-size:15px;color:{TEXT_SECONDARY};font-family:{F_BODY};margin-left:8px;line-height:1.6;">{esc(rule)}</span>
</td></tr>'''

    meta = f'<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};margin-left:14px;">{lessons} lessons &bull; {esc(rating)}</span>' if lessons or rating else ""

    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;">
<tr><td style="padding:0 0 12px 0;">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:3px;text-transform:uppercase;font-weight:bold;">STRATEGY ENGINE</span>
{meta}
</td></tr></table>
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;margin-bottom:24px;background:{BG_CARD};border-radius:8px;overflow:hidden;">
{rules_html}
</table>'''

def build_footer(cycle):
    """Email footer."""
    return f'''<table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse;border-top:1px solid {BORDER};margin-top:8px;">
<tr><td style="padding:24px 0;text-align:center;">
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_MONO};letter-spacing:3px;">&#9670; STOCKPULSE</span><br/>
<span style="font-size:13px;color:{TEXT_MUTED};font-family:{F_SYS};line-height:2;">
Autonomous trading intelligence on Raspberry Pi 5 &bull; Cycle {esc(str(cycle))}
</span><br/>
<span style="font-size:12px;color:{TEXT_MUTED};font-family:{F_SYS};margin-top:4px;display:inline-block;">
This is an automated report. All trades are simulated on paper.
</span>
</td></tr></table>'''

# ---------- MAIN HTML BUILDER ----------

def build_email_html(email_type, summary="", message="", chart_cid=None):
    """Build the complete email HTML for the given type."""
    portfolio = load_json("portfolio.json", {})
    perf = load_json("performance.json", {})
    mood = load_json("mood.json", {})
    strategy = load_json("strategy.json", {})
    last_output = parse_last_output(load_text("last-output.txt"))
    cycle = load_text("cycle.txt") or "?"
    trades_data = load_jsonl("trades.jsonl")
    pnl_records = load_jsonl("daily-pnl.jsonl")

    cash = portfolio.get("cash", 0)
    positions = portfolio.get("positions", [])
    port_value = perf.get("portfolio_value", 100000)
    total_pnl = perf.get("total_pnl", 0)
    total_pnl_pct = perf.get("total_pnl_pct", 0)

    now = datetime.now()
    date_str = now.strftime("%A, %B %d %Y")
    time_str = now.strftime("%I:%M %p")

    # Type configuration
    type_configs = {
        "weekly": (ACCENT, "WEEKLY BRIEFING"),
        "trade": (GOLD, "TRADE EXECUTED"),
        "signal": (SIGNAL, "SIGNAL DETECTED"),
        "stop": (RED, "STOP TRIGGERED"),
    }
    badge_color, badge_text = type_configs.get(email_type, (ACCENT, "REPORT"))

    # Subject line
    pnl_sign = pnl_prefix(total_pnl)
    if email_type == "weekly":
        subject = f"◈ StockPulse Weekly | ${port_value:,.2f} | {pnl_sign}${total_pnl:,.2f} P&L | Cycle {cycle}"
    elif email_type == "trade":
        subject = f"◈ StockPulse Trade | {summary or 'Trade Executed'}"
    elif email_type == "signal":
        subject = f"◈ StockPulse Signal | {message or 'Setup Detected'}"
    elif email_type == "stop":
        subject = f"◈ StockPulse Stop | {summary or 'Stop Hit'}"
    else:
        subject = f"◈ StockPulse Report | Cycle {cycle}"

    # --- Build sections ---
    action_text = last_output.get("ACTION", summary or message or "No action this cycle")
    reasoning_text = last_output.get("REASONING", "")

    # Common sections
    header = build_header(cycle, date_str, time_str, badge_color, badge_text)
    action_box = build_action_box(badge_color, badge_text, action_text, reasoning_text)
    portfolio_cards = build_portfolio_cards(port_value, total_pnl, total_pnl_pct, cash)
    chart_section = build_chart_section(chart_cid)
    positions_section = build_positions_table(positions)
    footer = build_footer(cycle)

    # Type-specific sections
    type_specific = ""
    if email_type == "trade" and summary:
        type_specific += build_trade_detail(summary, trades_data)
    elif email_type == "signal" and message:
        type_specific += build_signal_detail(message)
    elif email_type == "stop" and summary:
        type_specific += build_stop_detail(summary, trades_data)

    # Stats row (all types)
    stats_row = build_stats_row(perf)

    # Weekly-only sections
    weekly_sections = ""
    if email_type == "weekly":
        weekly_sections += build_weekly_pnl_summary(pnl_records)
        weekly_sections += build_weekly_trades(trades_data)
        weekly_sections += build_mind_section(last_output)
        weekly_sections += build_mood_section(mood)
        weekly_sections += build_strategy_section(strategy)
        weekly_sections += build_tags_section(last_output.get("TAGS", ""))

    # --- Assemble ---
    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>StockPulse Report</title>
</head>
<body style="margin:0;padding:0;background:{BG_DARK};font-family:{F_SYS};-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">

<table cellpadding="0" cellspacing="0" border="0" width="100%" style="background:{BG_DARK};border-collapse:collapse;">
<tr><td align="center" style="padding:0;">

<table cellpadding="0" cellspacing="0" border="0" width="640" style="border-collapse:collapse;max-width:640px;width:100%;">

<!-- Header -->
<tr><td style="padding:0 32px;">
{header}
</td></tr>

<!-- Body -->
<tr><td style="padding:0 32px;">

{type_specific}

{action_box}

{portfolio_cards}

{stats_row}

{chart_section}

{positions_section}

{weekly_sections}

</td></tr>

<!-- Footer -->
<tr><td style="padding:0 32px 32px 32px;">
{footer}
</td></tr>

</table>

</td></tr>
</table>

</body>
</html>'''

    return subject, html

# ---------- SEND ----------

def send_email(email_type, summary="", message=""):
    today_count = check_rate_limit()

    # Generate chart
    chart_data = generate_chart()
    chart_cid = "stockpulse_chart" if chart_data else None

    subject, html = build_email_html(email_type, summary=summary, message=message, chart_cid=chart_cid)

    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = TO_EMAIL

    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)

    # Plain text fallback
    portfolio = load_json("portfolio.json", {})
    perf = load_json("performance.json", {})
    cycle = load_text("cycle.txt")
    plain = f"""StockPulse Report - Cycle {cycle}
Type: {email_type.upper()}
Portfolio: ${perf.get('portfolio_value', 0):,.2f}
Total P&L: ${perf.get('total_pnl', 0):,.2f}
Cash: ${portfolio.get('cash', 0):,.2f}
Positions: {len(portfolio.get('positions', []))}
{f'Action: {summary}' if summary else ''}
{f'Signal: {message}' if message else ''}
"""
    msg_alt.attach(MIMEText(plain, "plain"))
    msg_alt.attach(MIMEText(html, "html"))

    # Attach chart
    if chart_data and chart_cid:
        img = MIMEImage(chart_data, _subtype="png")
        img.add_header("Content-ID", f"<{chart_cid}>")
        img.add_header("Content-Disposition", "inline", filename="chart.png")
        msg.attach(img)

    # Send
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"Sent {email_type} email: {subject}")
        print(f"  To: {TO_EMAIL}")
        print(f"  Chart: {'embedded' if chart_data else 'skipped'}")
        print(f"  Daily count: {today_count + 1}/{MAX_EMAILS_PER_DAY}")
    except Exception as e:
        print(f"FAILED to send email: {e}", file=sys.stderr)
        sys.exit(1)

    log_sent(email_type, subject, summary or message)

# ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(
        description="StockPulse email report tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 stockpulse-email.py --type weekly
  python3 stockpulse-email.py --type trade --summary "BUY NVDA 50 @ 142.50"
  python3 stockpulse-email.py --type signal --message "UVXY approaching target $40"
  python3 stockpulse-email.py --type stop --summary "UVXY stopped out at $35.40"
""")
    parser.add_argument("--type", required=True, choices=["weekly", "trade", "signal", "stop"],
                        help="Email report type")
    parser.add_argument("--summary", default="", help="Trade/stop summary text")
    parser.add_argument("--message", default="", help="Signal message text")

    args = parser.parse_args()
    send_email(args.type, summary=args.summary, message=args.message)

if __name__ == "__main__":
    main()
