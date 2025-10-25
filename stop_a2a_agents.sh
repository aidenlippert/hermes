#!/bin/bash

# Stop A2A-Compliant Travel Agents

echo "🛑 Stopping A2A agents..."

# Kill processes on A2A agent ports
for port in 10005 10006 10007 10008; do
    echo "   Stopping agent on port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null
done

echo "✅ A2A agents stopped"