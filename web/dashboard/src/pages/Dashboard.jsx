import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useData } from '../hooks/useData'
import StatCard from '../components/StatCard'
import EquityCurve from '../components/EquityCurve'
import SectorHeatmap from '../components/SectorHeatmap'
import MoodGauge from '../components/MoodGauge'

function fmt(n, d = 0) {
  if (n == null) return '—'
  return n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d })
}

function daysSince(dateStr) {
  if (!dateStr) return 0
  return Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000)
}

function HeartbeatChart() {
  // ECG-style heartbeat pattern repeated across the width — stock chart meets pulse monitor
  const beat = (x) => [
    `${x},40`, `${x+55},40`,
    `${x+62},35`, `${x+70},45`, `${x+74},40`,  // P-wave
    `${x+88},40`,
    `${x+93},12`, `${x+100},68`, `${x+106},28`, `${x+112},40`,  // QRS spike
    `${x+130},40`,
    `${x+138},33`, `${x+150},40`,  // T-wave
    `${x+185},40`,
  ].join(' L')

  const path = `M${beat(0)} L${beat(190)} L${beat(380)} L${beat(570)} L800,40`

  return (
    <svg className="hero-heartbeat" viewBox="0 0 800 80" preserveAspectRatio="none">
      <defs>
        <linearGradient id="hbGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a7f3d0" stopOpacity="0.06" />
          <stop offset="100%" stopColor="#a7f3d0" stopOpacity="0" />
        </linearGradient>
        <filter id="hbGlow">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <clipPath id="hbReveal">
          <rect x="0" y="0" width="800" height="80" className="hb-clip-rect" />
        </clipPath>
      </defs>
      {/* Dim baseline always visible */}
      <path d={path} fill="none" stroke="rgba(167,243,208,0.08)" strokeWidth="1" />
      {/* Area fill revealed with clip */}
      <path d={`${path} L800,80 L0,80 Z`} fill="url(#hbGrad)" clipPath="url(#hbReveal)" className="hb-area" />
      {/* Bright animated line */}
      <path d={path} fill="none" stroke="rgba(167,243,208,0.5)" strokeWidth="1.5" filter="url(#hbGlow)" clipPath="url(#hbReveal)" className="hb-line" />
    </svg>
  )
}

function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0)
  const prevTarget = useRef(0)

  useEffect(() => {
    if (!target || target === prevTarget.current) return
    const from = prevTarget.current
    prevTarget.current = target
    let start = null
    const step = (ts) => {
      if (!start) start = ts
      const progress = Math.min((ts - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
      setValue(Math.floor(from + (target - from) * eased))
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [target, duration])

  return value
}

function ThoughtCycler({ voices }) {
  const [idx, setIdx] = useState(0)
  const [phase, setPhase] = useState('visible') // visible | exiting | entering
  const items = voices.slice(0, 6)
  const timerRef = useRef(null)
  const progressRef = useRef(null)
  const [progress, setProgress] = useState(0)
  const pausedRef = useRef(false)

  const advance = useCallback((newIdx) => {
    if (items.length <= 1) return
    setPhase('exiting')
    setTimeout(() => {
      setIdx(typeof newIdx === 'number' ? newIdx : (i) => (i + 1) % items.length)
      setPhase('entering')
      setProgress(0)
      setTimeout(() => setPhase('visible'), 50)
    }, 400)
  }, [items.length])

  const pause = useCallback(() => { pausedRef.current = true }, [])
  const resume = useCallback(() => { pausedRef.current = false }, [])

  useEffect(() => {
    if (items.length <= 1) return
    const CYCLE_MS = 7000
    const TICK_MS = 50
    let elapsed = 0
    progressRef.current = setInterval(() => {
      if (pausedRef.current) return
      elapsed += TICK_MS
      setProgress(Math.min(elapsed / CYCLE_MS, 1))
    }, TICK_MS)
    timerRef.current = setInterval(() => {
      if (pausedRef.current) return
      elapsed = 0
      advance()
    }, CYCLE_MS)
    return () => {
      clearInterval(timerRef.current)
      clearInterval(progressRef.current)
    }
  }, [items.length, advance])

  if (!items.length) return <div className="card-empty">No thoughts yet</div>

  const current = items[idx % items.length]

  return (
    <div className="thought-cycle" onMouseEnter={pause} onMouseLeave={resume}>
      <div className={`thought-cycle-item ${phase}`}>
        <div className="thought-badge">Cycle {current?.cycle} {current?.time && `· ${current.time}`}</div>
        <p style={{ fontSize: '0.88rem', lineHeight: 1.6 }}>{current?.text}</p>
      </div>
      {items.length > 1 && (
        <>
          <div className="thought-cycle-dots">
            {items.map((_, i) => (
              <span
                key={i}
                className={`thought-cycle-dot ${i === idx % items.length ? 'active' : ''}`}
                onClick={() => { clearInterval(timerRef.current); advance(i); }}
              />
            ))}
          </div>
          <div className="thought-cycle-progress">
            <div className="thought-cycle-bar" style={{ width: `${progress * 100}%` }} />
          </div>
        </>
      )}
    </div>
  )
}

function LiveFeed({ data }) {
  const items = []

  // Recent trades
  const trades = data.trades || []
  for (const t of trades.slice(0, 3)) {
    items.push({
      icon: t.action === 'BUY' ? '↗' : '↘',
      text: <><strong>{t.action} {t.ticker}</strong> — {t.shares} shares @ ${t.entry_price?.toFixed(2)}</>,
      time: t.time || '',
      sort: t.timestamp || 0,
    })
  }

  // Recent predictions
  const preds = data.predictions || []
  for (const p of preds.slice(0, 2)) {
    const status = p.was_correct === true ? '✓' : p.was_correct === false ? '✗' : '◎'
    items.push({
      icon: status,
      text: <>{p.prediction?.slice(0, 100)}{p.prediction?.length > 100 ? '...' : ''}</>,
      time: '',
      sort: 0,
    })
  }

  if (!items.length) return <div className="card-empty">Waiting for activity...</div>

  return (
    <div className="live-feed">
      {items.map((item, i) => (
        <div className="live-feed-item" key={i}>
          <span className="live-feed-icon">{item.icon}</span>
          <span className="live-feed-text">{item.text}</span>
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const { data, health } = useData()
  const perf = data.performance || {}
  const port = data.portfolio || {}
  const positions = port.positions || []
  const pnl = perf.total_pnl || 0
  const dailyPnl = health?.daily_pnl || []
  const voices = data.inner_voice || []

  const animatedValue = useCountUp(perf.portfolio_value, 1500)

  return (
    <div className="page">
      {/* Hero */}
      <div className="hero">
        <HeartbeatChart />
        <div className="hero-text">
          <h1>Stockpulse</h1>
          <p>
            An autonomous AI agent that analyses live market data every 5 minutes, forms its own
            trading theses, executes trades, and evolves its strategy — running 24/7 on a Raspberry Pi 5
            with $100k paper trading capital.
          </p>
          <div className="hero-links">
            <Link to="/agent" className="btn btn-light">See what it's thinking</Link>
            <Link to="/about" className="btn btn-outline">How it works</Link>
          </div>
        </div>
        <div className="hero-value">
          <div className="hero-label">Portfolio Value</div>
          <div className={`hero-amount ${pnl >= 0 ? 'up' : 'down'}`}>
            ${animatedValue ? fmt(animatedValue) : fmt(perf.portfolio_value)}
          </div>
          <div className={`hero-pnl ${pnl >= 0 ? 'up' : 'down'}`}>
            {pnl >= 0 ? '+' : ''}${fmt(pnl)} ({(perf.total_pnl_pct || 0).toFixed(1)}%)
          </div>
          <div className="hero-since">
            Day {daysSince(port.started_at)} — Cycle {data.cycle}
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="stats-row">
        <StatCard label="Win Rate" value={`${(perf.win_rate || 0).toFixed(0)}%`} sub={`${perf.wins}W / ${perf.losses}L`} />
        <StatCard label="Total Trades" value={perf.total_trades || 0} sub={`Avg win $${fmt(perf.avg_win)} / Avg loss $${fmt(perf.avg_loss)}`} />
        <StatCard label="Best Trade" value={`+$${fmt(perf.best_trade)}`} className="up" />
        <StatCard label="Worst Trade" value={`$${fmt(perf.worst_trade)}`} className="down" />
        <StatCard label="Max Drawdown" value={`${(perf.max_drawdown || 0).toFixed(1)}%`} sub={`Current: ${(perf.current_drawdown || 0).toFixed(1)}%`} />
        <StatCard label="Cash Available" value={`$${fmt(perf.cash_available)}`} />
      </div>

      {/* Equity curve */}
      {dailyPnl.length > 1 && (
        <div className="card">
          <div className="card-header">
            <h3>Equity Curve</h3>
            <span className="card-sub">Daily portfolio value since inception</span>
          </div>
          <EquityCurve dailyPnl={dailyPnl} />
        </div>
      )}

      {/* Two columns: positions + live activity */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3>Open Positions</h3>
            <Link to="/portfolio" className="card-link">View all trades →</Link>
          </div>
          {positions.length === 0 ? (
            <div className="card-empty">All cash — waiting for setups</div>
          ) : (
            <div className="card-body">
              {positions.map((pos, i) => {
                const pl = pos.unrealized_pnl || 0
                return (
                  <div className="pos-row" key={i}>
                    <div className="pos-left">
                      <span className="pos-ticker">{pos.ticker}</span>
                      <span className={`badge ${pos.direction}`}>{pos.direction}</span>
                      <span className="pos-detail">{pos.shares} @ ${pos.entry_price?.toFixed(2)}</span>
                    </div>
                    <div className={`pos-pnl ${pl >= 0 ? 'up' : 'down'}`}>
                      {pl >= 0 ? '+' : ''}${pl.toFixed(2)}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Recent Activity</h3>
            <span className="live-badge"><span className="live-dot" /> Live</span>
          </div>
          <div className="card-body">
            <LiveFeed data={data} />
          </div>
        </div>
      </div>

      {/* Agent mood + cycling thoughts */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3>Agent Mood</h3>
            <Link to="/agent" className="card-link">Full mind view →</Link>
          </div>
          <div className="card-body">
            <MoodGauge mood={data.mood} />
            {data.mood?.overall && (
              <div className="card-quote">"{data.mood.overall}"</div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Latest Thoughts</h3>
            <Link to="/agent" className="card-link">All thoughts →</Link>
          </div>
          <div className="card-body">
            <ThoughtCycler voices={voices} />
          </div>
        </div>
      </div>

      {/* Sectors */}
      <div className="card">
        <div className="card-header">
          <h3>Sector Performance</h3>
          <Link to="/market" className="card-link">Full market →</Link>
        </div>
        <div className="card-body">
          <SectorHeatmap sectorsMd={data.market?.sectors} />
        </div>
      </div>
    </div>
  )
}
