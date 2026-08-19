# 🚀 Quick Start Guide

Get your LLM Performance Router running in minutes!

## Step 1: Set Up API Keys

1. Copy the environment template:
```bash
cd backend
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

**Note**: You need at least 2 API keys to see the comparison feature.

## Step 2: Install Backend

```bash
cd backend
pip install -r requirements.txt
```

## Step 3: Install Frontend

```bash
cd ../frontend
npm install
```

## Step 4: Run the Application

### Option A: Run Both Servers (Recommended)

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option B: Test Backend Only

```bash
cd backend
python app.py
```

Then visit: `http://localhost:8000/docs` for the API documentation

## Step 5: Open the App

Open your browser and go to: **http://localhost:3000**

## 🎮 Quick Test

1. Type a question like: "Explain photosynthesis in simple terms"
2. Click "Ask All LLMs"
3. Wait for all 5 responses
4. Click on your favorite response
5. Go to Dashboard to see your profile building!

## 🐛 Troubleshooting

### Backend won't start
- Make sure port 8000 is available
- Check that all dependencies are installed: `pip list`
- Verify your API keys are set in `.env`

### Frontend won't start
- Make sure port 3000 is available
- Delete `node_modules` and run `npm install` again
- Clear npm cache: `npm cache clean --force`

### Database errors
- Delete `llm_router.db` and restart the backend
- The database will be recreated automatically

### LLM API errors
- Verify your API keys are correct
- Check your API quota/billing status
- Some LLMs may not be available without specific setup

## 📚 Next Steps

1. Try questions in different subjects (Chemistry, Programming, etc.)
2. Select your favorite responses to build your profile
3. Check the Dashboard to see your preferences
4. Experiment with the hallucination checker by asking controversial questions
5. Try the response fusion feature for complex questions

## 🎯 Example Questions to Try

**Chemistry**: "What is the difference between ionic and covalent bonds?"

**Programming**: "Explain recursion with a Python example"

**Calculus**: "What is the derivative of x^2 + 3x?"

**Physics**: "How does quantum entanglement work?"

**General**: "What are the key differences between AI and machine learning?"

## 💡 Tips

- Answer at least 5 questions per subject to build a reliable profile
- Try different subjects to see how the profiling adapts
- The Dashboard updates in real-time as you make choices
- Higher confidence = better recommendations

Enjoy building your personalized LLM router! 🎉
