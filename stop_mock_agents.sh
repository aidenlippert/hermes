#!/bin/bash

echo "🛑 Stopping ASTRAEUS Mock Agent Servers"
echo "========================================"
echo ""

# Kill processes on agent ports
echo "Stopping agents..."
lsof -ti:8001 | xargs kill -9 2>/dev/null && echo "  ✅ Translation Bot stopped" || echo "  ⚠️  Translation Bot not running"
lsof -ti:8002 | xargs kill -9 2>/dev/null && echo "  ✅ Free Summarizer stopped" || echo "  ⚠️  Free Summarizer not running"
lsof -ti:8003 | xargs kill -9 2>/dev/null && echo "  ✅ Code Analyzer stopped" || echo "  ⚠️  Code Analyzer not running"
lsof -ti:8004 | xargs kill -9 2>/dev/null && echo "  ✅ LangChain Agent stopped" || echo "  ⚠️  LangChain Agent not running"

echo ""
echo "✅ All mock agents stopped"
echo "========================================"
