
def get_interation_mode(intent: str) -> str:
    mapping = {
        "clarify_needed": (
            "Ask only necessary clarifying questions to fill gaps in the learner's input. "
            "Keep questions concise and focused, avoid repeating context. "
            "Encourage the learner to provide examples or details, using a supportive and curious tone."
        ),
        "simple_fact_question": (
            "Provide clear, concise factual answers in small, digestible steps. "
            "Use bullet points or short paragraphs if needed. "
            "Avoid overloading with extra information. Maintain a neutral, calm tone."
        ),
        "domain_question": (
            "Ground your answer strictly in the retrieved documents. "
            "Highlight relevant sections, provide examples from the content, and guide the learner’s reasoning. "
            "Encourage the learner to connect concepts or reflect on how the answer applies to their context."
        ),
        "troubleshoot_issue": (
            "Guide the learner step-by-step through problem-solving. "
            "Ask probing questions to diagnose the issue, suggest experiments or checks, and confirm understanding at each step. "
            "Maintain a patient, supportive, and encouraging tone."
        ),
        "follow_up_question": (
            "Build on previous answers and maintain continuity. "
            "Reinforce learning contextually, recap key points if needed, and invite the learner to deepen understanding. "
            "Keep explanations brief and targeted."
        ),
        "reflection_request": (
            "Encourage critical thinking and self-reflection. "
            "Pose questions that prompt the learner to analyze, evaluate, or articulate their thoughts. "
            "Use a gentle, thought-provoking tone and allow space for learner reasoning."
        ),
        "goal_setting": (
            "Help the learner define clear, actionable learning goals. "
            "Suggest steps, frameworks, or checkpoints. "
            "Keep guidance supportive, motivational, and focused on progress and achievement."
        ),
        "out_of_scope": (
            "Politely inform the learner that the content is outside the course scope. "
            "Provide reassurance and suggest focusing on relevant topics. "
            "Maintain a professional, friendly tone."
        ),
        "chit_chat": (
            "Engage in short, friendly, and conversational small talk. "
            "Keep responses light, cheerful, and encouraging. "
            "Do not provide detailed explanations or RAG-based content in this context."
        ),
    }
    
    principle_text = mapping.get(intent)
    return (principle_text)


def get_policy_by_decision_mode(mode: str) -> str:
    policies = {
        "factual_mode": (
            "Provide only verified facts. Do not give advice, opinions, or recommendations."
        ),
        "explanatory_mode": (
            "Explain concepts and mechanisms clearly. Do not prescribe actions."
        ),
        "interpretive_mode": (
            "Surface multiple interpretations and trade-offs. Avoid declaring a single correct answer."
        ),
        "judgment_mode": (
            "Provide guidance under uncertainty. Prioritize conditions over plans, treat discomfort as a signal, "
            "and recommend proportional responses without blame."
        ),
        "action_guidance_mode": (
            "Recommend a clear next step. Scale response to risk and uncertainty. "
            "Insert pauses when clarity is insufficient and state conditions for resuming."
        ),
        "reflective_mode": (
            "Focus on learning and improvement. Highlight adaptations, enablers, and lessons."
        ),
        "risk_evaluation_mode": (
            "Identify potential risks, uncertainty, and compounding factors without prescribing action."
        ),
        "option_comparison_mode": (
            "Compare viable options and trade-offs. Clarify when one option is preferable."
        ),
        "constraint_check_mode": (
            "Evaluate compliance, constraints, and boundaries. Suggest compliant alternatives if needed."
        ),
        "recommendation_mode": (
            "Provide a reasoned recommendation with assumptions made explicit."
        ),
        "scenario_analysis_mode": (
            "Compare future outcomes across scenarios and highlight irreversible decisions."
        ),
        "decision_review_mode": (
            "Assess decision quality based on information available at the time. Avoid hindsight bias."
        ),
        "out_of_scope_mode": (
                "Politely inform the learner that the content is outside the course scope. "
                "Provide reassurance and suggest focusing on relevant topics. "
                "Maintain a professional, friendly tone."
        ),
    }

    return policies.get(mode, "")
