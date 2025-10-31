#!/bin/bash

echo "🤖 Starting ASTRAEUS Mock Agent Servers"
echo "========================================"
echo ""

# Kill any existing processes on these ports
echo "Cleaning up existing processes..."
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
lsof -ti:8004 | xargs kill -9 2>/dev/null || true

sleep 1

# Start mock agents in background
echo ""
echo "Starting Translation Bot (port 8001)..."
python3 mock_agents/translation_agent.py > logs/translation_agent.log 2>&1 &
TRANSLATION_PID=$!

echo "Starting Free Summarizer (port 8002)..."
python3 mock_agents/summarizer_agent.py > logs/summarizer_agent.log 2>&1 &
SUMMARIZER_PID=$!

echo "Starting Code Analyzer (port 8003)..."
python3 mock_agents/code_analyzer_agent.py > logs/code_analyzer_agent.log 2>&1 &
ANALYZER_PID=$!

echo "Starting LangChain Agent (port 8004)..."
python3 langchain_agent/agent_server.py > logs/langchain_agent.log 2>&1 &
LANGCHAIN_PID=$!

# Wait for servers to start
sleep 3

echo ""
echo "✅ Mock agents started successfully!"
echo ""
echo "📊 Agent Status:"
echo "  - Translation Bot:    http://localhost:8001/health (PID: $TRANSLATION_PID)"
echo "  - Free Summarizer:    http://localhost:8002/health (PID: $SUMMARIZER_PID)"
echo "  - Code Analyzer Pro:  http://localhost:8003/health (PID: $ANALYZER_PID)"
echo "  - LangChain Agent:    http://localhost:8004/health (PID: $LANGCHAIN_PID)"
echo ""
echo "📝 Logs available in logs/ directory"
echo ""
echo "To stop all agents: ./stop_mock_agents.sh"
echo "========================================"
