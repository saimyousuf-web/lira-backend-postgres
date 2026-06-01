from fastapi import APIRouter, Body, HTTPException, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid

from dependencies.auth import require_permission
from create_departments.schema import (
    CreateDepartmentsRequest,
    CreateDepartmentsResponse,
)
from models.nodes import Node, NodeType, Org, Dept
from core.db import get_db_session

router = APIRouter()


@router.post(
    "/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}",
    response_model=CreateDepartmentsResponse,
)
async def create_departments(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    payload: CreateDepartmentsRequest = Body(...),
    # auth_data=Depends(require_permission("create_department")),
    db: AsyncSession = Depends(get_db_session),
):
    if len(payload.names) > 12:
        raise HTTPException(
            status_code=400,
            detail="Maximum 12 departments allowed per request",
        )

    # user_id = uuid.UUID(auth_data["userId"])
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")  # placeholder for testing

    try:
        parent_node_id = uuid.UUID(ctx_ndid)

        org = await db.scalar(
            select(Org).where(
                Org.node_id == parent_node_id,
                Org.is_active == True,
            )
        )

        if not org:
            raise HTTPException(
                status_code=404,
                detail="Parent organization not found or inactive",
            )

        dept_type = await db.scalar(
            select(NodeType).where(NodeType.type == "DEPT")
        )

        if not dept_type:
            raise HTTPException(
                status_code=500,
                detail="DEPT node type not configured",
            )

        new_depts = []

        for name in payload.names:
            node = Node(
                node_type_id=dept_type.id,
            )

            db.add(node)
            await db.flush() 

            dept = Dept(
                node_id=node.id,
                org_id=org.node_id,
                parent_id=parent_node_id,  ## same as org.node_id 
                name=name.strip(),
                is_active=True,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(dept)

            new_depts.append(dept)

        await db.commit()

    except IntegrityError as e:
        await db.rollback()

        if "uq_dept_name_per_parent" in str(e.orig):
            raise HTTPException(
                status_code=409,
                detail="One or more department names already exist under this ORG",
            )

        raise HTTPException(
            status_code=500,
            detail="Database error",
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID format",
        )

    return CreateDepartmentsResponse(
        status="success",
        message="All departments created successfully",
        data=[
            {
                "name": dept.name,
                "success": True,
            }
            for dept in new_depts
        ],
    )