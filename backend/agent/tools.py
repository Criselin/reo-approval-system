"""Tool definitions for the Reolink customer service agent (OpenAI function calling format)."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the Reolink troubleshooting knowledge base for articles matching "
                "a query. Use this tool BEFORE answering any technical support question to "
                "find relevant troubleshooting guides. Returns article summaries with "
                "relevance scores."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing the customer's issue, e.g. 'camera offline after power outage'",
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "camera_offline",
                            "night_vision",
                            "motion_detection",
                            "app_connectivity",
                            "nvr_recording",
                            "firmware_update",
                            "poe_connection",
                            "wifi_signal",
                            "video_quality",
                            "storage_sd_card",
                            "two_way_audio",
                            "playback_issues",
                        ],
                        "description": "Optional category filter to narrow results",
                    },
                },
                "required": ["query"],
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
                        "description": "Product model name or partial name, e.g. 'RLC-810A', 'Argus 3 Pro', 'E1 Zoom'",
                    },
                },
                "required": ["model_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_troubleshooting_steps",
            "description": (
                "Get the full step-by-step troubleshooting guide for a specific article. "
                "Use this after search_knowledge_base returns matching articles, to get "
                "the complete solution steps for the most relevant article."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "string",
                        "description": "The article ID from search results, e.g. 'co_001', 'nv_002'",
                    },
                },
                "required": ["article_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": (
                "Escalate the conversation to a human support agent. Use this when: "
                "(1) troubleshooting steps didn't resolve the issue after 2-3 attempts, "
                "(2) the issue likely requires hardware repair/RMA, "
                "(3) the customer explicitly requests human support, or "
                "(4) the issue is outside the scope of troubleshooting (billing, returns, etc.)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Detailed reason for escalation, including what was tried",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Severity: low=general inquiry, medium=persistent issue, high=hardware defect/safety concern",
                    },
                },
                "required": ["reason", "severity"],
            },
        },
    },
]
