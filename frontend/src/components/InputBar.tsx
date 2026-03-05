import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { AgentStatus } from '../types';

interface Props {
  onSend: (message: string) => void;
  status: AgentStatus;
}

export function InputBar({ onSend, status }: Props) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isDisabled = status !== 'idle' && status !== 'error';

  useEffect(() => {
    if (status === 'idle') {
      textareaRef.current?.focus();
    }
  }, [status]);

  const handleSubmit = () => {
    if (!input.trim() || isDisabled) return;
    onSend(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <div className="flex items-end gap-2 max-w-4xl mx-auto">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => { setInput(e.target.value); handleInput(); }}
            onKeyDown={handleKeyDown}
            placeholder={isDisabled ? 'Agent is processing...' : 'Describe your issue...'}
            disabled={isDisabled}
            rows={1}
            className="w-full resize-none rounded-xl border border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[var(--color-reolink-blue)] focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          />
        </div>
        <button
          onClick={handleSubmit}
          disabled={!input.trim() || isDisabled}
          className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-reolink-blue)] text-white hover:bg-[var(--color-reolink-dark)] disabled:opacity-40 disabled:cursor-not-allowed transition-all flex-shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
      <p className="text-[10px] text-slate-400 text-center mt-2">
        Powered by MiniMax AI · Agent Loop Architecture
      </p>
    </div>
  );
}
