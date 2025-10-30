"""
Integration test for Orgs/ACL admin APIs.

Requires a running backend at http://localhost:8000 and a valid Bearer JWT token
with sufficient privileges. Set HERMES_BEARER_TOKEN in your environment before
running this script.
"""
import os
import time
import uuid
import requests
import random
import string

BASE = os.getenv("HERMES_BASE_URL", "http://localhost:8000")
TOKEN = os.getenv("HERMES_BEARER_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"} if TOKEN else {"Content-Type": "application/json"}

# Mutable holders to appease strict linters that treat uppercase as constants
current_token = TOKEN
current_headers = HEADERS


def require_token():
    global current_token, current_headers
    if not current_token:
        print("\nℹ️  No token provided; attempting on-the-fly registration to obtain one...")
        try:
            email = f"orgtest_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            r = requests.post(
                f"{BASE}/api/v1/auth/register",
                headers={"Content-Type": "application/json"},
                json={"email": email, "password": password}
            )
            if r.ok:
                data = r.json()
                token = data.get("access_token")
                if token:
                    current_token = token
                    current_headers = {"Authorization": f"Bearer {current_token}", "Content-Type": "application/json"}
                    print(f"✅ Registered temp user {email}")
                    return True
                else:
                    print("❌ Registration succeeded but token missing in response")
            else:
                print(f"❌ Registration failed: {r.status_code} {r.text}")
        except Exception as e:
            print(f"❌ Registration error: {e}")
        return False
    return True


def get(url: str):
    return requests.get(f"{BASE}{url}", headers=current_headers)


from typing import Any, Dict


def post(url: str, json: Dict[str, Any]):
    return requests.post(f"{BASE}{url}", headers=current_headers, json=json)


def main():
    print("\n=== Orgs/ACL API Smoke Test ===\n")

    # Health
    r = get("/api/v1/health")
    print(f"Health: {r.status_code}")
    try:
        print(r.json())
    except Exception:
        print(r.text)

    if not require_token():
        return

    # 1) List orgs
    r = get("/api/v1/orgs")
    print(f"\nList orgs: {r.status_code}")
    if r.ok:
        data = r.json()
        print(f"Orgs count: {len(data.get('orgs', []))}")
    else:
        print(r.text)
        return

    # 2) Create org
    org_name = f"TestOrg-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    r = post("/api/v1/orgs", {"name": org_name})
    print(f"\nCreate org: {r.status_code}")
    if not r.ok:
        print(r.text)
        return
    org = r.json()
    org_id = org.get("id")
    print(f"Created org: {org}")

    # 3) List members (should include caller as admin)
    r = get(f"/api/v1/orgs/{org_id}/members")
    print(f"\nList members: {r.status_code}")
    if r.ok:
        members = r.json().get("members", [])
        print(f"Members: {members}")
    else:
        print(r.text)
        return

    # 4) Try assigning demo agents to this org (if endpoint exists)
    try:
        r = post(f"/api/v1/orgs/{org_id}/assign_demo_agents", json={})
        if r.status_code == 200:
            data = r.json()
            print(f"\nAssign demo agents: {r.status_code} -> assigned={data.get('assigned')} skipped={data.get('skipped')} missing={data.get('missing')}")
        elif r.status_code == 404:
            print("\nAssign demo agents: endpoint not found (skipping)")
        else:
            print(f"\nAssign demo agents: {r.status_code} {r.text}")
    except Exception as e:
        print(f"\nAssign demo agents error: {e}")

    # 5) List agents (owned or in user's orgs)
    r = get("/api/v1/agents")
    print(f"\nList agents: {r.status_code}")
    if r.ok:
        agents = r.json().get("agents", [])
        print(f"Agents: {len(agents)}")
    else:
        print(r.text)

    print("\n✅ Done")


if __name__ == "__main__":
    main()
