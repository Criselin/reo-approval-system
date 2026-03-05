"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str


class ToolCallInfo(BaseModel):
    name: str
    arguments: dict
    result: str | None = None


class AgentEvent(BaseModel):
    """SSE event emitted during agent loop execution."""

    type: Literal["thinking", "tool_call", "tool_result", "token", "response", "error", "done"]
    content: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: str | None = None


class MessageResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)
    timestamp: str


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    tool_calls: list[ToolCallInfo] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: list[MessageResponse]
    created_at: str


class BatchRunRequest(BaseModel):
    scenario_ids: list[str] | None = None
    concurrency: int = 3


class BatchRunResponse(BaseModel):
    run_id: str
    status: str
    total_scenarios: int


class EvalScore(BaseModel):
    score: int = Field(ge=1, le=5)
    reasoning: str


class EvalResult(BaseModel):
    relevance: EvalScore
    accuracy: EvalScore
    helpfulness: EvalScore
    tone: EvalScore
    overall: EvalScore


class HealthResponse(BaseModel):
    status: str = "ok"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
