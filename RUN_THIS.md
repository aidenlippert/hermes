# 🎯 RUN THIS - Test The REAL Backend

Stop overthinking. Let's see if this actually works!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Start the Test Agent (Terminal 1)

```bash
python test_agent_code_generator.py
```

Leave it running.

## Step 3: Start the Backend (Terminal 2)

```bash
python backend/main.py
```

You should see:
```
🚀 HERMES BACKEND - PRODUCTION API
📍 API: http://localhost:8000
📚 Docs: http://localhost:8000/docs
```

## Step 4: Send a REAL Request (Terminal 3)

```bash
curl -X POST http://localhost:8000/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"query": "Write me a Python function to calculate fibonacci"}'
```

## What You Should Get Back:

```json
{
  "task_id": "xxx-xxx-xxx",
  "status": "completed",
  "message": "Completed 1/1 steps",
  "result": "def fibonacci(n):\n    if n <= 0:\n        return []\n    ...",
  "steps": [
    {
      "step_number": 1,
      "agent_name": "CodeGenerator",
      "status": "completed",
      "result": "..."
    }
  ],
  "error": null
}
```

## If It Works:

**🎉 YOU HAVE A WORKING A2A ORCHESTRATION BACKEND!**

## If It Doesn't:

Check:
1. Both terminals still running?
2. Port 10001 (agent) and 8000 (backend) free?
3. Dependencies installed?
4. Google API key set?

## Next: Try the Interactive Docs

Open http://localhost:8000/docs

Click on "POST /api/v1/chat" → Try it out

Enter:
```json
{
  "query": "Create a JavaScript function that reverses a string"
}
```

Execute and watch it work!

---

**This is the REAL backend. No mocks. No simulations. Actual A2A orchestration!**
