# StudyMate

**Study from your own notes. Duel your friends. Stay focused.**

StudyMate is an AI study platform that turns your class notes into quizzes and flashcards, so you review what your professor actually taught instead of generic material. Challenge a study partner to a duel, run focused Pomodoro sessions, and let StudyMate learn which AI model explains each subject best for you.

**[Live Demo](https://delight-bot.github.io/Study-Mate/)**

---

## Features

### Upload Your Notes
Upload your class notes and StudyMate indexes them for semantic search. Everything it generates, from quizzes to flashcards to duel questions, comes from *your* material.

### Quizzes
Generate multiple-choice quizzes from your notes and get your answers graded instantly.

### Flashcards with Spaced Repetition
Generate flashcards from your notes. Reviews are scheduled with the SM-2 spaced-repetition algorithm, so cards you struggle with come back sooner and cards you know well come back later.

### Study Duels
Challenge a study partner head to head. You can play a duel two ways:
- **From notes:** upload notes and StudyMate generates the questions for both of you.
- **Bring your own:** add your own questions and use StudyMate as the dueling platform.

### Pomodoro Timer
A built-in Pomodoro timer keeps sessions focused, with timed work blocks and breaks.

### Ask Any Question, Get the Best Answer
Ask a question and StudyMate sends it to 5 LLMs in parallel, then shows the responses side by side. Pick the one that helped most, and StudyMate learns your preference for that subject.

---

## How the AI Works

### LLM Router with Subject Profiling
StudyMate learns which model works best for you in each subject, such as Chemistry, Calculus, or Programming.

1. **Classify:** each question is automatically tagged with a subject and difficulty level.
2. **Compare:** the question goes to all 5 LLMs, each with a prompt adapted to your profile, the subject, and the difficulty.
3. **Choose:** you pick the most helpful response, and that choice updates your subject profile.
4. **Route:** as confidence grows, StudyMate recommends your best model for that subject.

| Profile strength | Questions answered | Confidence |
|---|---|---|
| Weak | Fewer than 3 | Low |
| Moderate | 3 to 10 | Building |
| Strong | More than 10 | High |

Once a subject has 10+ questions and confidence above 85%, StudyMate auto-suggests the best model.

### Automatic Response Scoring
Every response is scored on four weighted metrics:

| Metric | Weight | What it measures |
|---|---|---|
| Depth | 0.30 | Technical detail and thoroughness |
| Clarity | 0.25 | Sentence structure and readability |
| Correctness | 0.25 | Fact-checking and verification |
| Formatting | 0.20 | Structure, code blocks, and lists |

### Hallucination Checker
StudyMate cross-checks answers across all 5 models, flags numerical discrepancies and contradicting statements, and produces a consensus score.

### Response Fusion
StudyMate can combine the strongest parts of several responses, for example one model's explanation with another's code and a third's examples, and attributes each section to its source model.

### Supported Models
| Provider | Default model |
|---|---|
| OpenAI | `gpt-4` |
| Anthropic | `claude-3-5-sonnet-20241022` |
| Google | `gemini-pro` |
| DeepSeek | `deepseek-chat` |
| Together AI (Llama) | `meta-llama/Llama-2-70b-chat-hf` |

Models are configured in `backend/services/`.

---

## Architecture

StudyMate runs as independently deployable agent services behind a FastAPI gateway.

```text
                    User
                      |
                      v
              React Frontend (nginx)
                      |
                      v
               FastAPI Gateway
                      |
     +----------+-----+-----+----------+
     v          v           v          v
 Quiz Agent  Flashcard  Notes Agent  LLM Router
              Agent
     |          |           |
     +----------+-----------+
          Qdrant (vector DB)
```

| Service | Path | Responsibility |
|---|---|---|
| Gateway | `gateway/` | Reverse proxy that routes `/api/*` requests to the right service |
| LLM Router Agent | `backend/` | Chat, scoring, subject profiles, and model routing |
| Quiz Agent | `services/quiz-agent/` | Generates quizzes from source text and grades answers |
| Flashcard Agent | `services/flashcard-agent/` | Generates flashcards and schedules SM-2 reviews |
| Notes Agent | `services/notes-agent/` | Stores notes and indexes them in Qdrant for semantic search |
| Qdrant | | Vector database behind note search |

Each backend agent has its own Dockerfile and its own Postgres database (one shared instance, one database per service), backed by a PersistentVolumeClaim in Kubernetes and a named volume in Docker Compose, so data survives restarts.

Because the agents are separate, each one scales on its own. If quiz generation gets busy, Kubernetes scales only the Quiz Agent. Deployments include health probes that restart failed agents and a HorizontalPodAutoscaler for the Quiz Agent.

### Project Structure

```text
StudyMate/
├── backend/            # LLM Router Agent (FastAPI)
│   ├── routers/        # API endpoints
│   ├── services/       # LLM integrations
│   ├── models/         # Data models
│   ├── memory/         # Subject profiling
│   ├── evaluation/     # Scoring and hallucination detection
│   ├── utils/          # Helpers
│   └── app.py          # Entry point
├── gateway/            # FastAPI gateway
├── services/
│   ├── quiz-agent/
│   ├── flashcard-agent/
│   └── notes-agent/
├── frontend/           # React app
│   ├── components/
│   ├── pages/          # Chat and dashboard
│   └── main.jsx
├── database/
│   └── schema.sql
└── k8s/                # Kubernetes manifests
```

---

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (for Compose or Kubernetes)
- API keys for OpenAI, Anthropic, and Google Gemini (DeepSeek and Together AI are optional)

### Option 1: Docker Compose

```bash
docker compose build
docker compose up -d
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3001 |
| Gateway | http://localhost:8080 |
| Qdrant | http://localhost:6333 |

Stop everything with `docker compose down`.

### Option 2: Kubernetes

Requires a local cluster, for example Docker Desktop with Kubernetes enabled (Settings > Kubernetes > Enable Kubernetes).

```bash
# Build images so the cluster can see them
docker build -t studeymate/llm-router:local -f backend/Dockerfile .
docker build -t studeymate/gateway:local ./gateway
docker build -t studeymate/quiz-agent:local ./services/quiz-agent
docker build -t studeymate/flashcard-agent:local ./services/flashcard-agent
docker build -t studeymate/notes-agent:local ./services/notes-agent
docker build -t studeymate/frontend:local ./frontend

# Create your secret from the template (never commit the result)
cp k8s/secret.example.yaml k8s/secret.yaml
# Add your API keys to k8s/secret.yaml

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
kubectl get pods -n studeymate -w
```

Scale just the Quiz Agent:

```bash
kubectl scale deployment/quiz-agent --replicas=5 -n studeymate
```

### Option 3: Local Development

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env    # add your API keys
python app.py           # http://localhost:8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev             # http://localhost:3000
```

---

## API Reference

### Chat
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat/ask` | Send a question to all LLMs |
| GET | `/api/chat/history/{user_id}` | Get chat history |

### Scoring
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/score/choose` | Record the user's chosen response |
| POST | `/api/score/feedback` | Submit detailed feedback |
| GET | `/api/score/stats/{user_id}` | Get user statistics |

### Profiles
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/profile/{user_id}` | Get the full user profile |
| GET | `/api/profile/{user_id}/subject/{subject}` | Get a subject-specific profile |
| GET | `/api/profile/{user_id}/recommendations` | Get model recommendations |

### LLMs
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/llm/query/{llm_name}` | Query a single model |
| GET | `/api/llm/available` | List available models |
| GET | `/api/llm/models` | Get model details |

---

## Database

| Table | Purpose |
|---|---|
| `users` | User accounts |
| `subjects` | Subject areas |
| `llm_responses` | All model responses |
| `user_choices` | Responses users picked as best |
| `profiles` | Per-subject performance profiles |
| `difficulty_scores` | Question difficulty analysis |
| `hallucination_logs` | Detected inconsistencies |
| `evaluation_scores` | Automatic quality scores |

---

## Tech Stack

**Frontend:** React, nginx
**Backend:** FastAPI, Python
**AI:** OpenAI, Anthropic, Google Gemini, DeepSeek, Llama (Together AI), RAG
**Data:** PostgreSQL, Qdrant
**Infrastructure:** Docker, Docker Compose, Kubernetes

---

## Roadmap

- Collaborative filtering that learns from all users
- PDF export for study reports
- More models (Mistral, Cohere)
- Voice input and output
- A/B testing for prompt optimization
- Real-time fact-checking with external APIs
- Mobile app (React Native)

---

## License

MIT License

## Contact

**Delight Nyanhete**
[LinkedIn](https://www.linkedin.com/in/delight-nyanhete) | [GitHub](https://github.com/Delight-bot) | [Portfolio](https://delight-bot.github.io/Current_Portfolio/)
Built with ❤️ for demonstrating full-stack AI system development

---

**Star this repo if you find it useful for learning!** ⭐
