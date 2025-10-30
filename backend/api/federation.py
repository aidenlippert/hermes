"""
Federation routing (P1) for A2A (agent@domain addressing).

Implements:
- Health endpoint
- Inbound inbox with optional HMAC signature verification
- Persistence into A2AConversation/A2AMessage + delivery receipt
- Best-effort WS fanout to local agent if online

Signature (optional): If FEDERATION_SHARED_SECRET is set, require request
header 'X-Hub-Signature-256' with value 'sha256=<hex-digest>' where digest is
HMAC-SHA256 of the raw request body using the shared secret. If not set, accept
unsigned requests (dev mode) and log a warning.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any, Dict, Optional, cast
import os
import logging
import hmac
import hashlib
from datetime import datetime, timezone

from backend.database.connection import get_db
from backend.websocket.manager import manager
from backend.services.federation_client import FederationClient
from backend.database.models import (
    Agent,
    AgentStatus,
    A2AConversation,
    A2AMessage,
    A2AMessageReceipt,
    MessageType,
    ConversationStatus,
    Organization,
    A2AOrgAllow,
    A2AAgentAllow,
    FederationContact,
    A2APolicyCache,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/a2a/federation", tags=["a2a-federation"]) 


def _get_domain() -> str:
    return os.getenv("FEDERATION_DOMAIN", os.getenv("PUBLIC_DOMAIN", "localhost"))


def _fmt_dt(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _verify_hmac_signature(raw_body: bytes, header_value: Optional[str]) -> bool:
    """Validate HMAC signature if required.

    Rules:
    - If FEDERATION_HMAC_REQUIRED=true (default unless HERMES_ENV is dev), a valid
      FEDERATION_SHARED_SECRET must be set and request must include a valid header.
    - If not required, accept unsigned and log a warning.
    """
    env = (os.getenv("HERMES_ENV") or os.getenv("ENV") or "").lower()
    required = (os.getenv("FEDERATION_HMAC_REQUIRED", "true").lower() == "true") and env not in ("dev", "development", "local")
    secret = os.getenv("FEDERATION_SHARED_SECRET")
    if not required:
        if not secret:
            logger.warning("Federation HMAC not required and no secret configured (dev mode)")
            return True
        # If optional and secret set, validate when header present
        if not header_value:
            logger.warning("Federation HMAC optional: missing signature header accepted")
            return True
    else:
        # Required: must have secret and header
        if not secret or not header_value:
            return False

    if not header_value or not header_value.startswith("sha256="):
        return False

    sent_hex = header_value.split("=", 1)[1].strip()
    mac = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256)
    expected_hex = mac.hexdigest()
    try:
        return hmac.compare_digest(sent_hex, expected_hex)
    except Exception:
        return False


async def _get_or_create_stub_remote_agent(db: AsyncSession, agent_at_domain: str) -> Agent:
    """Create a local stub Agent row for a remote agent identity if not present.

    Uses the unique name constraint; sets INACTIVE status and category 'federated'.
    """
    # Prefer exact name match; name is unique
    res = await db.execute(select(Agent).where(Agent.name == agent_at_domain))
    existing = res.scalar_one_or_none()
    if existing:
        return existing

    # Create stub
    stub = Agent(
        name=agent_at_domain,
        description=f"Federated agent stub for {agent_at_domain}",
        endpoint="",  # unknown for remote
        capabilities=[],
        category="federated",
        status=AgentStatus.INACTIVE,
        is_free=True,
    )
    db.add(stub)
    await db.flush()
    return stub


async def _get_or_create_conversation(db: AsyncSession, initiator_id: str, target_id: str) -> A2AConversation:
    res = await db.execute(
        select(A2AConversation).where(
            A2AConversation.initiator_id == initiator_id,
            A2AConversation.target_id == target_id,
            A2AConversation.status == ConversationStatus.ACTIVE,
        )
    )
    conv = res.scalar_one_or_none()
    if conv:
        return conv
    conv = A2AConversation(
        initiator_id=initiator_id,
        target_id=target_id,
        topic="federated",
        status=ConversationStatus.ACTIVE,
        context_data={},
    )
    db.add(conv)
    await db.flush()
    return conv


async def _get_or_create_org_for_domain(db: AsyncSession, domain: str) -> Organization:
    res = await db.execute(select(Organization).where(Organization.domain == domain))
    org = res.scalar_one_or_none()
    if org:
        return org
    # Fallback: try name match too
    res2 = await db.execute(select(Organization).where(Organization.name == domain))
    org2 = res2.scalar_one_or_none()
    if org2:
        return org2
    org = Organization(name=domain, domain=domain)
    db.add(org)
    await db.flush()
    return org


@router.get("/health")
async def fed_health() -> Dict[str, Any]:
    """Federation health and metadata."""
    return {
        "status": "ok",
        "domain": _get_domain(),
        "signing": {
            "enabled": bool(os.getenv("FEDERATION_PUBLIC_KEY")),
            "key_id": os.getenv("FEDERATION_KEY_ID") or None,
            "hmac_required": (os.getenv("FEDERATION_HMAC_REQUIRED", "true").lower() == "true"),
        },
        "inbox": "POST /api/v1/a2a/federation/inbox",
    }


@router.post("/inbox")
async def inbound_inbox(req: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Accept inbound inter-hub messages.

    Expected JSON envelope (subject to change as spec evolves):
    {
      "id": "<uuid>",
      "from": "agent@remote-domain",
      "to": "agent@local-domain",
      "type": "message",
      "payload": { ... },
      "timestamp": "ISO8601",
      "signature": {
        "key_id": "...",
        "alg": "ed25519",
        "sig": "base64..."
      }
    }
    """
    # Read raw body for signature verification first
    raw_body = await req.body()
    sig_header = req.headers.get("X-Hub-Signature-256") or req.headers.get("X-Signature")
    if not _verify_hmac_signature(raw_body, sig_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse JSON
    try:
        data = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Basic validation
    to_addr: str = data.get("to") or ""
    if "@" not in to_addr:
        raise HTTPException(status_code=400, detail="Invalid 'to' address")

    to_agent, to_domain = to_addr.split("@", 1)
    local_domain = _get_domain()
    if to_domain and local_domain and to_domain != local_domain:
        # Not for us
        raise HTTPException(status_code=404, detail="Domain mismatch for recipient")

    # Look up local target agent by name
    res = await db.execute(select(Agent).where(Agent.name == to_agent))
    local_agent = res.scalar_one_or_none()
    if not local_agent:
        raise HTTPException(status_code=404, detail="Target agent not found")

    # Prepare remote stub agent and its organization for sender
    from_addr: str = data.get("from") or ""
    if "@" not in from_addr:
        raise HTTPException(status_code=400, detail="Invalid 'from' address")
    from_agent_name, from_domain = from_addr.split("@", 1)
    remote_agent = await _get_or_create_stub_remote_agent(db, from_addr)
    # Ensure remote agent linked to its domain org
    remote_org: Optional[Organization] = None
    try:
        remote_org = await _get_or_create_org_for_domain(db, from_domain)
        if getattr(remote_agent, "org_id", None) != str(remote_org.id):
            setattr(remote_agent, "org_id", str(remote_org.id))
            await db.flush()
    except Exception as e:
        logger.warning(f"Failed linking remote agent to org {from_domain}: {e}")

    # Upsert federation contact
    try:
        fc_res = await db.execute(select(FederationContact).where(FederationContact.remote_agent_at == from_addr))
        fc = fc_res.scalar_one_or_none()
        if not fc:
            fc = FederationContact(
                remote_agent_at=from_addr,
                remote_agent_name=from_agent_name,
                remote_domain=from_domain,
                remote_org_id=str(getattr(remote_org, 'id')) if remote_org else None,
                local_agent_id=str(getattr(local_agent, 'id')) if local_agent else None,
                local_org_id=str(getattr(local_agent, 'org_id')) if getattr(local_agent, 'org_id', None) else None,
            )
            db.add(fc)
        setattr(fc, "last_seen_at", datetime.now(timezone.utc))
        await db.flush()
    except Exception as e:
        logger.warning(f"Failed upserting federation contact for {from_addr}: {e}")

    # Idempotency: use provided 'id' if present
    envelope_id = data.get("id") or None

    # Enforce basic federation ACLs (org-level first, then agent-level)
    def _default_allow() -> bool:
        return (os.getenv("FEDERATION_DEFAULT_ALLOW", "true").lower() == "true")

    allow = _default_allow()
    try:
        # org-level check if both orgs present
        target_org_id = getattr(local_agent, "org_id", None)
        source_org_id = getattr(remote_agent, "org_id", None)
        if source_org_id and target_org_id:
            res = await db.execute(
                select(A2AOrgAllow).where(
                    A2AOrgAllow.source_org_id == str(source_org_id),
                    A2AOrgAllow.target_org_id == str(target_org_id),
                )
            )
            row = res.scalar_one_or_none()
            if row is not None:
                allow = bool(getattr(row, "allowed", False))

        # agent-level check overrides if rule exists
        res2 = await db.execute(
            select(A2AAgentAllow).where(
                A2AAgentAllow.source_agent_id == str(remote_agent.id),
                A2AAgentAllow.target_agent_id == str(local_agent.id),
            )
        )
        row2 = res2.scalar_one_or_none()
        if row2 is not None:
            allow = bool(getattr(row2, "allowed", False))
        # Write policy cache rows (best effort)
        try:
            pc_org = A2APolicyCache(
                source_org_id=str(source_org_id) if source_org_id else None,
                target_org_id=str(target_org_id) if target_org_id else None,
                source_agent_id=None,
                target_agent_id=None,
                allowed=allow,
            )
            db.add(pc_org)
        except Exception:
            pass

    except Exception as e:
        logger.warning(f"ACL evaluation failed, using default: {e}")

    if not allow:
        raise HTTPException(status_code=403, detail="Federation ACL denied")

    # Upsert conversation and persist message
    conv = await _get_or_create_conversation(db, initiator_id=str(remote_agent.id), target_id=str(local_agent.id))

    # Dedupe on (idempotency_key, from_agent)
    if envelope_id:
        existing_msg_q = await db.execute(
            select(A2AMessage).where(
                A2AMessage.conversation_id == conv.id,
                A2AMessage.idempotency_key == envelope_id,
                A2AMessage.from_agent_id == remote_agent.id,
            )
        )
        if existing_msg_q.scalar_one_or_none():
            return {"status": "duplicate", "conversation_id": conv.id}

    msg_type_str = (data.get("type") or "notification").lower()
    try:
        msg_type = MessageType(msg_type_str)  # may raise
    except Exception:
        msg_type = MessageType.NOTIFICATION

    payload = cast(Dict[str, Any], data.get("payload") or {})
    a2a_msg = A2AMessage(
        conversation_id=str(conv.id),
        from_agent_id=str(remote_agent.id),
        to_agent_id=str(local_agent.id),
        message_type=msg_type,
        content=payload,
        requires_response=bool(data.get("requires_response", False)),
        idempotency_key=envelope_id,
    )
    db.add(a2a_msg)
    await db.flush()

    # Create delivery receipt skeleton
    receipt = A2AMessageReceipt(
        message_id=str(a2a_msg.id),
        agent_id=str(local_agent.id),
        delivery_attempts=1,
        last_attempt_at=datetime.now(timezone.utc),
    )
    # Try best-effort push via WebSocket to local agent
    delivered = False
    try:
        await manager.send_to_agent(str(local_agent.id), {
            "type": "a2a_federated_message",
            "from": from_addr,
            "payload": payload,
            "id": envelope_id or str(a2a_msg.id),
            "timestamp": data.get("timestamp"),
            "conversation_id": conv.id,
        })
        delivered = True
        setattr(receipt, "delivered_at", datetime.now(timezone.utc))
    except Exception as e:
        logger.warning(f"Federation push failed for {to_agent}@{to_domain}: {e}")

    db.add(receipt)
    await db.commit()

    # Best-effort: send acknowledgement back to sender hub
    try:
        client = FederationClient()
        if from_domain:
            await client.ack(to_domain=from_domain, message_id=(envelope_id or str(a2a_msg.id)))
    except Exception as e:
        logger.warning(f"Failed sending federation ack to {from_domain}: {e}")

    return {
        "status": "accepted",
        "domain": local_domain,
        "delivered": delivered,
        "conversation_id": conv.id,
        "message_id": a2a_msg.id,
        "receipt_id": receipt.id,
    }


# ================================
# Address Book & Policy Cache APIs
# ================================

@router.get("/contacts")
async def list_contacts(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    res = await db.execute(select(FederationContact))
    rows = res.scalars().all()
    return {
        "contacts": [
            {
                "id": r.id,
                "remote_agent_at": r.remote_agent_at,
                "remote_agent_name": r.remote_agent_name,
                "remote_domain": r.remote_domain,
                "remote_org_id": r.remote_org_id,
                "local_agent_id": r.local_agent_id,
                "local_org_id": r.local_org_id,
                "last_seen_at": _fmt_dt(getattr(r, "last_seen_at", None)),
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/contacts")
async def upsert_contact(body: Dict[str, Any], db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Create or update a federation contact mapping.

    Body requires remote_agent_at; optional fields to link local agent/org.
    """
    ra = body.get("remote_agent_at")
    if not ra:
        raise HTTPException(status_code=400, detail="remote_agent_at required")
    res = await db.execute(select(FederationContact).where(FederationContact.remote_agent_at == ra))
    row = res.scalar_one_or_none()
    if not row:
        row = FederationContact(remote_agent_at=ra)
        db.add(row)
        await db.flush()
    for k in ("remote_agent_name", "remote_domain", "remote_org_id", "local_agent_id", "local_org_id"):
        if k in body:
            setattr(row, k, body[k])
    await db.commit()
    return {"id": row.id}


@router.get("/policy_cache")
async def list_policy_cache(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    res = await db.execute(select(A2APolicyCache))
    rows = res.scalars().all()
    return {
        "entries": [
            {
                "id": r.id,
                "source_org_id": r.source_org_id,
                "target_org_id": r.target_org_id,
                "source_agent_id": r.source_agent_id,
                "target_agent_id": r.target_agent_id,
                "allowed": bool(r.allowed),
                "evaluated_at": _fmt_dt(getattr(r, "evaluated_at", None)),
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/ack")
async def inbound_ack(req: Request, db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Inbound acknowledgement from a remote hub.

    Body: {"message_id": "<id>"}
    Effect: set A2AMessageReceipt.acked_at for rows with message_id.
    """
    raw_body = await req.body()
    sig_header = req.headers.get("X-Hub-Signature-256") or req.headers.get("X-Signature")
    if not _verify_hmac_signature(raw_body, sig_header):
        raise HTTPException(status_code=401, detail="Invalid signature")
    try:
        data = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    message_id = data.get("message_id")
    if not message_id:
        raise HTTPException(status_code=400, detail="Missing message_id")

    # Update any receipts for this message
    from sqlalchemy import update
    await db.execute(
        update(A2AMessageReceipt)
        .where(A2AMessageReceipt.message_id == message_id)
        .values(acked_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"ok": True, "message_id": message_id}
