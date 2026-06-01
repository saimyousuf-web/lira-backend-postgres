import boto3
from fastapi import HTTPException
from core.config import settings

cognito = boto3.client(
    "cognito-idp",
    region_name=settings.REGION
)


def find_user(identifier_id: str, identifier_email: str) -> bool:
    try:
        cognito.admin_get_user(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=identifier_id
        )
        return True

    except cognito.exceptions.UserNotFoundException:

        try:
            response = cognito.list_users(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Filter=f'email = "{identifier_email}"',
                Limit=1
            )

            users = response.get("Users", [])

            return len(users) > 0

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )