import { AgentEvent } from '../types';

const API_BASE = '/api';

/**
 * Send a message via SSE streaming POST.
 * Uses fetch + ReadableStream since EventSource only supports GET.
 */
export async function sendMessageStream(
  message: string,
  conversationId: string | null,
  onEvent: (event: AgentEvent) => void,
  onError: (error: Error) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = '';
      let currentData = '';

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim();
        } else if (line.startsWith('data:')) {
          currentData = line.slice(5).trim();
        } else if (line === '' && currentData) {
          // Empty line = end of SSE message
          try {
            const parsed = JSON.parse(currentData);
            if (currentEvent === 'conversation_id') {
              onEvent({
                type: 'conversation_id',
                conversation_id: parsed.conversation_id,
              });
            } else {
              onEvent(parsed as AgentEvent);
            }
          } catch {
            // Skip unparseable events
          }
          currentEvent = '';
          currentData = '';
        }
      }
    }
  } catch (error) {
    onError(error instanceof Error ? error : new Error(String(error)));
  }
}

/**
 * Fetch conversation list.
 */
export async function fetchConversations() {
  const res = await fetch(`${API_BASE}/conversations`);
  return res.json();
}

/**
 * Fetch conversation detail.
 */
export async function fetchConversation(id: string) {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  return res.json();
}

/**
 * Delete a conversation.
 */
export async function deleteConversation(id: string) {
  await fetch(`${API_BASE}/conversations/${id}`, { method: 'DELETE' });
}
