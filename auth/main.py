# import requests
# from functools import lru_cache

# from fastapi import Depends, HTTPException
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from jose import jwt

# from core.config import settings

# security = HTTPBearer()

# COGNITO_POOL_ID = settings.COGNITO_USER_POOL_ID
# COGNITO_REGION = settings.REGION


# @lru_cache()
# def get_cognito_jwks():
#     url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}/.well-known/jwks.json"
#     response = requests.get(url, timeout=10)
#     response.raise_for_status()
#     return response.json()["keys"]


# def verify_jwt(token: str):
#     try:
#         headers = jwt.get_unverified_header(token)
#     except Exception:
#         raise HTTPException(status_code=401, detail="Invalid JWT header")

#     jwks = get_cognito_jwks()
#     key = next((k for k in jwks if k["kid"] == headers["kid"]), None)

#     if not key:
#         raise HTTPException(status_code=401, detail="Public key not found")

#     try:
#         payload = jwt.decode(
#             token,
#             key,
#             algorithms=["RS256"],
#             options={"verify_aud": False},
#         )
#         return payload
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security),
# ):
#     if not credentials:
#         raise HTTPException(status_code=401, detail="Authorization header missing")

#     token = credentials.credentials
#     print("TOKEN => ",token)
#     return verify_jwt(token)