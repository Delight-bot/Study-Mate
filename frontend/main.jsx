import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter, Routes, Route, NavLink } from 'react-router-dom'
import Chat from './pages/Chat'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import StudyTimer from './components/StudyTimer'
import DeskAccessories from './components/DeskAccessories'
import CatMark from './components/CatMark'
import RoomList from './components/RoomList'
import StudyContest from './components/StudyContest'
import { ROOM_STORAGE_KEY } from './components/rooms'
import { getSession, clearSession } from './auth'
import './styles.css'

function getInitialRoom() {
  try {
    return localStorage.getItem(ROOM_STORAGE_KEY) || 'General'
  } catch {
    return 'General'
  }
}

function App() {
  const [session, setSessionState] = useState(getSession)
  const [timerRunning, setTimerRunning] = useState(false)
  const [activeRoom, setActiveRoom] = useState(getInitialRoom)
  const [focusSeconds, setFocusSeconds] = useState(0)

  if (!session) {
    return <Login onAuthed={() => setSessionState(getSession())} />
  }

  const logOut = () => {
    clearSession()
    setSessionState(null)
  }

  return (
    <HashRouter>
      <div className="app">
        <header className="header">
          <div className="brand">
            <CatMark />
            <h1>StudeyMate</h1>
          </div>
          <nav>
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
              Chat
            </NavLink>
            <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>
              Dashboard
            </NavLink>
          </nav>
          <div className="account-pill">
            <span>{session.username}</span>
            <button className="account-logout" onClick={logOut}>Log out</button>
          </div>
        </header>

        <div className="app-body">
          <aside className="sidebar">
            <StudyTimer
              onRunningChange={setTimerRunning}
              onFocusSecond={() => setFocusSeconds((s) => s + 1)}
            />
            <RoomList activeRoom={activeRoom} onChange={setActiveRoom} />
            <StudyContest focusSeconds={focusSeconds} room={activeRoom} displayName={session.username} />
          </aside>

          <main className="main">
            <Routes>
              <Route path="/" element={<Chat activeRoom={activeRoom} />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </main>
        </div>

        <DeskAccessories active={timerRunning} />
      </div>
    </HashRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
