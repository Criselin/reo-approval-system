import { Loader2 } from 'lucide-react';
import { AgentStatus } from '../types';

interface Props {
  status: AgentStatus;
}

const statusMessages: Record<AgentStatus, string> = {
  idle: '',
  thinking: 'Agent is thinking...',
  calling_tool: 'Executing tool...',
  streaming: 'Generating response...',
  error: 'An error occurred',
};

export function AgentThinking({ status }: Props) {
  if (status === 'idle') return null;

  return (
    <div className="flex items-center gap-3 px-4 py-3 message-enter">
      <div className="w-8 h-8 rounded-full bg-[var(--color-reolink-blue)] flex items-center justify-center flex-shrink-0">
        <Loader2 className="w-4 h-4 text-white animate-spin" />
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-500">{statusMessages[status]}</span>
        <div className="flex gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-reolink-blue)] thinking-dot" />
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-reolink-blue)] thinking-dot" />
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-reolink-blue)] thinking-dot" />
        </div>
      </div>
    </div>
  );
}
