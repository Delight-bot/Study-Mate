# Study Mate (StudeyMate)

Study Mate is an AI learning assistant platform with a React frontend and FastAPI-based backend services. It helps users ask study questions, compare responses from multiple LLMs, and use quiz/flashcard/notes tools in one system.

## What this project includes

- **LLM Router (`backend/`)**: sends questions to configured LLMs, scores responses, and tracks user preferences.
- **Gateway (`gateway/`)**: routes frontend API calls to backend services.
- **Quiz Agent (`services/quiz-agent/`)**: generates and grades quizzes.
- **Flashcard Agent (`services/flashcard-agent/`)**: creates flashcards and supports spaced repetition.
- **Notes Agent (`services/notes-agent/`)**: stores notes and supports semantic search with Qdrant.
- **Frontend (`frontend/`)**: user interface for chat, learning tools, and dashboards.

## Architecture

- Frontend → Gateway → LLM Router + Quiz/Flashcard/Notes agents
- Postgres is used for service data storage.
- Qdrant is used by the Notes Agent for vector search.

## Quick start (local development)

### 1) Configure environment

```bash
cd backend
cp .env.example .env
```

Add your API keys in `backend/.env` (at least two keys recommended for model comparison).

### 2) Run backend + frontend

Backend:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`

## Run full multi-service stack (Docker Compose)

```bash
docker compose build
docker compose up -d
```

- Frontend: `http://localhost:3001`
- Gateway: `http://localhost:8080`
- Qdrant: `http://localhost:6333`

Stop services:

```bash
docker compose down
```

## Repository structure

```text
backend/                LLM router service (FastAPI)
frontend/               React app
gateway/                API gateway (FastAPI)
services/quiz-agent/    Quiz microservice
services/flashcard-agent/ Flashcard microservice
services/notes-agent/   Notes + vector search microservice
database/               Database schema resources
k8s/                    Kubernetes manifests
postgres/               Postgres bootstrap scripts
```

## Notes

- Keep secrets in `.env` files only; never commit credentials.
- For detailed setup notes, see `QUICKSTART.md`.
