import { useState } from 'react';
import { ChevronDown, ChevronRight, Search, Package, ListChecks, PhoneForwarded, CheckCircle2, Loader2 } from 'lucide-react';
import { ToolCallInfo } from '../types';

interface Props {
  toolCalls: ToolCallInfo[];
  isActive?: boolean;
}

const toolIcons: Record<string, React.ReactNode> = {
  search_knowledge_base: <Search className="w-3.5 h-3.5" />,
  get_product_info: <Package className="w-3.5 h-3.5" />,
  get_troubleshooting_steps: <ListChecks className="w-3.5 h-3.5" />,
  escalate_to_human: <PhoneForwarded className="w-3.5 h-3.5" />,
};

const toolLabels: Record<string, string> = {
  search_knowledge_base: 'Searching Knowledge Base',
  get_product_info: 'Looking Up Product',
  get_troubleshooting_steps: 'Getting Troubleshooting Steps',
  escalate_to_human: 'Escalating to Human Agent',
};

function ToolCallCard({ tc, isLast, isActive }: { tc: ToolCallInfo; isLast: boolean; isActive: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const hasResult = tc.result !== undefined;
  const isPending = isLast && isActive && !hasResult;

  let parsedResult: Record<string, unknown> | null = null;
  if (tc.result) {
    try {
      parsedResult = JSON.parse(tc.result);
    } catch {
      // Keep as string
    }
  }

  return (
    <div className="tool-card-enter border border-slate-200 rounded-lg overflow-hidden bg-white/80 backdrop-blur-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-50 transition-colors"
      >
        <span className="text-[var(--color-reolink-blue)]">
          {toolIcons[tc.name] || <Search className="w-3.5 h-3.5" />}
        </span>
        <span className="text-xs font-medium text-slate-700 flex-1">
          {toolLabels[tc.name] || tc.name}
        </span>
        {isPending ? (
          <Loader2 className="w-3.5 h-3.5 text-[var(--color-reolink-blue)] animate-spin" />
        ) : hasResult ? (
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
        ) : null}
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
        )}
      </button>

      {expanded && (
        <div className="border-t border-slate-100 px-3 py-2 space-y-2">
          <div>
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Arguments</span>
            <pre className="text-xs text-slate-600 bg-slate-50 rounded p-2 mt-1 overflow-x-auto">
              {JSON.stringify(tc.arguments, null, 2)}
            </pre>
          </div>
          {tc.result && (
            <div>
              <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Result</span>
              <pre className="text-xs text-slate-600 bg-slate-50 rounded p-2 mt-1 overflow-x-auto max-h-48 overflow-y-auto custom-scrollbar">
                {parsedResult ? JSON.stringify(parsedResult, null, 2) : tc.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ToolCallDisplay({ toolCalls, isActive = false }: Props) {
  if (toolCalls.length === 0) return null;

  return (
    <div className="space-y-1.5 my-2">
      <div className="flex items-center gap-1.5">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider px-2">
          Agent Loop — {toolCalls.length} tool call{toolCalls.length > 1 ? 's' : ''}
        </span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>
      {toolCalls.map((tc, i) => (
        <ToolCallCard
          key={`${tc.name}-${i}`}
          tc={tc}
          isLast={i === toolCalls.length - 1}
          isActive={isActive}
        />
      ))}
    </div>
  );
}
