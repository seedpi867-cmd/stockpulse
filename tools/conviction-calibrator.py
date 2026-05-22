#!/usr/bin/env python3
"""Tracks whether conviction levels actually predict outcomes."""
import json
from pathlib import Path

DATA = Path.home() / 'edge-agent' / 'data'
TRADES = DATA / 'trades.jsonl'
CONTEXT = Path.home() / 'edge-agent' / 'context' / 'conviction-calibration.md'

def run():
    if not TRADES.exists(): return
    trades = [json.loads(l) for l in TRADES.read_text().strip().split('\n') if l.strip()]
    closed = [t for t in trades if t.get('status') == 'closed' and t.get('conviction')]
    if len(closed) < 3: return

    buckets = {'high': [], 'medium': [], 'low': []}
    for t in closed:
        c = t.get('conviction', 0.5)
        pnl = t.get('realized_pnl', 0)
        if c >= 0.8: buckets['high'].append(pnl)
        elif c >= 0.5: buckets['medium'].append(pnl)
        else: buckets['low'].append(pnl)

    lines = ['# Conviction Calibration\n\n']
    for level, pnls in buckets.items():
        if not pnls: continue
        wins = sum(1 for p in pnls if p > 0)
        wr = round(wins / len(pnls), 2)
        avg = round(sum(pnls) / len(pnls), 2)
        lines.append(f'**{level.upper()}**: {len(pnls)} trades, {int(wr*100)}% win rate, avg ${avg}\n')
    
    high_wr = sum(1 for p in buckets['high'] if p > 0) / max(len(buckets['high']), 1) if buckets['high'] else 0
    low_wr = sum(1 for p in buckets['low'] if p > 0) / max(len(buckets['low']), 1) if buckets['low'] else 0
    if buckets['high'] and buckets['low'] and high_wr <= low_wr:
        lines.append('\n**WARNING: High conviction is NOT winning more. Your confidence is miscalibrated.**\n')
    
    CONTEXT.write_text(''.join(lines))
    print('[conviction] calibration updated')

if __name__ == '__main__':
    run()
