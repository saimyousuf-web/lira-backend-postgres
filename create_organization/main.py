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
    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")  # placeholder for testing
    # user_id = uuid.UUID(auth_data["userId"])
    

    node_type = await db.scalar(
        select(NodeType).where(NodeType.type == "ORG")
    )
    if not node_type:
        raise HTTPException(status_code=500, detail="ORG node type not configured")

    # ── 6. Create nodes + orgs atomically ────────────────────────────
    try:
        node = Node(node_type_id=node_type.id)
        db.add(node)
        await db.flush()                  # resolves node.id before org insert

        org = Org(
            node_id=node.id,
            parent_id=None,               # ORG is always root
            org_id=node.id,               # self-ref since ORG is root
            name=payload.name.strip(),
            is_active=True,
            created_by=user_id,
            updated_by=user_id,
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
            "name": org.name,
        }
    }