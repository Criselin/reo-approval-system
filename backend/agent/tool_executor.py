"""Tool execution dispatcher for the SOP-based agent loop."""

import json
from backend.knowledge.kb_search import (
    list_goals,
    get_clarifying_questions,
    match_scene,
    get_sop,
    get_sop_step,
)
from backend.knowledge.product_info import get_product_info


async def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    try:
        match name:
            case "identify_goal":
                lang = arguments.get("lang", "en")
                goals = list_goals(lang)
                return json.dumps(
                    {
                        "status": "success",
                        "goals": goals,
                        "instruction": (
                            "Match the user's description to one of these goal_ids. "
                            "Then call get_clarifying_questions with the goal_id to "
                            "determine the exact scene."
                        ),
                    },
                    ensure_ascii=False,
                )

            case "get_clarifying_questions":
                goal_id = arguments["goal_id"]
                lang = arguments.get("lang", "en")
                questions = get_clarifying_questions(goal_id, lang)
                if not questions:
                    return json.dumps(
                        {"status": "not_found", "message": f"Goal '{goal_id}' not found."}
                    )
                return json.dumps(
                    {
                        "status": "success",
                        "goal_id": goal_id,
                        "questions": questions,
                        "instruction": (
                            "Ask the user these questions naturally (not as a robotic list). "
                            "Based on their answers, call match_scene_and_get_sop."
                        ),
                    },
                    ensure_ascii=False,
                )

            case "match_scene_and_get_sop":
                goal_id = arguments["goal_id"]
                answers = arguments.get("answers", {})
                lang = arguments.get("lang", "en")

                scene = match_scene(goal_id, answers)
                if not scene:
                    return json.dumps(
                        {
                            "status": "no_match",
                            "message": "Could not determine exact scene. Ask more clarifying questions or try the most general SOP.",
                        }
                    )

                sop = get_sop(scene["sop_id"], lang)
                if not sop:
                    return json.dumps(
                        {"status": "error", "message": f"SOP '{scene['sop_id']}' not found."}
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "matched_scene": {
                            "scene_id": scene["scene_id"],
                            "scene_name": scene["scene_name"].get(lang, scene["scene_name"]["en"]),
                        },
                        "sop": sop,
                        "instruction": (
                            "Guide the user through the SOP steps ONE AT A TIME. "
                            "Start with step s1. After each step, ask if it worked. "
                            "If success → follow on_success. If failure → follow on_failure. "
                            "'resolved' means the issue is fixed. 'escalate' means transfer to human. "
                            "A value like 'sop_xxx' means switch to that SOP."
                        ),
                    },
                    ensure_ascii=False,
                )

            case "get_sop_step":
                sop_id = arguments["sop_id"]
                step_id = arguments["step_id"]
                lang = arguments.get("lang", "en")

                step = get_sop_step(sop_id, step_id, lang)
                if not step:
                    return json.dumps(
                        {"status": "not_found", "message": f"Step '{step_id}' not found in SOP '{sop_id}'."}
                    )

                return json.dumps(
                    {
                        "status": "success",
                        "sop_id": sop_id,
                        "step": step,
                    },
                    ensure_ascii=False,
                )

            case "get_product_info":
                product = get_product_info(arguments["model_name"])
                if not product:
                    return json.dumps(
                        {
                            "status": "not_found",
                            "message": f"Product '{arguments['model_name']}' not found.",
                        }
                    )
                return json.dumps({"status": "success", "product": product})

            case "escalate_to_human":
                return json.dumps(
                    {
                        "status": "escalated",
                        "message": "This conversation has been escalated to a human support agent.",
                        "reason": arguments["reason"],
                        "severity": arguments["severity"],
                        "ticket_id": "TKT-" + str(abs(hash(arguments["reason"])))[-6:],
                    }
                )

            case _:
                return json.dumps(
                    {"status": "error", "message": f"Unknown tool: {name}"}
                )

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Tool execution error: {str(e)}"})
