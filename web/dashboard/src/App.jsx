import { useState, useEffect, useRef, useCallback } from 'react'
import { Routes, Route } from 'react-router-dom'
import { DataProvider, useData } from './hooks/useData'
import Nav from './components/Nav'
import MarketTicker from './components/MarketTicker'
import Footer from './components/Footer'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import Market from './pages/Market'
import AgentMind from './pages/AgentMind'
import About from './pages/About'

function IntroScreen({ onFinished }) {
  const [fadeOut, setFadeOut] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      setFadeOut(true)
      setTimeout(onFinished, 800)
    }, 3500)
    return () => clearTimeout(timer)
  }, [onFinished])

  return (
    <div className={`intro-screen ${fadeOut ? 'fade-out' : ''}`}>
      <div className="intro-content">
        <video
          src="/intro.webm"
          autoPlay
          muted
          playsInline
          className="intro-video"
        />
        <div className="intro-text">
          <div className="intro-title">Stockpulse</div>
          <div className="intro-sub">Autonomous AI Trading Agent</div>
        </div>
        <div className="intro-loader">
          <div className="intro-loader-bar" />
        </div>
        <div className="intro-status">Connecting to agent on Raspberry Pi 5...</div>
      </div>
    </div>
  )
}

function AppContent() {
  const { data, loading, error, refetch } = useData()
  const [introDone, setIntroDone] = useState(false)

  const handleIntroDone = useCallback(() => setIntroDone(true), [])

  const dataReady = !loading && !!data

  // Show intro until both: intro animation done AND data loaded
  if (!introDone || !dataReady) {
    return (
      <>
        {!introDone && <IntroScreen onFinished={handleIntroDone} />}
        {introDone && !dataReady && (
          <div className="loading-screen">
            <div className="loading-spinner" />
            <p>Almost there...</p>
          </div>
        )}
      </>
    )
  }

  if (error && !data) {
    return (
      <div className="loading-screen">
        <div className="loading-logo">SP</div>
        <h2>Agent Offline</h2>
        <p>The autonomous trading agent on the Raspberry Pi 5 is currently unreachable.</p>
        <button className="btn" onClick={refetch}>Retry</button>
      </div>
    )
  }

  return (
    <>
      <Nav />
      <MarketTicker />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/market" element={<Market />} />
          <Route path="/agent" element={<AgentMind />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
      <Footer />
    </>
  )
}

export default function App() {
  return (
    <DataProvider>
      <AppContent />
    </DataProvider>
  )
}
