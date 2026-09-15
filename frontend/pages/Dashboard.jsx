import React, { useState, useEffect } from 'react'
import axios from '../api'

const LLM_ORDER = ['gpt', 'claude', 'gemini', 'deepseek', 'llama']

export default function Dashboard() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [ago, setAgo] = useState(0)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    fetchProfile()
  }, [])

  useEffect(() => {
    const id = setInterval(() => setAgo((a) => a + 1), 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true))
    return () => cancelAnimationFrame(id)
  }, [])

  const fetchProfile = async () => {
    setAgo(0)
    try {
      const response = await axios.get('/api/profile/me')
      setProfile(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error loading profile')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading your performance data…</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  if (!profile || !profile.profiles || profile.profiles.length === 0) {
    return (
      <div className="dashboard-container">
        <h2>Your Dashboard</h2>
        <div className="empty-state">
          <span className="empty-emoji">🌱</span>
          <p>No profile data yet. Start asking questions to grow your performance profile!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <div className="panel-heading">
        <h2>Your Performance Dashboard</h2>
        <span className="timestamp-pill">
          <span className="live-dot" /> Updated {ago < 2 ? 'just now' : `${ago}s ago`}
          <button className="refresh-btn" onClick={fetchProfile} title="Refresh">↻</button>
        </span>
      </div>

      <div className="stats-card">
        <div className="stat">
          <span className="stat-label">Best Overall LLM</span>
          <span className="stat-value">{profile.overall_best_llm.toUpperCase()}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Total Interactions</span>
          <span className="stat-value">{profile.total_interactions}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Subjects Tracked</span>
          <span className="stat-value">{profile.profiles.length}</span>
        </div>
      </div>

      <h3>Performance by Subject</h3>
      <div className="profile-cards">
        {profile.profiles.map((subjectProfile, idx) => (
          <div key={idx} className="profile-card">
            <span className="washi-tape" />
            <h3>{subjectProfile.subject_name}</h3>

            <div className="profile-meta">
              <p><strong>Best LLM:</strong> {subjectProfile.best_llm.toUpperCase()}</p>
              <p><strong>Confidence:</strong> {(subjectProfile.confidence * 100).toFixed(0)}%</p>
              <p><strong>Total Questions:</strong> {subjectProfile.total_questions}</p>
            </div>

            <div className="win-rates">
              <h4>Win Rates</h4>

              {LLM_ORDER.map(llm => {
                const wins = subjectProfile[`wins_${llm}`]
                const rate = subjectProfile.total_questions > 0
                  ? (wins / subjectProfile.total_questions) * 100
                  : 0

                return (
                  <div key={llm} className="win-rate-bar">
                    <span className="win-rate-label">{llm}</span>
                    <div className="win-rate-visual">
                      <div
                        className="win-rate-fill"
                        style={{ width: mounted ? `${rate}%` : '0%' }}
                      />
                    </div>
                    <span className="win-rate-count">{wins}</span>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
