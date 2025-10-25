#!/bin/bash

# Start A2A-Compliant Travel Agents

echo "🚀 Starting A2A-compliant agents..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Kill any existing processes on these ports
echo "🔄 Cleaning up old processes..."
for port in 10005 10006 10007 10008; do
    lsof -ti:$port | xargs kill -9 2>/dev/null
done

# Start agents in background
echo ""
echo -e "${BLUE}Starting FlightBooker on port 10005...${NC}"
python3 backend/agents/flight_agent_a2a.py > logs/flight_agent.log 2>&1 &
echo "   PID: $!"

echo -e "${BLUE}Starting HotelBooker on port 10006...${NC}"
python3 backend/agents/hotel_agent_a2a.py > logs/hotel_agent.log 2>&1 &
echo "   PID: $!"

# Give them time to start
sleep 2

echo ""
echo -e "${GREEN}✅ A2A Agents Started!${NC}"
echo ""
echo "📍 Agent Cards Available At:"
echo "   - http://localhost:10005/.well-known/agent.json (FlightBooker)"
echo "   - http://localhost:10006/.well-known/agent.json (HotelBooker)"
echo ""
echo "🔗 A2A Endpoints:"
echo "   - http://localhost:10005/a2a (FlightBooker)"
echo "   - http://localhost:10006/a2a (HotelBooker)"
echo ""
echo "📝 Logs:"
echo "   - logs/flight_agent.log"
echo "   - logs/hotel_agent.log"
echo ""
echo "To stop: ./stop_a2a_agents.sh"