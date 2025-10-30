import os
import time
import uuid
import requests

BASE = os.getenv("HERMES_BASE_URL", "http://127.0.0.1:8000")

from typing import Dict, Any


def wait_for_health(timeout: int = 30) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(BASE + "/api/v1/health", timeout=3)
            js = r.json()
            print("health:", r.status_code, js)
            if r.status_code == 200:
                return True
        except Exception as e:
            print("waiting for health...", e)
        time.sleep(1)
    return False


def main() -> None:
    if not wait_for_health(45):
        raise SystemExit("Backend did not become healthy in time")

    # Register temp user
    email = f"local_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
    r = requests.post(BASE + "/api/v1/auth/register", json={"email": email, "password": "demo123"}, timeout=10)
    r.raise_for_status()
    tok = r.json()["access_token"]
    hdr = {"Authorization": f"Bearer {tok}"}

    # Create org
    oname = f"LocalOrg-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    r = requests.post(BASE + "/api/v1/orgs", headers=hdr, json={"name": oname}, timeout=10)
    r.raise_for_status()
    org = r.json()
    oid = org["id"]
    print("created org:", org)

    # Assign demo agents (if supported)
    r = requests.post(BASE + f"/api/v1/orgs/{oid}/assign_demo_agents", headers=hdr, timeout=10)
    print("assign demo agents:", r.status_code, getattr(r, 'text', ''))

    # List agents
    r = requests.get(BASE + "/api/v1/agents", headers=hdr, timeout=10)
    r.raise_for_status()
    agents = r.json().get("agents", [])
    print("agents:", len(agents))

    # If we have at least 2 agents, send a local A2A message from agent[0] -> agent[1]
    if len(agents) >= 2:
        a_from = agents[0]["id"]
        a_to = agents[1]["id"]
        # Send message using JWT via query param 'authorization' (API expects this)
        msg_payload: Dict[str, Any] = {
            "from_agent_id": a_from,
            "message_type": "notification",
            "content": {"hello": "world"},
            "to_agent_id": a_to,
            "requires_response": False,
        }
        r = requests.post(
            BASE + "/api/v1/a2a/messages",
            params={"authorization": f"Bearer {tok}"},
            json=msg_payload,
            timeout=10,
        )
        r.raise_for_status()
        sent = r.json()
        print("sent a2a:", sent)

        # List receipts for recipient via JWT endpoint
        r = requests.get(
            BASE + "/api/v1/a2a/receipts",
            headers=hdr,
            params={"agent_id": a_to, "limit": 10},
            timeout=10,
        )
        r.raise_for_status()
        receipts = r.json().get("receipts", [])
        print("receipts count:", len(receipts))
        if receipts:
            mid = receipts[0]["message_id"]
            # Ack via JWT (same /ack endpoint supports JWT)
            r = requests.post(
                BASE + "/api/v1/a2a/ack",
                headers=hdr,
                params={"message_id": mid, "agent_id": a_to},
                timeout=10,
            )
            print("ack status:", r.status_code, r.text)

    # Federation health
    r = requests.get(BASE + "/api/v1/a2a/federation/health", timeout=5)
    print("federation health:", r.status_code, r.json())

    print("local smoke passed")

if __name__ == "__main__":
    main()
