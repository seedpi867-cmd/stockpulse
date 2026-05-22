#!/usr/bin/env python3
"""Simple API endpoint to receive owner messages and drop them into the prompt."""
import json, os, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INBOX = DATA / "owner-inbox.md"

def add_message(message):
    """Append a message to the owner inbox."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = "\n---\n[{}] Owner says:\n{}\n".format(now, message.strip())
    with open(str(INBOX), "a") as f:
        f.write(entry)
    print("[owner-input] Message queued for next cycle")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        add_message(" ".join(sys.argv[1:]))
    else:
        print("Usage: python3 owner-input.py 'your message here'")
