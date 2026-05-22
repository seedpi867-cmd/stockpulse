import { useMemo } from 'react'
import { useData } from '../hooks/useData'

function parsePrices(md) {
  if (!md) return []
  const items = []
  for (const line of md.split('\n')) {
    const commodity = line.match(/^- (.+?):\s*\$?([\d,.]+)\s*\(([^)]+)\)/)
    if (commodity && !line.startsWith('- UP') && !line.startsWith('- DOWN')) {
      items.push({ ticker: commodity[1], price: commodity[2], change: commodity[3], neg: commodity[3].includes('-') })
      continue
    }
    const mover = line.match(/^- (UP|DOWN):\s*(.+?)\s+([+-]?\d+\.?\d*%)/)
    if (mover) {
      items.push({ ticker: mover[2], price: '', change: mover[3], neg: mover[1] === 'DOWN' })
    }
  }
  return items
}

export default function MarketTicker() {
  const { data } = useData()
  const items = useMemo(() => parsePrices(data?.market?.prices), [data?.market?.prices])

  if (!items.length) return null

  // Triple items for seamless infinite scroll
  const scrollItems = [...items, ...items, ...items]

  return (
    <div className="ticker">
      <div className="ticker-track">
        {scrollItems.map((item, i) => (
          <span className="ticker-item" key={i}>
            <span className="ticker-name">{item.ticker}</span>
            {item.price && <span className="ticker-price">{item.price}</span>}
            <span className={`ticker-change ${item.neg ? 'neg' : 'pos'}`}>{item.change}</span>
          </span>
        ))}
      </div>
    </div>
  )
}
