import boto3
from boto3 import dynamodb
from fastapi import HTTPException
from core.config import settings
    
dynamodb = boto3.resource('dynamodb', region_name=settings.REGION)
convo_table = dynamodb.Table(settings.DYNAMODB_CONVERSATION_TABLE)
    
async def update_message_to_dynamodb(user_message_checked, message_id, orgid, ndid, ndty, user_id):
    try:
        print("Message id ", message_id)

        convo_table.update_item(
            Key={
                'PK': f"ORG#{orgid}#NODE#{ndty}#{ndid}#USER#{user_id}",
                'SK': message_id
            },
            UpdateExpression="set msg = :msg",
            ExpressionAttributeValues={
                ':msg': user_message_checked
            },
            ReturnValues="UPDATED_NEW"
        )
        print("Updated")
        return True
    
    except Exception as e:
        print(f"Error updating message to DynamoDB: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))