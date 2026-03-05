"""LLM-as-Judge evaluator for agent responses."""

import json
import re
from backend.llm.minimax_client import chat_completion, clean_think_tags
from backend.evaluation.criteria import format_criteria_for_prompt

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for an AI customer service agent that handles Reolink security camera support.

Your task: evaluate the agent's latest response given the conversation history.

## Evaluation Criteria
{criteria}

## Instructions
1. Read the full conversation history carefully
2. Focus on the agent's LATEST response
3. Score each criterion from 1-5 based on the rubric
4. Provide brief reasoning for each score
5. Calculate an overall score (weighted average, not just mean)

## Output Format
You MUST output valid JSON in exactly this format:
{{
  "relevance": {{"score": <1-5>, "reasoning": "<brief explanation>"}},
  "accuracy": {{"score": <1-5>, "reasoning": "<brief explanation>"}},
  "helpfulness": {{"score": <1-5>, "reasoning": "<brief explanation>"}},
  "tone": {{"score": <1-5>, "reasoning": "<brief explanation>"}},
  "overall": {{"score": <1-5>, "reasoning": "<brief summary>"}}
}}

Output ONLY the JSON, no other text."""


def _format_conversation(conversation_history: list[dict], agent_response: str) -> str:
    """Format conversation for the judge."""
    lines = ["## Conversation History"]
    for msg in conversation_history:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        if role in ("USER", "ASSISTANT"):
            lines.append(f"\n**{role}**: {content}")

    lines.append(f"\n## Agent's Latest Response (to evaluate)")
    lines.append(agent_response)

    return "\n".join(lines)


def _parse_eval_result(text: str) -> dict:
    """Parse the judge's JSON response, handling potential formatting issues."""
    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find any JSON object in the text
    json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback: return default scores
    return {
        "relevance": {"score": 3, "reasoning": "Could not parse evaluation"},
        "accuracy": {"score": 3, "reasoning": "Could not parse evaluation"},
        "helpfulness": {"score": 3, "reasoning": "Could not parse evaluation"},
        "tone": {"score": 3, "reasoning": "Could not parse evaluation"},
        "overall": {"score": 3, "reasoning": "Could not parse evaluation"},
    }


async def evaluate_turn(
    conversation_history: list[dict],
    agent_response: str,
) -> dict:
    """Evaluate a single agent response using LLM-as-Judge.

    Args:
        conversation_history: List of message dicts (role + content)
        agent_response: The agent's latest response to evaluate

    Returns:
        Dict with scores and reasoning for each criterion
    """
    criteria_text = format_criteria_for_prompt()
    system_prompt = JUDGE_SYSTEM_PROMPT.format(criteria=criteria_text)
    user_content = _format_conversation(conversation_history, agent_response)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    response = await chat_completion(messages, temperature=0.1)
    clean_content = clean_think_tags(response.content or "")
    result = _parse_eval_result(clean_content)

    # Validate and normalize scores
    for key in ["relevance", "accuracy", "helpfulness", "tone", "overall"]:
        if key not in result:
            result[key] = {"score": 3, "reasoning": "Missing from evaluation"}
        else:
            score = result[key].get("score", 3)
            result[key]["score"] = max(1, min(5, int(score)))

    return result
