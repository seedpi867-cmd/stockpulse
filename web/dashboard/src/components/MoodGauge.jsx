const MOODS = [
  { key: 'confidence', label: 'Confidence', desc: 'Certainty in market read' },
  { key: 'conviction', label: 'Conviction', desc: 'Willingness to act' },
  { key: 'frustration', label: 'Frustration', desc: 'Rises after losses' },
  { key: 'satisfaction', label: 'Satisfaction', desc: 'Rises after wins' },
  { key: 'curiosity', label: 'Curiosity', desc: 'Exploring new patterns' },
  { key: 'caution', label: 'Caution', desc: 'Risk aversion level' },
]

function barColor(key, val) {
  if (key === 'frustration') return val > 0.5 ? '#c0392b' : '#b8860b'
  if (key === 'caution') return val > 0.7 ? '#b8860b' : '#2d6a4f'
  return '#2d6a4f'
}

export default function MoodGauge({ mood }) {
  if (!mood) return null
  return (
    <div className="mood-gauges">
      {MOODS.map(({ key, label, desc }) => {
        const val = mood[key] || 0
        return (
          <div className="mood-row" key={key} title={desc}>
            <div className="mood-row-label">
              <span>{label}</span>
              <span className="mono-sm">{Math.round(val * 100)}%</span>
            </div>
            <div className="mood-bar">
              <div className="mood-fill" style={{ width: `${val * 100}%`, background: barColor(key, val) }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}
