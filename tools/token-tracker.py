#!/usr/bin/env python3
"""Parse cycle logs and build token usage tracking file."""
import json
import re
import time
from pathlib import Path
from datetime import datetime

DATA_DIR = Path.home() / "edge-agent" / "data"
LOGS_DIR = DATA_DIR / "logs"
TOKEN_FILE = DATA_DIR / "token-usage.json"

def parse_cycle_log(log_path):
    """Extract prompt/response bytes and duration from a cycle log."""
    text = log_path.read_text()
    prompt = 0
    response = 0
    duration = 0
    timestamp = None

    m = re.search(r'Prompt size:\s*(\d+)\s*bytes', text)
    if m:
        prompt = int(m.group(1))

    m = re.search(r'LLM response:\s*(\d+)\s*bytes', text)
    if m:
        response = int(m.group(1))

    m = re.search(r'Cycle \d+ complete \((\d+)s\)', text)
    if m:
        duration = int(m.group(1))

    # Get timestamp from first line
    m = re.search(r'CYCLE \d+ .+ (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', text)
    if m:
        timestamp = m.group(1)

    return {
        "prompt_bytes": prompt,
        "response_bytes": response,
        "prompt_tokens_est": prompt // 4,
        "response_tokens_est": response // 4,
        "total_tokens_est": (prompt + response) // 4,
        "duration_secs": duration,
        "timestamp": timestamp
    }

def build_usage():
    """Scan all cycle logs and build token usage summary."""
    logs = sorted(LOGS_DIR.glob("cycle_*.log"))
    if not logs:
        return {}

    cycles = []
    total_prompt = 0
    total_response = 0
    total_duration = 0
    daily = {}

    for log in logs:
        cycle_num = int(log.stem.replace("cycle_", ""))
        info = parse_cycle_log(log)
        info["cycle"] = cycle_num
        cycles.append(info)

        total_prompt += info["prompt_bytes"]
        total_response += info["response_bytes"]
        total_duration += info["duration_secs"]

        # Daily aggregation
        day = (info["timestamp"] or "")[:10]
        if day:
            if day not in daily:
                daily[day] = {"cycles": 0, "prompt_bytes": 0, "response_bytes": 0, "duration_secs": 0}
            daily[day]["cycles"] += 1
            daily[day]["prompt_bytes"] += info["prompt_bytes"]
            daily[day]["response_bytes"] += info["response_bytes"]
            daily[day]["duration_secs"] += info["duration_secs"]

    # Last 10 cycles for live view
    recent = cycles[-10:] if len(cycles) >= 10 else cycles

    # Per-cycle averages
    n = len(cycles)
    avg_prompt = total_prompt // n if n else 0
    avg_response = total_response // n if n else 0
    avg_duration = total_duration // n if n else 0

    # Daily summary with token estimates
    daily_summary = []
    for day in sorted(daily.keys())[-7:]:
        d = daily[day]
        daily_summary.append({
            "date": day,
            "cycles": d["cycles"],
            "prompt_tokens": d["prompt_bytes"] // 4,
            "response_tokens": d["response_bytes"] // 4,
            "total_tokens": (d["prompt_bytes"] + d["response_bytes"]) // 4,
            "total_minutes": round(d["duration_secs"] / 60, 1)
        })

    result = {
        "updated": datetime.now().isoformat(),
        "total_cycles": n,
        "total_prompt_tokens": total_prompt // 4,
        "total_response_tokens": total_response // 4,
        "total_tokens": (total_prompt + total_response) // 4,
        "total_compute_minutes": round(total_duration / 60, 1),
        "avg_prompt_tokens": avg_prompt // 4,
        "avg_response_tokens": avg_response // 4,
        "avg_cycle_secs": avg_duration,
        "recent_cycles": recent,
        "daily": daily_summary,
        "current_cycle": cycles[-1]["cycle"] if cycles else 0,
        "last_prompt_tokens": cycles[-1]["prompt_tokens_est"] if cycles else 0,
        "last_response_tokens": cycles[-1]["response_tokens_est"] if cycles else 0,
        "last_duration": cycles[-1]["duration_secs"] if cycles else 0,
    }

    TOKEN_FILE.write_text(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    r = build_usage()
    print(f"[token-tracker] {r['total_cycles']} cycles, {r['total_tokens']:,} tokens, {r['total_compute_minutes']}min compute")
