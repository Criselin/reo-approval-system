import { useChat } from '../hooks/useChat';
import { MessageList } from './MessageList';
import { InputBar } from './InputBar';
import { Sidebar } from './Sidebar';
import { AlertCircle, X } from 'lucide-react';

export function ChatWindow() {
  const {
    messages,
    status,
    conversationId,
    currentToolCalls,
    streamingContent,
    error,
    sendMessage,
    resetChat,
  } = useChat();

  return (
    <div className="flex h-screen bg-slate-100">
      {/* Sidebar */}
      <Sidebar
        currentConversationId={conversationId}
        onNewChat={resetChat}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-200 flex items-center px-4 gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <h2 className="text-sm font-semibold text-slate-800">Reolink Support Assistant</h2>
          </div>
          {conversationId && (
            <span className="text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
              {conversationId.slice(0, 8)}
            </span>
          )}
          <div className="ml-auto flex items-center gap-2">
            {status !== 'idle' && (
              <span className="text-xs text-[var(--color-reolink-blue)] font-medium">
                {status === 'thinking' && 'Thinking...'}
                {status === 'calling_tool' && 'Using tools...'}
                {status === 'streaming' && 'Responding...'}
              </span>
            )}
          </div>
        </header>

        {/* Error Banner */}
        {error && (
          <div className="mx-4 mt-2 flex items-center gap-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span className="flex-1">{error}</span>
            <button onClick={() => {}} className="text-red-400 hover:text-red-600">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Messages */}
        <MessageList
          messages={messages}
          status={status}
          currentToolCalls={currentToolCalls}
          streamingContent={streamingContent}
        />

        {/* Input */}
        <InputBar onSend={sendMessage} status={status} />
      </div>
    </div>
  );
}
