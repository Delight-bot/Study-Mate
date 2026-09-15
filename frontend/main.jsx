import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter, Routes, Route, NavLink } from 'react-router-dom'
import Chat from './pages/Chat'
import Dashboard from './pages/Dashboard'
import StudyTimer from './components/StudyTimer'
import DeskAccessories from './components/DeskAccessories'
import CatMark from './components/CatMark'
import RoomList from './components/RoomList'
import StudyContest from './components/StudyContest'
import { ROOM_STORAGE_KEY } from './components/rooms'
import './styles.css'

function getInitialRoom() {
  try {
    return localStorage.getItem(ROOM_STORAGE_KEY) || 'General'
  } catch {
    return 'General'
  }
}

function App() {
  const [timerRunning, setTimerRunning] = useState(false)
  const [activeRoom, setActiveRoom] = useState(getInitialRoom)
  const [focusSeconds, setFocusSeconds] = useState(0)

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
        </header>

        <div className="app-body">
          <aside className="sidebar">
            <StudyTimer
              onRunningChange={setTimerRunning}
              onFocusSecond={() => setFocusSeconds((s) => s + 1)}
            />
            <RoomList activeRoom={activeRoom} onChange={setActiveRoom} />
            <StudyContest focusSeconds={focusSeconds} room={activeRoom} />
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
