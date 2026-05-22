import { useState } from 'react'
import { useData } from '../hooks/useData'
import MoodGauge from '../components/MoodGauge'

export default function AgentMind() {
  const { data } = useData()
  const [tab, setTab] = useState('voice')

  const voices = data.inner_voice || []
  const thoughts = data.thoughts || []
  const notes = data.notes_to_future || []
  const collisions = data.collisions || []
  const theses = data.active_theses || []
  const predictions = data.predictions || []
  const strategy = data.strategy || {}
  const predStats = data.prediction_stats || {}

  const tabs = [
    { id: 'voice', label: 'Inner Voice', count: voices.length },
    { id: 'thoughts', label: 'Insights', count: thoughts.length },
    { id: 'notes', label: 'Notes to Self', count: notes.length },
    { id: 'collisions', label: 'Contradictions', count: collisions.length },
  ]

  return (
    <div className="page">
      <div className="page-header">
        <h1>Agent Mind</h1>
        <p>
          What the agent is thinking, its current beliefs, contradictions it's spotted,
          and how its strategy is evolving. This is full transparency into an autonomous AI's decision-making.
        </p>
      </div>

      {/* Thought stream */}
      <div className="card card-accent">
        <div className="card-header accent-header">
          <h3>Thought Stream</h3>
          <span className="live-badge"><span className="live-dot" /> Live</span>
        </div>
        <div className="tabs">
          {tabs.map(t => (
            <button key={t.id} className={`tab ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
              {t.label} <span className="tab-num">{t.count}</span>
            </button>
          ))}
        </div>
        <div className="card-body card-scroll">
          {tab === 'voice' && voices.map((v, i) => (
            <div className={`thought-item ${i === 0 ? 'latest' : ''}`} key={i}>
              <div className="thought-badge">C{v.cycle} {v.time && `• ${v.time}`}</div>
              <p>{v.text}</p>
            </div>
          ))}
          {tab === 'thoughts' && thoughts.map((t, i) => (
            <div className={`thought-item ${i === 0 ? 'latest' : ''}`} key={i}>
              <div className="thought-badge">C{t.cycle} {t.time && `• ${t.time}`}</div>
              <p>{t.text}</p>
            </div>
          ))}
          {tab === 'notes' && notes.map((n, i) => (
            <div className="thought-item" key={i}>
              <div className="thought-badge">C{n.cycle}</div>
              <p>{n.text}</p>
            </div>
          ))}
          {tab === 'collisions' && collisions.map((c, i) => (
            <div className="thought-item collision" key={i}>
              <div className="thought-badge">C{c.cycle} — Conflict</div>
              <p>{c.text}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid-2">
        {/* Mood */}
        <div className="card">
          <div className="card-header">
            <h3>Current Mood</h3>
            <span className="card-sub">Emotional state influences risk appetite and position sizing</span>
          </div>
          <div className="card-body">
            <MoodGauge mood={data.mood} />
            {data.mood?.overall && <div className="card-quote">"{data.mood.overall}"</div>}
          </div>
        </div>

        {/* Active theses */}
        <div className="card">
          <div className="card-header">
            <h3>Active Theses ({theses.length})</h3>
            <span className="card-sub">What the agent currently believes and is betting on</span>
          </div>
          <div className="card-body">
            {theses.map((t, i) => (
              <div className="thesis-item" key={i}>
                <div className="thesis-top">
                  <span className="mono-bold">{t.ticker}</span>
                  <span className={`badge ${t.direction}`}>{t.direction}</span>
                  <span className="mono-dim">Entry ${t.entry?.toFixed(2)}</span>
                  {t.conviction && <span className="mono-dim">{Math.round(t.conviction * 100)}% conv</span>}
                </div>
                {t.reasoning && <p className="thesis-reasoning">{t.reasoning}</p>}
              </div>
            ))}
            {theses.length === 0 && <div className="card-empty">No active theses</div>}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Strategy */}
        <div className="card">
          <div className="card-header">
            <h3>Strategy</h3>
            <span className="card-sub">Evolves automatically based on trade outcomes</span>
          </div>
          <div className="card-body">
            {strategy.overall_rating && <div className="strategy-rating">{strategy.overall_rating}</div>}
            {(strategy.hypotheses || []).length > 0 && (
              <div className="strategy-section">
                <div className="section-title">Hypotheses Being Tested</div>
                {strategy.hypotheses.map((h, i) => <div className="hyp-item" key={i}>{i + 1}. {h}</div>)}
              </div>
            )}
            {(strategy.preferred_setups || []).length > 0 && (
              <div className="strategy-section">
                <div className="section-title">Preferred Setups</div>
                <div className="pills">{strategy.preferred_setups.map((s, i) => <span className="pill green" key={i}>{s}</span>)}</div>
              </div>
            )}
            {(strategy.avoid_setups || []).length > 0 && (
              <div className="strategy-section">
                <div className="section-title">Avoiding</div>
                <div className="pills">{strategy.avoid_setups.map((s, i) => <span className="pill red" key={i}>{s}</span>)}</div>
              </div>
            )}
          </div>
        </div>

        {/* Predictions */}
        <div className="card">
          <div className="card-header">
            <h3>Predictions</h3>
            <span className="card-sub">
              {predStats.total || 0} total — {predStats.correct || 0} correct, {predStats.wrong || 0} wrong, {predStats.open || 0} open
            </span>
          </div>
          <div className="card-body card-scroll">
            {predictions.map((p, i) => {
              const status = p.was_correct === true ? 'correct' : p.was_correct === false ? 'wrong' : 'open'
              return (
                <div className="prediction-item" key={i}>
                  <div className="prediction-top">
                    <span className={`badge ${status === 'open' ? 'open' : status === 'correct' ? 'long' : 'short'}`}>{status}</span>
                    <span className="prediction-text">{p.prediction}</span>
                  </div>
                  {p.post_mortem && <p className="prediction-pm">{p.post_mortem}</p>}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
