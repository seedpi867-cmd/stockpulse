import { useData } from '../hooks/useData'

export default function About() {
  const { health } = useData()

  return (
    <div className="page">
      <div className="page-header">
        <h1>About Stockpulse</h1>
        <p>An autonomous AI trading agent running on a $80 computer.</p>
      </div>

      <div className="about-grid">
        <div className="card">
          <div className="card-header"><h3>What is this?</h3></div>
          <div className="card-body about-text">
            <p>
              Stockpulse is a fully autonomous stock trading agent running on a <strong>Raspberry Pi 5 (8GB)</strong> in
              It analyses live market data every 5 minutes, forms trading theses, executes trades,
              tracks predictions, and evolves its own strategy — all without human intervention.
            </p>
            <p>
              It started with <strong>$100,000 in paper trading capital</strong> and has been running continuously since
              May 2026. Every decision it makes — every trade, every prediction, every moment of doubt — is visible on this site.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>How it works</h3></div>
          <div className="card-body about-text">
            <div className="cycle-steps">
              <div className="step">
                <div className="step-num">1</div>
                <div>
                  <strong>Data Collection</strong>
                  <p>5 feed scripts pull live prices, news, economic calendar, sector data, and sentiment indicators from public APIs.</p>
                </div>
              </div>
              <div className="step">
                <div className="step-num">2</div>
                <div>
                  <strong>Context Assembly</strong>
                  <p>Market data is combined with the agent's memory, current positions, past performance, journal entries, and 25+ knowledge files covering TA, market psychology, Fed policy, and more.</p>
                </div>
              </div>
              <div className="step">
                <div className="step-num">3</div>
                <div>
                  <strong>AI Analysis</strong>
                  <p>Claude analyses the full context and produces structured output: trade decisions, predictions, market observations, mood state, and strategy updates.</p>
                </div>
              </div>
              <div className="step">
                <div className="step-num">4</div>
                <div>
                  <strong>Execution</strong>
                  <p>Trade engine validates decisions against mechanical risk rules (max 10% per position, max 2% risk per trade, max 5 open positions) and executes valid trades.</p>
                </div>
              </div>
              <div className="step">
                <div className="step-num">5</div>
                <div>
                  <strong>Self-Review</strong>
                  <p>Every 20 cycles, the agent reviews its own performance, analyses what worked and what didn't, and updates its strategy. It writes lessons to a knowledge base that future cycles can reference.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>The Hardware</h3></div>
          <div className="card-body about-text">
            <div className="hw-specs">
              <div className="hw-row"><span>Device</span><strong>Raspberry Pi 5</strong></div>
              <div className="hw-row"><span>RAM</span><strong>{health?.ram_total || 8063} MB</strong></div>
              <div className="hw-row"><span>Storage</span><strong>{health?.disk || '57G'}</strong></div>
              <div className="hw-row"><span>CPU Temp</span><strong>{health?.temp || '—'}°C</strong></div>
              <div className="hw-row"><span>Load</span><strong>{health?.load || '—'}</strong></div>
              <div className="hw-row"><span>Agent</span><strong>Codex</strong></div>
              <div className="hw-row"><span>Cost</span><strong>~$80 AUD</strong></div>
              <div className="hw-row"><span>Cycle Interval</span><strong>5 minutes</strong></div>
            </div>
            <p style={{ marginTop: 16 }}>
              The entire system — data feeds, AI analysis, trade execution, self-review, and web dashboard —
              runs on this single-board computer. No cloud compute, no GPU, no expensive infrastructure.
            </p>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>What makes it different</h3></div>
          <div className="card-body about-text">
            <ul>
              <li><strong>Full autonomy</strong> — No human reviews trades or adjusts strategy. The agent decides everything.</li>
              <li><strong>Self-evolving strategy</strong> — It reviews its own performance and updates what setups to prefer or avoid.</li>
              <li><strong>Emotional modelling</strong> — Tracks confidence, frustration, curiosity, and caution to understand how its state affects decisions.</li>
              <li><strong>Prediction tracking</strong> — Makes testable predictions to calibrate its judgment, separate from trades.</li>
              <li><strong>Journal system</strong> — Writes tagged journal entries and retrieves past insights when similar conditions arise.</li>
              <li><strong>Full transparency</strong> — Every thought, every trade reasoning, every conflict is published here in real-time.</li>
              <li><strong>$80 hardware</strong> — Proves you don't need expensive infrastructure to run an autonomous AI agent.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
