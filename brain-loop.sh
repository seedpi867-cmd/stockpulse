#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# brain-loop.sh — Stockpulse Market Intelligence Engine
#
# Codex CLI with full terminal access. The agent can:
# - Think about markets and make trades
# - Fix its own broken tools
# - Research online
# - Modify its own files
# - Add tickers to its watchlist
# ═══════════════════════════════════════════════════════════════
set -o pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/config.sh" 2>/dev/null || true

: "${SLEEP_SECONDS:=300}"
: "${MAX_TIMEOUT:=300}"
: "${CYCLE_LOG_KEEP:=200}"
: "${REVIEW_INTERVAL:=20}"

mkdir -p "$ROOT/data/logs" "$ROOT/context" "$ROOT/output" "$ROOT/knowledge/lessons" "$ROOT/data/journal"

# Singleton lock
LOCKFILE="/tmp/stockpulse-brain.lock"
exec 200>"$LOCKFILE" || exit 1
flock -n 200 || { echo "[stockpulse] Already running."; exit 1; }

# Cycle counter
CYCLE=0
[ -f "$ROOT/data/cycle.txt" ] && CYCLE=$(cat "$ROOT/data/cycle.txt" 2>/dev/null || echo 0)

echo "[stockpulse] ═══════════════════════════════════════════"
echo "[stockpulse] Stockpulse starting (PID $$)"
echo "[stockpulse] Cycle: $CYCLE | Sleep: ${SLEEP_SECONDS}s"
echo "[stockpulse] ═══════════════════════════════════════════"


# -- CLEANUP: strip instruction echo + dedup (GPT-5.5 workaround) --
clean_llm_output() {
    echo "$1" | python3 "$ROOT/tools/clean-output.py"
}

while true; do
    CYCLE=$((CYCLE + 1))
    echo "$CYCLE" > "$ROOT/data/cycle.txt"
    LOG="$ROOT/data/logs/cycle_${CYCLE}.log"
    STARTED=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[stockpulse] ── CYCLE $CYCLE ── $STARTED" | tee "$LOG"

    # ── 1. FEEDERS — gather market data ──────────────────
    echo "[stockpulse] Running feeders..." | tee -a "$LOG"
    python3 "$ROOT/tools/feed-prices.py" >> "$LOG" 2>&1 || echo "[stockpulse] feed-prices FAILED" >> "$LOG"
    python3 "$ROOT/tools/feed-news.py" >> "$LOG" 2>&1 || echo "[stockpulse] feed-news FAILED" >> "$LOG"
    python3 "$ROOT/tools/feed-calendar.py" >> "$LOG" 2>&1 || echo "[stockpulse] feed-calendar FAILED" >> "$LOG"
    python3 "$ROOT/tools/feed-sentiment.py" >> "$LOG" 2>&1 || echo "[stockpulse] feed-sentiment FAILED" >> "$LOG"
    python3 "$ROOT/tools/feed-sectors.py" >> "$LOG" 2>&1 || echo "[stockpulse] feed-sectors FAILED" >> "$LOG"
    python3 "$ROOT/tools/data-freshness.py" >> "$LOG" 2>&1 || true
    echo "[stockpulse] Feeders complete" | tee -a "$LOG"

    # ── 2. PORTFOLIO UPDATE ──────────────────────────────
    PORTFOLIO_OUT=$(python3 "$ROOT/tools/portfolio-tracker.py" 2>&1) || echo "[stockpulse] portfolio-tracker FAILED" >> "$LOG"
    echo "$PORTFOLIO_OUT" >> "$LOG"
    # Email on stop-loss hits
    if echo "$PORTFOLIO_OUT" | grep -q "\[portfolio-tracker\] STOP:"; then
        STOP_SUMMARY=$(echo "$PORTFOLIO_OUT" | grep "\[portfolio-tracker\] STOP:" | head -1 | sed 's/\[portfolio-tracker\] STOP: //')
        python3 "$ROOT/tools/stockpulse-email.py" --type stop --summary "$STOP_SUMMARY" >> "$LOG" 2>&1 || true
        echo "[stockpulse] Stop-loss email sent: $STOP_SUMMARY" | tee -a "$LOG"
    fi

    # ── 3. PREDICTION CHECK ──────────────────────────────
    python3 "$ROOT/tools/prediction-tracker.py" >> "$LOG" 2>&1 || echo "[stockpulse] prediction-tracker FAILED" >> "$LOG"

    # ── 3.5. JOURNAL ROUTER ──────────────────────────────
    python3 "$ROOT/tools/journal-router.py" >> "$LOG" 2>&1 || echo "[stockpulse] journal-router FAILED" >> "$LOG"

    # ── 4. CHECK FOR ERRORS — only tool failures, not the agent's own text ──
    ERRORS=$(grep "^\[stockpulse\].*FAILED\|^Traceback\|^ImportError\|^SyntaxError\|^ModuleNotFoundError" "$LOG" 2>/dev/null | head -20)

    # ── 5. SMART PROMPT COMPILER ────────────────────────
    python3 "$ROOT/tools/compactor.py" >> "$LOG" 2>&1 || true
    CYCLE_ERRORS="$ERRORS" AGENT_ROOT="$ROOT" python3 "$ROOT/tools/prompt-compiler.py" >> "$LOG" 2>&1 || true

    PROMPT="$ROOT/tmp_prompt.md"
    PROMPT_SIZE=$(wc -c < "$PROMPT")
    echo "[stockpulse] Prompt size: ${PROMPT_SIZE} bytes" | tee -a "$LOG"

    # Read dynamic mode config
    MODE_TURNS=5
    MODE_TIMEOUT=180
    MODE_SLEEP=300
    if [ -f "$ROOT/data/cycle-mode.json" ]; then
        MODE_TURNS=$(python3 -c "import json; print(json.load(open('$ROOT/data/cycle-mode.json')).get('max_turns',5))" 2>/dev/null || echo 5)
        MODE_TIMEOUT=$(python3 -c "import json; print(json.load(open('$ROOT/data/cycle-mode.json')).get('timeout',180))" 2>/dev/null || echo 180)
        MODE_SLEEP=$(python3 -c "import json; print(json.load(open('$ROOT/data/cycle-mode.json')).get('sleep',300))" 2>/dev/null || echo 300)
    fi
    echo "[stockpulse] Mode: turns=$MODE_TURNS timeout=$MODE_TIMEOUT sleep=$MODE_SLEEP" | tee -a "$LOG"

    # ── 6. LLM CALL (Codex) ─────────────────────────────
    if [ "$MODE_TURNS" -eq 0 ]; then
        echo "[stockpulse] SKIP mode — no LLM call needed" | tee -a "$LOG"
        LLM_OUTPUT=""
    else
        echo "[stockpulse] Calling Codex (timeout=$MODE_TIMEOUT)..." | tee -a "$LOG"
        # Build combined prompt: system instructions + market data
        SYSPROMPT=$(cat "$ROOT/AGENT.md" "$ROOT/INSTRUCTIONS.md" 2>/dev/null)
        COMBINED_PROMPT="$ROOT/tmp_combined_prompt.md"
        {
            echo "$SYSPROMPT"
            echo ""
            echo "---"
            echo ""
            cat "$PROMPT"
        } > "$COMBINED_PROMPT"

        rm -f "$ROOT/tmp_raw_output.txt"
        cat "$COMBINED_PROMPT" | timeout "$MODE_TIMEOUT" codex exec --sandbox read-only --skip-git-repo-check --ephemeral -C "$ROOT" - > "$ROOT/tmp_raw_output.txt" 2>&1 || true

        LLM_OUTPUT=$(clean_llm_output "$(cat "$ROOT/tmp_raw_output.txt")")
        echo "$LLM_OUTPUT" > "$ROOT/data/last-output.txt"
        rm -f "$COMBINED_PROMPT"

        if [ -z "$LLM_OUTPUT" ]; then
            echo "[stockpulse] WARNING: Empty LLM response" | tee -a "$LOG"
            # Log raw output for debugging empty responses only
            echo "[stockpulse] Raw output:" >> "$LOG"
            cat "$ROOT/tmp_raw_output.txt" >> "$LOG" 2>/dev/null
            # Check if auth expired
            if grep -q "401\|auth\|token.*expired\|unauthorized\|OAuth" "$ROOT/tmp_raw_output.txt" 2>/dev/null; then
                echo "[stockpulse] AUTH ERROR detected — waiting 60s then retrying" | tee -a "$LOG"
                sleep 60
                {
                    echo "$SYSPROMPT"
                    echo ""
                    echo "---"
                    echo ""
                    cat "$PROMPT"
                } > "$COMBINED_PROMPT"
                rm -f "$ROOT/tmp_raw_output.txt"
                cat "$COMBINED_PROMPT" | timeout "$MODE_TIMEOUT" codex exec --sandbox read-only --skip-git-repo-check --ephemeral -C "$ROOT" - > "$ROOT/tmp_raw_output.txt" 2>&1 || true
                LLM_OUTPUT=$(clean_llm_output "$(cat "$ROOT/tmp_raw_output.txt")")
                echo "$LLM_OUTPUT" > "$ROOT/data/last-output.txt"
                rm -f "$COMBINED_PROMPT"
                if [ -z "$LLM_OUTPUT" ]; then
                    echo "[stockpulse] RETRY FAILED — skipping cycle" | tee -a "$LOG"
                    cat "$ROOT/tmp_raw_output.txt" >> "$LOG" 2>/dev/null
                else
                    echo "[stockpulse] RETRY OK — response: $(echo "$LLM_OUTPUT" | wc -c) bytes" | tee -a "$LOG"
                fi
            fi
        else
            echo "[stockpulse] LLM response: $(echo "$LLM_OUTPUT" | wc -c) bytes" | tee -a "$LOG"
        fi

        # Log the cleaned output once
        if [ -n "$LLM_OUTPUT" ]; then
            echo "$LLM_OUTPUT" >> "$LOG"
        fi
        rm -f "$ROOT/tmp_raw_output.txt"
    fi

    # ── 6.5. TRAINING DATA CAPTURE ──────────────────────
    if [ -n "$LLM_OUTPUT" ] && [ "$MODE_TURNS" -gt 0 ]; then
        echo "$LLM_OUTPUT" > "$ROOT/tmp_response.txt"
        CAPTURE_MODE=$(python3 -c "import json; print(json.load(open('$ROOT/data/cycle-mode.json')).get('mode','normal'))" 2>/dev/null || echo normal)
        AGENT_ROOT="$ROOT" python3 "$ROOT/tools/training-capture.py" "$CYCLE" "$CAPTURE_MODE" "$ROOT/tmp_prompt.md" "$ROOT/tmp_response.txt" >> "$LOG" 2>&1 || true
        rm -f "$ROOT/tmp_response.txt"
    fi

    # ── 7. PARSE LLM OUTPUT ─────────────────────────────
    echo "[stockpulse] Parsing output..." | tee -a "$LOG"

    # Inner voice
    INNER=$(echo "$LLM_OUTPUT" | sed -n '/^INNER_VOICE:/,/^[A-Z_]*:/p' | head -20 | sed '1s/^INNER_VOICE: *//' | sed '$d')
    if [ -n "$INNER" ]; then
        printf '\n---\nCycle %d (%s):\n%s\n' "$CYCLE" "$(date '+%H:%M')" "$INNER" >> "$ROOT/data/inner-voice.md"
    fi

    # Thoughts
    THOUGHT_LINE=$(echo "$LLM_OUTPUT" | grep "^THOUGHTS:" | head -1 | sed 's/^THOUGHTS: *//')
    if [ -n "$THOUGHT_LINE" ]; then
        printf '\n---\nCycle %d (%s):\n%s\n' "$CYCLE" "$(date '+%H:%M')" "$THOUGHT_LINE" >> "$ROOT/data/thoughts.md"
    fi

    # Mood
    MOOD_LINE=$(echo "$LLM_OUTPUT" | grep "^MOOD:" | head -1)
    if [ -n "$MOOD_LINE" ]; then
        python3 "$ROOT/tools/parse-mood.py" "$MOOD_LINE" > "$ROOT/data/mood.json.tmp" 2>/dev/null && \
            mv "$ROOT/data/mood.json.tmp" "$ROOT/data/mood.json"
    fi

    # Overall mood
    OVERALL_LINE=$(echo "$LLM_OUTPUT" | grep "^OVERALL:" | head -1 | sed 's/^OVERALL: *//')
    if [ -n "$OVERALL_LINE" ]; then
        python3 "$ROOT/tools/parse-overall.py" "$OVERALL_LINE" 2>/dev/null || true
    fi

    # Memory
    MEMORY_LINE=$(echo "$LLM_OUTPUT" | grep "^MEMORY:" | head -1 | sed 's/^MEMORY: *//')
    if [ -n "$MEMORY_LINE" ]; then
        echo "- Cycle $CYCLE ($(date '+%H:%M')): $MEMORY_LINE" >> "$ROOT/data/memory.md"
    else
        echo "- Cycle $CYCLE ($(date '+%H:%M')): completed" >> "$ROOT/data/memory.md"
    fi

    # ── 8. TRADE EXECUTION ───────────────────────────────
    PLAYBOOK_OUT=$(python3 "$ROOT/tools/playbook.py" 2>&1) || echo "[stockpulse] playbook FAILED" >> "$LOG"
    echo "$PLAYBOOK_OUT" >> "$LOG"

    # ── 8.1. EMAIL ALERTS (only on real trades/stops) ────
    if echo "$PLAYBOOK_OUT" | grep -q "OK: BOUGHT\|OK: SOLD\|OK: SHORTED\|OK: COVERED"; then
        TRADE_SUMMARY=$(echo "$PLAYBOOK_OUT" | grep "OK: BOUGHT\|OK: SOLD\|OK: SHORTED\|OK: COVERED" | head -1 | sed 's/\[playbook\] OK: //')
        python3 "$ROOT/tools/stockpulse-email.py" --type trade --summary "$TRADE_SUMMARY" >> "$LOG" 2>&1 || true
        echo "[stockpulse] Trade email sent: $TRADE_SUMMARY" | tee -a "$LOG"
        python3 "$ROOT/tools/speak.py" alert "$TRADE_SUMMARY" >> "$LOG" 2>&1 &
    fi
    if echo "$PLAYBOOK_OUT" | grep -q "STOPPED\|STOP HIT\|stop.*triggered"; then
        STOP_SUMMARY=$(echo "$PLAYBOOK_OUT" | grep "STOPPED\|STOP HIT\|stop.*triggered" | head -1 | sed 's/\[playbook\] OK: //')
        python3 "$ROOT/tools/stockpulse-email.py" --type stop --summary "$STOP_SUMMARY" >> "$LOG" 2>&1 || true
        echo "[stockpulse] Stop email sent: $STOP_SUMMARY" | tee -a "$LOG"
        python3 "$ROOT/tools/speak.py" alert "$STOP_SUMMARY" >> "$LOG" 2>&1 &
    fi

    # ── 8.5. JOURNAL ─────────────────────────────────────
    python3 "$ROOT/tools/journal-writer.py" >> "$LOG" 2>&1 || true

    # ── 9. DASHBOARD UPDATE ──────────────────────────────
    python3 "$ROOT/tools/daily-pnl.py" >> "$LOG" 2>&1 || true
    python3 "$ROOT/tools/update-dashboard.py" >> "$LOG" 2>&1 || true
    python3 "$ROOT/tools/token-tracker.py" >> "$LOG" 2>&1 || true

    # ── 9.1. WEEKLY EMAIL (Saturday only, first cycle of the day) ──
    if [ "$(date +%u)" = "6" ] && [ "$CYCLE" -gt 1 ]; then
        LAST_WEEKLY=$(grep '"type":"weekly"' "$ROOT/data/email-sent.jsonl" 2>/dev/null | tail -1 | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('date','')[:10])" 2>/dev/null || echo "")
        if [ "$LAST_WEEKLY" != "$(date +%Y-%m-%d)" ]; then
            python3 "$ROOT/tools/stockpulse-email.py" --type weekly >> "$LOG" 2>&1 || true
            echo "[stockpulse] Weekly email sent" | tee -a "$LOG"
        fi
    fi

    # ── 10. SELF-REVIEW (every N cycles) ─────────────────
    if [ $((CYCLE % REVIEW_INTERVAL)) -eq 0 ]; then
        echo "[stockpulse] Running self-review..." | tee -a "$LOG"
        python3 "$ROOT/tools/self-review.py" >> "$LOG" 2>&1 || true
    fi

    # ── HOUSEKEEPING ─────────────────────────────────────
    if [ -f "$ROOT/data/memory.md" ]; then
        tail -50 "$ROOT/data/memory.md" > "$ROOT/data/memory.md.tmp"
        mv "$ROOT/data/memory.md.tmp" "$ROOT/data/memory.md"
    fi
    if [ -f "$ROOT/data/inner-voice.md" ]; then
        tail -100 "$ROOT/data/inner-voice.md" > "$ROOT/data/inner-voice.md.tmp"
        mv "$ROOT/data/inner-voice.md.tmp" "$ROOT/data/inner-voice.md"
    fi
    ls -t "$ROOT/data/logs"/cycle_*.log 2>/dev/null | tail -n +$((CYCLE_LOG_KEEP + 1)) | xargs rm -f 2>/dev/null
    rm -f "$PROMPT"

    ELAPSED=$(( $(date +%s) - $(date -d "$STARTED" +%s 2>/dev/null || echo 0) ))
    echo "[stockpulse] Cycle $CYCLE complete (${ELAPSED}s). Sleeping ${SLEEP_SECONDS}s..." | tee -a "$LOG"
    # Dynamic sleep based on mode
    ACTUAL_SLEEP=${MODE_SLEEP:-$SLEEP_SECONDS}
    sleep "$ACTUAL_SLEEP"
done
