from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid
from create_organization.schema import CreateOrganizationRequest, CreateOrganizationResponse
from dependencies.auth import require_permission
from core.db import get_db_session
from models.nodes import Node, NodeType, Org

router = APIRouter()

@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}", response_model=CreateOrganizationResponse)
async def create_organization(
    payload: CreateOrganizationRequest = Body(...),
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    # auth_data=Depends(require_permission("create_organization")),
    db: AsyncSession = Depends(get_db_session),
):
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")  # placeholder for testing
    # user_id = uuid.UUID(auth_data["userId"])
    

    node_type = await db.scalar(
        select(NodeType).where(NodeType.ty == "ORG")
    )
    if not node_type:
        raise HTTPException(status_code=500, detail="ORG node type not configured")

    # ── 6. Create nodes + orgs atomically ────────────────────────────
    try:
        node = Node(nodtyid=node_type.id)
        db.add(node)
        await db.flush()                  # resolves node.id before org insert

        org = Org(
            ndid=node.id,
            prtndid=None,               # ORG is always root
            orgid=node.id,               # self-ref since ORG is root
            nm=payload.name.strip(),
            isact=True,
            crtby=user_id,
            updby=user_id,
        )
        db.add(org)
        await db.flush()

        await db.commit()
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "status": "success",
        "status_code": 201,
        "message": "Organization created successfully",
        "data": {
            "org_id": str(node.id),
            "name": org.nm,
        }
    }