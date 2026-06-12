from fastapi import APIRouter, HTTPException, Depends, Response
from dependencies.auth import get_current_user
from mangum import Mangum
from pydantic import BaseModel
from typing import Optional
import uuid
import boto3
import json
from botocore.exceptions import ClientError

router = APIRouter()

dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client("bedrock-runtime")

class DashboardChatRequest(BaseModel):
    question: str
    dashboardData: dict

@router.post("")
async def dashboard_chat(
    data: DashboardChatRequest,
    response: Response
):
    question = data.question
    dashboard_data = data.dashboardData

    # System prompt and user prompt formatting
    system_prompt = (
        "You are a dashboard assistant.\n"
        "Answer ONLY from the provided dashboard data.\n"
        "Do not invent values.\n"
        "If the answer is not in the data, say that it is not available in the dashboard.\n"
        "Keep answers very short, business-friendly, and output only the values in bullet points. Do not use Markdown, bold, or asterisks. Output only plain text bullet points."
    )

    user_prompt = f"""
        Dashboard data:
        {json.dumps(dashboard_data, indent=2)}

        User question:
        {question}
    """

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": user_prompt}],
            }
        ],
    }
    
    model_id = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    request = json.dumps(native_request)

    try:
        response = bedrock.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(response["body"].read())
        answer = (
            model_response["content"][0]["text"]
            if model_response.get("content") and model_response["content"][0].get("text")
            else "No answer returned."
        )
        return {"answer": answer}
    except (ClientError, Exception) as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to query Haiku")
