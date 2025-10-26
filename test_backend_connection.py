"""
Test Backend Connection
Run this to verify Railway backend is working
"""

import requests
import json

# Your Railway backend URL
BACKEND_URL = "https://web-production-3df46.up.railway.app"

def test_health():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_register():
    """Test user registration"""
    try:
        payload = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "username": "testuser",
            "full_name": "Test User"
        }
        response = requests.post(f"{BACKEND_URL}/api/v1/auth/register", json=payload)
        print(f"\n{'✅' if response.status_code in [200, 201] else '❌'} Registration: {response.status_code}")
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   User created: {data.get('user', {}).get('email')}")
            return data.get('access_token')
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Registration failed: {e}")
    return None

def test_login():
    """Test user login"""
    try:
        payload = {
            "email": "test@example.com",
            "password": "TestPassword123!"
        }
        response = requests.post(f"{BACKEND_URL}/api/v1/auth/login", json=payload)
        print(f"\n{'✅' if response.status_code == 200 else '❌'} Login: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Token received: {data.get('access_token', '')[:20]}...")
            return data.get('access_token')
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Login failed: {e}")
    return None

def test_chat(token):
    """Test chat endpoint"""
    if not token:
        print("\n⚠️  Skipping chat test (no token)")
        return

    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "query": "Find me flights from New York to Paris"
        }
        response = requests.post(f"{BACKEND_URL}/api/v1/chat", json=payload, headers=headers)
        print(f"\n{'✅' if response.status_code == 200 else '❌'} Chat endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Task ID: {data.get('task_id', '')[:20]}...")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Chat test failed: {e}")

def test_agents(token):
    """Test agent listing"""
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(f"{BACKEND_URL}/api/v1/agents", headers=headers)
        print(f"\n{'✅' if response.status_code == 200 else '❌'} Agent listing: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Agents found: {len(data.get('agents', []))}")
            for agent in data.get('agents', [])[:3]:
                print(f"   - {agent.get('name')}: {agent.get('description', '')[:50]}...")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Agent listing failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("HERMES BACKEND CONNECTION TEST")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 60)

    # Test health
    health_ok = test_health()

    if not health_ok:
        print("\n⚠️  Backend appears to be down or not responding")
        print("Check Railway logs for deployment status")
    else:
        # Try to register (might fail if user exists)
        token = test_register()

        # If registration failed (user exists), try login
        if not token:
            token = test_login()

        # Test other endpoints
        test_chat(token)
        test_agents(token)

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)