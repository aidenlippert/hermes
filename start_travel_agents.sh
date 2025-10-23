#!/bin/bash

# Start Travel Planning Agents
# Launch all agents for the travel planning demo

echo "🚀 Starting Hermes Travel Planning Agents..."
echo ""

# Create logs directory
mkdir -p logs

# Start Flight Agent
echo "🛫 Starting Flight Booking Agent (port 10010)..."
python agents/flight_agent.py > logs/flight_agent.log 2>&1 &
FLIGHT_PID=$!
echo "   PID: $FLIGHT_PID"

# Start Hotel Agent
echo "🏨 Starting Hotel Booking Agent (port 10011)..."
python agents/hotel_agent.py > logs/hotel_agent.log 2>&1 &
HOTEL_PID=$!
echo "   PID: $HOTEL_PID"

# Start Restaurant Agent
echo "🍽️  Starting Restaurant Finder Agent (port 10012)..."
python agents/restaurant_agent.py > logs/restaurant_agent.log 2>&1 &
RESTAURANT_PID=$!
echo "   PID: $RESTAURANT_PID"

# Start Events Agent
echo "🎭 Starting Events Finder Agent (port 10013)..."
python agents/events_agent.py > logs/events_agent.log 2>&1 &
EVENTS_PID=$!
echo "   PID: $EVENTS_PID"

echo ""
echo "✅ All agents started!"
echo ""
echo "Agent Endpoints:"
echo "   Flight:      http://localhost:10010"
echo "   Hotel:       http://localhost:10011"
echo "   Restaurant:  http://localhost:10012"
echo "   Events:      http://localhost:10013"
echo ""
echo "Logs directory: ./logs/"
echo ""
echo "To stop all agents: ./stop_travel_agents.sh"
