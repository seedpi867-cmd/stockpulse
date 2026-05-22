import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'

const DataContext = createContext(null)

function getVisitorId() {
  let id = localStorage.getItem('sp_vid')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('sp_vid', id)
  }
  return id
}

export function DataProvider({ children }) {
  const [data, setData] = useState(null)
  const [health, setHealth] = useState(null)
  const [visitors, setVisitors] = useState({ live: 0, total: 0 })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastFetch, setLastFetch] = useState(null)
  const vidRef = useRef(null)

  const fetchData = useCallback(async () => {
    try {
      const [allRes, healthRes] = await Promise.all([
        fetch('/api/all'),
        fetch('/api/health')
      ])
      if (!allRes.ok) throw new Error(`${allRes.status}`)
      setData(await allRes.json())
      if (healthRes.ok) setHealth(await healthRes.json())
      setError(null)
      setLastFetch(new Date())
    } catch (e) {
      setError(e.message === '502' ? 'Agent offline' : e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  const heartbeat = useCallback(async () => {
    try {
      if (!vidRef.current) vidRef.current = getVisitorId()
      const res = await fetch('/api/visitors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: vidRef.current })
      })
      if (res.ok) {
        setVisitors(await res.json())
      }
    } catch {}
  }, [])

  useEffect(() => {
    fetchData()
    heartbeat()
    const dataId = setInterval(fetchData, 30000)
    const visitorId = setInterval(heartbeat, 60000)
    return () => { clearInterval(dataId); clearInterval(visitorId) }
  }, [fetchData, heartbeat])

  return (
    <DataContext.Provider value={{ data, health, visitors, error, loading, lastFetch, refetch: fetchData }}>
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  return useContext(DataContext)
}
