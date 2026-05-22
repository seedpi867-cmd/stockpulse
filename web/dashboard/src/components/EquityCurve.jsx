import { useRef, useEffect, useState } from 'react'

export default function EquityCurve({ dailyPnl }) {
  if (!dailyPnl || dailyPnl.length < 2) return null

  const values = dailyPnl.map(d => d.portfolio_value || 100000)
  const min = Math.min(...values) * 0.998
  const max = Math.max(...values) * 1.002
  const range = max - min || 1

  const w = 600
  const h = 140
  const padX = 0
  const padY = 8

  const points = values.map((v, i) => {
    const x = padX + (i / (values.length - 1)) * (w - padX * 2)
    const y = padY + (1 - (v - min) / range) * (h - padY * 2)
    return { x, y, v }
  })

  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
  const areaPath = `${line} L${points[points.length - 1].x},${h} L${points[0].x},${h} Z`

  const latest = values[values.length - 1]
  const isUp = latest >= 100000
  const color = isUp ? '#1b7a3d' : '#c0392b'

  const pathRef = useRef(null)
  const [pathLength, setPathLength] = useState(0)

  useEffect(() => {
    if (pathRef.current) {
      setPathLength(pathRef.current.getTotalLength())
    }
  }, [line])

  return (
    <div className="equity-curve">
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="equity-svg">
        <defs>
          <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.15" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#eqGrad)" className="equity-area" />
        <path
          ref={pathRef}
          d={line}
          fill="none"
          stroke={color}
          strokeWidth="2"
          className="equity-line"
          style={pathLength ? {
            strokeDasharray: pathLength,
            strokeDashoffset: pathLength,
          } : undefined}
        />
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="2.5"
            fill={color}
            className="equity-dot"
            style={{ animationDelay: `${1.5 + (i / points.length) * 0.8}s` }}
          >
            <title>{dailyPnl[i]?.date}: ${p.v.toLocaleString()}</title>
          </circle>
        ))}
      </svg>
      <div className="equity-labels">
        <span>{dailyPnl[0]?.date}</span>
        <span>{dailyPnl[dailyPnl.length - 1]?.date}</span>
      </div>
    </div>
  )
}
