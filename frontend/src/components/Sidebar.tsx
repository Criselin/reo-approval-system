import { useState, useEffect } from 'react';
import { Plus, MessageSquare, Trash2, Camera, Shield } from 'lucide-react';
import { ConversationSummary } from '../types';
import { fetchConversations, deleteConversation } from '../api/client';

interface Props {
  currentConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation?: (id: string) => void;
}

export function Sidebar({ currentConversationId, onNewChat }: Props) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const loadConversations = async () => {
    try {
      const data = await fetchConversations();
      setConversations(data);
    } catch {
      // Silently fail - conversations are optional
    }
  };

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await deleteConversation(id);
    loadConversations();
  };

  if (isCollapsed) {
    return (
      <div className="w-16 bg-slate-900 flex flex-col items-center py-4 gap-4">
        <button
          onClick={() => setIsCollapsed(false)}
          className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition-colors"
        >
          <Camera className="w-5 h-5 text-white" />
        </button>
        <button
          onClick={onNewChat}
          className="w-10 h-10 rounded-lg bg-[var(--color-reolink-blue)] flex items-center justify-center hover:bg-[var(--color-reolink-dark)] transition-colors"
        >
          <Plus className="w-5 h-5 text-white" />
        </button>
      </div>
    );
  }

  return (
    <div className="w-72 bg-slate-900 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[var(--color-reolink-blue)] flex items-center justify-center">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">Reolink</h1>
            <p className="text-[10px] text-slate-400">AI Customer Service</p>
          </div>
          <button
            onClick={() => setIsCollapsed(true)}
            className="ml-auto text-slate-500 hover:text-slate-300 text-xs"
          >
            ←
          </button>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors text-sm"
        >
          <Plus className="w-4 h-4" />
          New Conversation
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-3 space-y-1">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
              conv.id === currentConversationId
                ? 'bg-slate-700 text-white'
                : 'text-slate-400 hover:bg-slate-800 hover:text-slate-300'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="text-xs truncate flex-1">
              {conv.preview || `Conversation ${conv.id.slice(0, 8)}`}
            </span>
            <button
              onClick={(e) => handleDelete(conv.id, e)}
              className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition-all"
            >
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-700">
        <div className="text-[10px] text-slate-500 text-center space-y-0.5">
          <p>Agent Loop Architecture</p>
          <p>MiniMax LLM · TF-IDF Knowledge Base</p>
        </div>
      </div>
    </div>
  );
}
