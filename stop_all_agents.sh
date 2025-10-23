#!/bin/bash

# Stop All Agents Script
# Kills all running A2A agents

echo ""
echo "=========================================="
echo "🛑 Stopping All Hermes Agents"
echo "=========================================="
echo ""

# Find and kill all agent processes
for agent in "code_generator" "content_writer" "data_analyzer" "web_searcher"; do
    if pgrep -f "test_agent_${agent}.py" > /dev/null; then
        echo "🔴 Stopping ${agent}..."
        pkill -f "test_agent_${agent}.py"
    else
        echo "⚪ ${agent} not running"
    fi
done

echo ""
echo "✅ All agents stopped"
echo ""
echo "=========================================="
