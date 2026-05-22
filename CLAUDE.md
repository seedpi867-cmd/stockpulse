# Stockpulse -- Autonomous Market Brain

## What This Is
An autonomous stock trading agent running 24/7 on a Raspberry Pi 5 (8GB RAM). Reads global market data, forms convictions, makes virtual trades, tracks accuracy, evolves strategy.

## Architecture
- brain-loop.sh -- the engine. Feeders > compactor > prompt compiler > Claude CLI > playbook > dashboard
- tools/prompt-compiler.py -- smart prompt builder. Only sends what changed. Dynamic modes (fast/normal/deep)
- tools/playbook.py -- executes trades, predictions, watchlist changes. Deterministic.
- tools/compactor.py -- keeps memory/voice/context lean
- tools/feed-*.py -- market data feeders (prices, news, sentiment, sectors, calendar)
- webserver.py -- serves dashboard at :8080

## Key Files
- AGENT.md -- identity (system prompt, cached)
- INSTRUCTIONS.md -- trading playbook (system prompt, cached)
- data/portfolio.json -- current positions and cash
- data/predictions.jsonl -- all predictions
- data/trades.jsonl -- trade history
- data/inner-voice.md -- agent thoughts
- data/thoughts.md -- background thinking
- data/memory.md -- compressed long-term memory
- data/watchlist.json -- dynamic ticker watchlist (agent-managed)
- data/prompt-state.json -- compiler state and change detection
- data/cycle-mode.json -- current mode and turns/timeout
- context/*.md -- feeder outputs consumed each cycle

## Action Format
The agent uses ACTION: commands that the playbook executes:
  ACTION: BUY ticker shares stop target
  ACTION: SELL ticker
  ACTION: SHORT ticker shares stop target
  ACTION: COVER ticker
  ACTION: WATCH ticker reason
  ACTION: ADD_WATCHLIST ticker
  ACTION: PREDICT long|short ticker deadline conviction

## Owner
Configure your timezone in config.sh

## Rules
- No dark mode on dashboard
- No paid API calls -- OAuth only
- Agent can trade any ticker (no watchlist restriction)
- Ticker aliases: BTC>BTC-USD, ETH>ETH-USD, GOLD>GC=F, OIL>CL=F, SILVER>SI=F
- Self-repair: fix your own errors from logs before doing anything else
