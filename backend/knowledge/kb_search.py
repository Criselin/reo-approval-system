"""SOP-based knowledge base with decision tree structure.

Architecture:
  User Goal (intent) → Scene (conditions) → SOP (decision tree steps)

Language-agnostic: LLM extracts goal_id from user message in any language,
then uses structured IDs to navigate the decision tree.
"""

import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_goals: list[dict] = []
_sops: dict[str, dict] = {}  # sop_id → sop
_loaded = False


def load_knowledge_base():
    """Load SOP goals and decision trees at startup."""
    global _goals, _sops, _loaded

    # Load goals (intent → scene mapping)
    goals_path = _DATA_DIR / "sop_goals.json"
    with open(goals_path, "r", encoding="utf-8") as f:
        goals_data = json.load(f)
    _goals = goals_data["goals"]

    # Load SOP decision trees
    sops_path = _DATA_DIR / "sop_trees.json"
    with open(sops_path, "r", encoding="utf-8") as f:
        sops_data = json.load(f)
    _sops = {sop["sop_id"]: sop for sop in sops_data["sops"]}

    _loaded = True


def _ensure_loaded():
    if not _loaded:
        load_knowledge_base()


def list_goals(lang: str = "en") -> list[dict]:
    """List all available troubleshooting goals.

    Returns structured goal list for the LLM to match user intent.
    Language-agnostic: returns goal_id + name in requested language.
    """
    _ensure_loaded()
    return [
        {
            "goal_id": g["goal_id"],
            "goal_name": g["goal_name"].get(lang, g["goal_name"]["en"]),
            "intent_keywords": g["intent_keywords"],
        }
        for g in _goals
    ]


def get_goal(goal_id: str) -> dict | None:
    """Get a specific goal with its scenes and clarifying questions."""
    _ensure_loaded()
    for g in _goals:
        if g["goal_id"] == goal_id:
            return g
    return None


def get_clarifying_questions(goal_id: str, lang: str = "en") -> list[dict]:
    """Get clarifying questions for a goal to determine the scene.

    The LLM uses these questions to narrow down which SOP to use.
    """
    _ensure_loaded()
    goal = get_goal(goal_id)
    if not goal:
        return []

    return [
        {
            "question_id": q["question_id"],
            "question": q["question"].get(lang, q["question"]["en"]),
            "options": q["options"],
        }
        for q in goal.get("clarifying_questions", [])
    ]


def match_scene(goal_id: str, answers: dict[str, str]) -> dict | None:
    """Match a scene based on user's answers to clarifying questions.

    Args:
        goal_id: The identified user goal
        answers: Dict of question_id → selected option

    Returns:
        Matched scene dict with sop_id, or None if no match
    """
    _ensure_loaded()
    goal = get_goal(goal_id)
    if not goal:
        return None

    best_match = None
    best_score = 0

    for scene in goal.get("scenes", []):
        conditions = scene.get("match_conditions", {})
        if not conditions:
            continue

        score = 0
        total = len(conditions)
        matched = 0

        for question_id, valid_options in conditions.items():
            if question_id in answers:
                if answers[question_id] in valid_options:
                    matched += 1

        if total > 0:
            score = matched / total

        if score > best_score:
            best_score = score
            best_match = scene

    return best_match


def get_scenes_for_goal(goal_id: str, lang: str = "en") -> list[dict]:
    """Get all scenes for a goal (for display/selection)."""
    _ensure_loaded()
    goal = get_goal(goal_id)
    if not goal:
        return []

    return [
        {
            "scene_id": s["scene_id"],
            "scene_name": s["scene_name"].get(lang, s["scene_name"]["en"]),
            "sop_id": s["sop_id"],
            "match_conditions": s["match_conditions"],
        }
        for s in goal.get("scenes", [])
    ]


def get_sop(sop_id: str, lang: str = "en") -> dict | None:
    """Get a full SOP decision tree.

    Returns the SOP with steps localized to the requested language.
    """
    _ensure_loaded()
    sop = _sops.get(sop_id)
    if not sop:
        return None

    return {
        "sop_id": sop["sop_id"],
        "sop_name": sop["sop_name"].get(lang, sop["sop_name"]["en"]),
        "applicable_products": sop["applicable_products"],
        "steps": [
            {
                "step_id": step["step_id"],
                "instruction": step["instruction"].get(lang, step["instruction"]["en"]),
                "expected_result": step["expected_result"].get(lang, step["expected_result"]["en"]),
                "on_success": step["on_success"],
                "on_failure": step["on_failure"],
            }
            for step in sop["steps"]
        ],
    }


def get_sop_step(sop_id: str, step_id: str, lang: str = "en") -> dict | None:
    """Get a specific step from an SOP."""
    sop = get_sop(sop_id, lang)
    if not sop:
        return None

    for step in sop["steps"]:
        if step["step_id"] == step_id:
            return step
    return None
