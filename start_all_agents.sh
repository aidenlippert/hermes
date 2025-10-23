#!/bin/bash

# Start All Agents Script
# Launches all A2A agents in the background

echo ""
echo "=========================================="
echo "🚀 Starting All Hermes Agents"
echo "=========================================="
echo ""

# Check if agents are already running
if pgrep -f "test_agent_code_generator.py" > /dev/null; then
    echo "⚠️  Agents already running. Stop them first:"
    echo "   ./stop_all_agents.sh"
    exit 1
fi

# Start each agent in background
echo "🤖 Starting CodeGenerator (port 10001)..."
python3 test_agent_code_generator.py > logs/agent_code_generator.log 2>&1 &
CODE_PID=$!
sleep 2

echo "✍️  Starting ContentWriter (port 10002)..."
python3 test_agent_content_writer.py > logs/agent_content_writer.log 2>&1 &
CONTENT_PID=$!
sleep 2

echo "📊 Starting DataAnalyzer (port 10003)..."
python3 test_agent_data_analyzer.py > logs/agent_data_analyzer.log 2>&1 &
DATA_PID=$!
sleep 2

echo "🔍 Starting WebSearcher (port 10004)..."
python3 test_agent_web_searcher.py > logs/agent_web_searcher.log 2>&1 &
WEB_PID=$!
sleep 2

echo ""
echo "✅ All agents started!"
echo ""
echo "Process IDs:"
echo "  CodeGenerator: $CODE_PID"
echo "  ContentWriter: $CONTENT_PID"
echo "  DataAnalyzer:  $DATA_PID"
echo "  WebSearcher:   $WEB_PID"
echo ""
echo "📋 Agent Endpoints:"
echo "  CodeGenerator: http://localhost:10001"
echo "  ContentWriter: http://localhost:10002"
echo "  DataAnalyzer:  http://localhost:10003"
echo "  WebSearcher:   http://localhost:10004"
echo ""
echo "📝 Logs in: logs/"
echo ""
echo "🛑 To stop all agents:"
echo "   ./stop_all_agents.sh"
echo ""
echo "=========================================="
