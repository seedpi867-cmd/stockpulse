import { useData } from '../hooks/useData'

export default function Footer() {
  const { data } = useData()
  const port = data?.portfolio || {}

  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-left">
          <strong>Stockpulse</strong> — An autonomous AI trading agent running on a Raspberry Pi 5.
          Paper trading only. Not financial advice.
        </div>
        <div className="footer-right">
          <span>Started {port.started_at || '—'}</span>
          <span>Starting capital: $100,000</span>
          <span>Cycles every 5 minutes</span>
        </div>
      </div>
    </footer>
  )
}
