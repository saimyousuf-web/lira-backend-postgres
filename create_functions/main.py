from fastapi import APIRouter, HTTPException, Depends, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import uuid
from dependencies.auth import require_permission
from create_functions.schema import CreateFunctionsRequest, CreateFunctionsResponse
from core.db import get_db_session
from models.nodes import Node, NodeType, Org, Dept, Func

router = APIRouter()


@router.post("/{ctx_orgid}/{ctx_ndid}/{ctx_ndty}", response_model=CreateFunctionsResponse)
async def create_functions(
    ctx_orgid: str = Path(...),
    ctx_ndid: str = Path(...),
    ctx_ndty: str = Path(...),
    payload: CreateFunctionsRequest = Body(...),
    # auth_data = Depends(require_permission("create_function")),
    db: AsyncSession = Depends(get_db_session),
):
    user_id = uuid.UUID("6418e458-50a1-70fe-9d3e-b52f5d2df57c")  # placeholder for testing
    org_id = uuid.UUID(ctx_orgid)
    parent_dept_id = uuid.UUID(payload.department_id)

    if len(payload.names) > 8:
        raise HTTPException(
            status_code=400,
            detail="Maximum 8 functions allowed per request",
        )

    normalized_names = [name.strip() for name in payload.names]

    if len(set(normalized_names)) != len(normalized_names):
        raise HTTPException(
            status_code=409,
            detail="Duplicate function names in the request",
        )

    try:
        # Optional: keep this if you want explicit org existence validation
        org = await db.scalar(
            select(Org).where(
                Org.ndid == org_id,
                Org.isact == True,
            )
        )
        if not org:
            raise HTTPException(
                status_code=404,
                detail="Organization not found or inactive",
            )

        parent_dept = await db.scalar(
            select(Dept).where(
                Dept.ndid == parent_dept_id,
                Dept.orgid == org_id,
                Dept.isact == True,
            )
        )
        if not parent_dept:
            raise HTTPException(
                status_code=404,
                detail="Parent department not found or inactive",
            )

        func_type = await db.scalar(
            select(NodeType).where(NodeType.ty == "FUNC")
        )
        if not func_type:
            raise HTTPException(
                status_code=500,
                detail="FUNC node type not configured",
            )

        new_funcs = []

        for name in normalized_names:
            node = Node(ndtyid=func_type.id)
            db.add(node)
            await db.flush()

            func = Func(
                ndid=node.id,
                orgid=org_id,
                prtndid=parent_dept_id,
                nm=name,
                isact=True,
                crtby=user_id,
                updby=user_id,
            )
            db.add(func)
            new_funcs.append(func)

        await db.commit()

    except IntegrityError as e:
        await db.rollback()
        if "uq_func_name_per_parent" in str(e.orig):
            raise HTTPException(
                status_code=409,
                detail="One or more function names already exist under this department",
            )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid UUID format",
        )

    return CreateFunctionsResponse(
        status="success",
        message="Functions created successfully",
        data=[{"name": func.nm, "success": True} for func in new_funcs],
    )