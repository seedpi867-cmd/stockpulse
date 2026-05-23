# ═══════════════════════════════════════════════════════════════
# config.sh — LLM backend and timing config
# ═══════════════════════════════════════════════════════════════

# Codex (OpenAI) — free with OAuth login
LLM_CMD="codex exec --sandbox read-only --skip-git-repo-check --ephemeral"

# ── Timing ──
SLEEP_SECONDS=300      # seconds between cycles (5 min default)
MAX_TIMEOUT=1800       # kill the LLM call after this many seconds
CYCLE_LOG_KEEP=50      # keep last N cycle logs

# ── Risk ──
MAX_POSITIONS=8        # max open positions
MAX_POSITION_PCT=12    # max % of portfolio per position
