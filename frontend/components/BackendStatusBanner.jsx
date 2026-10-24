import React, { useEffect, useState } from 'react'
import axios from '../api'

// Edit this whenever you take the backend down on purpose — it only shows
// up when the backend is actually unreachable.
const MAINTENANCE_MESSAGE =
  "Hi! I turned the backend off myself to save money on hosting — it'll be back up Monday by 9am CST. Sorry about that!"

export default function BackendStatusBanner() {
  const [backendDown, setBackendDown] = useState(false)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    let cancelled = false
    axios.get('/health', { timeout: 8000 })
      .then(() => { if (!cancelled) setBackendDown(false) })
      .catch(() => { if (!cancelled) setBackendDown(true) })
      .finally(() => { if (!cancelled) setChecked(true) })
    return () => { cancelled = true }
  }, [])

  if (!checked || !backendDown) return null

  return (
    <div className="cloud-bubble-wrap">
      <div className="cloud-bubble">
        <p>{MAINTENANCE_MESSAGE}</p>
      </div>
    </div>
  )
}
