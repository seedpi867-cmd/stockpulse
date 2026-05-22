import { useState } from 'react'
import { useData } from '../hooks/useData'
import StatCard from '../components/StatCard'
import EquityCurve from '../components/EquityCurve'

function fmt(n, d = 2) {
  if (n == null) return '—'
  return n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })
}

function timeAgo(ts) {
  if (!ts) return ''
  const s = (Date.now() - new Date(ts).getTime()) / 1000
  if (s < 60) return `${Math.round(s)}s ago`
  if (s < 3600) return `${Math.round(s / 60)}m ago`
  if (s < 86400) return `${Math.round(s / 3600)}h ago`
  return `${Math.round(s / 86400)}d ago`
}

function stopProgress(pos) {
  const { entry_price, current_price, stop, target, direction } = pos
  if (!stop || !target || stop === target) return 50
  if (direction === 'long') return Math.max(0, Math.min(100, ((current_price - stop) / (target - stop)) * 100))
  return Math.max(0, Math.min(100, ((stop - current_price) / (stop - target)) * 100))
}

export default function Portfolio() {
  const { data, health } = useData()
  const [expandedPos, setExpandedPos] = useState(null)
  const [expandedTrade, setExpandedTrade] = useState(null)
  const [showAllTrades, setShowAllTrades] = useState(false)

  const perf = data.performance || {}
  const positions = data.portfolio?.positions || []
  const trades = data.trades || []
  const dailyPnl = health?.daily_pnl || []
  const visible = showAllTrades ? trades : trades.slice(0, 15)

  return (
    <div className="page">
      <div className="page-header">
        <h1>Portfolio</h1>
        <p>Current positions, trade history, and performance metrics.</p>
      </div>

      {/* Performance stats */}
      <div className="stats-row">
        <StatCard label="Portfolio Value" value={`$${fmt(perf.portfolio_value, 0)}`} className={perf.total_pnl >= 0 ? 'up' : 'down'} />
        <StatCard label="Cash" value={`$${fmt(perf.cash_available, 0)}`} />
        <StatCard label="Total P&L" value={`${perf.total_pnl >= 0 ? '+' : ''}$${fmt(perf.total_pnl, 0)}`} sub={`${(perf.total_pnl_pct || 0).toFixed(1)}%`} className={perf.total_pnl >= 0 ? 'up' : 'down'} />
        <StatCard label="Win Rate" value={`${(perf.win_rate || 0).toFixed(0)}%`} sub={`${perf.wins}W / ${perf.losses}L`} />
        <StatCard label="Streak" value={`${perf.streak || 0} ${perf.streak_type || ''}`} className={perf.streak_type === 'win' ? 'up' : 'down'} />
        <StatCard label="Drawdown" value={`${(perf.current_drawdown || 0).toFixed(1)}%`} sub={`Max: ${(perf.max_drawdown || 0).toFixed(1)}%`} />
      </div>

      {/* Equity curve */}
      {dailyPnl.length > 1 && (
        <div className="card">
          <div className="card-header"><h3>Equity Curve</h3></div>
          <EquityCurve dailyPnl={dailyPnl} />
        </div>
      )}

      {/* Open positions */}
      <div className="card">
        <div className="card-header">
          <h3>Open Positions ({positions.length})</h3>
          <span className="card-sub">{positions.length === 0 ? 'All cash' : 'Click a position to see the reasoning'}</span>
        </div>
        {positions.length === 0 ? (
          <div className="card-empty">No open positions — the agent is analysing the market and waiting for a setup that meets its criteria.</div>
        ) : (
          <div className="card-body">
            {positions.map((pos, i) => {
              const pl = pos.unrealized_pnl || 0
              const plPct = pos.unrealized_pnl_pct || 0
              const progress = stopProgress(pos)
              const isUp = pl >= 0

              return (
                <div className={`position-card ${expandedPos === i ? 'expanded' : ''}`} key={i} onClick={() => setExpandedPos(expandedPos === i ? null : i)}>
                  <div className="position-top">
                    <div className="position-left">
                      <span className="position-ticker">{pos.ticker}</span>
                      <span className={`badge ${pos.direction}`}>{pos.direction}</span>
                      <span className="position-info">{pos.shares} shares @ ${fmt(pos.entry_price)}</span>
                    </div>
                    <div className={`position-pnl ${isUp ? 'up' : 'down'}`}>
                      {isUp ? '+' : ''}${fmt(pl)} ({plPct >= 0 ? '+' : ''}{plPct.toFixed(1)}%)
                    </div>
                  </div>

                  <div className="position-metrics">
                    <span>Current: <strong>${fmt(pos.current_price)}</strong></span>
                    <span>Stop: ${fmt(pos.stop)}</span>
                    <span>Target: ${fmt(pos.target)}</span>
                    <span>Conviction: {pos.conviction ? `${Math.round(pos.conviction * 100)}%` : '—'}</span>
                  </div>

                  <div className="progress-bar">
                    <div className="progress-fill" style={{ width: `${progress}%`, background: isUp ? 'var(--green)' : 'var(--red)' }} />
                  </div>
                  <div className="progress-labels">
                    <span>Stop ${fmt(pos.stop)}</span>
                    <span>Target ${fmt(pos.target)}</span>
                  </div>

                  {expandedPos === i && pos.reasoning && (
                    <div className="position-reasoning">{pos.reasoning}</div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Trade history */}
      <div className="card">
        <div className="card-header">
          <h3>Trade History</h3>
          <span className="card-sub">{trades.length} recent trades — click to see reasoning</span>
        </div>
        <div className="card-body">
          <div className="trade-table">
            <div className="trade-header-row">
              <span>Action</span>
              <span>Ticker</span>
              <span>Details</span>
              <span>P&L</span>
              <span>Time</span>
            </div>
            {visible.map((t, i) => {
              const isBuy = t.action?.toUpperCase().includes('BUY') || t.action?.toUpperCase() === 'LONG'
              const pnl = t.pnl || t.realized_pnl
              const hasPnl = pnl != null && pnl !== 0
              return (
                <div key={i}>
                  <div className="trade-row" onClick={() => setExpandedTrade(expandedTrade === i ? null : i)}>
                    <span><span className={`badge ${isBuy ? 'long' : 'short'}`}>{t.action}</span></span>
                    <span className="mono-bold">{t.ticker}</span>
                    <span className="mono-dim">{t.shares} @ ${fmt(t.price)}</span>
                    <span className={hasPnl ? (pnl >= 0 ? 'up mono-bold' : 'down mono-bold') : 'mono-dim'}>
                      {hasPnl ? `${pnl >= 0 ? '+' : ''}$${fmt(pnl)}` : '—'}
                    </span>
                    <span className="mono-dim">{timeAgo(t.timestamp)}</span>
                  </div>
                  {expandedTrade === i && t.reasoning && (
                    <div className="trade-reasoning">{t.reasoning}</div>
                  )}
                </div>
              )
            })}
          </div>
          {trades.length > 15 && (
            <button className="btn-show-more" onClick={() => setShowAllTrades(!showAllTrades)}>
              {showAllTrades ? 'Show less' : `Show all ${trades.length} trades`}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
