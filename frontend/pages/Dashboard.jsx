import React, { useState, useEffect } from 'react'
import axios from 'axios'

export default function Dashboard() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await axios.get('/api/profile/1') // Default user
      setProfile(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error loading profile')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading your performance data...</div>
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  if (!profile || !profile.profiles || profile.profiles.length === 0) {
    return (
      <div className="dashboard-container">
        <h2>Your Dashboard</h2>
        <div style={{padding: '2rem', background: 'white', borderRadius: '10px', textAlign: 'center'}}>
          <p>No profile data yet. Start asking questions to build your performance profile!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <h2>Your Performance Dashboard</h2>

      <div style={{background: 'white', padding: '2rem', borderRadius: '10px', marginBottom: '2rem'}}>
        <h3>Overall Statistics</h3>
        <p><strong>Best Overall LLM:</strong> {profile.overall_best_llm.toUpperCase()}</p>
        <p><strong>Total Interactions:</strong> {profile.total_interactions}</p>
        <p><strong>Subjects Tracked:</strong> {profile.profiles.length}</p>
      </div>

      <h3>Performance by Subject</h3>
      <div className="profile-cards">
        {profile.profiles.map((subjectProfile, idx) => (
          <div key={idx} className="profile-card">
            <h3>{subjectProfile.subject_name}</h3>

            <div style={{marginBottom: '1rem'}}>
              <p><strong>Best LLM:</strong> {subjectProfile.best_llm.toUpperCase()}</p>
              <p><strong>Confidence:</strong> {(subjectProfile.confidence * 100).toFixed(0)}%</p>
              <p><strong>Total Questions:</strong> {subjectProfile.total_questions}</p>
            </div>

            <div className="win-rates">
              <h4>Win Rates:</h4>

              {['gpt', 'claude', 'gemini', 'deepseek', 'llama'].map(llm => {
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
                        style={{width: `${rate}%`}}
                      />
                    </div>
                    <span style={{fontSize: '0.9rem'}}>{wins}</span>
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
