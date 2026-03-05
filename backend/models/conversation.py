"""In-memory conversation state management."""

import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Conversation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    escalated: bool = False

    def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))

    def add_assistant_message(self, content: str, tool_calls: list[dict] | None = None):
        self.messages.append(
            Message(role="assistant", content=content, tool_calls=tool_calls)
        )

    def get_display_messages(self) -> list[dict]:
        """Get messages suitable for display (user + assistant only)."""
        return [
            {
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "timestamp": m.timestamp,
            }
            for m in self.messages
            if m.role in ("user", "assistant")
        ]


# In-memory conversation store
_conversations: dict[str, Conversation] = {}


def get_or_create_conversation(conversation_id: str | None = None) -> Conversation:
    if conversation_id and conversation_id in _conversations:
        return _conversations[conversation_id]

    conv = Conversation()
    _conversations[conv.id] = conv
    return conv


def get_conversation(conversation_id: str) -> Conversation | None:
    return _conversations.get(conversation_id)


def delete_conversation(conversation_id: str) -> bool:
    if conversation_id in _conversations:
        del _conversations[conversation_id]
        return True
    return False


def list_conversations() -> list[dict]:
    return [
        {
            "id": c.id,
            "created_at": c.created_at,
            "message_count": len(c.messages),
            "preview": c.messages[0].content[:100] if c.messages else "",
        }
        for c in sorted(
            _conversations.values(),
            key=lambda x: x.created_at,
            reverse=True,
        )
    ]
