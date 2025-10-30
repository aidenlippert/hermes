"""
Federation inbox smoke test (local).

Run with optional env:
  set FEDERATION_SHARED_SECRET=change_me
  set FEDERATION_DOMAIN=localhost

Then:
  python scripts/federation_inbox_smoke.py
"""
import os
import time
import json
import uuid
import hmac
import hashlib
import requests

BASE = os.getenv("HERMES_BASE_URL", "http://127.0.0.1:8000")
TARGET_AGENT = os.getenv("FED_TARGET_AGENT", "FlightBooker")
TARGET_DOMAIN = os.getenv("FED_TARGET_DOMAIN", os.getenv("FEDERATION_DOMAIN", "localhost"))
SECRET = os.getenv("FEDERATION_SHARED_SECRET")

body = {
    "id": str(uuid.uuid4()),
    "from": "remoteAgent@remote.example",
    "to": f"{TARGET_AGENT}@{TARGET_DOMAIN}",
    "type": "notification",
    "payload": {"hello": "from remote"},
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
headers = {"Content-Type": "application/json"}
if SECRET:
    sig = "sha256=" + hmac.new(SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    headers["X-Hub-Signature-256"] = sig

r = requests.post(f"{BASE}/api/v1/a2a/federation/inbox", data=raw, headers=headers)
print(r.status_code)
print(r.text)

# Verify contact and policy cache endpoints (best-effort)
try:
  rc = requests.get(f"{BASE}/api/v1/a2a/federation/contacts", timeout=5)
  print("contacts:", rc.status_code, rc.json().get("total"))
except Exception as e:
  print("contacts check failed:", e)
try:
  rp = requests.get(f"{BASE}/api/v1/a2a/federation/policy_cache", timeout=5)
  print("policy_cache:", rp.status_code, rp.json().get("total"))
except Exception as e:
  print("policy cache check failed:", e)
