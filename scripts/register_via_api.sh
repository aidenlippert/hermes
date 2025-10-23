#!/bin/bash

# Register Travel Agents via API
# This registers agents in the production database through the API

echo "🎯 Registering Travel Planning Agents via API..."
echo ""

# Get auth token first (you'll need to have a user registered)
# For now, we'll create the agents directly in the database using psql

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set. Please set it first:"
    echo "   export DATABASE_URL='postgresql://...'"
    exit 1
fi

echo "📝 Inserting agents into database..."

psql "$DATABASE_URL" << 'EOF'
-- Delete existing travel agents to avoid duplicates
DELETE FROM agents WHERE category = 'travel';

-- Insert FlightBooker
INSERT INTO agents (
    id, name, description, endpoint, capabilities, category,
    status, average_rating, total_calls, successful_calls, failed_calls
) VALUES (
    gen_random_uuid(),
    'FlightBooker',
    'Search and book flights worldwide. I can find the best deals based on your dates, budget, and preferences.',
    'http://localhost:10010',
    '["flight_search", "flight_booking", "price_comparison", "travel", "book_flight"]'::json,
    'travel',
    'active',
    5.0,
    0,
    0,
    0
);

-- Insert HotelBooker
INSERT INTO agents (
    id, name, description, endpoint, capabilities, category,
    status, average_rating, total_calls, successful_calls, failed_calls
) VALUES (
    gen_random_uuid(),
    'HotelBooker',
    'Find and book hotels worldwide. I can search by location, price range, amenities, and ratings.',
    'http://localhost:10011',
    '["hotel_search", "hotel_booking", "accommodation", "travel", "book_hotel"]'::json,
    'travel',
    'active',
    5.0,
    0,
    0,
    0
);

-- Insert RestaurantFinder
INSERT INTO agents (
    id, name, description, endpoint, capabilities, category,
    status, average_rating, total_calls, successful_calls, failed_calls
) VALUES (
    gen_random_uuid(),
    'RestaurantFinder',
    'Discover amazing restaurants and make reservations. I can find dining options based on cuisine, location, budget, and dietary preferences.',
    'http://localhost:10012',
    '["restaurant_search", "restaurant_reservation", "dining", "food", "travel"]'::json,
    'travel',
    'active',
    5.0,
    0,
    0,
    0
);

-- Insert EventsFinder
INSERT INTO agents (
    id, name, description, endpoint, capabilities, category,
    status, average_rating, total_calls, successful_calls, failed_calls
) VALUES (
    gen_random_uuid(),
    'EventsFinder',
    'Discover local events, attractions, and activities. I can find concerts, shows, tours, museums, and unique experiences.',
    'http://localhost:10013',
    '["events_search", "activities", "attractions", "entertainment", "travel"]'::json,
    'travel',
    'active',
    5.0,
    0,
    0,
    0
);

-- Show registered agents
SELECT name, endpoint, capabilities FROM agents WHERE category = 'travel';
EOF

echo ""
echo "✅ Agent registration complete!"
echo ""
echo "Registered agents:"
echo "   - FlightBooker (http://localhost:10010)"
echo "   - HotelBooker (http://localhost:10011)"
echo "   - RestaurantFinder (http://localhost:10012)"
echo "   - EventsFinder (http://localhost:10013)"
echo ""
echo "Now you can ask Hermes:"
echo '   "Book me a trip to Cancun"'
echo '   "Plan a trip to Paris for me"'
echo '   "Find me flights and hotels to New York"'
