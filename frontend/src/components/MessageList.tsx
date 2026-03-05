import { useEffect, useRef } from 'react';
import { Message, ToolCallInfo, AgentStatus } from '../types';
import { MessageBubble } from './MessageBubble';
import { ToolCallDisplay } from './ToolCallDisplay';
import { AgentThinking } from './AgentThinking';
import { Bot } from 'lucide-react';

interface Props {
  messages: Message[];
  status: AgentStatus;
  currentToolCalls: ToolCallInfo[];
  streamingContent: string;
}

export function MessageList({ messages, status, currentToolCalls, streamingContent }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, status, streamingContent, currentToolCalls]);

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar px-4 py-6 space-y-4">
      {/* Welcome message */}
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center space-y-4 py-12">
          <div className="w-16 h-16 rounded-full bg-[var(--color-reolink-blue)] flex items-center justify-center">
            <Bot className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-slate-800">Reolink Support Assistant</h2>
            <p className="text-sm text-slate-500 mt-2 max-w-md">
              Hi! I'm your Reolink intelligent support assistant. I can help you troubleshoot
              issues with cameras, NVRs, doorbells, and more. How can I help you today?
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4 max-w-lg">
            {[
              'My camera is showing offline',
              'Night vision is blurry',
              'Motion detection not working',
              'NVR not recording',
            ].map((suggestion) => (
              <button
                key={suggestion}
                className="text-xs text-left px-3 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-[var(--color-reolink-light)] hover:border-[var(--color-reolink-blue)] hover:text-[var(--color-reolink-blue)] transition-all"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {/* Active tool calls (during agent processing) */}
      {currentToolCalls.length > 0 && status !== 'idle' && (
        <div className="flex gap-3 message-enter">
          <div className="w-8 h-8 rounded-full bg-[var(--color-reolink-blue)] flex items-center justify-center flex-shrink-0">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div className="max-w-[75%]">
            <ToolCallDisplay toolCalls={currentToolCalls} isActive />
          </div>
        </div>
      )}

      {/* Streaming response */}
      {streamingContent && status === 'streaming' && (
        <div className="flex gap-3 message-enter">
          <div className="w-8 h-8 rounded-full bg-[var(--color-reolink-blue)] flex items-center justify-center flex-shrink-0">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div className="max-w-[75%]">
            <div className="rounded-2xl rounded-tl-md px-4 py-2.5 bg-white border border-slate-200 shadow-sm">
              <div className="text-sm leading-relaxed whitespace-pre-wrap text-slate-800">
                {streamingContent}
                <span className="typing-cursor" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Thinking indicator */}
      {(status === 'thinking' || (status === 'calling_tool' && currentToolCalls.length === 0)) && (
        <AgentThinking status={status} />
      )}

      <div ref={bottomRef} />
    </div>
  );
}
