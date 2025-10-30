import os
import time
import uuid
import requests

BASE = os.getenv("HERMES_BASE_URL", "http://127.0.0.1:8000")

def wait_for_health(timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(BASE + "/api/v1/health", timeout=3)
            js = r.json()
            if r.status_code == 200 and js.get("status") in ("healthy", "starting"):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def smoke_orgs_flow():
    # Register temp user
    email = f"ci_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
    r = requests.post(BASE + "/api/v1/auth/register", json={"email": email, "password": "demo123"}, timeout=10)
    r.raise_for_status()
    tok = r.json()["access_token"]
    hdr = {"Authorization": f"Bearer {tok}"}

    # Create org
    oname = f"CIOrg-{int(time.time())}-{uuid.uuid4().hex[:6]}"
    r = requests.post(BASE + "/api/v1/orgs", headers=hdr, json={"name": oname}, timeout=10)
    r.raise_for_status()
    org = r.json()
    oid = org["id"]

    # Assign demo agents (if available)
    r = requests.post(BASE + f"/api/v1/orgs/{oid}/assign_demo_agents", headers=hdr, timeout=10)
    if r.status_code not in (200, 404):
        r.raise_for_status()

    # List agents
    r = requests.get(BASE + "/api/v1/agents", headers=hdr, timeout=10)
    r.raise_for_status()


def smoke_federation_inbox():
    # Send an unsigned inbox payload to ourselves (dev mode accepts if no secret)
    payload = {
        "id": str(uuid.uuid4()),
        "from": "CISmoke@remote.example",
        "to": "FlightBooker@localhost",
        "type": "notification",
        "payload": {"ping": True},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    r = requests.post(BASE + "/api/v1/a2a/federation/inbox", json=payload, timeout=10)
    # Accept 200 or 202; if 404 (no local FlightBooker), skip
    if r.status_code == 404 and "Target agent not found" in r.text:
        return
    r.raise_for_status()


def main():
    if not wait_for_health(45):
        raise SystemExit("Backend did not become healthy in time")
    # Federation health
    requests.get(BASE + "/api/v1/a2a/federation/health", timeout=5)
    # Core orgs flow
    smoke_orgs_flow()
    # Federation inbox
    smoke_federation_inbox()
    print("CI smoke passed")

if __name__ == "__main__":
    main()
