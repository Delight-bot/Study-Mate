import React, { useEffect, useState } from 'react'
import axios from '../api'
import { DEFAULT_ROOMS, ROOM_STORAGE_KEY, VISIBLE_ROOM_COUNT } from './rooms'

export default function RoomList({ activeRoom, onChange }) {
  const [rooms, setRooms] = useState(DEFAULT_ROOMS)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    let cancelled = false
    axios.get('/api/chat/subjects')
      .then((res) => {
        if (!cancelled && Array.isArray(res.data) && res.data.length > 0) {
          setRooms(res.data)
        }
      })
      .catch(() => {
        // Backend unreachable — keep the built-in default room list.
      })
    return () => { cancelled = true }
  }, [])

  const selectRoom = (name) => {
    onChange(name)
    try {
      localStorage.setItem(ROOM_STORAGE_KEY, name)
    } catch {
      // localStorage unavailable (private mode, etc.) — selection just won't persist.
    }
  }

  const visibleRooms = expanded ? rooms : rooms.slice(0, VISIBLE_ROOM_COUNT)
  const hiddenCount = rooms.length - VISIBLE_ROOM_COUNT

  return (
    <div className="room-list-card">
      <span className="sidebar-heading">Rooms</span>
      <ul className="room-list">
        {visibleRooms.map((room) => (
          <li key={room.name}>
            <button
              className={`room-list-item ${activeRoom === room.name ? 'active' : ''}`}
              onClick={() => selectRoom(room.name)}
              title={room.description}
            >
              {room.name}
            </button>
          </li>
        ))}
      </ul>
      {hiddenCount > 0 && (
        <button className="room-list-toggle" onClick={() => setExpanded((e) => !e)}>
          {expanded ? 'Show fewer' : `Show ${hiddenCount} more`}
        </button>
      )}
    </div>
  )
}
