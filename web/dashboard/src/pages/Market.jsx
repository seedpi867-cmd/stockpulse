import { useMemo } from 'react'
import { useData } from '../hooks/useData'
import SectorHeatmap from '../components/SectorHeatmap'
import StatCard from '../components/StatCard'

function parseSentiment(md) {
  if (!md) return {}
  const out = {}
  const fgMatch = md.match(/Score:\s*(\d+)\/100\s*\((\w+)\)/)
  if (fgMatch) { out.fearGreed = parseInt(fgMatch[1]); out.fgLabel = fgMatch[2]; }
  const fgStatus = md.match(/\*\*(NEUTRAL|GREED|EXTREME GREED|FEAR|EXTREME FEAR)\*\*/i)
  if (fgStatus) out.fgStatus = fgStatus[1]

  const vixMatch = md.match(/VIX:\s*([\d.]+)\s*\(([^)]+)\)/)
  if (vixMatch) { out.vix = parseFloat(vixMatch[1]); out.vixChange = vixMatch[2]; }
  const vixStatus = md.match(/VIX.*?\n-.*?\n.*?\*\*(\w+)\*\*/i)
  if (vixStatus) out.vixStatus = vixStatus[1]

  const pcMatch = md.match(/Equity P\/C:\s*([\d.]+)/)
  if (pcMatch) out.putCall = parseFloat(pcMatch[1])
  const pcStatus = md.match(/Put\/Call.*?\n.*?\n.*?\*\*([^*]+)\*\*/i)
  if (pcStatus) out.pcStatus = pcStatus[1]

  const yields = {}
  const yieldMatches = md.matchAll(/(\d+[MY]) Treasury:\s*([\d.]+)%/g)
  for (const m of yieldMatches) yields[m[1]] = parseFloat(m[2])
  if (Object.keys(yields).length) out.yields = yields

  const spreadMatch = md.match(/10Y-3M Spread:\s*([\d.]+)%\s*\(([^)]+)\)/)
  if (spreadMatch) { out.spread10y3m = parseFloat(spreadMatch[1]); out.spreadStatus = spreadMatch[2]; }

  const dxyMatch = md.match(/DXY:\s*([\d.]+)/)
  if (dxyMatch) out.dxy = parseFloat(dxyMatch[1])
  const dxyStatus = md.match(/DXY.*?\n.*?\*\*([^*]+)\*\*/i)
  if (dxyStatus) out.dxyStatus = dxyStatus[1]

  return out
}

function parseNews(md) {
  if (!md) return []
  const articles = []
  const blocks = md.split('###').slice(1)
  for (const block of blocks) {
    const lines = block.trim().split('\n')
    const title = lines[0]?.trim()
    const sourceLine = lines[1]?.trim() || ''
    const sourceMatch = sourceLine.match(/\*(.+?)\*\s*—\s*(.+)/)
    const body = lines.slice(2).join(' ').trim()
    articles.push({
      title,
      source: sourceMatch?.[1] || '',
      date: sourceMatch?.[2] || '',
      body: body.slice(0, 200),
    })
  }
  return articles
}

function parseCalendar(md) {
  if (!md) return { earnings: [], events: [] }
  const earnings = []
  const events = []
  const lines = md.split('\n')
  let inEarnings = false, inEvents = false

  for (const line of lines) {
    if (line.includes('Earnings')) { inEarnings = true; inEvents = false; continue; }
    if (line.includes('Standing Events') || line.includes('Events to Track')) { inEvents = true; inEarnings = false; continue; }
    const item = line.match(/^-\s*\*?\*?(.+?)\*?\*?:\s*(.+)/)
    if (item) {
      if (inEarnings) earnings.push({ date: item[1], tickers: item[2] })
      if (inEvents) events.push(item[2] || item[1])
    } else if (line.startsWith('- ') && inEvents) {
      events.push(line.slice(2).replace(/\*\*/g, ''))
    }
  }
  return { earnings, events }
}

function FearGreedGauge({ value, label }) {
  const angle = (value / 100) * 180 - 90
  const color = value > 75 ? 'var(--green)' : value > 55 ? '#52b788' : value > 45 ? 'var(--amber)' : value > 25 ? '#e67e22' : 'var(--red)'

  return (
    <div className="fg-gauge">
      <svg viewBox="0 0 200 110" className="fg-svg">
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="var(--border)" strokeWidth="12" strokeLinecap="round" />
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
          strokeDasharray={`${(value / 100) * 251.3} 251.3`} />
        <text x="100" y="85" textAnchor="middle" fontSize="28" fontWeight="700" fontFamily="var(--mono)" fill="var(--text)">{value}</text>
        <text x="100" y="105" textAnchor="middle" fontSize="11" fill="var(--dim)">{label}</text>
      </svg>
    </div>
  )
}

export default function Market() {
  const { data } = useData()
  const market = data.market || {}
  const sent = useMemo(() => parseSentiment(market.sentiment), [market.sentiment])
  const news = useMemo(() => parseNews(market.news), [market.news])
  const cal = useMemo(() => parseCalendar(market.calendar), [market.calendar])

  return (
    <div className="page">
      <div className="page-header">
        <h1>Market Data</h1>
        <p>Live market data refreshed every 5 minutes — sentiment, sectors, news, and economic calendar.</p>
      </div>

      {/* Sentiment row */}
      <div className="card">
        <div className="card-header">
          <h3>Market Sentiment</h3>
          <span className="card-sub">Real-time indicators the agent uses to gauge market mood</span>
        </div>
        <div className="card-body">
          <div className="sentiment-grid">
            {sent.fearGreed != null && (
              <div className="sent-block">
                <FearGreedGauge value={sent.fearGreed} label={sent.fgStatus || sent.fgLabel || ''} />
                <div className="sent-title">Fear & Greed</div>
              </div>
            )}
            <div className="sent-stats">
              {sent.vix != null && (
                <div className="sent-stat">
                  <div className="sent-stat-label">VIX</div>
                  <div className="sent-stat-value">{sent.vix.toFixed(2)}</div>
                  <div className="sent-stat-sub">{sent.vixChange} — {sent.vixStatus || ''}</div>
                </div>
              )}
              {sent.putCall != null && (
                <div className="sent-stat">
                  <div className="sent-stat-label">Put/Call Ratio</div>
                  <div className="sent-stat-value">{sent.putCall.toFixed(2)}</div>
                  <div className="sent-stat-sub">{sent.pcStatus || ''}</div>
                </div>
              )}
              {sent.dxy != null && (
                <div className="sent-stat">
                  <div className="sent-stat-label">US Dollar (DXY)</div>
                  <div className="sent-stat-value">{sent.dxy.toFixed(2)}</div>
                  <div className="sent-stat-sub">{sent.dxyStatus || ''}</div>
                </div>
              )}
              {sent.spread10y3m != null && (
                <div className="sent-stat">
                  <div className="sent-stat-label">10Y-3M Spread</div>
                  <div className="sent-stat-value">{sent.spread10y3m.toFixed(3)}%</div>
                  <div className="sent-stat-sub">{sent.spreadStatus || ''}</div>
                </div>
              )}
            </div>
            {sent.yields && Object.keys(sent.yields).length > 0 && (
              <div className="yield-curve">
                <div className="sent-stat-label" style={{ marginBottom: 8 }}>Treasury Yields</div>
                <div className="yield-bars">
                  {Object.entries(sent.yields).map(([tenor, rate]) => (
                    <div className="yield-bar-item" key={tenor}>
                      <div className="yield-bar-fill" style={{ height: `${(rate / 6) * 100}%` }} />
                      <div className="yield-rate">{rate.toFixed(2)}%</div>
                      <div className="yield-tenor">{tenor}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sectors */}
      <div className="card">
        <div className="card-header">
          <h3>Sector Performance</h3>
          <span className="card-sub">S&P 500 sector ETFs — today's movement</span>
        </div>
        <div className="card-body">
          <SectorHeatmap sectorsMd={market.sectors} />
        </div>
      </div>

      {/* News + Calendar side by side */}
      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3>Financial News</h3>
            <span className="card-sub">{news.length} articles</span>
          </div>
          <div className="card-body card-scroll">
            {news.length === 0 && <div className="card-empty">No news available</div>}
            {news.map((article, i) => (
              <div className="news-item" key={i}>
                <div className="news-title">{article.title}</div>
                <div className="news-meta">
                  {article.source && <span className="news-source">{article.source}</span>}
                  {article.date && <span className="news-date">{article.date}</span>}
                </div>
                {article.body && <div className="news-body">{article.body}</div>}
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Economic Calendar</h3>
          </div>
          <div className="card-body">
            {cal.earnings.length > 0 && (
              <div className="cal-section">
                <div className="section-title">Upcoming Earnings</div>
                {cal.earnings.map((e, i) => (
                  <div className="cal-item" key={i}>
                    <span className="cal-date">{e.date}</span>
                    <span className="cal-tickers">{e.tickers}</span>
                  </div>
                ))}
              </div>
            )}
            {cal.events.length > 0 && (
              <div className="cal-section">
                <div className="section-title">Key Events to Watch</div>
                {cal.events.map((e, i) => (
                  <div className="cal-event" key={i}>{e}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
