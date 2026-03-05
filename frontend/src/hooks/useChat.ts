import { useState, useCallback, useRef } from 'react';
import { Message, ToolCallInfo, AgentStatus, AgentEvent } from '../types';
import { sendMessageStream } from '../api/client';

let messageIdCounter = 0;
function nextId(): string {
  return `msg_${++messageIdCounter}_${Date.now()}`;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<AgentStatus>('idle');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [currentToolCalls, setCurrentToolCalls] = useState<ToolCallInfo[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef(false);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || status !== 'idle') return;

    setError(null);
    abortRef.current = false;

    // Add user message
    const userMsg: Message = {
      id: nextId(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setStatus('thinking');
    setCurrentToolCalls([]);
    setStreamingContent('');

    let accumulatedContent = '';
    const toolCalls: ToolCallInfo[] = [];

    try {
      await sendMessageStream(
        text.trim(),
        conversationId,
        (event: AgentEvent) => {
          if (abortRef.current) return;

          switch (event.type) {
            case 'conversation_id':
              if (event.conversation_id) {
                setConversationId(event.conversation_id);
              }
              break;

            case 'thinking':
              setStatus('thinking');
              break;

            case 'tool_call':
              setStatus('calling_tool');
              const newToolCall: ToolCallInfo = {
                name: event.tool_name || '',
                arguments: event.tool_args || {},
              };
              toolCalls.push(newToolCall);
              setCurrentToolCalls([...toolCalls]);
              break;

            case 'tool_result':
              const lastTc = toolCalls[toolCalls.length - 1];
              if (lastTc) {
                lastTc.result = event.tool_result;
                setCurrentToolCalls([...toolCalls]);
              }
              setStatus('thinking');
              break;

            case 'token':
              setStatus('streaming');
              accumulatedContent += event.content || '';
              setStreamingContent(accumulatedContent);
              break;

            case 'response':
              accumulatedContent = event.content || accumulatedContent;
              break;

            case 'done': {
              const assistantMsg: Message = {
                id: nextId(),
                role: 'assistant',
                content: accumulatedContent,
                toolCalls: toolCalls.length > 0 ? [...toolCalls] : undefined,
                timestamp: new Date(),
              };
              setMessages(prev => [...prev, assistantMsg]);
              setStreamingContent('');
              setCurrentToolCalls([]);
              setStatus('idle');
              break;
            }

            case 'error':
              setError(event.content || 'An error occurred');
              setStatus('error');
              break;
          }
        },
        (err: Error) => {
          setError(err.message);
          setStatus('error');
        },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed');
      setStatus('error');
    }
  }, [conversationId, status]);

  const resetChat = useCallback(() => {
    abortRef.current = true;
    setMessages([]);
    setConversationId(null);
    setCurrentToolCalls([]);
    setStreamingContent('');
    setStatus('idle');
    setError(null);
  }, []);

  return {
    messages,
    status,
    conversationId,
    currentToolCalls,
    streamingContent,
    error,
    sendMessage,
    resetChat,
  };
}
