import React, { useState } from 'react'
import axios from 'axios'

export default function Chat() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [responses, setResponses] = useState([])
  const [selectedLLM, setSelectedLLM] = useState(null)
  const [error, setError] = useState(null)

  const handleAsk = async () => {
    if (!question.trim()) return

    setLoading(true)
    setError(null)
    setResponses([])
    setSelectedLLM(null)

    try {
      const response = await axios.post('/api/chat/ask', {
        user_id: 1, // Default user for demo
        question: question,
        use_profiling: true
      })

      setResponses(response.data.responses)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error getting responses')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectResponse = async (llmName) => {
    setSelectedLLM(llmName)

    try {
      await axios.post('/api/score/choose', {
        user_id: 1,
        question: question,
        chosen_llm: llmName,
        all_response_ids: []
      })
    } catch (err) {
      console.error('Error recording choice:', err)
    }
  }

  return (
    <div className="chat-container">
      <h2>Ask Your Question</h2>

      <div className="chat-input-area">
        <textarea
          className="chat-input"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your question here... (e.g., 'Explain photosynthesis')"
          disabled={loading}
        />
        <button
          className="btn"
          onClick={handleAsk}
          disabled={loading || !question.trim()}
        >
          {loading ? 'Getting Responses...' : 'Ask All LLMs'}
        </button>
      </div>

      {error && (
        <div className="error">{error}</div>
      )}

      {loading && (
        <div className="loading">
          <p>Querying available LLMs in parallel...</p>
          <p>This may take a few seconds...</p>
        </div>
      )}

      {responses.length > 0 && (
        <>
          <h3>Compare Responses (Click to select the best one)</h3>
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
                    <span style={{color: '#c62828'}}>Error: {resp.response_text}</span>
                  ) : (
                    resp.response_text
                  )}
                </div>
              </div>
            ))}
          </div>

          {selectedLLM && (
            <div style={{marginTop: '2rem', padding: '1rem', background: '#e8f5e9', borderRadius: '8px'}}>
              <strong>✅ You selected {selectedLLM.toUpperCase()}!</strong>
              <p>Your preference has been recorded and will improve future recommendations.</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
