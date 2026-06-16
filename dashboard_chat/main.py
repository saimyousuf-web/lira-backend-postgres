from fastapi import APIRouter, HTTPException, Depends, Response
from dependencies.auth import get_current_user
from pydantic import BaseModel
from typing import Optional
import uuid
import json

from core.llm import generate

router = APIRouter()

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

    try:
        answer = await generate(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=300,
            temperature=0.5,
        )
        return {"answer": answer.strip() if answer else "No answer returned."}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to query LLM")
