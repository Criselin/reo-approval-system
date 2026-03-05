"""API route definitions."""

import json
import uuid
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
    HealthResponse,
    BatchRunRequest,
    BatchRunResponse,
)
from backend.models.conversation import (
    get_or_create_conversation,
    get_conversation,
    delete_conversation,
    list_conversations,
)
from backend.agent.loop import agent_loop_stream, agent_loop_sync
from backend.api.sse import format_sse_event

router = APIRouter()


@router.get("/api/health")
async def health_check() -> HealthResponse:
    return HealthResponse()


@router.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming chat endpoint. The primary endpoint for the frontend."""
    conversation = get_or_create_conversation(request.conversation_id)
    conversation.add_user_message(request.message)

    async def event_generator():
        # First emit conversation_id so frontend can track it
        yield {
            "event": "conversation_id",
            "data": json.dumps({"conversation_id": conversation.id}),
        }

        async for event in agent_loop_stream(conversation):
            yield format_sse_event(event)

    return EventSourceResponse(event_generator())


@router.post("/api/chat")
async def chat_sync(request: ChatRequest) -> ChatResponse:
    """Non-streaming chat endpoint for testing/batch use."""
    conversation = get_or_create_conversation(request.conversation_id)
    conversation.add_user_message(request.message)

    result = await agent_loop_sync(conversation)

    return ChatResponse(
        conversation_id=conversation.id,
        response=result["response"],
        tool_calls=[
            {"name": tc["name"], "arguments": tc["arguments"], "result": tc["result"]}
            for tc in result.get("tool_calls", [])
        ],
    )


@router.get("/api/conversations")
async def get_conversations():
    """List all conversations."""
    return list_conversations()


@router.get("/api/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: str) -> ConversationResponse:
    """Get a specific conversation with full history."""
    conv = get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = [
        MessageResponse(
            role=m.role,
            content=m.content,
            tool_calls=[
                {"name": tc["name"], "arguments": tc["arguments"], "result": tc.get("result")}
                for tc in (m.tool_calls or [])
            ],
            timestamp=m.timestamp,
        )
        for m in conv.messages
        if m.role in ("user", "assistant")
    ]

    return ConversationResponse(
        conversation_id=conv.id,
        messages=messages,
        created_at=conv.created_at,
    )


@router.delete("/api/conversations/{conversation_id}")
async def remove_conversation(conversation_id: str):
    """Delete a conversation."""
    if delete_conversation(conversation_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/api/batch/run")
async def run_batch_test(request: BatchRunRequest) -> BatchRunResponse:
    """Trigger a batch test run."""
    from backend.batch.runner import run_batch_tests

    run_id = str(uuid.uuid4())[:8]

    import asyncio
    asyncio.create_task(
        run_batch_tests(
            run_id=run_id,
            scenario_ids=request.scenario_ids,
            concurrency=request.concurrency,
        )
    )

    return BatchRunResponse(
        run_id=run_id,
        status="running",
        total_scenarios=0,  # Will be determined by the runner
    )


@router.get("/api/batch/results/{run_id}")
async def get_batch_results(run_id: str):
    """Get batch test results."""
    from backend.batch.runner import get_results

    results = get_results(run_id)
    if results is None:
        raise HTTPException(status_code=404, detail="Run not found or still in progress")
    return results
