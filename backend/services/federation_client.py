"""
Federation outbound client: send signed messages to remote hubs.

Usage:
    from backend.services.federation_client import FederationClient
    client = FederationClient()
    await client.send(
        to_agent="FlightBooker",
        to_domain="remote.example",
        payload={"hello": "world"},
        msg_type="notification",
        requires_response=False,
        from_agent_name="LocalAgent@localhost",
        base_url="https://remote.example"  # remote hub base
    )
"""
from __future__ import annotations

import os
import hmac
import hashlib
import json
from typing import Any, Dict, Optional
import httpx


class FederationClient:
    def __init__(self):
        self.shared_secret = os.getenv("FEDERATION_SHARED_SECRET")
        self.local_domain = os.getenv("FEDERATION_DOMAIN", os.getenv("PUBLIC_DOMAIN", "localhost"))

    def _sign(self, raw_body: bytes) -> Optional[str]:
        if not self.shared_secret:
            return None
        mac = hmac.new(self.shared_secret.encode("utf-8"), raw_body, hashlib.sha256)
        return "sha256=" + mac.hexdigest()

    async def send(
        self,
        *,
        to_agent: str,
        to_domain: str,
        payload: Dict[str, Any],
        msg_type: str = "notification",
        requires_response: bool = False,
        from_agent_name: Optional[str] = None,
        base_url: Optional[str] = None,
        message_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
        """Send a federated message to a remote hub's inbox.

        - base_url: if not provided, constructed as http://{to_domain}
        - from_agent_name: defaults to "unknown@{self.local_domain}"
        - message_id/timestamp: optional overrides
        """
        base = base_url or f"http://{to_domain}"
        from_name = from_agent_name or f"unknown@{self.local_domain}"
        body = {
            "id": message_id,
            "from": from_name,
            "to": f"{to_agent}@{to_domain}",
            "type": msg_type,
            "payload": payload,
            "timestamp": timestamp,
            "requires_response": requires_response,
        }
        # Compact JSON for signature stability
        raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        sig = self._sign(raw)
        if sig:
            headers["X-Hub-Signature-256"] = sig
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(f"{base}/api/v1/a2a/federation/inbox", content=raw, headers=headers)

    async def ack(
        self,
        *,
        to_domain: str,
        message_id: str,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ) -> httpx.Response:
        """Send an acknowledgement to a remote hub for a message previously sent.

        Posts to /api/v1/a2a/federation/ack with body {"message_id": "..."}.
        """
        base = base_url or f"http://{to_domain}"
        body = {"message_id": message_id}
        raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        sig = self._sign(raw)
        if sig:
            headers["X-Hub-Signature-256"] = sig
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.post(f"{base}/api/v1/a2a/federation/ack", content=raw, headers=headers)
