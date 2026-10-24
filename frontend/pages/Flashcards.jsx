import React, { useEffect, useState } from 'react'
import axios from '../api'

const MAX_SOURCE_CHARS = 6000
const MIN_SOURCE_CHARS = 30
const CARD_COUNT = 10

const QUALITY_OPTIONS = [
  { label: 'Again', quality: 0 },
  { label: 'Hard', quality: 3 },
  { label: 'Good', quality: 4 },
  { label: 'Easy', quality: 5 },
]

export default function Flashcards({ activeRoom }) {
  const [dueCards, setDueCards] = useState([])
  const [loading, setLoading] = useState(true)
  const [flipped, setFlipped] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [reviewing, setReviewing] = useState(false)
  const [notice, setNotice] = useState(null)
  const [error, setError] = useState(null)

  const fetchDue = () => {
    setLoading(true)
    axios.get('/api/flashcards/me', { params: { subject: activeRoom } })
      .then((res) => setDueCards(res.data))
      .catch(() => setDueCards([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchDue()
    setFlipped(false)
    setNotice(null)
    setError(null)
  }, [activeRoom])

  const generate = async () => {
    setGenerating(true)
    setNotice(null)
    setError(null)
    try {
      const notesRes = await axios.get('/api/notes/me')
      const sourceText = notesRes.data
        .filter((n) => n.subject === activeRoom)
        .map((n) => n.content)
        .join('\n\n')
        .slice(0, MAX_SOURCE_CHARS)
        .trim()

      if (sourceText.length < MIN_SOURCE_CHARS) {
        setNotice(`No notes yet in ${activeRoom} — add some first so there's something to make cards from.`)
        return
      }

      await axios.post('/api/flashcards/generate', {
        subject: activeRoom,
        source_text: sourceText,
        count: CARD_COUNT,
      })
      fetchDue()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not generate flashcards.')
    } finally {
      setGenerating(false)
    }
  }

  const review = async (quality) => {
    const card = dueCards[0]
    setReviewing(true)
    try {
      await axios.post(`/api/flashcards/${card.id}/review`, { quality })
      setDueCards((prev) => prev.slice(1))
      setFlipped(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save that review.')
    } finally {
      setReviewing(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading flashcards…</div>
  }

  const card = dueCards[0]

  return (
    <div className="flashcards-page">
      <div className="panel-heading">
        <h2>{activeRoom} Flashcards</h2>
        <span className="live-pill">
          <span className="live-dot" /> {dueCards.length} due
        </span>
      </div>

      {error && <div className="error">{error}</div>}

      {!card ? (
        <div className="empty-state">
          <p>No flashcards due right now in {activeRoom}.</p>
          <button className="btn btn-pink" onClick={generate} disabled={generating}>
            {generating ? 'Generating…' : `Generate ${CARD_COUNT} from ${activeRoom} notes`}
          </button>
          {notice && <p className="contest-notice">{notice}</p>}
        </div>
      ) : (
        <div className="flashcard-review">
          <p className="flashcard-progress">{dueCards.length} card{dueCards.length === 1 ? '' : 's'} left this round</p>

          <div className="flashcard-flip-container" onClick={() => setFlipped((f) => !f)}>
            <div className={`flashcard-inner ${flipped ? 'flipped' : ''}`}>
              <div className="flashcard-face flashcard-face-front">
                <span className="flashcard-text">{card.front}</span>
                <span className="flashcard-hint">Tap to reveal</span>
              </div>
              <div className="flashcard-face flashcard-face-back">
                <span className="flashcard-text">{card.back}</span>
              </div>
            </div>
          </div>

          {!flipped ? (
            <button className="btn btn-pink btn-block" onClick={() => setFlipped(true)}>
              Show answer
            </button>
          ) : (
            <div className="flashcard-quality-row">
              {QUALITY_OPTIONS.map((opt) => (
                <button
                  key={opt.label}
                  className="btn btn-ghost flashcard-quality-btn"
                  onClick={() => review(opt.quality)}
                  disabled={reviewing}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
