import React, { useState } from 'react'
import axios from '../api'
import { setSession } from '../auth'
import CatMark from '../components/CatMark'

const DEMO_CREDENTIALS = { username: 'demo_user', password: 'demo1234' }

export default function Login({ onAuthed }) {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const logIn = async (loginUsername, loginPassword) => {
    setBusy(true)
    setError(null)
    try {
      const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register'
      const payload = mode === 'login'
        ? { username: loginUsername, password: loginPassword }
        : { username: loginUsername, email: email.trim() || null, password: loginPassword }

      const res = await axios.post(endpoint, payload)
      setSession({ token: res.data.token, userId: res.data.user_id, username: res.data.username })
      onAuthed()
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong — try again.')
    } finally {
      setBusy(false)
    }
  }

  const submit = (e) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return
    logIn(username.trim(), password)
  }

  const continueAsDemo = () => {
    setMode('login')
    logIn(DEMO_CREDENTIALS.username, DEMO_CREDENTIALS.password)
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand auth-brand">
          <CatMark />
          <h1>StudeyMate</h1>
        </div>

        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError(null) }}
            type="button"
          >
            Log in
          </button>
          <button
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError(null) }}
            type="button"
          >
            Sign up
          </button>
        </div>

        <form onSubmit={submit} className="auth-form">
          <input
            className="contest-input"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
          {mode === 'register' && (
            <input
              className="contest-input"
              placeholder="Email (optional)"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          )}
          <input
            className="contest-input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          />
          {error && <div className="error small-error">{error}</div>}
          <button className="btn btn-pink btn-block" type="submit" disabled={busy || !username.trim() || !password.trim()}>
            {busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}
          </button>
        </form>

        <button className="btn btn-ghost btn-block auth-demo-btn" onClick={continueAsDemo} disabled={busy}>
          Continue as demo
        </button>
      </div>
    </div>
  )
}
