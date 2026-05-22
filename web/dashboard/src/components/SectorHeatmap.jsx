import { useMemo } from 'react'

function parseSectors(md) {
  if (!md) return []
  const sectors = []
  for (const line of md.split('\n')) {
    const m = line.match(/[▲▼]\s*(\w+)\s+(.+?):\s*\$?([\d,.]+)\s*\(([^)]+)\)/)
    if (m) {
      const pctMatch = m[4].match(/([+-]?\d+\.?\d*)%/)
      if (pctMatch) {
        sectors.push({ ticker: m[1], name: m[2], price: m[3], pct: parseFloat(pctMatch[1]) })
      }
    }
  }
  return sectors
}

function heatColor(pct) {
  if (pct > 1.5) return { bg: '#1b7a3d', fg: '#fff' }
  if (pct > 0.5) return { bg: '#52b788', fg: '#fff' }
  if (pct > 0) return { bg: '#d8f3dc', fg: '#1a1a1a' }
  if (pct > -0.5) return { bg: '#fde8e6', fg: '#1a1a1a' }
  if (pct > -1.5) return { bg: '#e74c3c', fg: '#fff' }
  return { bg: '#922b21', fg: '#fff' }
}

export default function SectorHeatmap({ sectorsMd }) {
  const sectors = useMemo(() => parseSectors(sectorsMd), [sectorsMd])
  if (!sectors.length) return null

  return (
    <div className="heatmap-grid">
      {sectors.map((s, i) => {
        const { bg, fg } = heatColor(s.pct)
        return (
          <div className="heatmap-cell" key={i} style={{ background: bg, color: fg }} title={`${s.name}: $${s.price}`}>
            <div className="heatmap-ticker">{s.ticker}</div>
            <div className="heatmap-pct">{s.pct >= 0 ? '+' : ''}{s.pct.toFixed(2)}%</div>
            <div className="heatmap-name">{s.name}</div>
          </div>
        )
      })}
    </div>
  )
}
