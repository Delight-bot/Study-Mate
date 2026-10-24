import React, { useEffect, useRef, useState } from 'react'
import axios from '../api'
import RoomSidebar from '../components/RoomSidebar'
import MarkdownAnswer from '../components/MarkdownAnswer'

const LLM_ORDER = ['gpt', 'claude', 'gemini', 'deepseek', 'llama']
const MAX_CONTEXT_CHARS = 6000

export default function Chat({ activeRoom }) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [responses, setResponses] = useState([])
  const [selectedLLM, setSelectedLLM] = useState(null)
  const [error, setError] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [askedAt, setAskedAt] = useState(null)
  const [historyVersion, setHistoryVersion] = useState(0)
  const [roomNotes, setRoomNotes] = useState([])
  const [walkthrough, setWalkthrough] = useState(null)
  const [walkthroughLoading, setWalkthroughLoading] = useState(false)
  const [walkthroughError, setWalkthroughError] = useState(null)
  const elapsedTimer = useRef(null)

  useEffect(() => {
    if (loading) {
      setElapsed(0)
      elapsedTimer.current = setInterval(() => setElapsed((e) => e + 0.1), 100)
    } else {
      clearInterval(elapsedTimer.current)
    }
    return () => clearInterval(elapsedTimer.current)
  }, [loading])

  useEffect(() => {
    let cancelled = false
    axios.get('/api/notes/me')
      .then((res) => {
        if (!cancelled) setRoomNotes(res.data.filter((n) => n.subject === activeRoom))
      })
      .catch(() => { if (!cancelled) setRoomNotes([]) })
    return () => { cancelled = true }
  }, [activeRoom])

  const handleAsk = async () => {
    if (!question.trim()) return

    setLoading(true)
    setError(null)
    setResponses([])
    setSelectedLLM(null)
    setWalkthrough(null)
    setWalkthroughError(null)
    setAskedAt(new Date())

    const context = roomNotes.length > 0
      ? roomNotes.map((n) => n.content).join('\n\n').slice(0, MAX_CONTEXT_CHARS)
      : undefined

    try {
      const response = await axios.post('/api/chat/ask', {
        question: question,
        subject: activeRoom,
        context,
        use_profiling: true
      })

      setResponses(response.data.responses)
      setHistoryVersion((v) => v + 1)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error getting responses')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAsk()
    }
  }

  const handleSelectResponse = async (llmName) => {
    setSelectedLLM(llmName)
    setWalkthrough(null)
    setWalkthroughError(null)

    try {
      await axios.post('/api/score/choose', {
        question: question,
        chosen_llm: llmName,
        all_response_ids: []
      })
    } catch (err) {
      console.error('Error recording choice:', err)
    }

    const chosen = responses.find((r) => r.llm_name === llmName)
    if (!chosen || chosen.error) return

    setWalkthroughLoading(true)
    try {
      const res = await axios.post('/api/chat/walkthrough', {
        llm_name: llmName,
        question: question,
        previous_answer: chosen.response_text,
        subject: activeRoom,
      })
      setWalkthrough(res.data)
    } catch (err) {
      setWalkthroughError(err.response?.data?.detail || 'Could not generate a walkthrough.')
    } finally {
      setWalkthroughLoading(false)
    }
  }

  return (
    <div className="chat-layout">
      <div className="chat-container">
          <div className="panel-heading">
            <h2>Ask Your Question</h2>
            <span className="live-pill">
              <span className="live-dot" /> Live · comparing {LLM_ORDER.length} models
            </span>
          </div>

          <div className="chat-input-area">
            <textarea
              className="chat-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`Type your ${activeRoom} question here... (e.g., 'Explain photosynthesis')`}
              disabled={loading}
            />
            <div className="chat-input-footer">
              <span className="char-count">
                {question.length} characters · Enter to send, Shift+Enter for a new line
                {roomNotes.length > 0 && ` · Using ${roomNotes.length} note${roomNotes.length === 1 ? '' : 's'} from ${activeRoom} as context`}
              </span>
              <button
                className="btn btn-pink"
                onClick={handleAsk}
                disabled={loading || !question.trim()}
              >
                {loading ? `Thinking… ${elapsed.toFixed(1)}s` : 'Ask All LLMs'}
              </button>
            </div>
          </div>

          {error && (
            <div className="error">{error}</div>
          )}

          {loading && (
            <div className="skeleton-grid">
              {LLM_ORDER.map((llm) => (
                <div key={llm} className="response-card skeleton">
                  <div className="response-header">
                    <span className="llm-name">{llm}</span>
                    <span className="thinking-dots"><i /><i /><i /></span>
                  </div>
                  <div className="skeleton-line" />
                  <div className="skeleton-line" />
                  <div className="skeleton-line short" />
                </div>
              ))}
            </div>
          )}

          {!loading && responses.length > 0 && (
            <>
              <div className="panel-heading">
                <h3>Compare Responses</h3>
                {askedAt && (
                  <span className="timestamp-pill">
                    Asked at {askedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>
              <p className="hint-text">Click the response you liked best — it sharpens future recommendations.</p>
              <div className="responses-grid">
                {responses.map((resp, idx) => (
                  <div
                    key={idx}
                    className={`response-card ${selectedLLM === resp.llm_name ? 'selected' : ''}`}
                    onClick={() => handleSelectResponse(resp.llm_name)}
                  >
                    <div className="response-header">
                      <span className="llm-name">{resp.llm_name}</span>
                      <span className="response-time">
                        {resp.response_time ? `${resp.response_time.toFixed(2)}s` : 'N/A'}
                      </span>
                    </div>
                    <div className="response-text">
                      {resp.error ? (
                        <span className="response-error">Error: {resp.response_text}</span>
                      ) : (
                        <MarkdownAnswer>{resp.response_text}</MarkdownAnswer>
                      )}
                    </div>
                    {selectedLLM === resp.llm_name && <span className="selected-tag">✓ selected</span>}
                  </div>
                ))}
              </div>

              {selectedLLM && (
                <div className="selection-banner">
                  <strong>You picked {selectedLLM.toUpperCase()}</strong>
                  <p>Saved — StudeyMate will lean on this the next time you ask something similar.</p>
                </div>
              )}

              {selectedLLM && (walkthroughLoading || walkthrough || walkthroughError) && (
                <div className="walkthrough-panel">
                  <h3>Step-by-step from {selectedLLM.toUpperCase()}</h3>
                  {walkthroughLoading && (
                    <p className="hint-text">Breaking it down into steps…</p>
                  )}
                  {walkthroughError && (
                    <div className="error small-error">{walkthroughError}</div>
                  )}
                  {walkthrough && !walkthroughLoading && (
                    <MarkdownAnswer>{walkthrough.steps_text}</MarkdownAnswer>
                  )}
                </div>
              )}
            </>
          )}
      </div>

      <RoomSidebar key={`${activeRoom}-${historyVersion}`} room={activeRoom} />
    </div>
  )
}
