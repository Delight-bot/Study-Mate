-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table (Chemistry, Calculus, Programming, etc.)
CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM Responses table
CREATE TABLE IF NOT EXISTS llm_responses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    subject_id INTEGER,
    llm_name TEXT NOT NULL,  -- 'gpt', 'claude', 'gemini', 'deepseek', 'llama'
    response_text TEXT NOT NULL,
    response_time REAL NOT NULL,  -- in seconds
    token_count INTEGER,
    prompt_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- User Choices table (which model the user selected as best)
CREATE TABLE IF NOT EXISTS user_choices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    subject_id INTEGER,
    chosen_llm TEXT NOT NULL,
    all_responses TEXT NOT NULL,  -- JSON array of response IDs
    metadata TEXT,  -- JSON with user feedback/refinement
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- Subject Profiles table (Best LLM per subject per user)
CREATE TABLE IF NOT EXISTS profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    subject_id INTEGER NOT NULL,
    best_llm TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,  -- 0.0 to 1.0
    wins_gpt INTEGER DEFAULT 0,
    wins_claude INTEGER DEFAULT 0,
    wins_gemini INTEGER DEFAULT 0,
    wins_deepseek INTEGER DEFAULT 0,
    wins_llama INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (subject_id) REFERENCES subjects(id),
    UNIQUE(user_id, subject_id)
);

-- Difficulty Scores table
CREATE TABLE IF NOT EXISTS difficulty_scores (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    subject_id INTEGER,
    difficulty_level TEXT,  -- 'easy', 'medium', 'hard'
    difficulty_score REAL,  -- 0.0 to 1.0
    keyword_complexity REAL,
    avg_response_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)
);

-- Hallucination Logs table
CREATE TABLE IF NOT EXISTS hallucination_logs (
    id SERIAL PRIMARY KEY,
    llm_name TEXT NOT NULL,
    question TEXT NOT NULL,
    response_text TEXT NOT NULL,
    inconsistency_score REAL,  -- 0.0 to 1.0
    conflicting_llms TEXT,  -- JSON array of LLMs that disagreed
    flagged_content TEXT,  -- What was flagged as potential hallucination
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Evaluation Scores table
CREATE TABLE IF NOT EXISTS evaluation_scores (
    id SERIAL PRIMARY KEY,
    response_id INTEGER NOT NULL,
    clarity_score REAL,
    depth_score REAL,
    formatting_score REAL,
    correctness_score REAL,
    overall_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (response_id) REFERENCES llm_responses(id)
);

-- Insert default demo user (the frontend has no auth flow and hardcodes user_id=1 everywhere)
INSERT INTO users (id, username, email) VALUES (1, 'demo_user', 'demo@studeymate.local')
ON CONFLICT (id) DO NOTHING;
SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));

-- Insert default subjects
INSERT INTO subjects (name, description) VALUES
    ('Chemistry', 'Chemistry and chemical sciences'),
    ('Calculus', 'Calculus and mathematical analysis'),
    ('Programming', 'Computer programming and software development'),
    ('Physics', 'Physics and physical sciences'),
    ('Biology', 'Biology and life sciences'),
    ('History', 'History and historical topics'),
    ('Literature', 'Literature and language arts'),
    ('General', 'General knowledge and miscellaneous topics')
ON CONFLICT (name) DO NOTHING;
