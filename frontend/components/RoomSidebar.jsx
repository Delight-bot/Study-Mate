import React, { useEffect, useRef, useState } from 'react'
import axios from '../api'

const TEXT_EXTENSIONS = ['.txt', '.md', '.markdown']

function isTextFile(file) {
  const name = file.name.toLowerCase()
  return file.type.startsWith('text/') || TEXT_EXTENSIONS.some((ext) => name.endsWith(ext))
}

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function RoomSidebar({ room }) {
  const [notes, setNotes] = useState([])
  const [history, setHistory] = useState([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [saving, setSaving] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    let cancelled = false

    axios.get('/api/notes/me')
      .then((res) => {
        if (!cancelled) setNotes(res.data.filter((n) => n.subject === room))
      })
      .catch(() => { if (!cancelled) setNotes([]) })

    axios.get('/api/chat/history', { params: { subject: room, limit: 6 } })
      .then((res) => { if (!cancelled) setHistory(res.data) })
      .catch(() => { if (!cancelled) setHistory([]) })

    return () => { cancelled = true }
  }, [room])

  const readFile = (file) => {
    setUploadError(null)
    if (!isTextFile(file)) {
      setUploadError('Only .txt and .md files can be read right now — paste other content instead.')
      return
    }
    const reader = new FileReader()
    reader.onload = () => {
      setContent(String(reader.result || ''))
      if (!title) setTitle(file.name.replace(/\.(txt|md|markdown)$/i, ''))
    }
    reader.onerror = () => setUploadError('Could not read that file.')
    reader.readAsText(file)
  }

  const handleFilePick = (e) => {
    const file = e.target.files?.[0]
    if (file) readFile(file)
    e.target.value = ''
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) readFile(file)
  }

  const handleSave = async () => {
    if (!content.trim()) return
    setSaving(true)
    setUploadError(null)
    try {
      const res = await axios.post('/api/notes', {
        subject: room,
        title: title.trim() || 'Untitled note',
        content: content.trim(),
      })
      setNotes((prev) => [
        { id: res.data.id, subject: room, title: res.data.title, content, created_at: new Date().toISOString() },
        ...prev,
      ])
      setTitle('')
      setContent('')
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Could not save that note.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="room-sidebar">
      <div className="room-sidebar-card">
        <h4>{room} notes</h4>

        <div
          className={`dropzone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <span>Drop a .txt/.md file here, or click to choose</span>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.markdown,text/plain,text/markdown"
            hidden
            onChange={handleFilePick}
          />
        </div>

        <input
          className="note-title-input"
          placeholder="Note title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          className="note-content-input"
          placeholder={`Or paste ${room} notes here…`}
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        {uploadError && <div className="error small-error">{uploadError}</div>}
        <button className="btn btn-pink btn-block" onClick={handleSave} disabled={saving || !content.trim()}>
          {saving ? 'Saving…' : 'Save to room'}
        </button>

        {notes.length > 0 && (
          <ul className="note-list">
            {notes.map((n) => (
              <li key={n.id} className="note-item">
                <span className="note-item-title">{n.title}</span>
                <span className="note-item-time">{timeAgo(n.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {history.length > 0 && (
        <div className="room-sidebar-card">
          <h4>Recent in {room}</h4>
          <ul className="history-list">
            {history.map((h, idx) => (
              <li key={idx} className="history-item">{h.question}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
