"""
Agent-to-Agent (A2A) Collaboration API

Endpoints for agent presence (WebSocket), conversations, and messages.
Auth:
- Agent WebSocket and agent-sent messages are authenticated via API key (?api_key=...)
- User-initiated conversations/messages use JWT like the rest of the API

Minimal viable substrate to enable agent discovery and infinite communication.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any, cast, List
from datetime import datetime, timezone
import os
import logging

from backend.database.connection import get_db
from backend.database.models import Agent, A2AConversation, A2AMessage, MessageType, ConversationStatus, User, OrganizationMember, A2AOrgAllow, A2AAgentAllow, A2AMessageReceipt
from backend.services.rate_limiter import check_and_increment, rl_key_for_api_key, rl_key_for_org
from backend.services.auth import AuthService, get_current_user
from backend.services.auth import AuthService, get_current_user
from backend.websocket.manager import manager
from backend.services.federation_client import FederationClient

router = APIRouter(prefix="/api/v1/a2a", tags=["a2a"])
logger = logging.getLogger(__name__)


def _fmt_dt(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None

# Cache env domain to avoid repeated lookups and satisfy type checkers
ENV_PUBLIC_DOMAIN = os.getenv("FEDERATION_DOMAIN", os.getenv("PUBLIC_DOMAIN", "localhost"))


async def _is_a2a_allowed(db: AsyncSession, from_agent: Agent, to_agent: Agent) -> bool:
    """Enforce ACL: allow if same org; else require agent-level allow, else org-level allow."""
    from sqlalchemy import select
    # Fetch org ids (may be None)
    from_org = getattr(from_agent, "org_id", None)
    to_org = getattr(to_agent, "org_id", None)

    if from_org is not None and to_org is not None and str(from_org) == str(to_org):
        return True

    # Agent-level allow (unidirectional)
    res = await db.execute(
        select(A2AAgentAllow).where(
            A2AAgentAllow.source_agent_id == str(getattr(from_agent, "id")),
            A2AAgentAllow.target_agent_id == str(getattr(to_agent, "id")),
            A2AAgentAllow.allowed.is_(True),
        )
    )
    if res.scalar_one_or_none():
        return True

    # Org-level allow (if both orgs known)
    if from_org and to_org:
        res2 = await db.execute(
            select(A2AOrgAllow).where(
                A2AOrgAllow.source_org_id == str(from_org),
                A2AOrgAllow.target_org_id == str(to_org),
                A2AOrgAllow.allowed.is_(True),
            )
        )
        if res2.scalar_one_or_none():
            return True

    return False


@router.post("/conversations")
async def create_conversation(
    initiator_id: str,
    target_id: str,
    topic: str,
    context: Optional[Dict[str, Any]] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
)-> Dict[str, Any]:
    """Create an agent-to-agent conversation (user mediated)."""

    # Validate agents exist
    res_i = await db.execute(select(Agent).where(Agent.id == initiator_id))
    initiator = res_i.scalar_one_or_none()
    if not initiator:
        raise HTTPException(status_code=404, detail=f"Agent not found: {initiator_id}")
    res_t = await db.execute(select(Agent).where(Agent.id == target_id))
    target = res_t.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail=f"Agent not found: {target_id}")

    # Enforce ACLs
    if not await _is_a2a_allowed(db, initiator, target):
        raise HTTPException(status_code=403, detail="A2A not allowed by ACLs")

    conv = A2AConversation(
        initiator_id=initiator_id,
        target_id=target_id,
        topic=topic,
        status=ConversationStatus.ACTIVE,
        context_data=context or {},
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return {"id": conv.id, "status": conv.status.value}


@router.post("/messages")
async def send_message(
    # Required first (Python requires non-default params before defaults)
    from_agent_id: str,
    message_type: MessageType,
    content: Dict[str, Any],
    # Optional params
    conversation_id: Optional[str] = None,
    to_agent_id: Optional[str] = None,
    to_address: Optional[str] = Query(None, description="Federated address agent@domain for outbound federation"),
    requires_response: bool = False,
    idempotency_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    authorization: Optional[str] = Query(None, description="Bearer token for users"),
    api_key: Optional[str] = Query(None, description="API key for agents"),
)-> Dict[str, Any]:
    """Send a message between agents within a conversation.

    AuthN:
    - Agents: provide ?api_key=... (validated and must own the from_agent_id)
    - Users: provide Authorization: Bearer <JWT>
    """

    # Validate or create conversation (allows federated flow to create on the fly)
    conv: Optional[A2AConversation] = None
    if conversation_id:
        res = await db.execute(select(A2AConversation).where(A2AConversation.id == conversation_id))
        conv = res.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Validate agents
    r_from = await db.execute(select(Agent).where(Agent.id == from_agent_id))
    from_agent = r_from.scalar_one_or_none()
    if not from_agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {from_agent_id}")
    # Determine local vs federated target
    to_agent = None
    federated_out = False
    federated_to_name = None
    federated_to_domain = None
    if to_address and "@" in to_address:
        federated_out = True
        federated_to_name, federated_to_domain = to_address.split("@", 1)
    elif to_agent_id:
        r_to = await db.execute(select(Agent).where(Agent.id == to_agent_id))
        to_agent = r_to.scalar_one_or_none()
        if not to_agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {to_agent_id}")
    else:
        raise HTTPException(status_code=400, detail="Specify either to_agent_id (local) or to_address (federated)")

    # Authenticate: either API key (agent) or JWT (user)
    authed_user: Optional[User] = None
    if api_key:
        authed_user = await AuthService.validate_api_key(db, api_key)
        if not authed_user:
            raise HTTPException(status_code=401, detail="Invalid API key")
        # Optional: enforce ownership - user must be creator of from_agent_id if set
        res = await db.execute(select(Agent).where(Agent.id == from_agent_id))
        agent = res.scalar_one_or_none()
        if agent:
            creator_val = cast(Optional[str], getattr(agent, "creator_id", None))
            if creator_val is not None and creator_val != authed_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to send from this agent")

        # Rate limits per API key and per org (if agent has org)
        api_key_row = await AuthService.get_api_key(db, api_key)
        if api_key_row:
            limit = int(getattr(api_key_row, "rate_limit", 100) or 100)
            ok = await check_and_increment(rl_key_for_api_key(str(api_key_row.id)), limit, window_seconds=60)
            if not ok:
                raise HTTPException(status_code=429, detail="API key rate limit exceeded")
        from_org_id = cast(Optional[str], getattr(agent, "org_id", None)) if agent else None
        if from_org_id:
            import os
            org_limit = int(os.getenv("A2A_ORG_RATE_LIMIT_PER_MIN", "600"))
            ok2 = await check_and_increment(rl_key_for_org(str(from_org_id)), org_limit, window_seconds=60)
            if not ok2:
                raise HTTPException(status_code=429, detail="Org rate limit exceeded")
    else:
        # Try JWT from Authorization header value ("Bearer ...")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            payload_any: Any = AuthService.decode_token(token)  # type: ignore
            payload = cast(Dict[str, Any], payload_any or {})
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")
            sub = cast(Optional[str], payload.get("sub"))
            if not sub:
                raise HTTPException(status_code=401, detail="Invalid token payload")
        else:
            raise HTTPException(status_code=401, detail="Missing auth (api_key or Bearer token)")

    # Enforce ACLs for local delivery only (inbound federation enforces on the receiver side)
    if not federated_out:
        if not await _is_a2a_allowed(db, from_agent, to_agent):
            raise HTTPException(status_code=403, detail="A2A not allowed by ACLs")

    # Idempotency: return existing if idempotency_key matches prior from same sender
    if idempotency_key:
        prev_q = await db.execute(
            select(A2AMessage).where(
                A2AMessage.from_agent_id == from_agent_id,
                A2AMessage.idempotency_key == idempotency_key,
            )
        )
        prev = prev_q.scalar_one_or_none()
        if prev:
            return {"id": prev.id, "status": "duplicate", "message": "Idempotent replay"}

    # Helper to persist message and (optionally) create conversation
    async def _persist_message(_to_agent_id: str) -> A2AMessage:
        nonlocal conv, conversation_id
        if not conv:
            # Create conversation on the fly
            conv = A2AConversation(
                initiator_id=from_agent_id,
                target_id=_to_agent_id,
                topic="a2a",
                status=ConversationStatus.ACTIVE,
                context_data={},
            )
            db.add(conv)
            await db.flush()
            conversation_id = cast(str, conv.id)
        msg = A2AMessage(
            conversation_id=conversation_id,  # type: ignore[arg-type]
            from_agent_id=from_agent_id,
            to_agent_id=_to_agent_id,
            message_type=message_type,
            content=content,
            requires_response=requires_response,
            idempotency_key=idempotency_key,
        )
        db.add(msg)
        await db.commit()
        await db.refresh(msg)
        return msg

    if not federated_out:
        # Local delivery path
        msg = await _persist_message(cast(str, to_agent_id))
        # Create receipt row for recipient
        receipt = A2AMessageReceipt(
            message_id=msg.id,
            agent_id=cast(str, to_agent_id),
            delivery_attempts=0,
        )
        db.add(receipt)
        await db.commit()

        # Push over agent channel if recipient online
        await manager.send_to_agent(cast(str, to_agent_id), {
            "type": "a2a_message",
            "conversation_id": conversation_id,
            "from_agent_id": from_agent_id,
            "message_type": message_type.value,
            "content": content,
            "requires_response": requires_response,
        })

        # Mark delivery attempt and timestamp (best-effort)
        setattr(receipt, "delivery_attempts", int((getattr(receipt, "delivery_attempts", 0) or 0)) + 1)
        ts = datetime.now(timezone.utc)
        setattr(receipt, "last_attempt_at", ts)
        setattr(receipt, "delivered_at", ts)
        await db.commit()

        return {"id": msg.id, "status": "queued", "conversation_id": conversation_id}
    else:
        # Federated outbound path
        # Create a stub remote agent record by name "name@domain" for local tracking
        remote_name = f"{federated_to_name}@{federated_to_domain}"
        # Find or create stub agent by name
        r_stub = await db.execute(select(Agent).where(Agent.name == remote_name))
        stub = r_stub.scalar_one_or_none()
        if not stub:
            stub = Agent(name=remote_name, description=f"Federated agent {remote_name}", endpoint="", capabilities=[], category="federated")
            db.add(stub)
            await db.flush()
        # Persist message locally against stub remote agent
        msg = await _persist_message(cast(str, getattr(stub, "id")))
        # Create receipt row representing remote delivery/ack lifecycle
        receipt = A2AMessageReceipt(
            message_id=msg.id,
            agent_id=cast(str, getattr(stub, "id")),
            delivery_attempts=0,
        )
        db.add(receipt)
        await db.commit()

        # Attempt federated send
        client = FederationClient()
        # Determine from agent display name
        from_display = None
        if getattr(from_agent, "name", None):
            from_display = f"{getattr(from_agent, 'name')}@" + ENV_PUBLIC_DOMAIN
        try:
            resp = await client.send(
                to_agent=cast(str, federated_to_name),
                to_domain=cast(str, federated_to_domain),
                payload=content,
                msg_type=message_type.value,
                requires_response=requires_response,
                from_agent_name=from_display,
                # Use our local message id as envelope id so remote can ack back
                message_id=cast(str, msg.id),
            )
            status = "sent" if resp.status_code in (200, 202) else f"error:{resp.status_code}"
            if resp.status_code in (200, 202):
                # Best-effort mark delivered_at and attempt count
                setattr(receipt, "delivery_attempts", int((getattr(receipt, "delivery_attempts", 0) or 0)) + 1)
                ts = datetime.now(timezone.utc)
                setattr(receipt, "last_attempt_at", ts)
                setattr(receipt, "delivered_at", ts)
                await db.commit()
        except Exception as e:
            status = f"error:{e}"

        return {"id": msg.id, "status": status, "conversation_id": conversation_id, "federated_to": remote_name}


@router.get("/inbox")
async def get_inbox(
    agent_id: str,
    limit: int = 50,
    api_key: Optional[str] = Query(None, description="API key for agents"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return recent messages for an agent that are not yet acked. Auth via API key."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    authed_user = await AuthService.validate_api_key(db, api_key)
    if not authed_user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Authorization: user must own the agent or be org member
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    creator_val = cast(Optional[str], getattr(agent, "creator_id", None))
    if creator_val is None or creator_val != authed_user.id:
        if getattr(agent, "org_id", None):
            mem = await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.organization_id == agent.org_id,
                    OrganizationMember.user_id == authed_user.id,
                )
            )
            if not mem.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Not authorized for this agent")
        else:
            raise HTTPException(status_code=403, detail="Not authorized for this agent")

    # Fetch unacked receipts
    q = await db.execute(
        select(A2AMessage, A2AMessageReceipt)
        .where(A2AMessageReceipt.agent_id == agent_id)
        .where(A2AMessageReceipt.acked_at.is_(None))
        .where(A2AMessageReceipt.message_id == A2AMessage.id)
        .limit(limit)
    )
    rows = q.all()

    # Mark delivered_at for any rows missing it
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    updated = False
    items: List[Dict[str, Any]] = []
    for (msg, rec) in rows:
        if not rec.delivered_at:
            rec.delivered_at = now
            updated = True
        items.append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "from_agent_id": msg.from_agent_id,
            "to_agent_id": msg.to_agent_id,
            "message_type": msg.message_type.value,
            "content": msg.content,
            "requires_response": bool(msg.requires_response),
            "receipt": {
                "receipt_id": rec.id,
                "delivered_at": _fmt_dt(getattr(rec, "delivered_at", None)),
                "acked_at": _fmt_dt(getattr(rec, "acked_at", None)),
            }
        })
    if updated:
        await db.commit()

    return {"messages": items, "total": len(items)}


@router.post("/ack")
async def ack_message(
    message_id: str,
    agent_id: str,
    api_key: Optional[str] = Query(None, description="API key for agents"),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Mark a message as acknowledged by the recipient agent.

    Auth: either API key (agent) or JWT (user) via Authorization header.
    """
    authed_user: Optional[User] = None
    if api_key:
        authed_user = await AuthService.validate_api_key(db, api_key)
        if not authed_user:
            raise HTTPException(status_code=401, detail="Invalid API key")
    else:
        # Try JWT via Authorization header
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing auth (api_key or Bearer token)")
        token = authorization.replace("Bearer ", "")
        payload_any: Any = AuthService.decode_token(token)  # type: ignore
        payload = cast(Dict[str, Any], payload_any or {})
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        sub = cast(Optional[str], payload.get("sub"))
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        authed_user = await AuthService.get_user_by_id(db, sub)
        if not authed_user:
            raise HTTPException(status_code=401, detail="User not found")

    # Authorization: same check as inbox
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    creator_val = cast(Optional[str], getattr(agent, "creator_id", None))
    authorized = (creator_val is not None and creator_val == authed_user.id)
    if not authorized and getattr(agent, "org_id", None):
        mem = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == agent.org_id,
                OrganizationMember.user_id == authed_user.id,
            )
        )
        authorized = bool(mem.scalar_one_or_none())
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized for this agent")

    # Update receipt
    from sqlalchemy import update
    from datetime import datetime, timezone
    await db.execute(
        update(A2AMessageReceipt)
        .where(A2AMessageReceipt.message_id == message_id)
        .where(A2AMessageReceipt.agent_id == agent_id)
        .values(acked_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"ok": True}


@router.get("/receipts")
async def list_receipts(
    agent_id: str,
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """List recent receipts for an agent (JWT auth)."""
    # Authorization: user must own the agent or be org member
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    creator_val = cast(Optional[str], getattr(agent, "creator_id", None))
    if creator_val is None or creator_val != user.id:
        if getattr(agent, "org_id", None):
            mem = await db.execute(
                select(OrganizationMember).where(
                    OrganizationMember.organization_id == agent.org_id,
                    OrganizationMember.user_id == user.id,
                )
            )
            if not mem.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Not authorized for this agent")
        else:
            raise HTTPException(status_code=403, detail="Not authorized for this agent")

    q = await db.execute(
        select(A2AMessage, A2AMessageReceipt)
        .where(A2AMessageReceipt.agent_id == agent_id)
        .where(A2AMessageReceipt.message_id == A2AMessage.id)
        .order_by(A2AMessageReceipt.created_at.desc())
        .limit(limit)
    )
    rows = q.all()
    items: List[Dict[str, Any]] = []
    for (msg, rec) in rows:
        items.append({
            "message_id": msg.id,
            "conversation_id": msg.conversation_id,
            "from_agent_id": msg.from_agent_id,
            "to_agent_id": msg.to_agent_id,
            "message_type": msg.message_type.value,
            "requires_response": bool(msg.requires_response),
            "receipt_id": rec.id,
            "delivered_at": _fmt_dt(getattr(rec, "delivered_at", None)),
            "acked_at": _fmt_dt(getattr(rec, "acked_at", None)),
        })
    return {"receipts": items, "total": len(items)}


@router.websocket("/ws/agents/{agent_id}")
async def agent_ws(websocket: WebSocket, agent_id: str, api_key: str = Query("")):
    """WebSocket presence channel for agents.

    Connect with: ws://.../api/v1/a2a/ws/agents/{agent_id}?api_key=YOUR_KEY
    """
    # Basic API key validation (associate to a user)
    from backend.database.connection import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        user = await AuthService.validate_api_key(db, api_key)
        if not user:
            await websocket.close(code=1008, reason="Invalid API key")
            return
        # Optional: verify user owns this agent if it has a creator
        res = await db.execute(select(Agent).where(Agent.id == agent_id))
        agent = res.scalar_one_or_none()
        if agent:
            # If creator set, must match
            creator_val2 = cast(Optional[str], getattr(agent, "creator_id", None))
            if creator_val2 is not None and creator_val2 != user.id:
                await websocket.close(code=1008, reason="Not authorized for this agent")
                return
            # If org set, user must be a member
            if getattr(agent, "org_id", None):
                mem = await db.execute(
                    select(OrganizationMember).where(
                        OrganizationMember.organization_id == agent.org_id,
                        OrganizationMember.user_id == user.id,
                    )
                )
                if not mem.scalar_one_or_none():
                    await websocket.close(code=1008, reason="Not a member of the agent's organization")
                    return

    await manager.connect_agent(websocket, agent_id)

    # Send welcome
    await websocket.send_json({
        "type": "connected",
        "agent_id": agent_id,
        "message": "✅ Agent connected"
    })

    try:
        while True:
            data = cast(Dict[str, Any], await websocket.receive_json())
            # Expect messages like {"type":"heartbeat"} or {"type":"ack", "message_id": "..."}
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "heartbeat_ack"})
            else:
                logger.info(f"📨 Agent {agent_id} sent: {data}")
    except WebSocketDisconnect:
        logger.info(f"🤖 Agent disconnected: {agent_id}")
        manager.disconnect_agent(websocket, agent_id)
