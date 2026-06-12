import json
import boto3
from core.config import settings
import asyncio

bedrock = boto3.client("bedrock-runtime", region_name=settings.REGION)



async def analyze_user_message(user_message: str, context_history: str, coach_mode: bool, step:str, voice_mode: bool):
    if coach_mode and step in ['done'] and not voice_mode:    
      prompt = f"""
You are a strict orchestration engine for a coaching-oriented
Retrieval-Augmented Generation (RAG) system.

You must:
1. Determine the SINGLE best intent.
2. Determine the SINGLE best decision mode.
3. Generate a precise search query representing the user's core informational need.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTENT DEFINITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- clarify_needed:
  The message is ambiguous, incomplete, or missing critical details.

- simple_fact_question:
  The user requests a direct fact, definition, or short explanation.

- domain_question:
  The user asks about course/domain concepts that likely require retrieved documents.

- troubleshoot_issue:
  The user describes a problem and seeks help resolving it.

- follow_up_question:
  The user continues a prior topic without introducing a new objective.

- reflection_request:
  The user asks for analysis, reflection, or meaning-making.

- redo_assessment:
  The user wants to start assessment over.

- goal_setting:
  The user expresses learning goals or development intentions.

- out_of_scope:
  The message is clearly unrelated to the course/domain.

- chit_chat:
  Greeting or casual talk with no instructional goal.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DECISION MODE DEFINITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- factual_mode:
  A single correct answer exists. No ambiguity.

- explanatory_mode:
  The user wants conceptual understanding or mechanisms explained.

- interpretive_mode:
  Multiple interpretations are possible; context and nuance matter.

- judgment_mode:
  The user asks what should be done under uncertainty.

- action_guidance_mode:
  The user is in an active situation and needs a next step.

- reflective_mode:
  The user wants learning extraction or self-evaluation.

- risk_evaluation_mode:
  The user asks about risk, severity, likelihood, or uncertainty.

- option_comparison_mode:
  The user compares multiple approaches or asks to evaluate tradeoffs.

- constraint_check_mode:
  The user asks whether something is allowed, compliant, or ethical.

- recommendation_mode:
  The user asks for an advisory recommendation with reasoning.

- scenario_analysis_mode:
  The user asks “what if” or future-outcome projection questions.

- decision_review_mode:
  The user evaluates a past decision.

- out_of_scope_mode:
  Used ONLY if intent = out_of_scope.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLASSIFICATION PRIORITY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. If the topic is clearly unrelated to the course/domain,
   intent MUST be "out_of_scope"
   and decision_mode MUST be "out_of_scope_mode".

2. If the user asks:
   - "should", "what should I do", "how do I handle"
   → prefer judgment_mode or action_guidance_mode.

3. If the user compares options
   → prefer option_comparison_mode.

4. If the user asks about risks or consequences
   → prefer risk_evaluation_mode.

5. If the user evaluates a past action
   → prefer decision_review_mode.

6. Do NOT default to explanatory_mode
   unless the user explicitly seeks conceptual understanding.

7. Maintain continuity:
   If the current message clearly continues the previous topic,
   consider follow_up_question unless strong signals indicate change.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUERY REFORMULATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate a single-line, self-contained search query that captures
the core informational need of the user message.

Guidelines:
- Focus on factual, procedural, or conceptual keywords.
- Remove conversational language.
- Use relevant context from chat history.
- Generalize scenario descriptions to their underlying topic.
- Even if the message is chit_chat or out_of_scope, produce a minimal normalized topic query.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User Message:
{user_message}

Chat History:
{context_history}
"""
    


      native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 600,
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
                        "intent": {
                            "type": "string",
                            "enum": [
                                "clarify_needed",
                                "simple_fact_question",
                                "domain_question",
                                "troubleshoot_issue",
                                "follow_up_question",
                                "redo_assessment",
                                "reflection_request",
                                "goal_setting",
                                "out_of_scope",
                                "chit_chat"
                            ]
                        },
                        "decision_mode": {
                            "type": "string",
                            "enum": [
                                "factual_mode",
                                "explanatory_mode",
                                "interpretive_mode",
                                "judgment_mode",
                                "action_guidance_mode",
                                "reflective_mode",
                                "risk_evaluation_mode",
                                "option_comparison_mode",
                                "constraint_check_mode",
                                "recommendation_mode",
                                "scenario_analysis_mode",
                                "decision_review_mode",
                                "out_of_scope_mode"
                            ]
                        },
                        "search_query": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "intent",
                        "decision_mode",
                        "search_query"
                    ],
                    "additionalProperties": False
                }
            }
        }
    }
      response = await asyncio.to_thread(
      bedrock.invoke_model,
      modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
      body=json.dumps(native_request))

      model_response = json.loads(response["body"].read())
      output = json.loads(model_response["content"][0]["text"])

      return output
    
    else:

      prompt = f"""
You are a query rewriting engine for a Retrieval-Augmented Generation (RAG) system.

Your task is ONLY to generate a precise search query that will retrieve the most relevant course material.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Convert the user message into a concise search query.
2. Focus on the key domain concepts or problem described.
3. Remove conversational language and filler words.
4. Use terminology likely to appear in training/course documents.
5. If the message describes a scenario, generalize it to the underlying topic.
6. Use context from the chat history only if it clarifies the topic.

Return only a short query phrase (not a sentence).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User Message:
{user_message}

Chat History:
{context_history}
"""
      native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
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
                "search_query": {
                    "type": "string"
                }
            },
            "required": ["search_query"],
            "additionalProperties": False
        }
        }
    }
      }

      response = await asyncio.to_thread(
      bedrock.invoke_model,
      modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
      body=json.dumps(native_request))

      model_response = json.loads(response["body"].read())
      output = json.loads(model_response["content"][0]["text"])

      return output
