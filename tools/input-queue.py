#!/usr/bin/env python3
"""Surfaces random knowledge files each cycle to challenge current positions."""
import json, random, time
from pathlib import Path

ROOT = Path.home() / 'edge-agent'
KNOWLEDGE = ROOT / 'knowledge'
CONTEXT = ROOT / 'context' / 'knowledge-recall.md'

def run():
    files = [f for f in KNOWLEDGE.rglob('*.md')]
    if not files: return
    picks = random.sample(files, min(3, len(files)))
    
    lines = ['# Knowledge Recall\n\n']
    lines.append('Do any of these contradict or support your current positions?\n\n')
    for f in picks:
        title = f.stem.replace('-', ' ')
        try:
            content = f.read_text()[:400]
            first = content.split('\n')[0].lstrip('# ').strip()
            if first: title = first
            snippet = ' '.join(content.split('\n')[2:5]).strip()[:200]
        except:
            snippet = ''
        lines.append(f'### {title}\n')
        if snippet: lines.append(f'{snippet}\n\n')
    
    CONTEXT.write_text(''.join(lines))
    print(f'[knowledge-recall] {len(picks)} files surfaced')

if __name__ == '__main__':
    run()
