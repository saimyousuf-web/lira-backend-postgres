from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid

from dependencies.auth import require_permission
from create_departments.schema import CreateDepartmentsRequest, CreateDepartmentsResponse
from models.nodes import Node, NodeType, Org, Dept
from core.db import get_db_session

router = APIRouter()


@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}", response_model=CreateDepartmentsResponse)
async def create_departments(
    ctx_orgid: str,
    ctx_ndid: str,
    ctx_ndty: str,
    payload: CreateDepartmentsRequest,
    auth_data=Depends(require_permission("create_department")),
    db: AsyncSession = Depends(get_db_session),
):
    if len(payload.names) > 12:
        raise HTTPException(
            status_code=400,
            detail="Maximum 12 departments allowed per request"
        )

    user_id = uuid.UUID(auth_data["userId"])
    parent_node_id = uuid.UUID(ctx_ndid)

    # ── 1. Validate parent ORG exists and is active ──────────────────
    org = await db.scalar(
        select(Org).where(
            Org.node_id == parent_node_id,
            Org.is_active == True
        )
    )
    if not org:
        raise HTTPException(status_code=404, detail="Parent ORG not found")

    # ── 2. Fetch DEPT node_type id once ──────────────────────────────
    dept_type = await db.scalar(
        select(NodeType).where(NodeType.type == "DEPT")
    )
    if not dept_type:
        raise HTTPException(status_code=500, detail="DEPT node type not configured")

    # ── 3. Build all rows before opening the transaction ─────────────
    new_nodes = []
    new_depts = []

    for name in payload.names:
        node = Node(node_type_id=dept_type.id)
        dept = Dept(
            node_id=node.id,           # same UUID — class table inheritance
            parent_id=parent_node_id,
            name=name.strip(),
            is_active=True,
            created_by=user_id,
            updated_by=user_id,
        )
        new_nodes.append(node)
        new_depts.append(dept)

    # ── 4. Persist atomically ────────────────────────────────────────
    try:
        async with db.begin():
            # nodes must be inserted before depts (FK constraint)
            db.add_all(new_nodes)
            await db.flush()          # assigns IDs, keeps transaction open

            db.add_all(new_depts)
            await db.flush()          # triggers UniqueConstraint check here

    except IntegrityError as e:
        await db.rollback()
        if "uq_dept_name_per_parent" in str(e.orig):
            raise HTTPException(
                status_code=409,
                detail="One or more department names already exist under this ORG"
            )
        raise HTTPException(status_code=500, detail="Database error")

    return CreateDepartmentsResponse(
        status="success",
        message="All departments created successfully",
        data=[{"name": dept.name, "success": True} for dept in new_depts],
    )