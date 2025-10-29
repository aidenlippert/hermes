"""
Organization & ACL Admin API (minimal)

Endpoints:
- POST /api/v1/orgs                          : create an organization
- POST /api/v1/orgs/{org_id}/members         : add a member (role: member|admin)
- POST /api/v1/orgs/{org_id}/agents/{agent_id}/assign : assign agent to org
- POST /api/v1/a2a/allow/org                 : set org-level allow (source->target)
- POST /api/v1/a2a/allow/agent               : set agent-level allow (source->target)

Auth: JWT required; org operations require org admin
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List, Set, Optional, cast
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.connection import get_db
from backend.database.models import (
    Organization, OrganizationMember, OrganizationRole, Agent,
    A2AOrgAllow, A2AAgentAllow, User
)
from backend.services.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["orgs", "a2a-acl"]) 


class CreateOrgRequest(BaseModel):
    name: str
    domain: Optional[str] = None


@router.post("/orgs")
async def create_org(req: CreateOrgRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Create org
    existing = await db.execute(select(Organization).where(Organization.name == req.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Organization name already exists")

    if req.domain:
        dom = await db.execute(select(Organization).where(Organization.domain == req.domain))
        if dom.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Domain already used by another org")

    org = Organization(name=req.name, domain=req.domain)
    db.add(org)
    await db.flush()

    # Add creator as admin
    membership = OrganizationMember(organization_id=str(org.id), user_id=cast(str, user.id), role=OrganizationRole.ADMIN)
    db.add(membership)
    await db.commit()
    await db.refresh(org)

    return {"id": org.id, "name": org.name, "domain": org.domain}


@router.get("/orgs")
async def list_orgs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List organizations the user is a member of (admin or member)."""
    res = await db.execute(
        select(Organization).join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .where(OrganizationMember.user_id == user.id)
    )
    orgs = res.scalars().all()
    return {"orgs": [{"id": o.id, "name": o.name, "domain": o.domain} for o in orgs]}


class AddMemberRequest(BaseModel):
    user_id: str
    role: Optional[OrganizationRole] = OrganizationRole.MEMBER


async def _require_org_admin(db: AsyncSession, org_id: str, user_id: str):
    res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id,
            OrganizationMember.role == OrganizationRole.ADMIN,
        )
    )
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Admin role required for this organization")


@router.post("/orgs/{org_id}/members")
async def add_member(org_id: str, req: AddMemberRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _require_org_admin(db, org_id, cast(str, user.id))

    # prevent duplicates
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == req.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member of this org")

    member = OrganizationMember(organization_id=str(org_id), user_id=str(req.user_id), role=req.role or OrganizationRole.MEMBER)
    db.add(member)
    await db.commit()
    return {"ok": True}


@router.get("/orgs/{org_id}/members")
async def list_members(org_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    await _require_org_admin(db, org_id, cast(str, user.id))
    res = await db.execute(
        select(OrganizationMember).where(OrganizationMember.organization_id == org_id)
    )
    members = res.scalars().all()
    return {
        "members": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role.value,
                "joined_at": (m.joined_at.isoformat() if getattr(m, "joined_at", None) is not None else None),
            }
            for m in members
        ]
    }


@router.get("/agents")
async def list_agents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> Dict[str, List[Dict[str, Any]]]:
    """List basic agent info for selection in admin UI (limited to agents user owns or orgs they belong to)."""
    # Agents created by user
    q1 = await db.execute(select(Agent).where(Agent.creator_id == user.id))
    user_agents: List[Agent] = list(q1.scalars().all())
    # Agents in user's orgs
    orgs_res = await db.execute(
        select(OrganizationMember.organization_id).where(OrganizationMember.user_id == user.id)
    )
    org_ids = [row[0] for row in orgs_res.all()]
    org_agents: List[Agent] = []
    if org_ids:
        q2 = await db.execute(select(Agent).where(Agent.org_id.in_(org_ids)))
        org_agents = list(q2.scalars().all())
    # Merge unique
    seen: Set[str] = set()
    items: List[Dict[str, Any]] = []
    for a in list(user_agents) + list(org_agents):
        if a.id in seen:
            continue
        seen.add(cast(str, a.id))
        items.append({
            "id": cast(str, a.id),
            "name": a.name,
            "org_id": getattr(a, "org_id", None),
            "creator_id": getattr(a, "creator_id", None),
        })
    return {"agents": items}


@router.post("/orgs/{org_id}/agents/{agent_id}/assign")
async def assign_agent_to_org(org_id: str, agent_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require org admin
    await _require_org_admin(db, org_id, cast(str, user.id))

    # Validate agent exists
    res = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent: Any = res.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    setattr(agent, "org_id", str(org_id))
    await db.commit()
    return {"ok": True}


class SetOrgAllowRequest(BaseModel):
    source_org_id: str
    target_org_id: str
    allowed: bool = True


@router.post("/a2a/allow/org")
async def set_org_allow(req: SetOrgAllowRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Require admin of source org
    await _require_org_admin(db, req.source_org_id, cast(str, user.id))

    existing = await db.execute(
        select(A2AOrgAllow).where(
            A2AOrgAllow.source_org_id == req.source_org_id,
            A2AOrgAllow.target_org_id == req.target_org_id,
        )
    )
    row: Any = existing.scalar_one_or_none()
    if row:
        setattr(row, "allowed", bool(req.allowed))
        setattr(row, "created_by", cast(str, user.id))
    else:
        db.add(A2AOrgAllow(
            source_org_id=req.source_org_id,
            target_org_id=req.target_org_id,
            allowed=req.allowed,
            created_by=cast(str, user.id),
        ))
    await db.commit()
    return {"ok": True}


class SetAgentAllowRequest(BaseModel):
    source_agent_id: str
    target_agent_id: str
    allowed: bool = True


@router.post("/a2a/allow/agent")
async def set_agent_allow(req: SetAgentAllowRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Check source agent exists and ownership/admin
    res = await db.execute(select(Agent).where(Agent.id == req.source_agent_id))
    src: Any = res.scalar_one_or_none()
    if not src:
        raise HTTPException(status_code=404, detail="Source agent not found")

    # Require creator ownership or org admin
    creator_id_val = cast(Optional[str], getattr(src, "creator_id", None))
    if creator_id_val is not None and creator_id_val == cast(str, user.id):
        pass
    elif (org_id_val := cast(Optional[str], getattr(src, "org_id", None))):
        await _require_org_admin(db, org_id_val, cast(str, user.id))
    else:
        raise HTTPException(status_code=403, detail="Not authorized for this agent")

    existing = await db.execute(
        select(A2AAgentAllow).where(
            A2AAgentAllow.source_agent_id == req.source_agent_id,
            A2AAgentAllow.target_agent_id == req.target_agent_id,
        )
    )
    row: Any = existing.scalar_one_or_none()
    if row:
        setattr(row, "allowed", bool(req.allowed))
        setattr(row, "created_by", cast(str, user.id))
    else:
        db.add(A2AAgentAllow(
            source_agent_id=req.source_agent_id,
            target_agent_id=req.target_agent_id,
            allowed=req.allowed,
            created_by=cast(str, user.id),
        ))
    await db.commit()
    return {"ok": True}
