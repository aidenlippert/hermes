#!/bin/bash

# Stop all travel planning agents

echo "🛑 Stopping Travel Planning Agents..."

pkill -f "flight_agent.py"
pkill -f "hotel_agent.py"
pkill -f "restaurant_agent.py"
pkill -f "events_agent.py"

echo "✅ All agents stopped"
