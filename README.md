# 🤖 LLM Performance Router with Adaptive Prompting and Subject Profiling

A comprehensive system that intelligently routes questions to multiple LLMs, tracks user preferences, and builds personalized subject-specific profiles to recommend the best LLM for each domain.

## 🌟 Key Features

### 1. **Adaptive Prompt Rewriting**
Customizes prompts for each LLM based on:
- User preferences and style
- Subject area
- Question difficulty
- Historical performance

### 2. **Automatic Scoring System**
Evaluates responses on multiple metrics:
- **Clarity**: Sentence structure, readability
- **Depth**: Technical detail, thoroughness
- **Formatting**: Structure, code blocks, lists
- **Correctness**: Fact-checking and verification

### 3. **Memory-Based Subject Profiling** ⭐ (Featured)
Learns your preferences per subject:
- Tracks which LLM you prefer for Chemistry, Calculus, Programming, etc.
- Builds confidence scores over time
- Automatically recommends the best LLM for each subject
- Adapts routing based on your history

### 4. **Hallucination Checker**
Cross-checks responses to detect inconsistencies:
- Compares answers across all 5 LLMs
- Flags numerical discrepancies
- Detects contradicting statements
- Generates consensus scores

### 5. **Response Fusion**
Combines the best parts of multiple responses:
- Takes GPT's explanation + DeepSeek's code + Gemini's examples
- Creates superior hybrid answers
- Provides attribution for each section

## 🏗️ Architecture

```
/StudeyMate
├── /backend              # FastAPI backend
│   ├── /routers         # API endpoints
│   ├── /services        # LLM integrations
│   ├── /models          # Data models
│   ├── /memory          # Subject profiling system ⭐
│   ├── /evaluation      # Scoring & hallucination detection
│   ├── /utils           # Helper functions
│   └── app.py           # Main application
├── /frontend            # React frontend
│   ├── /components      # UI components
│   ├── /pages           # Chat & Dashboard
│   └── main.jsx         # Entry point
├── /database            # SQLite database
│   └── schema.sql       # Database schema
└── README.md
```

## 🤖 Agentic Microservice Architecture

Beyond the monolithic dev setup below, StudeyMate can run as an independently
deployable set of services behind a gateway — closer to how this would be run
in production, and a natural fit for Kubernetes:

```text
                    User
                      │
                      ▼
              React Frontend (nginx)
                      │
                      ▼
               FastAPI Gateway
                      │
     ┌──────────┬──────────┬──────────┐
     ▼          ▼          ▼          ▼
 Quiz Agent  Flashcard  Notes Agent  LLM Router
              Agent
     │          │          │
     └──────────┴──────────┘
              Qdrant (vector DB)
```

Five independently deployable services, each with its own Dockerfile:

- **Gateway Agent** (`gateway/`) — FastAPI reverse proxy that routes `/api/*`
  requests to the right upstream service.
- **LLM Router Agent** (`backend/`) — the existing chat/score/profile/llm
  routing system described above, unchanged, running as its own service.
- **Quiz Agent** (`services/quiz-agent/`) — generates multi-choice quizzes from
  source text via an LLM and grades submitted answers.
- **Flashcard Agent** (`services/flashcard-agent/`) — generates flashcards via
  an LLM and schedules reviews with the SM-2 spaced-repetition algorithm.
- **Notes Agent** (`services/notes-agent/`) — stores notes and indexes them in
  Qdrant for semantic search over embeddings.
- **Qdrant** — vector database backing the Notes Agent's semantic search.

Each of the 4 backend agents persists to its own Postgres database and can be
scaled independently — e.g. if quiz generation gets popular, Kubernetes can
scale just the Quiz Agent from 1 to 5 replicas without touching the others.

**Resume-friendly summary of this work:**
- Designed an agentic AI architecture with independent quiz, flashcard, and
  notes agent services behind a FastAPI gateway, enabling modular development
  and independent scaling.
- Containerized the React frontend, FastAPI gateway, and AI agent services
  with Docker, then orchestrated deployments using Kubernetes for
  fault-tolerant, scalable application management.
- Configured Kubernetes Deployments, Services, health probes, and a
  HorizontalPodAutoscaler to automatically restart failed agents and scale
  the Quiz Agent under load with minimal service disruption.

### Run locally with Docker Compose

```bash
docker compose build
docker compose up -d
# frontend:  http://localhost:3001
# gateway:   http://localhost:8080
# qdrant:    http://localhost:6333
docker compose down
```

### Deploy to Kubernetes

Requires a local cluster (e.g. enable Kubernetes in Docker Desktop: Settings →
Kubernetes → Enable Kubernetes).

```bash
# Build images so the cluster's local image cache can see them
docker build -t studeymate/llm-router:local -f backend/Dockerfile .
docker build -t studeymate/gateway:local ./gateway
docker build -t studeymate/quiz-agent:local ./services/quiz-agent
docker build -t studeymate/flashcard-agent:local ./services/flashcard-agent
docker build -t studeymate/notes-agent:local ./services/notes-agent
docker build -t studeymate/frontend:local ./frontend

# Create the real secret from the template (never commit the result)
cp k8s/secret.example.yaml k8s/secret.yaml
# edit k8s/secret.yaml with your real API keys

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
kubectl get pods -n studeymate -w

# Demonstrate independent scaling of just the Quiz Agent
kubectl scale deployment/quiz-agent --replicas=5 -n studeymate
kubectl get pods -n studeymate
```

All four services (llm-router, quiz-agent, flashcard-agent, notes-agent) persist to
Postgres — one shared instance, one database per service (`llm_router`, `quiz_agent`,
`flashcard_agent`, `notes_agent`), backed by a real PersistentVolumeClaim in Kubernetes
(and a named volume in Compose) — so data survives pod/container restarts, same as Qdrant.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- API Keys for:
  - OpenAI (GPT)
  - Anthropic (Claude)
  - Google (Gemini)
  - DeepSeek (optional)
  - Llama via Together AI (optional)

### Backend Setup

1. **Install Python dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. **Run the backend**:
```bash
python app.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install Node dependencies**:
```bash
cd frontend
npm install
```

2. **Run the development server**:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📊 How It Works

### 1. Ask a Question
- Type your question in the chat interface
- The system classifies the subject automatically
- Question difficulty is analyzed

### 2. Get All Responses
- Your question is sent to all 5 LLMs in parallel
- Each LLM gets an optimized prompt based on your profile
- Responses are scored automatically

### 3. Select Your Favorite
- Review all 5 responses side-by-side
- Click on the one you find most helpful
- Your choice is recorded

### 4. Build Your Profile
- Over time, the system learns which LLM you prefer for each subject
- Future questions will prioritize your preferred LLMs
- Confidence scores increase with more data

### 5. View Your Dashboard
- See your performance statistics
- Track which LLM is best for each subject
- Visualize win rates and confidence levels

## 🎯 API Endpoints

### Chat Endpoints
- `POST /api/chat/ask` - Send a question to all LLMs
- `GET /api/chat/history/{user_id}` - Get chat history

### Scoring Endpoints
- `POST /api/score/choose` - Record user's LLM choice
- `POST /api/score/feedback` - Submit detailed feedback
- `GET /api/score/stats/{user_id}` - Get user statistics

### Profile Endpoints
- `GET /api/profile/{user_id}` - Get complete user profile
- `GET /api/profile/{user_id}/subject/{subject}` - Get subject-specific profile
- `GET /api/profile/{user_id}/recommendations` - Get LLM recommendations

### LLM Endpoints
- `POST /api/llm/query/{llm_name}` - Query a single LLM
- `GET /api/llm/available` - Check which LLMs are available
- `GET /api/llm/models` - Get model information

## 💾 Database Schema

### Key Tables
- **users**: User accounts
- **subjects**: Subject areas (Chemistry, Calculus, etc.)
- **llm_responses**: All LLM responses
- **user_choices**: User's selected best responses
- **profiles**: Subject-specific performance profiles ⭐
- **difficulty_scores**: Question difficulty analysis
- **hallucination_logs**: Detected inconsistencies
- **evaluation_scores**: Automatic quality scores

## 🔧 Configuration

### LLM Models
Default models can be configured in `/backend/services/`:
- **GPT**: `gpt-4`
- **Claude**: `claude-3-5-sonnet-20241022`
- **Gemini**: `gemini-pro`
- **DeepSeek**: `deepseek-chat`
- **Llama**: `meta-llama/Llama-2-70b-chat-hf`

### Evaluation Weights
Scoring weights in `/backend/evaluation/scorer.py`:
```python
weights = {
    'clarity': 0.25,
    'depth': 0.30,
    'formatting': 0.20,
    'correctness': 0.25
}
```

## 📈 Subject Profiling Details

The Memory-Based Subject Profiling system is the core innovation:

### How It Learns
1. **Classification**: Questions are automatically classified into subjects
2. **Tracking**: Every user choice updates the subject profile
3. **Confidence**: Confidence grows with more interactions
4. **Routing**: Best LLM is recommended based on win rate

### Profile Strength Levels
- **Weak**: < 3 questions (low confidence)
- **Moderate**: 3-10 questions (building confidence)
- **Strong**: 10+ questions (high confidence)

### Auto-Selection Threshold
- Confidence > 85% + 10+ questions = Auto-suggest best LLM

## 🎓 Perfect for Interviews!

This project demonstrates:
- ✅ Full-stack development (FastAPI + React)
- ✅ Database design and ORM
- ✅ API integration (multiple LLM providers)
- ✅ Machine learning concepts (profiling, scoring)
- ✅ User behavior analysis
- ✅ Real-time data processing
- ✅ Clean architecture and separation of concerns
- ✅ Scalable design patterns

## 🔮 Future Enhancements

- [ ] Add authentication and multi-user support
- [ ] Implement collaborative filtering (learn from all users)
- [ ] Add export functionality (PDF reports)
- [ ] Integrate more LLMs (Mistral, Cohere, etc.)
- [ ] Add voice input/output
- [ ] Implement A/B testing for prompt optimization
- [ ] Add real-time fact-checking with external APIs
- [ ] Mobile app (React Native)

## 📝 License

MIT License - feel free to use this project for learning and interviews!

## 🤝 Contributing

This is a portfolio/interview project, but suggestions are welcome!

## 📧 Contact

Built with ❤️ for demonstrating full-stack AI system development

---

**Star this repo if you find it useful for learning!** ⭐
