import json
import boto3
from core.config import settings
import asyncio

bedrock = boto3.client("bedrock-runtime", region_name=settings.REGION)


async def generate_chat_title(user_message: str, initial_message: str):

    prompt = f"""
You are a title generator for a chat conversation.

Your task is to generate a short and clear title that summarizes the user's question.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Create a concise title (3–7 words).
2. Focus on the main topic of the user's message.
3. Remove filler words and conversational language.
4. Use key terms that describe the problem or concept.
5. Do NOT include punctuation like quotes or periods.
6. The title should look like a chat history label.

Return only the title.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User Message:
{user_message}

Lira's Initial Welcome Message:
{initial_message}
"""

    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 50,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "chat_title": {
                            "type": "string"
                        }
                    },
                    "required": ["chat_title"],
                    "additionalProperties": False
                }
            }
        }
    }

    response = await asyncio.to_thread(
        bedrock.invoke_model,
        modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        body=json.dumps(native_request)
    )

    model_response = json.loads(response["body"].read())
    output = json.loads(model_response["content"][0]["text"])

    return output