# 🔐 Setup Instructions for Your 2-LLM Configuration

## ⚠️ FIRST: Get New API Keys

Your old keys were exposed and need to be revoked! Get new ones:

### 1. OpenAI (GPT)
1. Go to: https://platform.openai.com/api-keys
2. **Delete the old key** (the one you shared)
3. Click "Create new secret key"
4. Name it "LLM Router Project"
5. Copy the key (starts with `sk-proj-...`)

### 2. Google Gemini
1. Go to: https://aistudio.google.com/app/apikey
2. **Delete the old key** (the one you shared)
3. Click "Create API key"
4. Copy the key (starts with `AIza...`)

---

## 🛠️ Configure Your Project

### Step 1: Open the `.env` file

The file is located at: `backend\.env`

### Step 2: Add Your NEW Keys

```bash
# Required - Add your NEW keys here
OPENAI_API_KEY=sk-proj-YOUR_NEW_OPENAI_KEY_HERE
GEMINI_API_KEY=AIzaSyYOUR_NEW_GEMINI_KEY_HERE

# Optional - Leave blank for now
ANTHROPIC_API_KEY=
DEEPSEEK_API_KEY=
LLAMA_API_KEY=
```

**Replace:**
- `sk-proj-YOUR_NEW_OPENAI_KEY_HERE` with your actual new OpenAI key
- `AIzaSyYOUR_NEW_GEMINI_KEY_HERE` with your actual new Gemini key

### Step 3: Save the file

Make sure to save `backend\.env` after editing!

---

## 🚀 Run Your Project

### Terminal 1 - Backend
```bash
cd backend
python app.py
```

You should see:
```
🚀 Starting LLM Performance Router...
✅ Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm run dev
```

You should see:
```
VITE ready in XXX ms
➜  Local:   http://localhost:3000/
```

---

## ✅ Test It Works

1. Open browser: http://localhost:3000
2. Type a question: "What is photosynthesis?"
3. Click "Ask All LLMs"
4. You should see **2 responses** (GPT and Gemini)
5. Click your favorite one
6. Go to Dashboard to see your profile building!

---

## 🔮 Adding More LLMs Later

When you want to add more LLMs, just:

1. Get the API key for that service
2. Open `backend\.env`
3. Add the key to the appropriate line
4. Restart the backend server
5. That's it! The new LLM will appear automatically

**Example - Adding Claude later:**
```bash
ANTHROPIC_API_KEY=sk-ant-YOUR_CLAUDE_KEY
```

---

## 🛡️ Security Tips

### DO:
✅ Keep your `.env` file private
✅ Never commit `.env` to git (already in `.gitignore`)
✅ Generate new keys if you think they're exposed
✅ Use different keys for different projects

### DON'T:
❌ Share API keys in chat/email
❌ Post keys in screenshots
❌ Commit keys to GitHub
❌ Use production keys for testing

---

## 🐛 Troubleshooting

### "Error: API key not valid"
- Make sure you copied the entire key
- Check for extra spaces before/after the key
- Verify the key hasn't been revoked

### "Only seeing 1 response instead of 2"
- Check both API keys are in `.env`
- Restart the backend server after adding keys
- Look at backend console for error messages

### "Can't connect to backend"
- Make sure backend is running on port 8000
- Check for error messages in the backend console

---

## 📞 Need Help?

Check the backend console output - it will show you which LLMs are available and any errors with API keys.

Happy coding! 🎉
