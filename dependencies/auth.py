import boto3
from boto3.dynamodb.conditions import Key, Attr
from fastapi import HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from jose import jwt
from fastapi import HTTPException
from functools import lru_cache
from core.config import settings
from fastapi.security import HTTPBearer
from botocore.exceptions import ClientError

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
        current_user = Depends(get_current_user),
    ):
        user_id = current_user["sub"]
        print(f"Checking permission for user {user_id} on org={ctx_orgid}, node={ctx_ndty}#{ctx_ndid} for permission={permission}")

        user_data = authorize_user(user_id, ctx_orgid, ctx_ndid, ctx_ndty)

        role = user_data.get("role")

        if not authorize_role_policies(ctx_orgid, ctx_ndid, ctx_ndty, role, permission):
            raise AuthorizationError("Permission denied")

        return user_data

    return checker


def authorize_user(userId: str, orgid: str, ndid: str, ndty: str):
    print(f"Authorizing user {userId} for org={orgid}, node={ndty}#{ndid}")
    try:
        response = userAccessTable.get_item(
            Key={
                "PK": f"USER#{userId}",
                "SK": f"ORG#{orgid}#NODE#{ndty}#{ndid}"
            },
            ProjectionExpression="#rl, is_approved, itc",
            ExpressionAttributeNames={"#rl": "role"}
        )

        item = response.get("Item")

        if not item:
            raise AuthorizationError("User not member of this node")


        if not item.get("is_approved"):
            raise AuthorizationError("User not approved")

        if not item.get("role"):
            raise AuthorizationError("User has no role assigned")

        return {
            "userId": userId,
            "role": item["role"],
            "itc": item.get("itc")
        }

    except ClientError as e:
        raise Exception(f"DynamoDB error: {e}")



# ROLE_CACHE = {}

def authorize_role_policies(orgid: str, ndid: str, ndty: str, role: str, permission: str):
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
    
    if role and permission and orgid and ndid and ndty:
        return True
    
    else:
        raise AuthorizationError("user not authorized for this action")




def get_role_permissions(orgid: str, role: str):
    print(f"Fetching permissions for org={orgid}, role={role}")

    response = role_policies_table.query(
        KeyConditionExpression=Key("PK").eq(f"ORG#{orgid}") & Key("SK").eq(f"ROLE#{role}"),
        ProjectionExpression="#perm",
        ExpressionAttributeNames={"#perm": "permissions"}
    )

    items = response.get("Items", [])

    if not items:
        return []   

    permissions = items[0].get("permissions", [])

    return permissions