import React, { useEffect, useRef, useState } from 'react'

const DURATIONS = {
  focus: 25 * 60,
  short: 5 * 60,
  long: 15 * 60,
}

const MODE_LABEL = { focus: 'Focus', short: 'Short Break', long: 'Long Break' }
const MODE_TAB_LABEL = { focus: 'Focus', short: 'Break', long: 'Long' }

function formatTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0')
  const s = Math.floor(totalSeconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

export default function StudyTimer({ onRunningChange, onFocusSecond }) {
  const [mode, setMode] = useState('focus')
  const [secondsLeft, setSecondsLeft] = useState(DURATIONS.focus)
  const [isRunning, setIsRunning] = useState(false)
  const [sessionsDone, setSessionsDone] = useState(0)
  const [now, setNow] = useState(new Date())
  const modeRef = useRef(mode)
  const sessionsRef = useRef(sessionsDone)
  modeRef.current = mode
  sessionsRef.current = sessionsDone

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  useEffect(() => {
    if (!isRunning) return
    const id = setInterval(() => {
      if (modeRef.current === 'focus') onFocusSecond?.()

      setSecondsLeft((prev) => {
        if (prev > 1) return prev - 1

        const finishedFocus = modeRef.current === 'focus'
        const nextSessions = finishedFocus ? sessionsRef.current + 1 : sessionsRef.current
        const nextMode = finishedFocus
          ? (nextSessions % 4 === 0 ? 'long' : 'short')
          : 'focus'
        setSessionsDone(nextSessions)
        setMode(nextMode)
        return DURATIONS[nextMode]
      })
    }, 1000)
    return () => clearInterval(id)
  }, [isRunning])

  useEffect(() => {
    onRunningChange?.(isRunning)
  }, [isRunning, onRunningChange])

  const total = DURATIONS[mode]
  const progress = 1 - secondsLeft / total
  const circumference = 2 * Math.PI * 45

  const handleReset = () => {
    setIsRunning(false)
    setSecondsLeft(DURATIONS[mode])
  }

  const switchMode = (m) => {
    setIsRunning(false)
    setMode(m)
    setSecondsLeft(DURATIONS[m])
  }

  const dotIndex = sessionsDone % 4

  return (
    <div className="study-timer">
      <div className="wall-clock">
        <span className="wall-clock-time">
          {now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>
        <span className="wall-clock-date">
          {now.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' })}
        </span>
      </div>

      <div className="timer-modes">
        {['focus', 'short', 'long'].map((m) => (
          <button
            key={m}
            className={`timer-mode-btn ${mode === m ? 'active' : ''}`}
            onClick={() => switchMode(m)}
          >
            {MODE_TAB_LABEL[m]}
          </button>
        ))}
      </div>

      <div className="timer-ring-wrap">
        <svg className="timer-ring" viewBox="0 0 100 100">
          <circle className="timer-ring-track" cx="50" cy="50" r="45" />
          <circle
            className="timer-ring-progress"
            cx="50" cy="50" r="45"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - progress)}
          />
        </svg>
        <div className="timer-readout">
          <span className="timer-time">{formatTime(secondsLeft)}</span>
          <span className="timer-label">{MODE_LABEL[mode]}</span>
        </div>
      </div>

      <div className="timer-controls">
        <button className="btn btn-pink" onClick={() => setIsRunning((r) => !r)}>
          {isRunning ? '⏸ Pause' : '▶ Start'}
        </button>
        <button className="btn btn-ghost" onClick={handleReset}>↺ Reset</button>
      </div>

      <div className="session-dots" title={`${sessionsDone} focus session${sessionsDone === 1 ? '' : 's'} completed today`}>
        {Array.from({ length: 4 }).map((_, i) => (
          <span key={i} className={`session-dot ${i < dotIndex ? 'filled' : ''}`} />
        ))}
        <span className="session-count">{sessionsDone} sessions</span>
      </div>
    </div>
  )
}
