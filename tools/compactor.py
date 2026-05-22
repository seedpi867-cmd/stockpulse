#!/usr/bin/env python3
"""Stockpulse Prompt Compactor — runs before prompt assembly each cycle.

Three passes:
1. Dedup — strip repeated lines from context files
2. Prune — keep only last N entries in voice/memory/predictions
3. Summarize — compress old inner voice into one-line summaries

Target: 86KB -> under 15KB prompt
"""
import json, os, re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTEXT = ROOT / "context"

def compact_inner_voice(path, keep_full=5, keep_summary=20):
    """Keep last N entries in full, summarize older ones to one line each."""
    if not path.exists():
        return
    text = path.read_text()
    entries = text.split('\n---\n')
    entries = [e.strip() for e in entries if e.strip()]

    if len(entries) <= keep_full:
        return  # Nothing to compact

    # Keep last N in full
    recent = entries[-keep_full:]
    # Summarize older ones to first line only
    old = entries[-(keep_full + keep_summary):-keep_full] if len(entries) > keep_full else []
    summaries = []
    for e in old:
        lines = e.strip().split('\n')
        first_line = lines[0] if lines else ''
        # Get just the cycle header + first sentence
        text_lines = [l for l in lines[1:] if l.strip()]
        summary = text_lines[0][:150] if text_lines else ''
        summaries.append(first_line + '\n' + summary)

    # Rebuild
    parts = []
    for s in summaries:
        parts.append(s)
    for r in recent:
        parts.append(r)

    path.write_text('\n---\n'.join(parts) + '\n')
    print("[compactor] inner-voice: %d entries -> %d summary + %d full" % (len(entries), len(summaries), len(recent)))

def compact_memory(path, keep=30):
    """Keep only last N memory lines."""
    if not path.exists():
        return
    lines = [l for l in path.read_text().strip().split('\n') if l.strip()]
    if len(lines) <= keep:
        return
    path.write_text('\n'.join(lines[-keep:]) + '\n')
    print("[compactor] memory: %d lines -> %d" % (len(lines), keep))

def compact_predictions(path, keep_open=True, keep_closed=10):
    """Keep all open predictions + last N closed ones."""
    if not path.exists():
        return
    preds = []
    for line in path.read_text().strip().split('\n'):
        try:
            preds.append(json.loads(line))
        except:
            pass

    if len(preds) <= 20:
        return

    open_preds = [p for p in preds if p.get('was_correct') is None]
    closed = [p for p in preds if p.get('was_correct') is not None]
    keep = open_preds + closed[-keep_closed:]

    with open(str(path), 'w') as f:
        for p in keep:
            f.write(json.dumps(p) + '\n')
    print("[compactor] predictions: %d -> %d (%d open + %d closed)" % (len(preds), len(keep), len(open_preds), min(len(closed), keep_closed)))

def compact_context_files(max_lines=20):
    """Trim context files to max N lines each."""
    if not CONTEXT.exists():
        return
    total_before = 0
    total_after = 0
    for f in CONTEXT.glob("*.md"):
        lines = f.read_text().strip().split('\n')
        total_before += len(lines)
        if len(lines) > max_lines:
            # Keep header + last N lines
            header = []
            body = []
            for l in lines:
                if l.startswith('#') and not body:
                    header.append(l)
                else:
                    body.append(l)
            trimmed = header + body[-max_lines:]
            f.write_text('\n'.join(trimmed) + '\n')
            total_after += len(trimmed)
        else:
            total_after += len(lines)
    if total_before != total_after:
        print("[compactor] context files: %d lines -> %d" % (total_before, total_after))

def dedup_context():
    """Remove duplicate lines from context files."""
    if not CONTEXT.exists():
        return
    for f in CONTEXT.glob("*.md"):
        lines = f.read_text().strip().split('\n')
        seen = set()
        deduped = []
        for l in lines:
            if l.startswith('#') or l.startswith('-') or l not in seen:
                deduped.append(l)
                if not l.startswith('#'):
                    seen.add(l)
        if len(deduped) < len(lines):
            f.write_text('\n'.join(deduped) + '\n')
            print("[compactor] dedup %s: %d -> %d" % (f.name, len(lines), len(deduped)))

def report_sizes():
    """Report prompt component sizes."""
    sizes = {}
    for f in CONTEXT.glob("*.md"):
        sizes[f.name] = f.stat().st_size
    for name in ['inner-voice.md', 'thoughts.md', 'memory.md', 'mood.json', 'portfolio.json', 'performance.json', 'strategy.json']:
        p = DATA / name
        if p.exists():
            sizes[name] = p.stat().st_size

    total = sum(sizes.values())
    print("[compactor] Total context: %d bytes (%.1f KB)" % (total, total/1024))
    # Show top 5 biggest
    top = sorted(sizes.items(), key=lambda x: -x[1])[:5]
    for name, size in top:
        print("[compactor]   %s: %d bytes" % (name, size))

def main():
    print("[compactor] Running...")
    dedup_context()
    compact_context_files(max_lines=20)
    compact_inner_voice(DATA / "inner-voice.md", keep_full=3, keep_summary=5)
    compact_inner_voice(DATA / "thoughts.md", keep_full=2, keep_summary=3)
    compact_memory(DATA / "memory.md", keep=10)
    compact_predictions(DATA / "predictions.jsonl", keep_closed=10)
    report_sizes()

if __name__ == "__main__":
    main()
