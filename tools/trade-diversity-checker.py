#!/usr/bin/env python3
"""Checks if the agent is stuck trading the same patterns or genuinely diversifying."""
import json
from pathlib import Path
from collections import Counter

DATA = Path.home() / 'edge-agent' / 'data'
TRADES = DATA / 'trades.jsonl'
PREDICTIONS = DATA / 'predictions.jsonl'
CONTEXT = Path.home() / 'edge-agent' / 'context' / 'trade-diversity.md'

def run():
    lines = ['# Trade Diversity Check\n\n']
    
    # Check ticker concentration
    all_trades = []
    for f in [TRADES, PREDICTIONS]:
        if f.exists():
            all_trades.extend([json.loads(l) for l in f.read_text().strip().split('\n') if l.strip()])
    
    if len(all_trades) < 5: return
    
    recent = all_trades[-20:]
    tickers = Counter(t.get('ticker', '?') for t in recent)
    directions = Counter(t.get('direction', t.get('action', '?')).lower() for t in recent)
    
    lines.append('## Last 20 actions\n')
    lines.append(f'Tickers: {dict(tickers)}\n')
    lines.append(f'Directions: {dict(directions)}\n\n')
    
    most_common = tickers.most_common(1)[0] if tickers else ('?', 0)
    if most_common[1] > 8:
        lines.append(f'**WARNING: {most_common[0]} appears {most_common[1]}/20 times. You are fixated. Look elsewhere.**\n')
    
    unique_tickers = len(tickers)
    if unique_tickers < 3:
        lines.append(f'**WARNING: Only {unique_tickers} unique tickers. Diversify your attention.**\n')
    
    CONTEXT.write_text(''.join(lines))
    print(f'[diversity] {unique_tickers} unique tickers in last 20 actions')

if __name__ == '__main__':
    run()
