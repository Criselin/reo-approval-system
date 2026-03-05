"""SSE (Server-Sent Events) streaming utilities."""

import json
from backend.models.schemas import AgentEvent


def format_sse_event(event: AgentEvent) -> dict:
    """Format an AgentEvent for SSE transmission."""
    return {
        "event": event.type,
        "data": event.model_dump_json(),
    }
