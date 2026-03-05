"""Core Agent Loop - PI-style while loop with tool calling.

The agent loop:
1. Receives a user message
2. Builds message history with system prompt
3. Calls LLM with available tools
4. If LLM returns tool_calls → execute tools → append results → loop back to 3
5. If LLM returns text → stream to user → exit loop
"""

import json
import asyncio
from typing import AsyncGenerator, Callable, Awaitable

from backend.config import get_settings
from backend.agent.system_prompt import SYSTEM_PROMPT
from backend.agent.tools import TOOLS
from backend.agent.tool_executor import execute_tool
from backend.llm.minimax_client import (
    chat_completion,
    chat_completion_stream,
    message_to_dict,
    clean_think_tags,
)
from backend.models.schemas import AgentEvent
from backend.models.conversation import Conversation


def _build_messages(conversation: Conversation) -> list[dict]:
    """Build the messages array for the LLM call."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in conversation.messages:
        entry = {"role": msg.role, "content": msg.content}
        if msg.tool_calls:
            entry["tool_calls"] = msg.tool_calls
        if msg.tool_call_id:
            entry["tool_call_id"] = msg.tool_call_id
        messages.append(entry)

    return messages


async def agent_loop_stream(
    conversation: Conversation,
) -> AsyncGenerator[AgentEvent, None]:
    """Run the agent loop, yielding SSE events.

    This is a generator that yields AgentEvent objects as the agent
    processes the user's message through the tool-calling loop.
    """
    settings = get_settings()
    messages = _build_messages(conversation)
    iteration = 0
    all_tool_calls_info = []

    while iteration < settings.max_agent_iterations:
        iteration += 1

        # Emit thinking event
        yield AgentEvent(type="thinking", content=f"Iteration {iteration}")

        # Call LLM (non-streaming for tool iterations)
        response_message = await chat_completion(messages, tools=TOOLS)

        # Preserve the full assistant message in history
        msg_dict = message_to_dict(response_message)
        messages.append(msg_dict)

        # Check if we have tool calls
        if not response_message.tool_calls:
            # No tool calls - this is the final text response
            clean_content = clean_think_tags(response_message.content or "")

            # Stream the final response token by token for better UX
            for i in range(0, len(clean_content), 3):
                chunk = clean_content[i : i + 3]
                yield AgentEvent(type="token", content=chunk)
                await asyncio.sleep(0.01)  # Small delay for streaming effect

            # Save to conversation history
            conversation.add_assistant_message(
                clean_content, tool_calls=[tc for tc in all_tool_calls_info] if all_tool_calls_info else None
            )

            yield AgentEvent(type="response", content=clean_content)
            yield AgentEvent(type="done")
            return

        # Execute tool calls
        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            # Emit tool_call event
            yield AgentEvent(
                type="tool_call",
                tool_name=fn_name,
                tool_args=fn_args,
            )

            # Execute the tool
            result = await execute_tool(fn_name, fn_args)

            # Track tool calls for conversation history
            all_tool_calls_info.append(
                {"name": fn_name, "arguments": fn_args, "result": result}
            )

            # Emit tool_result event
            yield AgentEvent(
                type="tool_result",
                tool_name=fn_name,
                tool_result=result,
            )

            # Append tool result to messages for the next LLM call
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

            # Check for escalation
            try:
                result_data = json.loads(result)
                if result_data.get("status") == "escalated":
                    conversation.escalated = True
            except json.JSONDecodeError:
                pass

    # Max iterations exceeded - fallback response
    fallback = (
        "I apologize, but I'm having difficulty resolving this issue through "
        "automated troubleshooting. Let me connect you with a human support "
        "agent who can provide more specialized assistance."
    )
    conversation.add_assistant_message(fallback)
    yield AgentEvent(type="response", content=fallback)
    yield AgentEvent(type="done")


async def agent_loop_sync(conversation: Conversation) -> dict:
    """Run the agent loop synchronously (for batch testing).

    Returns:
        Dict with 'response' (str) and 'tool_calls' (list)
    """
    settings = get_settings()
    messages = _build_messages(conversation)
    iteration = 0
    all_tool_calls_info = []

    while iteration < settings.max_agent_iterations:
        iteration += 1

        response_message = await chat_completion(messages, tools=TOOLS)
        msg_dict = message_to_dict(response_message)
        messages.append(msg_dict)

        if not response_message.tool_calls:
            clean_content = clean_think_tags(response_message.content or "")
            conversation.add_assistant_message(clean_content, tool_calls=all_tool_calls_info or None)
            return {
                "response": clean_content,
                "tool_calls": all_tool_calls_info,
                "iterations": iteration,
            }

        for tool_call in response_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            result = await execute_tool(fn_name, fn_args)
            all_tool_calls_info.append(
                {"name": fn_name, "arguments": fn_args, "result": result}
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

            try:
                result_data = json.loads(result)
                if result_data.get("status") == "escalated":
                    conversation.escalated = True
            except json.JSONDecodeError:
                pass

    fallback = (
        "I apologize, but I'm having difficulty resolving this issue. "
        "Let me connect you with a human support agent."
    )
    conversation.add_assistant_message(fallback)
    return {
        "response": fallback,
        "tool_calls": all_tool_calls_info,
        "iterations": iteration,
    }
