export interface ToolCallInfo {
  name: string;
  arguments: Record<string, unknown>;
  result?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  toolCalls?: ToolCallInfo[];
  timestamp: Date;
  isStreaming?: boolean;
}

export interface AgentEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'token' | 'response' | 'error' | 'done' | 'conversation_id';
  content?: string;
  tool_name?: string;
  tool_args?: Record<string, unknown>;
  tool_result?: string;
  conversation_id?: string;
}

export interface ConversationSummary {
  id: string;
  created_at: string;
  message_count: number;
  preview: string;
}

export type AgentStatus = 'idle' | 'thinking' | 'calling_tool' | 'streaming' | 'error';
