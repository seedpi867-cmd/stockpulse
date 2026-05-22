#!/usr/bin/env python3
"""Stockpulse voice output v2 — natural speech via Piper TTS + BlueALSA."""

import json
import subprocess
import sys
import re
import tempfile
from pathlib import Path
from datetime import datetime

DATA_DIR = Path.home() / "edge-agent" / "data"
CONTEXT_DIR = Path.home() / "edge-agent" / "context"
PIPER = str(Path.home() / "tts-env" / "bin" / "piper")
MODEL_HIGH = str(Path.home() / "tts-models" / "en_US-ryan-high.onnx")
MODEL_MED = str(Path.home() / "tts-models" / "en_US-ryan-medium.onnx")
BT_DEV = "bluealsa:DEV=82:37:26:45:F3:F0"

MODEL = MODEL_HIGH if Path(MODEL_HIGH).exists() else MODEL_MED

TICKER_SPEAK = {
    "SPY": "S P Y", "QQQ": "triple Q", "DIA": "diamonds",
    "IWM": "I W M", "AAPL": "Apple", "MSFT": "Microsoft",
    "GOOGL": "Google", "AMZN": "Amazon", "NVDA": "Nvidia",
    "TSLA": "Tesla", "META": "Meta", "XLK": "tech sector",
    "XLF": "financials", "XLE": "energy sector", "XLV": "healthcare",
    "XLB": "materials", "XLU": "utilities", "XLY": "consumer discretionary",
    "XLP": "consumer staples", "XLI": "industrials", "XLRE": "real estate",
    "XLC": "communications", "XBI": "biotech", "SMH": "semiconductors",
    "SOXX": "chip stocks", "ARKK": "ark innovation", "ARKG": "ark genomics",
    "SH": "short S P 500", "SQQQ": "triple short nasdaq",
    "TQQQ": "triple long nasdaq", "SPXL": "triple long S P",
    "UVXY": "U V X Y volatility", "SVXY": "short volatility",
    "TLT": "long bonds", "TBT": "short bonds", "HYG": "high yield bonds",
    "LQD": "investment grade bonds", "AGG": "bond aggregate",
    "GLD": "gold", "SLV": "silver", "GDX": "gold miners",
    "GDXJ": "junior gold miners", "IAU": "gold trust",
    "USO": "oil", "XOP": "oil and gas exploration",
    "BTC-USD": "bitcoin", "ETH-USD": "ethereum",
    "EWJ": "Japan", "EWZ": "Brazil", "EWG": "Germany",
    "FXI": "China large cap", "KWEB": "China internet",
    "INDA": "India", "EEM": "emerging markets", "VWO": "emerging markets",
    "EFA": "developed international",
    "FCX": "Freeport copper", "AA": "Alcoa aluminum",
    "VIX": "the vix", "DXY": "the dollar index", "CPER": "copper",
    "PPLT": "platinum", "PALL": "palladium",
    "LMT": "Lockheed", "RTX": "Raytheon", "NOC": "Northrop",
    "BA": "Boeing", "GE": "G E aerospace",
    "JETS": "airlines", "CCL": "Carnival cruise", "RCL": "Royal Caribbean",
    "DBA": "agriculture", "IYT": "transports", "XHB": "homebuilders",
    "KRE": "regional banks", "ITB": "home construction",
    "SI=F": "silver futures", "GC=F": "gold futures",
    "CL=F": "crude futures", "HG=F": "copper futures",
    "NQ=F": "nasdaq futures", "ES=F": "S P futures",
    "YM=F": "dow futures", "ZB=F": "bond futures",
}


def _human_number(val):
    """Say a number the way a human would on a trading desk."""
    if val >= 1000000:
        m = val / 1000000
        if m == int(m):
            return "%d million" % int(m)
        return "%.1f million" % m
    elif val >= 100000:
        # 100,043 -> "a hundred thousand"  /  147,500 -> "a hundred and forty seven thousand"
        k = round(val / 1000)
        return "%d thousand" % k
    elif val >= 10000:
        k = val / 1000
        if k == int(k):
            return "%d thousand" % int(k)
        return "%.1f thousand" % k
    elif val >= 1000:
        k = val / 1000
        if k == int(k):
            return "%d thousand" % int(k)
        # 3500 -> "three and a half thousand"
        frac = k - int(k)
        if abs(frac - 0.5) < 0.1:
            return "%d and a half thousand" % int(k)
        return "%.1f thousand" % k
    else:
        if val == int(val):
            return str(int(val))
        # Round to whole for speech
        return str(round(val))


def _speak_dollars(match):
    """Convert dollar amounts to natural conversational speech."""
    sign = match.group(1) or ""
    num = match.group(2).replace(",", "")
    prefix = "up " if sign == "+" else ("down " if sign == "-" else "")
    try:
        val = float(num)
        return "%s%s dollars" % (prefix, _human_number(val))
    except ValueError:
        return match.group(0)


def _speak_percent(match):
    """Convert percentages to how a human says them."""
    sign = match.group(1) or ""
    num = match.group(2)
    try:
        val = float(num)
        # Tiny moves
        if val < 0.2:
            phrase = "basically flat"
            if sign == "+": return "up, " + phrase
            elif sign == "-": return "down, " + phrase
            return phrase
        # Natural rounding
        if abs(val - round(val)) < 0.1:
            num_str = str(round(val))
        elif abs(val - 0.5) < 0.15 and int(val) == 0:
            num_str = "half a"
        elif abs(val - 0.25) < 0.1 and int(val) == 0:
            num_str = "a quarter"
        elif abs(val - 0.75) < 0.1 and int(val) == 0:
            num_str = "three quarters of a"
        elif abs(val - int(val) - 0.5) < 0.15:
            num_str = "%d and a half" % int(val)
        elif abs(val - int(val) - 0.25) < 0.1:
            num_str = "%d and a quarter" % int(val)
        elif abs(val - int(val) - 0.75) < 0.1:
            num_str = "%d and three quarters" % int(val)
        else:
            rounded = round(val, 1)
            if rounded == int(rounded):
                num_str = str(int(rounded))
            else:
                num_str = str(rounded)
        if sign == "+":
            return "up %s percent" % num_str
        elif sign == "-":
            return "down %s percent" % num_str
        return "%s percent" % num_str
    except ValueError:
        return match.group(0)


def _speak_bare_price(match):
    """Convert bare decimal prices to how traders say them.
    57.80 -> 'fifty seven eighty'
    170.73 -> 'one seventy point seventy three'
    """
    num = match.group(0)
    try:
        val = float(num)
        whole = int(val)
        cents = round((val - whole) * 100)
        if not cents:
            return str(whole)
        # Traders say "sixty eighty seven" for 60.87
        # or "one seventy three" for 170.73 would be confusing
        # Keep it simple: whole number, then cents
        if cents % 10 == 0:
            # .80 -> eighty, .50 -> fifty
            return "%d %d" % (whole, cents)
        else:
            # .73 -> seventy three, .87 -> eighty seven
            return "%d %d" % (whole, cents)
    except ValueError:
        return match.group(0)


def pronounce(text):
    # Tickers first (longest match first to avoid partial)
    for ticker, spoken in sorted(TICKER_SPEAK.items(), key=lambda x: -len(x[0])):
        text = re.sub(r'\b' + re.escape(ticker) + r'\b', spoken, text)

    # Markdown bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)

    # Abbreviations
    text = text.replace("P&L", "P and L")
    text = text.replace("P/C", "put call ratio")
    text = text.replace("R/R", "risk reward")
    text = text.replace("52w", "52 week")
    text = text.replace("52W", "52 week")
    text = text.replace("ATH", "all time high")
    text = text.replace("YTD", "year to date")
    text = text.replace("MoM", "month over month")

    # Dollar amounts: $60.87, +$100, -$3,500.00
    text = re.sub(r'([+\-])?\$([0-9,]+\.?\d*)', _speak_dollars, text)

    # Signed percentages: +3.70%, -2.43%, 57%
    text = re.sub(r'([+\-])?(\d+\.?\d*)%', _speak_percent, text)

    # Remaining bare decimals (prices like 57.80, 170.73)
    # Don't match if followed by " percent" (already converted) or preceded by "down/up"
    text = re.sub(r'\b(\d+\.\d{1,2})\b(?! percent)', _speak_bare_price, text)

    # Clean up ".0000" share counts from playbook output
    text = re.sub(r'(\d+)\.0000\b', r'\1', text)

    return text

BG_MUSIC = str(Path.home() / "tts-models" / "bg-music-22k.wav")
BG_VOLUME = 0.55

def _time_of_day():
    """Return time-of-day string for Adelaide (ACST/ACDT)."""
    hour = datetime.now().hour
    if hour < 6:
        return "late_night"
    elif hour < 12:
        return "morning"
    elif hour < 17:
        return "afternoon"
    elif hour < 21:
        return "evening"
    else:
        return "night"


def _market_state():
    """Check if US market is open based on data-freshness.md."""
    try:
        freshness = (CONTEXT_DIR / "data-freshness.md").read_text()
        if "LIVE SESSION" in freshness or "DATA MOVED" in freshness:
            return "open"
    except Exception:
        pass
    return "closed"


def greeting():
    """Time-aware, market-aware intro — feels like a real host."""
    import random
    tod = _time_of_day()
    mkt = _market_state()

    # Time-of-day greetings
    if tod == "morning":
        time_greets = [
            "Good morning Leigh!",
            "Morning! Rise and grind,",
            "Top of the morning Leigh!",
        ]
    elif tod == "afternoon":
        time_greets = [
            "Afternoon Leigh!",
            "Hey Leigh, afternoon check in,",
            "Good afternoon!",
        ]
    elif tod == "evening":
        time_greets = [
            "Evening Leigh!",
            "Hey Leigh, evening wrap up time,",
            "Good evening!",
        ]
    elif tod == "night":
        time_greets = [
            "Late one tonight Leigh!",
            "Hey Leigh, burning the midnight oil,",
            "Night owl update,",
        ]
    else:  # late_night
        time_greets = [
            "You're up early Leigh!",
            "Pre-dawn check in,",
            "Early bird gets the alpha,",
        ]

    # Market-state flavour
    if mkt == "open":
        mkt_flavours = [
            "Markets are live and moving, here's your Stockpulse!",
            "The bell has rung, let's see what's happening!",
            "Markets are open, Stockpulse is on the case!",
            "Trading is underway, here's the rundown!",
            "We're live! Here's your Stockpulse update!",
        ]
    else:
        mkt_flavours = [
            "Markets are closed but Stockpulse never sleeps!",
            "Markets are resting, here's where we stand!",
            "After hours update, here's your Stockpulse!",
            "Markets are shut, let's review the day!",
            "Off hours, but the numbers are still worth knowing!",
        ]

    return random.choice(time_greets) + " " + random.choice(mkt_flavours)


def generate_intro_wav(output_path):
    """Generate intro wav — slightly upbeat but still clear."""
    intro_text = pronounce(greeting())
    cmd = [PIPER, "--model", MODEL, "--output_file", output_path,
           "--sentence-silence", "0.4",
           "--noise-w-scale", "0.4",
           "--length-scale", "0.92"]
    proc = subprocess.run(cmd, input=intro_text, capture_output=True, text=True, timeout=30)
    return proc.returncode == 0


def get_outro():
    """Funny sign-off lines — rotates randomly."""
    import random
    outros = [
        "This has been Stockpulse. Remember, past performance does not guarantee future excuses. Leigh out!",
        "That is your lot! Stockpulse will return. Try not to panic sell in the meantime.",
        "And that is a wrap! Stockpulse signing off. May your stops never get hit. Peace!",
        "Stockpulse out! Go touch some grass Leigh. The market will still be there tomorrow.",
        "End of transmission! If you made money, you are welcome. If not, blame the fed.",
        "That is all folks! Stockpulse, reminding you that cash is also a position. Later!",
        "Signing off! Remember, the trend is your friend, until it is not. Stockpulse out!",
        "And we are done! Leigh, do not check the charts for at least five minutes. Good luck with that.",
        "Stockpulse complete! Now go do something productive. Or just refresh the dashboard again.",
        "That is your update! Stockpulse out. No stocks were harmed in the making of this broadcast.",
    ]
    return random.choice(outros)


def generate_outro_wav(output_path):
    """Generate outro wav with same clean settings."""
    outro_text = pronounce(get_outro())
    cmd = [PIPER, "--model", MODEL, "--output_file", output_path,
           "--sentence-silence", "0.4",
           "--noise-w-scale", "0.4",
           "--length-scale", "0.95"]
    proc = subprocess.run(cmd, input=outro_text, capture_output=True, text=True, timeout=30)
    return proc.returncode == 0


def mix_with_music(speech_wav, output_wav):
    """Mix speech with background music. Seamless loop, crossfade at loop points."""
    if not Path(BG_MUSIC).exists():
        return False
    try:
        # Get speech duration
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", speech_wav],
            capture_output=True, text=True, timeout=10)
        speech_dur = float(probe.stdout.strip())

        # Add 1s padding before and 2s after speech for music intro/outro
        total_dur = speech_dur + 3.0
        fade_out_start = max(0, total_dur - 2.5)

        # Build seamless looped music bed with crossfade at loop points.
        # The bg music is ~20s. We first create a long seamless bed by
        # concatenating copies with crossfade overlap, then layer speech on top.
        import math
        music_dur = 20.4  # bg-music-22k.wav duration
        xfade_dur = 3.0   # crossfade overlap between loops
        loops_needed = max(2, math.ceil(total_dur / (music_dur - xfade_dur)) + 1)

        # Step 1: Build seamless music bed with crossfaded loops
        music_bed = "/tmp/tts_music_bed.wav"
        # Use acrossfade to blend loop boundaries
        if loops_needed <= 2:
            # Simple: two copies with one crossfade
            subprocess.run([
                "ffmpeg", "-y",
                "-i", BG_MUSIC, "-i", BG_MUSIC,
                "-filter_complex",
                "acrossfade=d=%.1f:c1=tri:c2=tri" % xfade_dur,
                "-ar", "22050", "-ac", "1",
                music_bed
            ], capture_output=True, text=True, timeout=30)
        else:
            # Chain multiple crossfades for longer speech
            inputs = []
            for i in range(loops_needed):
                inputs.extend(["-i", BG_MUSIC])
            # Build filter chain: [0][1]acrossfade -> [a1]; [a1][2]acrossfade -> [a2]; ...
            fc_parts = []
            prev = "[0:a]"
            for i in range(1, loops_needed):
                out_label = "[a%d]" % i
                fc_parts.append(
                    "%s[%d:a]acrossfade=d=%.1f:c1=tri:c2=tri%s"
                    % (prev, i, xfade_dur, out_label)
                )
                prev = out_label
            # Last label goes to output
            fc_str = ";".join(fc_parts)
            subprocess.run(
                ["ffmpeg", "-y"] + inputs + [
                    "-filter_complex", fc_str,
                    "-map", prev, "-ar", "22050", "-ac", "1",
                    music_bed
                ], capture_output=True, text=True, timeout=60)

        # Step 2: Mix the seamless music bed with speech
        subprocess.run([
            "ffmpeg", "-y",
            "-i", music_bed,
            "-i", speech_wav,
            "-filter_complex",
            (
                "[0:a]volume=%.2f,"
                "afade=t=in:d=1.5,"
                "afade=t=out:st=%.1f:d=2.5[music];"
                "[1:a]adelay=1000|1000[speech];"
                "[music][speech]amix=inputs=2:duration=first:weights=1 1:normalize=0[out]"
            ) % (BG_VOLUME, fade_out_start),
            "-map", "[out]",
            "-t", str(total_dur),
            "-ar", "22050", "-ac", "1",
            output_wav
        ], capture_output=True, text=True, timeout=60)
        return Path(output_wav).exists() and Path(output_wav).stat().st_size > 1000
    except Exception:
        return False


def speak(text, urgent=False, bare=False):
    if not text or not text.strip():
        return "Nothing to say"
    text = pronounce(text)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name
    mixed_path = wav_path + ".mixed.wav"
    try:
        intro_path = wav_path + ".intro.wav"
        body_path = wav_path + ".body.wav"
        outro_path = wav_path + ".outro.wav"

        # Skip intro/outro for urgent alerts and bare mode (short reports)
        has_intro = False
        has_outro = False
        if not urgent and not bare:
            has_intro = generate_intro_wav(intro_path)
            has_outro = generate_outro_wav(outro_path)

        # Generate body wav — faster for urgent, normal pace otherwise
        cmd = [PIPER, "--model", MODEL, "--output_file", body_path,
               "--sentence-silence", "0.5",
               "--noise-w-scale", "0.4",
               "--length-scale", "0.90" if urgent else "1.0"]
        proc = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0:
            return "TTS failed"

        # Concat intro + body + outro
        parts_to_join = []
        if has_intro and Path(intro_path).exists():
            parts_to_join.append(intro_path)
        parts_to_join.append(body_path)
        if has_outro and Path(outro_path).exists():
            parts_to_join.append(outro_path)

        # Concat with silence gaps (no crossfade - causes static pops)
        silence_path = wav_path + ".silence.wav"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "anullsrc=r=22050:cl=mono", "-t", "0.7", silence_path
        ], capture_output=True, text=True, timeout=10)
        concat_list = wav_path + ".list.txt"
        with open(concat_list, "w") as cl:
            for j, part in enumerate(parts_to_join):
                cl.write("file '%s'\n" % part)
                if j < len(parts_to_join) - 1:
                    cl.write("file '%s'\n" % silence_path)
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list, "-ar", "22050", "-ac", "1", wav_path
        ], capture_output=True, text=True, timeout=30)
        try:
            Path(silence_path).unlink(missing_ok=True)
            Path(concat_list).unlink(missing_ok=True)
        except Exception:
            pass

        # Mix with background music
        play_file = wav_path
        if mix_with_music(wav_path, mixed_path):
            play_file = mixed_path
        # Play
        r = subprocess.run(["aplay", "-D", BT_DEV, play_file],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            subprocess.run(["aplay", play_file], capture_output=True, timeout=120)
            return "Spoke (HDMI fallback)"
        return "OK"
    except Exception as e:
        return "Error: " + str(e)[:30]
    finally:
        for tmp in [wav_path + ".intro.wav", wav_path + ".body.wav", wav_path + ".outro.wav"]:
            try:
                Path(tmp).unlink(missing_ok=True)
            except Exception:
                pass
        Path(wav_path).unlink(missing_ok=True)
        Path(mixed_path).unlink(missing_ok=True)


def load_json(name):
    try:
        return json.loads((DATA_DIR / name).read_text())
    except Exception:
        return {}


def load_text(name):
    try:
        return (DATA_DIR / name).read_text().strip()
    except Exception:
        return ""


def get_cycle():
    try:
        return int((DATA_DIR / "cycle.txt").read_text().strip())
    except Exception:
        return 0


def summary():
    portfolio = load_json("portfolio.json")
    perf = load_json("performance.json")
    mood = load_json("mood.json")
    positions = portfolio.get("positions", [])
    cash = portfolio.get("cash", 0)
    pos_val = sum(p.get("current_price", 0) * p.get("shares", 0) for p in positions)
    total = cash + pos_val
    pnl = perf.get("total_pnl", 0)
    wins = perf.get("wins", 0)
    losses = perf.get("losses", 0)
    mkt = _market_state()

    parts = ["Alright, cycle %d." % get_cycle()]
    parts.append("We're sitting at $%.0f total." % total)
    if abs(pnl) >= 1:
        parts.append("That's %s $%.0f on the day." % ("up" if pnl >= 0 else "down", abs(pnl)))
    if wins or losses:
        parts.append("Track record is %d wins, %d losses." % (wins, losses))

    if positions:
        # Split positions into movers vs flat
        movers = []
        flat = []
        for p in positions[:6]:
            pct = p.get("unrealized_pnl_pct", 0)
            if abs(pct) >= 0.3:
                movers.append(p)
            else:
                flat.append(p)

        parts.append("We've got %d positions open right now." % len(positions))

        # Only detail the movers individually
        for p in movers:
            ticker = p.get("ticker", "unknown")
            pct = p.get("unrealized_pnl_pct", 0)
            upnl = p.get("unrealized_pnl", 0)
            if pct >= 0:
                parts.append("%s is looking good, up %.1f%%, that's $%.0f." % (ticker, abs(pct), abs(upnl)))
            else:
                parts.append("%s is in the red, down %.1f%%, that's $%.0f." % (ticker, abs(pct), abs(upnl)))

        # Collapse flat positions into one sentence
        if flat:
            if len(flat) == 1:
                parts.append("%s is sitting flat." % flat[0].get("ticker", "unknown"))
            elif len(flat) == len(positions):
                tickers = " and ".join(p.get("ticker", "?") for p in flat)
                parts.append("All positions flat right now, %s, nothing moving." % tickers)
            else:
                tickers = " and ".join(p.get("ticker", "?") for p in flat)
                parts.append("%s sitting flat." % tickers)
    else:
        parts.append("No positions on right now, we're all cash.")

    # Market state context — brief when closed
    overall = mood.get("overall", "")
    if mkt == "open":
        if overall:
            parts.append("On the market, " + overall)
    else:
        if overall:
            parts.append(overall)
        parts.append("Markets are closed, next update when things start moving.")

    return speak(" ".join(parts))


def briefing():
    portfolio = load_json("portfolio.json")
    perf = load_json("performance.json")
    mood = load_json("mood.json")
    positions = portfolio.get("positions", [])
    cash = portfolio.get("cash", 0)
    pos_val = sum(p.get("current_price", 0) * p.get("shares", 0) for p in positions)
    total = cash + pos_val
    pnl = perf.get("total_pnl", 0)
    wins = perf.get("wins", 0)
    losses = perf.get("losses", 0)
    mkt = _market_state()

    parts = ["Here's the full rundown."]
    parts.append("Portfolio is at $%.0f, and we're %s $%.0f overall." % (total, "up" if pnl >= 0 else "down", abs(pnl)))
    parts.append("So far we've got %d wins and %d losses on the board." % (wins, losses))

    if positions:
        # Sort by absolute P&L so the interesting ones come first
        sorted_pos = sorted(positions, key=lambda p: abs(p.get("unrealized_pnl", 0)), reverse=True)
        parts.append("Running %d positions right now." % len(positions))
        for p in sorted_pos:
            ticker = p.get("ticker", "unknown")
            direction = p.get("direction", "long")
            upnl = p.get("unrealized_pnl", 0)
            stop = p.get("stop", 0)
            target = p.get("target", 0)
            if abs(upnl) < 1:
                parts.append("We're %s %s, currently flat. Stop at $%.0f, target $%.0f." % (direction, ticker, stop, target))
            elif upnl >= 0:
                parts.append("We're %s %s, up $%.0f so far. Stop at $%.0f, target $%.0f." % (direction, ticker, abs(upnl), stop, target))
            else:
                parts.append("We're %s %s, down $%.0f at the moment. Stop at $%.0f, target $%.0f." % (direction, ticker, abs(upnl), stop, target))
    else:
        parts.append("Nothing on right now, sitting in cash and looking for setups.")

    # Market data — only when market is open
    if mkt == "open":
        try:
            prices = (CONTEXT_DIR / "prices.md").read_text()
            for line in prices.split("\n"):
                m = re.match(r'- (.+?):\s*\$?([\d,.]+)\s*\(([^)]+)\)', line.strip())
                if m:
                    ticker = m.group(1).strip()
                    price = m.group(2).strip()
                    change = m.group(3).strip()
                    if any(t in ticker.upper() for t in ["SPY", "QQQ", "VIX", "BTC-USD", "GLD"]):
                        parts.append("%s at %s, %s." % (ticker, price, change))
        except Exception:
            pass

    # Catalysts — always useful
    try:
        cal = (CONTEXT_DIR / "calendar.md").read_text()
        for line in cal.split("\n"):
            if "[HIGH]" in line:
                event = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
                event = event.replace("- [HIGH] ", "").strip()
                parts.append("Watch out for %s." % event[:80])
                break
    except Exception:
        pass

    # Signal collision — skip if empty/generic
    try:
        last = (DATA_DIR / "last-output.txt").read_text()
        for line in last.split("\n"):
            if line.startswith("COLLISION:"):
                collision = line.replace("COLLISION:", "").strip()
                if collision and len(collision) > 10:
                    parts.append("Interesting signal collision, %s." % collision[:120])
                break
    except Exception:
        pass

    # Agent mood — conversational
    conf = mood.get("confidence", 0)
    caut = mood.get("caution", 0)
    if conf > 0.7:
        parts.append("The agent is feeling confident at %d percent." % int(conf * 100))
    elif conf < 0.4:
        parts.append("Confidence is low right now, only %d percent." % int(conf * 100))
    if caut > 0.7:
        parts.append("Caution is up though, running careful at %d percent." % int(caut * 100))

    overall = mood.get("overall", "")
    if overall:
        parts.append("Overall market read, " + overall)

    parts.append("That's the briefing.")
    return speak(" ".join(parts))


def thoughts():
    raw = load_text("thoughts.md")
    entries = [e.strip() for e in raw.split("---") if e.strip()]
    if not entries:
        return speak("No thoughts yet.", bare=True)
    entry = entries[-1]
    lines = entry.split("\n")
    body = " ".join(lines[1:]).strip() if len(lines) > 1 else entry
    return speak("Here's what's on my mind. " + body, bare=True)


def inner_voice():
    raw = load_text("inner-voice.md")
    entries = [e.strip() for e in raw.split("---") if e.strip()]
    if not entries:
        return speak("No inner voice recorded.", bare=True)
    entry = entries[-1]
    lines = entry.split("\n")
    body = " ".join(lines[1:]).strip() if len(lines) > 1 else entry
    return speak(body, bare=True)


def market():
    try:
        prices = (CONTEXT_DIR / "prices.md").read_text()
    except Exception:
        return speak("No price data available right now.", bare=True)

    parts = ["Let's look at the broader market."]
    movers_up = []
    movers_down = []

    for line in prices.split("\n"):
        m = re.match(r'- (.+?):\s*\$?([\d,.]+)\s*\(([^)]+)\)', line.strip())
        if not m:
            continue
        ticker = m.group(1).strip()
        price = m.group(2).strip()
        change = m.group(3).strip()

        if any(t in ticker.upper() for t in ["SPY", "QQQ", "VIX", "BTC-USD", "GLD", "TLT", "DIA"]):
            parts.append("%s is at %s, that's %s." % (ticker, price, change))

        try:
            chg_val = float(change.replace("%", "").replace("+", ""))
            if abs(chg_val) >= 2.0:
                if chg_val > 0:
                    movers_up.append("%s up %s" % (ticker, change))
                else:
                    movers_down.append("%s down %s" % (ticker, change))
        except ValueError:
            pass

    if movers_up:
        parts.append("Biggest winners today, " + ", ".join(movers_up[:3]) + ".")
    if movers_down:
        parts.append("On the downside, " + ", ".join(movers_down[:3]) + ".")

    try:
        sentiment = (CONTEXT_DIR / "sentiment.md").read_text()
        fg = re.search(r'Score:\s*(\d+)/100\s*\((\w+)\)', sentiment)
        if fg:
            parts.append("Fear and greed is sitting at %s, which puts us in %s territory." % (fg.group(1), fg.group(2).lower()))
    except Exception:
        pass

    return speak(" ".join(parts), bare=True)


def positions_report():
    portfolio = load_json("portfolio.json")
    pos = portfolio.get("positions", [])
    if not pos:
        return speak("No open positions right now, we're sitting in cash.", bare=True)
    # Sort by absolute P&L — interesting ones first
    sorted_pos = sorted(pos, key=lambda p: abs(p.get("unrealized_pnl", 0)), reverse=True)
    movers = [p for p in sorted_pos if abs(p.get("unrealized_pnl", 0)) >= 1]
    flat = [p for p in sorted_pos if abs(p.get("unrealized_pnl", 0)) < 1]

    parts = ["We've got %d positions on." % len(pos)]
    # Detail the movers
    for p in movers:
        ticker = p.get("ticker", "unknown")
        direction = p.get("direction", "long")
        shares = p.get("shares", 0)
        upnl = p.get("unrealized_pnl", 0)
        stop = p.get("stop", 0)
        target = p.get("target", 0)
        if upnl >= 0:
            parts.append("%s, we're %s %.0f shares, up $%.0f. Stop at $%.0f, target $%.0f." % (ticker, direction, shares, abs(upnl), stop, target))
        else:
            parts.append("%s, we're %s %.0f shares, down $%.0f. Stop at $%.0f, target $%.0f." % (ticker, direction, shares, abs(upnl), stop, target))
    # Collapse flat ones
    if flat:
        if len(flat) == 1:
            p = flat[0]
            parts.append("%s is flat, %s %.0f shares. Stop at $%.0f, target $%.0f." % (
                p.get("ticker", "?"), p.get("direction", "long"), p.get("shares", 0), p.get("stop", 0), p.get("target", 0)))
        else:
            tickers = ", ".join(p.get("ticker", "?") for p in flat)
            parts.append("The rest, %s, all sitting flat, no movement yet." % tickers)
    return speak(" ".join(parts), bare=True)


def mood_report():
    mood = load_json("mood.json")
    if not mood:
        return speak("No mood data to report.", bare=True)
    parts = ["Here's where my head is at."]
    conf = mood.get("confidence", 0)
    conv = mood.get("conviction", 0)
    caut = mood.get("caution", 0)
    frust = mood.get("frustration", 0)
    curio = mood.get("curiosity", 0)

    if conf > 0.7:
        parts.append("I'm feeling pretty confident right now.")
    elif conf < 0.4:
        parts.append("Confidence is a bit shaky if I'm honest.")
    else:
        parts.append("Confidence is sitting somewhere in the middle.")

    if conv > 0.7:
        parts.append("I've got strong conviction in the current thesis.")
    elif conv < 0.4:
        parts.append("Not super convicted on direction though, still feeling it out.")

    if caut > 0.7:
        parts.append("Running pretty cautious, keeping risk tight.")
    elif caut < 0.3:
        parts.append("I'm in aggressive mode, leaning into setups.")

    if frust > 0.5:
        parts.append("Getting a bit frustrated to be honest, things aren't clicking.")
    if curio > 0.7:
        parts.append("But I'm curious, there's some interesting stuff forming out there.")

    overall = mood.get("overall", "")
    if overall:
        parts.append("My overall read is, " + overall)
    return speak(" ".join(parts), bare=True)


def trades():
    try:
        lines = (DATA_DIR / "trades.jsonl").read_text().strip().split("\n")
        recent = [json.loads(l) for l in lines[-5:] if l.strip()]
    except Exception:
        return speak("No trade history yet.", bare=True)
    if not recent:
        return speak("Haven't made any trades yet.", bare=True)
    parts = ["Here's what we've been doing lately."]
    for t in reversed(recent):
        action = t.get("action", "?").lower()
        ticker = t.get("ticker", "?")
        price = t.get("price", 0)
        pnl = t.get("pnl")
        # Natural verb phrasing
        if "buy" in action or "add" in action:
            verb = "bought"
        elif "sell" in action or "cover" in action:
            verb = "sold"
        elif "short" in action:
            verb = "shorted"
        else:
            verb = action
        parts.append("We %s %s at $%.0f." % (verb, ticker, price))
        if pnl is not None and abs(pnl) >= 1:
            if pnl >= 0:
                parts.append("Walked away with $%.0f profit on that one." % abs(pnl))
            else:
                parts.append("Took a $%.0f hit on that one." % abs(pnl))
    perf = load_json("performance.json")
    total_pnl = perf.get("total_pnl", 0)
    if abs(total_pnl) < 1:
        parts.append("Overall we're basically break even.")
    elif total_pnl >= 0:
        parts.append("All up, we're in the green by $%.0f." % abs(total_pnl))
    else:
        parts.append("All up, we're in the red by $%.0f." % abs(total_pnl))
    return speak(" ".join(parts), bare=True)


def alert(message=None):
    if message:
        return speak("Heads up! " + message, urgent=True)
    try:
        lines = (DATA_DIR / "trades.jsonl").read_text().strip().split("\n")
        last = json.loads(lines[-1])
        action = last.get("action", "?").lower()
        ticker = last.get("ticker", "?")
        price = last.get("price", 0)
        pnl = last.get("pnl")
        # Natural verb
        if "buy" in action or "add" in action:
            verb = "bought"
        elif "sell" in action or "cover" in action:
            verb = "closed out"
        elif "short" in action:
            verb = "shorted"
        else:
            verb = action
        if pnl is not None and abs(pnl) >= 1:
            if pnl >= 0:
                return speak("Hey, trade just went through! We %s %s at $%.0f. Locked in $%.0f profit, nice one." % (verb, ticker, price, abs(pnl)), urgent=True)
            else:
                return speak("Hey, trade just went through. We %s %s at $%.0f. Took a $%.0f loss on that one, but we move on." % (verb, ticker, price, abs(pnl)), urgent=True)
        return speak("Hey, just %s %s at $%.0f. We're in, let's see how it plays out." % (verb, ticker, price), urgent=True)
    except Exception:
        return speak("Trade just went through! Check the dashboard for the details.", urgent=True)


COMMANDS = {
    "summary": summary,
    "briefing": briefing,
    "thoughts": thoughts,
    "voice": inner_voice,
    "market": market,
    "positions": positions_report,
    "mood": mood_report,
    "trades": trades,
    "alert": alert,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    msg = sys.argv[2] if len(sys.argv) > 2 else None
    func = COMMANDS.get(cmd, summary)
    if cmd == "alert" and msg:
        result = alert(msg)
    else:
        result = func()
    print(result)
