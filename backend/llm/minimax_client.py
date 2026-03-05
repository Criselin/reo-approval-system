import re
import json
from openai import OpenAI, AsyncOpenAI
from backend.config import get_settings


def _get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.minimax_api_key,
        base_url=settings.minimax_base_url,
    )


def _get_async_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.minimax_api_key,
        base_url=settings.minimax_base_url,
    )


_sync_client: OpenAI | None = None
_async_client: AsyncOpenAI | None = None


def get_sync_client() -> OpenAI:
    global _sync_client
    if _sync_client is None:
        _sync_client = _get_client()
    return _sync_client


def get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = _get_async_client()
    return _async_client


def clean_think_tags(content: str | None) -> str:
    """Remove <think>...</think> tags from MiniMax responses for display."""
    if not content:
        return ""
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


async def chat_completion(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
) -> dict:
    """Non-streaming chat completion. Returns the full response message."""
    settings = get_settings()
    client = get_async_client()

    kwargs = {
        "model": settings.minimax_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = await client.chat.completions.create(**kwargs)
    return response.choices[0].message


async def chat_completion_stream(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.7,
):
    """Streaming chat completion. Yields delta chunks."""
    settings = get_settings()
    client = get_async_client()

    kwargs = {
        "model": settings.minimax_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 2048,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    stream = await client.chat.completions.create(**kwargs)
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta:
            yield chunk.choices[0]


def message_to_dict(message) -> dict:
    """Convert an OpenAI message object to a dict for conversation history.
    Preserves tool_calls and full content (including <think> tags).
    """
    result = {"role": message.role}

    if message.content is not None:
        result["content"] = message.content
    else:
        result["content"] = ""

    if hasattr(message, "tool_calls") and message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ]

    return result
