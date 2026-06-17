from core.llm import generate
from core.config import settings


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

    schema = {
        "type": "object",
        "properties": {
            "chat_title": {"type": "string"}
        },
        "required": ["chat_title"],
        "additionalProperties": False,
    }

    output = await generate(
        prompt=prompt,
        max_tokens=50,
        temperature=0,
        json_schema=schema,
        model=settings.OLLAMA_FAST_MODEL,
    )

    return output