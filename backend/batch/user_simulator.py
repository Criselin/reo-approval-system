"""AI user simulator for batch testing.

Simulates a customer with a specific issue, persona, and product.
Uses the same MiniMax LLM to generate realistic customer responses.
"""

from backend.llm.minimax_client import chat_completion, clean_think_tags

SIMULATOR_SYSTEM_PROMPT = """You are simulating a customer contacting Reolink technical support.

## Your Persona
{persona}

## Your Issue
- Product: {product}
- Issue category: {issue_category}
- You are experiencing a real problem and need help resolving it.

## Behavior Rules
1. Stay in character as the customer described above
2. Respond naturally to the support agent's questions and instructions
3. When asked to try troubleshooting steps:
   - Sometimes report that a step worked (if it matches the expected resolution)
   - Sometimes report that a step didn't help (to test the agent's follow-up)
   - Occasionally say you're not sure how to do something (to test the agent's clarity)
4. Ask follow-up questions if instructions are unclear
5. Express appropriate emotions based on your persona
6. Keep responses concise (1-3 sentences typically)
7. Don't be overly cooperative - simulate realistic customer behavior
8. If the agent successfully resolves your issue, express gratitude and end naturally
9. If the agent asks about your product model, answer with: {product}

## Important
- You are the CUSTOMER, not the support agent
- Only describe your experience and respond to the agent
- Do NOT provide solutions yourself"""


async def simulate_user_response(
    conversation_history: list[dict],
    scenario: dict,
    turn_number: int,
) -> str:
    """Generate a simulated customer response.

    Args:
        conversation_history: List of message dicts (role + content)
        scenario: Test scenario definition
        turn_number: Current turn number (affects behavior)

    Returns:
        Simulated customer message
    """
    system_prompt = SIMULATOR_SYSTEM_PROMPT.format(
        persona=scenario["user_persona"],
        product=scenario["product"],
        issue_category=scenario["issue_category"],
    )

    # Convert conversation to simulator's perspective
    # The agent's messages become "assistant" (the support agent)
    # The user's messages become what the simulator has said before
    messages = [{"role": "system", "content": system_prompt}]

    for msg in conversation_history:
        if msg["role"] == "user":
            messages.append({"role": "assistant", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "user", "content": msg["content"]})

    # Add instruction for this turn
    turn_hint = ""
    if turn_number >= scenario.get("max_turns", 8) - 2:
        turn_hint = "\n(Hint: This conversation is nearing its end. If the issue seems resolved, express satisfaction. If not, consider asking to speak with a human.)"

    messages.append(
        {
            "role": "user",
            "content": f"Generate the customer's next response to the support agent.{turn_hint}",
        }
    )

    response = await chat_completion(messages, temperature=0.8)
    return clean_think_tags(response.content or "I'm not sure what to do next.")
