"""Tool execution dispatcher for the agent loop."""

import json
from backend.knowledge.kb_search import search_knowledge_base, get_article_by_id
from backend.knowledge.product_info import get_product_info


async def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name and return the result as a JSON string.

    Args:
        name: Tool function name
        arguments: Tool arguments dict

    Returns:
        JSON string with the tool result
    """
    try:
        match name:
            case "search_knowledge_base":
                results = search_knowledge_base(
                    query=arguments["query"],
                    category=arguments.get("category"),
                )
                if not results:
                    return json.dumps(
                        {
                            "status": "no_results",
                            "message": "No matching articles found. Try rephrasing the query or removing the category filter.",
                        }
                    )
                return json.dumps({"status": "success", "articles": results})

            case "get_product_info":
                product = get_product_info(arguments["model_name"])
                if not product:
                    return json.dumps(
                        {
                            "status": "not_found",
                            "message": f"Product '{arguments['model_name']}' not found. Common models: RLC-810A, RLC-820A, Argus 3 Pro, E1 Zoom, RLN8-410.",
                        }
                    )
                return json.dumps({"status": "success", "product": product})

            case "get_troubleshooting_steps":
                article = get_article_by_id(arguments["article_id"])
                if not article:
                    return json.dumps(
                        {
                            "status": "not_found",
                            "message": f"Article '{arguments['article_id']}' not found. Use search_knowledge_base first to find valid article IDs.",
                        }
                    )
                return json.dumps(
                    {
                        "status": "success",
                        "article": {
                            "id": article["id"],
                            "title": article["title"],
                            "category": article["category_name"],
                            "symptoms": article["symptoms"],
                            "steps": article["steps"],
                            "products": article["products"],
                            "difficulty": article["difficulty"],
                        },
                    }
                )

            case "escalate_to_human":
                return json.dumps(
                    {
                        "status": "escalated",
                        "message": "This conversation has been escalated to a human support agent.",
                        "reason": arguments["reason"],
                        "severity": arguments["severity"],
                        "ticket_id": "TKT-" + str(hash(arguments["reason"]))[-6:],
                    }
                )

            case _:
                return json.dumps(
                    {"status": "error", "message": f"Unknown tool: {name}"}
                )

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Tool execution error: {str(e)}"})
