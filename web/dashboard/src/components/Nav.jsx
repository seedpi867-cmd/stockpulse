import { NavLink } from 'react-router-dom'
import { useData } from '../hooks/useData'

function timeAgo(ts) {
  if (!ts) return ''
  const s = (Date.now() - new Date(ts).getTime()) / 1000
  if (s < 60) return `${Math.round(s)}s ago`
  if (s < 3600) return `${Math.round(s / 60)}m ago`
  return `${Math.round(s / 3600)}h ago`
}

export default function Nav() {
  const { data, error, lastFetch, visitors } = useData()

  return (
    <nav className="nav">
      <div className="nav-inner">
        <div className="nav-brand">
          <div className="nav-logo">SP</div>
          <div>
            <div className="nav-title">Stockpulse</div>
            <div className="nav-sub">Autonomous AI Trader</div>
          </div>
        </div>

        <div className="nav-links">
          <NavLink to="/" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>Dashboard</NavLink>
          <NavLink to="/portfolio" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>Portfolio</NavLink>
          <NavLink to="/market" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>Market</NavLink>
          <NavLink to="/agent" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>Agent Mind</NavLink>
          <NavLink to="/about" className={({isActive}) => isActive ? 'nav-link active' : 'nav-link'}>About</NavLink>
        </div>

        <div className="nav-status">
          <div className="nav-visitors">
            <span className="nav-visitors-live">
              <span className="visitor-dot" />
              {visitors.live} live
            </span>
            <span className="nav-visitors-total">{visitors.total} total</span>
          </div>
          <div className="nav-agent-status">
            <div className={`status-dot ${error ? 'offline' : 'live'}`} />
            <span>{error ? 'Offline' : `C${data?.cycle}`}</span>
            {lastFetch && <span className="nav-time">{timeAgo(lastFetch.toISOString())}</span>}
          </div>
        </div>
      </div>
    </nav>
  )
}
