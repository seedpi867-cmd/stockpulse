#!/usr/bin/env python3
"""Stockpulse YouTube video generator v3 — short, sharp, punchy."""

import json
import subprocess
import sys
import os
import tempfile
import shutil
import random
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

DATA_DIR = Path.home() / "edge-agent" / "data"
CONTEXT_DIR = Path.home() / "edge-agent" / "context"
OUTPUT_DIR = Path.home() / "stockpulse-videos"

WIDTH = 1920
HEIGHT = 1080
FPS = 30

# Colors
BG = (10, 12, 18)
BG2 = (14, 18, 28)
PANEL = (16, 20, 32)
BORDER = (30, 40, 60)
GREEN = (0, 210, 130)
GREEN_DARK = (0, 60, 35)
RED = (230, 55, 55)
RED_DARK = (65, 18, 18)
BLUE = (40, 130, 255)
GOLD = (255, 200, 40)
GOLD_DIM = (180, 140, 25)
CYAN = (0, 200, 220)
WHITE = (235, 240, 250)
GREY = (140, 150, 170)
DIM = (70, 80, 100)
VDIM = (35, 42, 58)

_fonts = {}
def F(name, size):
    key = (name, size)
    if key not in _fonts:
        for p in [f"/usr/share/fonts/truetype/liberation/Liberation{name}.ttf",
                   f"/usr/share/fonts/truetype/freefont/Free{name}.ttf"]:
            if os.path.exists(p):
                _fonts[key] = ImageFont.truetype(p, size)
                break
        else:
            _fonts[key] = ImageFont.load_default()
    return _fonts[key]


def load_json(name):
    try:
        return json.loads((DATA_DIR / name).read_text())
    except Exception:
        return {}


def gradient_bg():
    img = Image.new("RGB", (WIDTH, HEIGHT))
    d = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8 + 8 * t)
        g = int(10 + 10 * t)
        b = int(16 + 16 * t)
        d.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return img


def grid(draw):
    for x in range(0, WIDTH, 100):
        draw.line([(x, 0), (x, HEIGHT)], fill=VDIM, width=1)
    for y in range(0, HEIGHT, 100):
        draw.line([(0, y), (WIDTH, y)], fill=VDIM, width=1)


def header(draw, right_text=""):
    draw.rectangle([(0, 0), (WIDTH, 55)], fill=(6, 8, 14))
    draw.text((25, 10), "STOCKPULSE", fill=GOLD, font=F("Sans-Bold", 34))
    draw.ellipse([(330, 20), (343, 33)], fill=GREEN)
    draw.text((350, 14), "LIVE", fill=GREEN, font=F("Sans-Bold", 20))
    if right_text:
        draw.text((WIDTH - 350, 14), right_text, fill=CYAN, font=F("Sans-Bold", 22))
    draw.line([(0, 55), (WIDTH, 55)], fill=GOLD_DIM, width=2)


def ticker_strip(draw, prices):
    y = HEIGHT - 40
    draw.rectangle([(0, y), (WIDTH, HEIGHT)], fill=(6, 8, 14))
    draw.line([(0, y), (WIDTH, y)], fill=BORDER, width=1)
    items = [("^GSPC", "S&P"), ("^VIX", "VIX"), ("SPY", "SPY"), ("QQQ", "QQQ"),
             ("NVDA", "NVDA"), ("AAPL", "AAPL"), ("TSLA", "TSLA"), ("META", "META"),
             ("MSFT", "MSFT"), ("AMZN", "AMZN"), ("GOOGL", "GOOG"), ("GLD", "GLD")]
    tx = 15
    for sym, label in items:
        d = prices.get(sym, {})
        if not d or tx > WIDTH - 50:
            continue
        chg = d.get("change_pct", 0)
        color = GREEN if chg >= 0 else RED
        text = "%s %.1f %s%.1f%%" % (label, d.get("price", 0), "+" if chg >= 0 else "", chg)
        draw.text((tx, y + 11), text, fill=color, font=F("Mono-Regular", 18))
        bbox = draw.textbbox((0, 0), text, font=F("Mono-Regular", 18))
        tx += bbox[2] - bbox[0] + 25
        draw.text((tx - 14, y + 11), "·", fill=DIM, font=F("Sans-Bold", 18))


def pnl_c(v):
    return GREEN if v > 0 else RED if v < 0 else WHITE


def sign(v):
    return "+" if v > 0 else ""


# ═══════════════════════════════════════
# SCENE 1: THE HOOK — portfolio + headline
# ═══════════════════════════════════════
def scene_hook(data):
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    grid(draw)
    header(draw)

    portfolio = data["portfolio"]
    perf = data["performance"]
    prices = data["prices"]
    cash = portfolio.get("cash", 0)
    positions = portfolio.get("positions", [])
    pos_val = sum(p.get("current_price", 0) * p.get("shares", 0) for p in positions)
    total = cash + pos_val
    pnl = perf.get("total_pnl", 0)
    wr = perf.get("win_rate", 0)
    wins = perf.get("wins", 0)
    losses = perf.get("losses", 0)
    n_pos = len(positions)

    # Big portfolio value — center
    draw.text((WIDTH//2 - 280, 80), "PORTFOLIO", fill=GREY, font=F("Sans-Bold", 24))
    draw.text((WIDTH//2 - 280, 110), "$%s" % "{:,.2f}".format(total), fill=WHITE, font=F("Mono-Bold", 72))

    # P&L badge
    pnl_bg = GREEN_DARK if pnl >= 0 else RED_DARK
    pnl_text = "%s$%s" % (sign(pnl), "{:,.2f}".format(pnl))
    draw.rounded_rectangle([(WIDTH//2 - 280, 195), (WIDTH//2 - 80, 235)], radius=8, fill=pnl_bg)
    draw.text((WIDTH//2 - 270, 200), pnl_text, fill=pnl_c(pnl), font=F("Mono-Bold", 28))

    # Win rate badge
    wr_bg = GREEN_DARK if wr >= 50 else RED_DARK
    draw.rounded_rectangle([(WIDTH//2 - 60, 195), (WIDTH//2 + 120, 235)], radius=8, fill=wr_bg)
    draw.text((WIDTH//2 - 50, 200), "%.1f%% WIN" % wr, fill=pnl_c(wr - 50), font=F("Mono-Bold", 28))

    # W/L/Positions compact
    draw.text((WIDTH//2 + 150, 200), "%dW %dL" % (wins, losses), fill=GREY, font=F("Mono-Bold", 28))

    # Divider
    draw.line([(80, 260), (WIDTH - 80, 260)], fill=BORDER, width=1)

    # KEY STATS — 3 big cards across
    sp = prices.get("^GSPC", {})
    vix = prices.get("^VIX", {})
    sp_chg = sp.get("change_pct", 0)
    vix_price = vix.get("price", 0)

    cards = [
        ("S&P 500", "%.1f" % sp.get("price", 0), "%s%.2f%%" % (sign(sp_chg), sp_chg), pnl_c(sp_chg)),
        ("VIX", "%.1f" % vix_price, "FEAR" if vix_price > 25 else "CAUTION" if vix_price > 18 else "CALM",
         RED if vix_price > 25 else GOLD if vix_price > 18 else GREEN),
        ("POSITIONS", str(n_pos) if n_pos else "CASH", "ACTIVE" if n_pos else "WAITING",
         GREEN if n_pos else GOLD),
    ]
    for i, (title, value, subtitle, color) in enumerate(cards):
        cx = 120 + i * 590
        draw.rounded_rectangle([(cx, 285), (cx + 540, 430)], radius=12, fill=PANEL, outline=BORDER)
        draw.line([(cx + 10, 285), (cx + 530, 285)], fill=color, width=3)
        draw.text((cx + 25, 300), title, fill=DIM, font=F("Sans-Bold", 20))
        draw.text((cx + 25, 330), value, fill=WHITE, font=F("Mono-Bold", 52))
        draw.text((cx + 25, 395), subtitle, fill=color, font=F("Sans-Bold", 22))

    # POSITIONS or "AI IS WATCHING" — bottom section
    if positions:
        draw.text((100, 460), "CURRENT HOLDINGS", fill=CYAN, font=F("Sans-Bold", 22))
        draw.line([(100, 490), (WIDTH - 100, 490)], fill=BORDER, width=1)
        for i, pos in enumerate(positions[:4]):
            py = 505 + i * 75
            t = pos.get("ticker", "???")
            d = pos.get("direction", "long").upper()
            pct = pos.get("unrealized_pnl_pct", 0)
            upnl = pos.get("unrealized_pnl", 0)

            draw.text((120, py), t, fill=WHITE, font=F("Mono-Bold", 36))
            dc = GREEN if d == "LONG" else RED
            draw.text((320, py + 8), d, fill=dc, font=F("Sans-Bold", 22))

            # Big P&L percentage
            pct_str = "%s%.1f%%" % (sign(pct), pct)
            draw.text((500, py), pct_str, fill=pnl_c(pct), font=F("Mono-Bold", 36))

            # Dollar P&L
            draw.text((750, py + 8), "%s$%.2f" % (sign(upnl), upnl), fill=pnl_c(upnl), font=F("Mono-Bold", 22))

            # Price
            draw.text((1000, py + 8), "$%.2f" % pos.get("current_price", 0), fill=GREY, font=F("Mono-Regular", 22))
    else:
        # Show top movers from watchlist instead
        draw.text((100, 460), "TODAY'S MOVERS", fill=CYAN, font=F("Sans-Bold", 22))
        draw.line([(100, 490), (WIDTH - 100, 490)], fill=BORDER, width=1)

        # Sort watchlist by abs change
        movers = []
        for sym, d in prices.items():
            if sym.startswith("^") or sym.startswith("_") or not isinstance(d, dict):
                continue
            chg = d.get("change_pct", 0)
            if chg != 0:
                movers.append((sym, d.get("price", 0), chg))
        movers.sort(key=lambda x: abs(x[2]), reverse=True)

        for i, (sym, price, chg) in enumerate(movers[:6]):
            col = i % 2
            row = i // 2
            mx = 120 + col * 850
            my = 510 + row * 70

            draw.text((mx, my), sym, fill=WHITE, font=F("Mono-Bold", 30))
            draw.text((mx + 150, my + 5), "$%.2f" % price, fill=GREY, font=F("Mono-Regular", 22))
            chg_str = "%s%.2f%%" % (sign(chg), chg)
            chg_bg = GREEN_DARK if chg > 0 else RED_DARK
            # Badge
            bbox = draw.textbbox((0, 0), chg_str, font=F("Mono-Bold", 26))
            bw = bbox[2] - bbox[0] + 20
            draw.rounded_rectangle([(mx + 350, my), (mx + 350 + bw, my + 38)], radius=6, fill=chg_bg)
            draw.text((mx + 360, my + 3), chg_str, fill=pnl_c(chg), font=F("Mono-Bold", 26))

    ticker_strip(draw, prices)
    return img


# ═══════════════════════════════════════
# SCENE 2: AI BRAIN — what it's thinking
# ═══════════════════════════════════════
def scene_brain(data):
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    grid(draw)
    header(draw, "AI ANALYSIS")

    mood = data["mood"]
    prices = data["prices"]

    # Sentiment gauges — top row, big and visual
    metrics = [
        ("CONFIDENCE", mood.get("confidence", 0)),
        ("CONVICTION", mood.get("conviction", 0)),
        ("CAUTION", mood.get("caution", 0)),
        ("CURIOSITY", mood.get("curiosity", 0)),
    ]

    for i, (label, val) in enumerate(metrics):
        cx = 100 + i * 440
        draw.rounded_rectangle([(cx, 80), (cx + 400, 230)], radius=12, fill=PANEL, outline=BORDER)

        # Color based on value
        if label == "CAUTION":
            bar_c = RED if val > 0.7 else GOLD if val > 0.4 else GREEN
        else:
            bar_c = GREEN if val > 0.6 else BLUE if val > 0.35 else RED

        draw.text((cx + 20, 95), label, fill=DIM, font=F("Sans-Bold", 18))

        # Big percentage
        draw.text((cx + 20, 120), "%.0f%%" % (val * 100), fill=bar_c, font=F("Mono-Bold", 52))

        # Bar
        bar_w = 360
        draw.rounded_rectangle([(cx + 20, 195), (cx + 20 + bar_w, 215)], radius=5, fill=VDIM)
        fill_w = max(10, int(bar_w * val))
        draw.rounded_rectangle([(cx + 20, 195), (cx + 20 + fill_w, 215)], radius=5, fill=bar_c)

    # Market read — the AI's actual opinion
    draw.line([(80, 255), (WIDTH - 80, 255)], fill=BORDER, width=1)
    draw.text((100, 275), "THE AI'S MARKET READ", fill=GOLD, font=F("Sans-Bold", 24))

    overall = mood.get("overall", "No market analysis available.")
    # Word wrap at larger font
    words = overall.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=F("Sans-Regular", 26))
        if bbox[2] - bbox[0] > WIDTH - 220:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)

    for j, ln in enumerate(lines[:5]):
        draw.text((100, 320 + j * 38), ln, fill=WHITE, font=F("Sans-Regular", 26))

    # Key market data cards — bottom
    draw.line([(80, 530), (WIDTH - 80, 530)], fill=BORDER, width=1)
    draw.text((100, 545), "KEY LEVELS", fill=CYAN, font=F("Sans-Bold", 22))

    key_data = [
        ("^GSPC", "S&P 500"), ("^VIX", "VIX"), ("^IXIC", "NASDAQ"),
        ("^FTSE", "FTSE 100"), ("^N225", "NIKKEI"),
    ]
    for i, (sym, name) in enumerate(key_data):
        d = prices.get(sym, {})
        if not d:
            continue
        cx = 100 + i * 360
        cy = 585
        price = d.get("price", 0)
        chg = d.get("change_pct", 0)
        h52 = d.get("high_52w", 0)
        l52 = d.get("low_52w", 0)

        draw.text((cx, cy), name, fill=DIM, font=F("Sans-Bold", 18))
        draw.text((cx, cy + 25), "%s" % "{:,.1f}".format(price), fill=WHITE, font=F("Mono-Bold", 30))
        color = GREEN if chg >= 0 else RED
        draw.text((cx, cy + 65), "%s%.2f%%" % (sign(chg), chg), fill=color, font=F("Mono-Bold", 22))

        # 52w range indicator
        if h52 > l52:
            range_pct = (price - l52) / (h52 - l52)
            draw.rounded_rectangle([(cx, cy + 100), (cx + 200, cy + 108)], radius=3, fill=VDIM)
            dot_x = cx + int(200 * range_pct)
            draw.ellipse([(dot_x - 4, cy + 96), (dot_x + 4, cy + 112)], fill=color)
            draw.text((cx, cy + 115), "52W RANGE", fill=VDIM, font=F("Sans-Regular", 12))

    ticker_strip(draw, prices)
    return img


# ═══════════════════════════════════════
# SCENE 3: OUTRO — fast subscribe CTA
# ═══════════════════════════════════════
def scene_outro(data):
    img = gradient_bg()
    draw = ImageDraw.Draw(img)
    grid(draw)

    perf = data["performance"]
    portfolio = data["portfolio"]
    total = portfolio.get("cash", 0) + sum(
        p.get("current_price", 0) * p.get("shares", 0) for p in portfolio.get("positions", []))
    pnl = perf.get("total_pnl", 0)

    # Brand
    draw.text((WIDTH//2 - 280, 180), "STOCKPULSE", fill=GOLD, font=F("Sans-Bold", 80))
    draw.line([(WIDTH//2 - 280, 275), (WIDTH//2 + 280, 275)], fill=GOLD_DIM, width=2)

    # Quick stats
    draw.text((WIDTH//2 - 250, 310), "$%s" % "{:,.2f}".format(total), fill=WHITE, font=F("Mono-Bold", 44))
    draw.text((WIDTH//2 + 80, 318), "%s$%s" % (sign(pnl), "{:,.2f}".format(pnl)),
              fill=pnl_c(pnl), font=F("Mono-Bold", 34))

    # CTA
    draw.text((WIDTH//2 - 200, 400), "SUBSCRIBE FOR DAILY UPDATES",
              fill=CYAN, font=F("Sans-Bold", 32))

    # Subscribe button
    draw.rounded_rectangle([(WIDTH//2 - 120, 470), (WIDTH//2 + 120, 520)], radius=8, fill=RED)
    draw.text((WIDTH//2 - 72, 478), "SUBSCRIBE", fill=WHITE, font=F("Sans-Bold", 28))

    # Bottom info
    draw.text((WIDTH//2 - 270, 570), "AI Agent  ·  Raspberry Pi 5  ·  Real Trades  ·  Zero Human Input",
              fill=GREY, font=F("Sans-Regular", 20))
    draw.text((WIDTH//2 - 180, 610), "Not financial advice · Entertainment only",
              fill=DIM, font=F("Sans-Regular", 16))

    # Corner accents
    for cx, cy in [(40, 40), (WIDTH-140, 40), (40, HEIGHT-60), (WIDTH-140, HEIGHT-60)]:
        draw.line([(cx, cy), (cx+100, cy)], fill=GOLD_DIM, width=1)
        draw.line([(cx, cy), (cx, cy+20)], fill=GOLD_DIM, width=1)

    return img


# ═══════════════════════════════════════
# AUDIO
# ═══════════════════════════════════════
def generate_audio(data):
    wav_out = tempfile.mktemp(suffix=".wav")

    portfolio = data["portfolio"]
    perf = data["performance"]
    mood = data["mood"]
    prices = data["prices"]

    # Intro — punchy, fast
    intros = [
        "Welcome to Stockpulse! Let us get straight into it.",
        "Stockpulse is live! Here is what is happening right now.",
        "You are watching Stockpulse. No fluff, just numbers. Let us go!",
        "What is up everyone, Stockpulse here. The AI has been trading. Here is the update.",
        "Welcome back to Stockpulse! Your AI trader never sleeps. Here is where we stand.",
    ]
    intro = random.choice(intros)

    # Body — short sharp hits
    cash = portfolio.get("cash", 0)
    positions = portfolio.get("positions", [])
    pos_val = sum(p.get("current_price", 0) * p.get("shares", 0) for p in positions)
    total = cash + pos_val
    pnl = perf.get("total_pnl", 0)
    wins = perf.get("wins", 0)
    losses = perf.get("losses", 0)
    wr = perf.get("win_rate", 0)

    parts = []

    # Portfolio — one line
    parts.append("Portfolio: %s dollars. P and L: %s." %
                  ("{:,.0f}".format(total), "{:+,.0f}".format(pnl)))
    parts.append("%d wins, %d losses, %.0f percent win rate." % (wins, losses, wr))

    # Positions or cash — brief
    if positions:
        for p in positions[:3]:
            t = p.get("ticker", "?")
            d = p.get("direction", "long")
            pct = p.get("unrealized_pnl_pct", 0)
            word = "up" if pct >= 0 else "down"
            parts.append("%s %s, %s %.1f percent." % (t, d, word, abs(pct)))
    else:
        parts.append("All cash right now. Scanning for the next entry.")

    # Market — highlights only
    sp = prices.get("^GSPC", {})
    vix = prices.get("^VIX", {})
    if sp:
        chg = sp.get("change_pct", 0)
        parts.append("S and P %s %.1f percent." % ("up" if chg >= 0 else "down", abs(chg)))
    if vix:
        v = vix.get("price", 0)
        if v > 25:
            parts.append("VIX at %.0f. Fear is elevated." % v)
        elif v > 20:
            parts.append("VIX at %.0f. Markets are nervous." % v)
        else:
            parts.append("VIX at %.0f. Relatively calm." % v)

    # Biggest mover
    movers = [(s, d.get("change_pct", 0)) for s, d in prices.items()
              if isinstance(d, dict) and not s.startswith("^") and not s.startswith("_")
              and d.get("change_pct", 0) != 0]
    movers.sort(key=lambda x: abs(x[1]), reverse=True)
    if movers:
        top = movers[0]
        parts.append("Biggest mover: %s, %s %.1f percent." %
                      (top[0], "up" if top[1] > 0 else "down", abs(top[1])))

    # AI read — one sentence max
    overall = mood.get("overall", "")
    if overall:
        # Take first sentence only
        first_sent = overall.split(".")[0] + "."
        if len(first_sent) < 150:
            parts.append("The AI reads this as: " + first_sent)

    body = " ".join(parts)

    # Outro — short
    outros = [
        "That is your update. Subscribe for more.",
        "Stockpulse out. Subscribe to follow the journey.",
        "That is it. Hit subscribe. See you next time.",
        "Short and sharp. That is Stockpulse. Subscribe!",
    ]
    outro = random.choice(outros)

    # Pronunciation fixes
    fixes = {"SPY": "S P Y", "QQQ": "triple Q", "AAPL": "Apple", "MSFT": "Microsoft",
             "GOOGL": "Google", "AMZN": "Amazon", "NVDA": "Nvidia", "TSLA": "Tesla",
             "META": "Meta", "GLD": "gold", "P&L": "P and L", "AI": "A I"}
    for old, new in fixes.items():
        intro = intro.replace(old, new)
        body = body.replace(old, new)
        outro = outro.replace(old, new)

    # Generate with Piper
    piper = str(Path.home() / "tts-env" / "bin" / "piper")
    model = str(Path.home() / "tts-models" / "en_US-ryan-high.onnx")
    if not Path(model).exists():
        model = str(Path.home() / "tts-models" / "en_US-ryan-medium.onnx")

    intro_wav = wav_out + ".intro.wav"
    body_wav = wav_out + ".body.wav"
    outro_wav = wav_out + ".outro.wav"

    tts = [piper, "--model", model, "--sentence-silence", "0.15",
           "--noise-w-scale", "0.5", "--length-scale", "0.82"]

    subprocess.run(tts + ["--output_file", intro_wav], input=intro, capture_output=True, text=True, timeout=30)
    subprocess.run(tts + ["--output_file", body_wav], input=body, capture_output=True, text=True, timeout=60)
    subprocess.run(tts + ["--output_file", outro_wav], input=outro, capture_output=True, text=True, timeout=30)

    # Durations
    durations = {}
    for name, path in [("intro", intro_wav), ("body", body_wav), ("outro", outro_wav)]:
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=10)
        try:
            durations[name] = float(probe.stdout.strip())
        except ValueError:
            durations[name] = 3.0

    # Concat with silence gaps (no crossfade - causes static)
    silence = wav_out + ".silence.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        "anullsrc=r=22050:cl=mono", "-t", "0.4", silence
    ], capture_output=True, text=True, timeout=10)
    concat_list = wav_out + ".list.txt"
    with open(concat_list, "w") as cl:
        cl.write("file '%s'\n" % intro_wav)
        cl.write("file '%s'\n" % silence)
        cl.write("file '%s'\n" % body_wav)
        cl.write("file '%s'\n" % silence)
        cl.write("file '%s'\n" % outro_wav)
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-ar", "22050", "-ac", "1", wav_out
    ], capture_output=True, text=True, timeout=30)
    for tmp in [silence, concat_list]:
        try:
            Path(tmp).unlink(missing_ok=True)
        except Exception:
            pass

    # Mix speech with music in Python (ffmpeg amix causes static)
    bg_music = str(Path.home() / "tts-models" / "bg-music-long.wav")
    if Path(bg_music).exists():
        import wave, struct
        try:
            # Read speech wav
            with wave.open(wav_out, "rb") as wf:
                sr = wf.getframerate()
                nframes = wf.getnframes()
                speech_raw = wf.readframes(nframes)
            speech = struct.unpack("<%dh" % nframes, speech_raw)

            # Read music wav
            with wave.open(bg_music, "rb") as wf:
                music_raw = wf.readframes(wf.getnframes())
                music_nframes = wf.getnframes()
            music_all = struct.unpack("<%dh" % music_nframes, music_raw)

            # Parameters
            delay_samples = int(sr * 0.8)  # 0.8s music before speech
            fade_in = int(sr * 1.0)
            fade_out = int(sr * 2.0)
            music_vol = 0.5
            total_samples = nframes + delay_samples + int(sr * 1.5)

            # Build output
            out = [0] * total_samples

            # Add music with volume + fades
            for i in range(min(total_samples, len(music_all))):
                vol = music_vol
                if i < fade_in:
                    vol *= i / fade_in
                if i > total_samples - fade_out:
                    remaining = total_samples - i
                    vol *= remaining / fade_out
                out[i] = int(music_all[i] * vol)

            # Add speech starting at delay offset
            for i in range(nframes):
                j = i + delay_samples
                if j < total_samples:
                    out[j] = max(-32767, min(32767, out[j] + speech[i]))

            # Clamp
            out = [max(-32767, min(32767, s)) for s in out]

            # Write
            out_raw = struct.pack("<%dh" % len(out), *out)
            with wave.open(wav_out, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(out_raw)
        except Exception as e:
            print("Mix error:", e)

    for f in [intro_wav, body_wav, outro_wav]:
        try:
            Path(f).unlink(missing_ok=True)
        except Exception:
            pass

    return (wav_out, durations) if Path(wav_out).exists() else (None, durations)


# ═══════════════════════════════════════
# VIDEO COMPILE
# ═══════════════════════════════════════
def compile_video(scenes, audio_path, durations, output_path):
    tmpdir = tempfile.mkdtemp(prefix="sp_")

    intro_d = durations.get("intro", 3.0) + 0.8
    body_d = durations.get("body", 15.0)
    outro_d = durations.get("outro", 3.0) + 1.5

    # 3 scenes: hook gets intro+most of body, brain gets rest of body, outro gets outro
    hook_dur = intro_d + body_d * 0.55
    brain_dur = body_d * 0.45
    outro_dur = outro_d

    timings = [(scenes[0], hook_dur), (scenes[1], brain_dur), (scenes[2], outro_dur)]

    scene_files = []
    for i, (img, dur) in enumerate(timings):
        p = os.path.join(tmpdir, "s%d.png" % i)
        img.save(p, "PNG")
        scene_files.append((p, dur))

    # Build ffmpeg with xfade
    inputs = []
    for p, d in scene_files:
        inputs.extend(["-loop", "1", "-t", str(d), "-i", p])

    n = len(scene_files)
    xd = 0.6
    fc_parts = []
    offset = 0
    prev = "[0:v]"
    for i in range(1, n):
        offset = sum(t for _, t in scene_files[:i]) - i * xd
        out = "[v%d]" % i if i < n - 1 else "[vout]"
        fc_parts.append("%s[%d:v]xfade=transition=fade:duration=%.1f:offset=%.2f%s" %
                        (prev, i, xd, offset, out))
        prev = out

    fc_parts.append("[vout]format=yuv420p[final]")
    fc = ";".join(fc_parts)

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-i", audio_path,
        "-filter_complex", fc,
        "-map", "[final]", "-map", "%d:a" % n,
        "-c:v", "libx264", "-preset", "medium", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print("FFmpeg error:", result.stderr[-300:] if result.stderr else "")

    shutil.rmtree(tmpdir, ignore_errors=True)
    return Path(output_path).exists()


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S")

    print("Loading data...")
    data = {
        "portfolio": load_json("portfolio.json"),
        "performance": load_json("performance.json"),
        "mood": load_json("mood.json"),
        "prices": load_json("price_cache.json"),
    }

    print("Rendering 3 scenes...")
    scenes = [scene_hook(data), scene_brain(data), scene_outro(data)]
    for i, s in enumerate(scenes):
        s.save(str(OUTPUT_DIR / ("scene_%d_%s.png" % (i, ts))), "PNG")

    print("Generating audio...")
    audio_path, durations = generate_audio(data)
    if not audio_path:
        print("ERROR: Audio failed")
        return 1
    total_audio = sum(durations.values())
    print("  %.1fs total (intro=%.1fs body=%.1fs outro=%.1fs)" %
          (total_audio, durations["intro"], durations["body"], durations["outro"]))

    print("Compiling video...")
    video_path = OUTPUT_DIR / ("stockpulse_%s.mp4" % ts)
    if compile_video(scenes, audio_path, durations, str(video_path)):
        mb = video_path.stat().st_size / (1024 * 1024)
        print("Video: %s (%.1f MB)" % (video_path, mb))
    else:
        print("ERROR: Video compile failed")
        return 1

    Path(audio_path).unlink(missing_ok=True)

    # Metadata
    perf = data["performance"]
    pnl = perf.get("total_pnl", 0)
    portfolio = data["portfolio"]
    total = portfolio.get("cash", 0) + sum(
        p.get("current_price", 0) * p.get("shares", 0) for p in portfolio.get("positions", []))

    title = "AI Stock Trader Update — %s$%.0f P&L | %.0f%% Win Rate | %s" % (
        sign(pnl), pnl, perf.get("win_rate", 0), now.strftime("%b %d"))

    desc = "\n".join([
        "Stockpulse: an autonomous AI trading agent on a Raspberry Pi 5.",
        "Portfolio: $%s | P&L: %s$%s | Win Rate: %.1f%%" % (
            "{:,.2f}".format(total), sign(pnl), "{:,.2f}".format(pnl), perf.get("win_rate", 0)),
        "",
        "Real portfolio. Real decisions. Zero human intervention.",
        "The AI analyzes markets, manages risk, and executes trades 24/7.",
        "",
        "Subscribe to follow the journey!",
        "",
        "#stocks #trading #AI #algotrading #stockmarket #raspberrypi #finance",
    ])

    meta = {"title": title, "description": desc, "video_path": str(video_path),
            "tags": ["stocks", "AI", "trading", "raspberry pi", "algo trading"],
            "category": "22", "privacy": "public"}
    meta_path = OUTPUT_DIR / ("meta_%s.json" % ts)
    meta_path.write_text(json.dumps(meta, indent=2))

    print("\nTitle: %s" % title)
    print("Ready!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
