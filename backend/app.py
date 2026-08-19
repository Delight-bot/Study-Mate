from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv()

# Import routers
from routers import chat_router, llm_router, score_router, profile_router
from database import init_database

app = FastAPI(
    title="LLM Performance Router",
    description="Adaptive LLM routing with subject profiling and performance tracking",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database and load models on startup"""
    print("🚀 Starting LLM Performance Router...")
    await init_database()
    print("✅ Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down LLM Performance Router...")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "LLM Performance Router API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Check actual DB connection
        "services": {
            "openai": os.getenv("OPENAI_API_KEY") is not None,
            "anthropic": os.getenv("ANTHROPIC_API_KEY") is not None,
            "gemini": os.getenv("GEMINI_API_KEY") is not None,
        }
    }

# Register routers
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(llm_router.router, prefix="/api/llm", tags=["llm"])
app.include_router(score_router.router, prefix="/api/score", tags=["scoring"])
app.include_router(profile_router.router, prefix="/api/profile", tags=["profile"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
