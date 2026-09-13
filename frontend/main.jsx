import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter, Routes, Route } from 'react-router-dom'
import Chat from './pages/Chat'
import Dashboard from './pages/Dashboard'
import './styles.css'

function App() {
  return (
    <HashRouter>
      <div className="app">
        <header className="header">
          <h1>🤖 LLM Performance Router</h1>
          <nav>
            <a href="#/">Chat</a>
            <a href="#/dashboard">Dashboard</a>
          </nav>
        </header>
        <main className="main">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
