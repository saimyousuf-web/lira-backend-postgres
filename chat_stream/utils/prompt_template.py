import boto3
from core.config import settings

bedrock_agent = boto3.client(
    "bedrock-agent",
    region_name= settings.REGION
)


def getPromptTemplate(coach_mode: bool, voice_mode: bool, context_history:str, stringified_docs:str, user_message:str, citation_html:str, user_name:str, core_principle:str, interaction_mode:str, feedback_string: str, step_description:str, step:str) -> str:
    print("Getting prompt template with coach_mode=", coach_mode, "voice_mode=", voice_mode, "step=", step)
    if coach_mode and step in ['done'] and step is not None and not voice_mode:
        print("Coach mode is running")

        response =  bedrock_agent.invoke_prompt(
        promptIdentifier="lira_coach_mode_prompt",
        promptVersion="1",
        inputVariables={
            "user_name": user_name,
            "user_message": user_message,
            "citation_html": citation_html,
        "stringified_docs": stringified_docs,
        "context_history": context_history,
        "core_principle": core_principle,
        "interaction_mode": interaction_mode,
        "feedback_string": feedback_string
    }
)
        print ("respose bedrock coach", response)
        return response
    
    elif coach_mode and step not in ['done'] and step is not None and not voice_mode:
        print("guided flow is running")
        return bedrock_agent.invoke_prompt(
        promptIdentifier="lira_guided_flow_prompt",
        promptVersion="1",
        inputVariables={
        "user_name": user_name,
        "user_message": user_message,
        "citation_html": citation_html,
        "stringified_docs": stringified_docs,
        "context_history": context_history,
        "feedback_string": feedback_string,
        "step_description": step_description
    }
)
    elif not coach_mode and not voice_mode:
        print("live mode is running")
        return bedrock_agent.invoke_prompt(
        promptIdentifier="lira_live_mode_prompt",
        promptVersion="1",
        inputVariables={
        "user_name": user_name,
        "user_message": user_message,
        "citation_html": citation_html,
        "stringified_docs": stringified_docs,
        "context_history": context_history,
        "feedback_string": feedback_string
    }
)
        
    else:
        print("live mode is running")
        return bedrock_agent.invoke_prompt(
        promptIdentifier="lira_voice_mode_prompt",
        promptVersion="1",
        inputVariables={
        "user_name": user_name,
        "user_message": user_message,
        "citation_html": citation_html,
        "stringified_docs": stringified_docs,
        "context_history": context_history,
        "feedback_string": feedback_string
    }
)
    
    
    
    
    
    
    
    
    




