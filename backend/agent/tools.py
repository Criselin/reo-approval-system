"""Tool definitions for the Reolink customer service agent (OpenAI function calling format).

SOP-based tools:
  1. identify_goal → match user intent to a goal_id
  2. get_clarifying_questions → get questions to determine scene
  3. match_scene_and_get_sop → given answers, find the right SOP
  4. get_sop_step → get a specific step from the SOP decision tree
  5. get_product_info → look up product specs
  6. escalate_to_human → escalate unresolvable issues
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "identify_goal",
            "description": (
                "Identify the user's troubleshooting goal from their message. "
                "Returns a list of available goals with IDs. Use this FIRST to "
                "understand what the user needs help with. The LLM should map "
                "the user's description (in any language) to the correct goal_id."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lang": {
                        "type": "string",
                        "enum": ["en", "zh"],
                        "description": "Language for goal names. Use 'zh' if the user writes in Chinese, 'en' otherwise.",
                    },
                },
                "required": ["lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_clarifying_questions",
            "description": (
                "Get the clarifying questions needed to determine the exact "
                "troubleshooting scenario (scene) for a given goal. Ask the user "
                "these questions to narrow down the root cause. The questions help "
                "build a decision path to the correct SOP."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "string",
                        "description": "The goal ID identified from the user's intent (e.g., 'camera_offline', 'night_vision_issue')",
                    },
                    "lang": {
                        "type": "string",
                        "enum": ["en", "zh"],
                        "description": "Language for questions",
                    },
                },
                "required": ["goal_id", "lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "match_scene_and_get_sop",
            "description": (
                "Based on the user's answers to clarifying questions, match the "
                "correct scene and retrieve the full SOP decision tree. The answers "
                "dict should map question_id to the selected option. Returns the "
                "complete step-by-step troubleshooting SOP."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "string",
                        "description": "The goal ID",
                    },
                    "answers": {
                        "type": "object",
                        "description": (
                            "User's answers to clarifying questions. Keys are question_id, "
                            "values are the selected option string. Example: "
                            '{"connection_type": "wifi", "trigger_event": "power_outage"}'
                        ),
                    },
                    "lang": {
                        "type": "string",
                        "enum": ["en", "zh"],
                        "description": "Language for SOP steps",
                    },
                },
                "required": ["goal_id", "answers", "lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sop_step",
            "description": (
                "Get a specific step from an SOP by step_id. Use this when "
                "progressing through the SOP decision tree — after the user "
                "reports whether a step succeeded or failed, get the next step "
                "based on on_success or on_failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sop_id": {
                        "type": "string",
                        "description": "The SOP ID",
                    },
                    "step_id": {
                        "type": "string",
                        "description": "The step ID to retrieve (e.g., 's1', 's2', 's3')",
                    },
                    "lang": {
                        "type": "string",
                        "enum": ["en", "zh"],
                        "description": "Language for step content",
                    },
                },
                "required": ["sop_id", "step_id", "lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_info",
            "description": (
                "Get detailed information about a specific Reolink product including "
                "features, specifications, and common issues. Use this when a customer "
                "mentions a specific camera or NVR model."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "Product model name or partial name, e.g. 'RLC-810A', 'Argus 3 Pro'",
                    },
                },
                "required": ["model_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": (
                "Escalate the conversation to a human support agent. Use this when: "
                "(1) the SOP steps have been exhausted without resolution, "
                "(2) a step's on_failure points to 'escalate', "
                "(3) the issue likely requires hardware repair/RMA, "
                "(4) the customer explicitly requests human support."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Detailed reason for escalation, including what SOP steps were tried",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Severity: low=general inquiry, medium=persistent issue, high=hardware defect/safety",
                    },
                },
                "required": ["reason", "severity"],
            },
        },
    },
]
