import boto3
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
# from jose import jwt
from fastapi import HTTPException
from functools import lru_cache
from core.config import settings
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from core.db import get_db_session
from models.lira_access import LiraAccess
from models.nodes import Node, NodeType
from models.nodes import Org, Dept, Func
from shared.exceptions import AuthorizationError


security = HTTPBearer()

COGNITO_POOL_ID = settings.COGNITO_USER_POOL_ID
COGNITO_REGION = settings.REGION
security = HTTPBearer()

dynamodb = boto3.resource('dynamodb', region_name=settings.REGION)
userAccessTable = dynamodb.Table(settings.DYNAMODB_USERS_ACCESS_TABLE_NAME)
role_policies_table = dynamodb.Table(settings.DYNAMODB_LIRA_ROLE_POLICIES_TABLE_NAME)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials
    user = verify_jwt(token)
    return user


@lru_cache()
def get_cognito_jwks():
    url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}/.well-known/jwks.json"
    return requests.get(url).json()["keys"]

def verify_jwt(token: str):
    try:
        headers = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid JWT header")

    jwks = get_cognito_jwks()
    key = next((k for k in jwks if k["kid"] == headers["kid"]), None)
    if not key:
        raise HTTPException(status_code=401, detail="Public key not found")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


def require_permission(permission: str):
    def checker(
        ctx_orgid: str,
        ctx_ndid: str,
        ctx_ndty: str,
        db: AsyncSession = Depends(get_db_session),
        current_user=Depends(get_current_user),
    ):
        user_id = current_user["sub"]
        print(
            f"Checking permission for user {user_id} "
            f"on org={ctx_orgid}, node={ctx_ndty}#{ctx_ndid} "
            f"for permission={permission}"
        )

        user_data = authorize_user(
            db,
            user_id,
            ctx_orgid,
            ctx_ndid,
            ctx_ndty,
        )

        role_id = user_data["roleId"]

        if not authorize_role_policies(
            ctx_orgid,
            ctx_ndid,
            ctx_ndty,
            role_id,
            permission,
        ):
            raise AuthorizationError("Permission denied")

        return user_data

    return checker

def validate_org_membership(
    db: Session,
    org_id: str,
    node_id: str,
    node_type: str,
):

    if node_type == "ORG":
        org = (
            db.query(Org)
            .filter(Org.node_id == node_id)
            .first()
        )

        if not org:
            return False

        return str(org.node_id) == str(org_id)


    if node_type == "DEPT":
        dept = (
            db.query(Dept)
            .filter(Dept.node_id == node_id)
            .first()
        )

        if not dept:
            return False

        return str(dept.parent_id) == str(org_id)

    if node_type == "FUNC":
        func = (
            db.query(Func)
            .filter(Func.node_id == node_id)
            .first()
        )

        if not func:
            return False

        dept = (
            db.query(Dept)
            .filter(Dept.node_id == func.parent_id)
            .first()
        )

        if not dept:
            return False

        return str(dept.parent_id) == str(org_id)

    return False

def authorize_user(
    db: Session,
    user_id: str,
    org_id: str,
    node_id: str,
    node_type: str,
):
    print(
        f"Authorizing user={user_id} "
        f"org={org_id} node={node_id} type={node_type}"
    )

    try:
        if not validate_org_membership(
            db,
            org_id,
            node_id,
            node_type,
        ):
            raise AuthorizationError(
                "Node does not belong to org"
            )

        access = (
            db.query(LiraAccess)
            .join(Node, Node.id == LiraAccess.ndid)
            .join(NodeType, NodeType.id == Node.node_type_id)
            .filter(
                LiraAccess.uid == user_id,
                LiraAccess.ndid == node_id,
                NodeType.type == node_type,
            )
            .first()
        )

        if not access:
            raise AuthorizationError(
                "User not member of this node"
            )

        if not access.is_active:
            raise AuthorizationError(
                "User access is inactive"
            )

        if not access.is_approved:
            raise AuthorizationError(
                "User not approved"
            )

        return {
            "userId": user_id,
            "orgId": org_id,
            "nodeId": node_id,
            "roleId": access.rlid,
        }

    except AuthorizationError:
        raise

    except Exception as e:
        raise Exception(f"Database error: {str(e)}")

# ROLE_CACHE = {}

def authorize_role_policies(orgid: str, ndid: str, ndty: str, role_id: str, permission: str):
    # cache_key = f"{orgid}#{role}"

    # if cache_key not in ROLE_CACHE:
    #     response = role_policies_table.get_item(
    #         Key={
    #             "PK": f"ORG#{orgid}",
    #             "SK": f"ROLE#{role}"
    #         }
    #     )
    #     ROLE_CACHE[cache_key] = response.get("Item", {}).get("permissions", [])

    # permissions = ROLE_CACHE[cache_key]

    # if permission not in permissions:
    #     raise AuthorizationError("Permission denied")
    
    if role_id and permission and orgid and ndid and ndty:
        return True
    
    else:
        raise AuthorizationError("user not authorized for this action")




# def get_role_permissions(orgid: str, role_id: str):
#     print(f"Fetching permissions for org={orgid}, role={role_id}")

#     response = role_policies_table.query(
#         KeyConditionExpression=Key("PK").eq(f"ORG#{orgid}") & Key("SK").eq(f"ROLE#{role_id}"),
#         ProjectionExpression="#perm",
#         ExpressionAttributeNames={"#perm": "permissions"}
#     )

#     items = response.get("Items", [])

#     if not items:
#         return []   

#     permissions = items[0].get("permissions", [])

#     return permissions