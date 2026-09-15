import React, { useEffect, useRef, useState } from 'react'
import axios from '../api'

const STORAGE_KEY = 'studeymate.duel'
const POLL_MS = 8000
const SYNC_MS = 10000
const MAX_SOURCE_CHARS = 6000
const MIN_SOURCE_CHARS = 30
const NUM_QUESTIONS = 5

function formatDuration(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m`
  return `${totalSeconds}s`
}

function loadSaved() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveDuel(duel) {
  try {
    if (duel) localStorage.setItem(STORAGE_KEY, JSON.stringify(duel))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // localStorage unavailable — duel just won't survive a reload.
  }
}

export default function StudyContest({ focusSeconds, room, userId = 1 }) {
  const [duel, setDuel] = useState(loadSaved)
  const [name, setName] = useState('')
  const [joinCode, setJoinCode] = useState('')
  const [participants, setParticipants] = useState([])
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)
  const [busy, setBusy] = useState(false)
  const [quiz, setQuiz] = useState(null)
  const [quizStep, setQuizStep] = useState(null)
  const [answers, setAnswers] = useState([])
  const lastSyncedRef = useRef(0)

  useEffect(() => {
    if (!duel) return
    let cancelled = false

    const poll = () => {
      axios.get(`/api/contest/${duel.code}`)
        .then((res) => { if (!cancelled) setParticipants(res.data.participants) })
        .catch(() => {})
    }

    poll()
    const id = setInterval(poll, POLL_MS)
    return () => { cancelled = true; clearInterval(id) }
  }, [duel])

  useEffect(() => {
    if (!duel?.quizId || duel.myScore != null || quiz) return
    axios.get(`/api/quiz/${duel.quizId}`)
      .then((res) => setQuiz(res.data))
      .catch(() => {})
  }, [duel, quiz])

  useEffect(() => {
    if (!duel) return
    if (focusSeconds - lastSyncedRef.current < SYNC_MS / 1000) return
    lastSyncedRef.current = focusSeconds

    axios.post(`/api/contest/${duel.code}/progress`, {
      participant_id: duel.participantId,
      focus_seconds: focusSeconds,
    }).catch(() => {})
  }, [focusSeconds, duel])

  const buildQuizFromNotes = async () => {
    try {
      const res = await axios.get(`/api/notes/${userId}`)
      const sourceText = res.data
        .filter((n) => n.subject === room)
        .map((n) => n.content)
        .join('\n\n')
        .slice(0, MAX_SOURCE_CHARS)
        .trim()

      if (sourceText.length < MIN_SOURCE_CHARS) {
        setNotice(`No notes yet in ${room} — add some to unlock a quiz next duel.`)
        return null
      }

      const quizRes = await axios.post('/api/quiz/generate', {
        user_id: userId,
        subject: room,
        source_text: sourceText,
        num_questions: NUM_QUESTIONS,
        difficulty: 'medium',
      })
      return quizRes.data.quiz_id
    } catch {
      setNotice('Could not generate quiz questions — starting a time-only duel instead.')
      return null
    }
  }

  const startDuel = async () => {
    if (!name.trim()) return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const quizId = await buildQuizFromNotes()
      const res = await axios.post('/api/contest/create', { display_name: name.trim(), quiz_id: quizId })
      const newDuel = {
        code: res.data.code,
        participantId: res.data.participant_id,
        name: name.trim(),
        quizId: res.data.quiz_id,
        myScore: null,
        myTotal: null,
      }
      setDuel(newDuel)
      saveDuel(newDuel)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not start a duel.')
    } finally {
      setBusy(false)
    }
  }

  const joinDuel = async () => {
    if (!name.trim() || !joinCode.trim()) return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const code = joinCode.trim().toUpperCase()
      const res = await axios.post(`/api/contest/${code}/join`, { display_name: name.trim() })
      const newDuel = {
        code: res.data.code,
        participantId: res.data.participant_id,
        name: name.trim(),
        quizId: res.data.quiz_id,
        myScore: null,
        myTotal: null,
      }
      setDuel(newDuel)
      saveDuel(newDuel)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not find that duel code.')
    } finally {
      setBusy(false)
    }
  }

  const leaveDuel = () => {
    setDuel(null)
    setParticipants([])
    setQuiz(null)
    setQuizStep(null)
    saveDuel(null)
  }

  const beginQuiz = () => {
    setAnswers(new Array(quiz.questions.length).fill(null))
    setQuizStep(0)
  }

  const selectAnswer = (choiceIndex) => {
    setAnswers((prev) => {
      const next = [...prev]
      next[quizStep] = choiceIndex
      return next
    })
  }

  const advanceQuiz = async () => {
    if (quizStep < quiz.questions.length - 1) {
      setQuizStep((s) => s + 1)
      return
    }

    setBusy(true)
    try {
      const submitRes = await axios.post(`/api/quiz/${duel.quizId}/submit`, {
        user_id: userId,
        answers,
      })
      const { score, total } = submitRes.data
      await axios.post(`/api/contest/${duel.code}/quiz-result`, {
        participant_id: duel.participantId,
        score,
        total,
      }).catch(() => {})

      const updatedDuel = { ...duel, myScore: score, myTotal: total }
      setDuel(updatedDuel)
      saveDuel(updatedDuel)
      setParticipants((prev) => prev.map((p) => (
        p.id === duel.participantId ? { ...p, quiz_score: score, quiz_total: total } : p
      )))
      setQuizStep(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not submit the quiz.')
    } finally {
      setBusy(false)
    }
  }

  if (!duel) {
    return (
      <div className="contest-card">
        <span className="sidebar-heading">Study Duel</span>
        <p className="contest-intro">Pair up, and quiz each other from this room's notes.</p>
        <input
          className="contest-input"
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button className="btn btn-pink btn-block" onClick={startDuel} disabled={busy || !name.trim()}>
          {busy ? 'Starting…' : 'Start a duel'}
        </button>
        <div className="contest-join-row">
          <input
            className="contest-input"
            placeholder="Have a code?"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value)}
          />
          <button className="btn btn-ghost" onClick={joinDuel} disabled={busy || !name.trim() || !joinCode.trim()}>
            Join
          </button>
        </div>
        {notice && <p className="contest-notice">{notice}</p>}
        {error && <div className="error small-error">{error}</div>}
      </div>
    )
  }

  const maxSeconds = Math.max(focusSeconds, ...participants.map((p) => p.focus_seconds), 1)

  return (
    <div className="contest-card">
      <div className="contest-header">
        <span className="sidebar-heading">Study Duel</span>
        <button className="contest-leave" onClick={leaveDuel}>Leave</button>
      </div>
      <p className="contest-code">Code: <strong>{duel.code}</strong></p>

      <ul className="contest-participants">
        {participants.map((p) => {
          const isSelf = p.id === duel.participantId
          const seconds = isSelf ? focusSeconds : p.focus_seconds
          const quizTotal = isSelf ? duel.myTotal : p.quiz_total
          const quizScore = isSelf ? duel.myScore : p.quiz_score
          return (
            <li key={p.id} className={`contest-row ${isSelf ? 'self' : ''}`}>
              <div className="contest-row-top">
                <span>{p.display_name}{isSelf ? ' (you)' : ''}</span>
                <span>
                  {formatDuration(seconds)}
                  {quizTotal != null && ` · ${quizScore}/${quizTotal}`}
                </span>
              </div>
              <div className="contest-bar-track">
                <div className="contest-bar-fill" style={{ width: `${(seconds / maxSeconds) * 100}%` }} />
              </div>
            </li>
          )
        })}
      </ul>

      {notice && <p className="contest-notice">{notice}</p>}
      {error && <div className="error small-error">{error}</div>}

      {quiz && duel.myScore == null && quizStep === null && (
        <button className="btn btn-ghost btn-block contest-quiz-btn" onClick={beginQuiz}>
          Take the quiz ({quiz.questions.length} questions)
        </button>
      )}

      {quiz && quizStep !== null && (
        <div className="contest-quiz">
          <p className="contest-quiz-progress">Question {quizStep + 1} of {quiz.questions.length}</p>
          <p className="contest-quiz-question">{quiz.questions[quizStep].question}</p>
          <div className="contest-quiz-choices">
            {quiz.questions[quizStep].choices.map((choice, idx) => (
              <button
                key={idx}
                className={`contest-choice ${answers[quizStep] === idx ? 'selected' : ''}`}
                onClick={() => selectAnswer(idx)}
              >
                {choice}
              </button>
            ))}
          </div>
          <button
            className="btn btn-pink btn-block"
            onClick={advanceQuiz}
            disabled={busy || answers[quizStep] == null}
          >
            {quizStep < quiz.questions.length - 1 ? 'Next' : (busy ? 'Submitting…' : 'Finish')}
          </button>
        </div>
      )}

      {duel.myScore != null && (
        <p className="contest-notice">You scored {duel.myScore}/{duel.myTotal} on the {room} quiz.</p>
      )}
    </div>
  )
}
