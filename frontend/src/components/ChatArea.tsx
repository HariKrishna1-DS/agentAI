import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Files,
  Globe,
  FileText,
  Copy,
  Check,
  Terminal,
  RefreshCw,
  Sun,
  Moon
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage, DocFile } from '../services/api';
import { useTheme } from '../context/ThemeContext';

interface ChatAreaProps {
  messages: ChatMessage[];
  activeTarget: string;
  files: DocFile[];
  onSendMessage: (text: string) => void;
  onOpenSandbox: () => void;
  loading: boolean;
}

export const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  activeTarget,
  files,
  onSendMessage,
  onOpenSandbox,
  loading,
}) => {
  const { isNight, toggleTheme } = useTheme();
  const [input, setInput] = useState<string>('');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleCopy = (content: string, index: number) => {
    navigator.clipboard.writeText(content);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  };

  const getTargetTitle = () => {
    if (activeTarget === '__general__') return { name: 'General Assistant Mode', icon: Globe, color: 'text-purple-500' };
    if (activeTarget === '__all__') return { name: `All Documents QC Mode (${files.length} files)`, icon: Files, color: 'text-blue-500' };
    return { name: `Document Focus: ${activeTarget}`, icon: FileText, color: 'text-emerald-500' };
  };

  const currentTarget = getTargetTitle();

  const quickPrompts = [
    { label: '🔍 Verify Order IDs', prompt: 'Cross-verify Order IDs across all uploaded documents and point out any discrepancies.' },
    { label: '👤 Check Borrower Names', prompt: 'Verify borrower and property owner names across Search Package, Tax, Appraisal, and PA snapshots.' },
    { label: '⚖️ PACER & Patriot Screening', prompt: 'Check PACER for bankruptcy filings and Patriot Act (OFAC/SDN) lists for any negative hits.' },
    { label: '🏛️ Tax Status Audit', prompt: 'Audit property tax status across tax snapshot files and state if paid, open, or delinquent.' },
    { label: '💰 Fee Reconciliation', prompt: 'Reconcile fees and charges from the Cost Worksheet against invoice records.' },
  ];

  return (
    <main className="flex-1 flex flex-col h-screen overflow-hidden app-bg transition-colors duration-200">
      
      {/* Top Header Bar */}
      <header className="h-16 px-6 border-b border-theme-subtle header-bg backdrop-blur-md flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl card-bg border border-theme-subtle shadow-sm">
            <currentTarget.icon className={`w-5 h-5 ${currentTarget.color}`} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-theme-primary font-heading flex items-center gap-2">
              <span>{currentTarget.name}</span>
            </h2>
            <p className="text-[11px] text-theme-muted">Ask questions, generate chain of title tables, or audit QC records</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Header Theme Toggle */}
          <button
            onClick={toggleTheme}
            title={isNight ? "Switch to White Mode" : "Switch to Night Mode"}
            className="px-3 py-1.5 text-xs font-semibold card-bg hover:bg-black/5 dark:hover:bg-white/10 border border-theme-subtle rounded-xl transition-all flex items-center space-x-1.5 text-theme-secondary hover:text-theme-primary shadow-sm"
          >
            {isNight ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span>White Mode</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-indigo-600" />
                <span>Night Mode</span>
              </>
            )}
          </button>

          <button
            onClick={onOpenSandbox}
            className="px-3 py-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-300 bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 rounded-xl transition-colors flex items-center space-x-1.5 shadow-sm"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Python Sandbox</span>
          </button>
        </div>
      </header>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-2xl mx-auto text-center space-y-6">
            <div className="p-4 rounded-3xl bg-gradient-to-br from-blue-500/15 to-purple-500/15 border border-blue-500/30 shadow-xl">
              <Bot className="w-12 h-12 text-blue-500 animate-pulse" />
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-bold text-theme-primary font-heading">
                DocuAgent <span className="gradient-text">AI QC Intelligence</span>
              </h3>
              <p className="text-xs text-theme-muted max-w-md mx-auto leading-relaxed">
                Upload your title orders, tax snapshots, PACER & Patriot documents, or cost worksheets to get instant Quality Control audits.
              </p>
            </div>

            <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
              {quickPrompts.map((qp, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(qp.prompt)}
                  className="p-3 text-left rounded-2xl glass-panel glass-panel-hover border border-theme-subtle group flex items-start space-x-3 transition-all"
                >
                  <Sparkles className="w-4 h-4 text-blue-500 shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                  <div>
                    <span className="text-xs font-semibold text-theme-primary block">{qp.label}</span>
                    <span className="text-[11px] text-theme-muted line-clamp-1">{qp.prompt}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`flex space-x-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role !== 'user' && (
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-500 h-fit shrink-0 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-3xl rounded-2xl p-4 space-y-2 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'glass-panel border border-theme-subtle text-theme-primary rounded-bl-none'
                }`}
              >
                {msg.role === 'assistant' && msg.targetFile && (
                  <div className="flex items-center justify-between text-[10px] text-blue-500 dark:text-blue-400 border-b border-theme-subtle pb-2 mb-2 font-medium">
                    <span className="flex items-center space-x-1">
                      <FileText className="w-3 h-3" />
                      <span>Context: {msg.targetFile}</span>
                    </span>
                    <button
                      onClick={() => handleCopy(msg.content, index)}
                      className="text-theme-muted hover:text-theme-primary flex items-center space-x-1 transition-colors"
                    >
                      {copiedIndex === index ? (
                        <Check className="w-3 h-3 text-emerald-500" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                      <span>{copiedIndex === index ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>
                )}

                {msg.role === 'user' ? (
                  <p className="text-xs font-medium whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose dark:prose-invert prose-xs max-w-none text-theme-primary prose-headings:text-theme-primary prose-strong:text-theme-primary prose-code:text-blue-600 dark:prose-code:text-blue-300 prose-code:bg-black/5 dark:prose-code:bg-white/10 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-table:border prose-table:border-theme-subtle prose-th:bg-slate-100 dark:prose-th:bg-slate-800/90 prose-th:text-theme-primary prose-th:p-2 prose-td:p-2 prose-td:border-t prose-td:border-theme-subtle">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-500 h-fit shrink-0 shadow-sm">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-500 shadow-sm">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="glass-panel p-3 rounded-2xl border border-theme-subtle flex items-center space-x-2 text-xs text-blue-600 dark:text-blue-300 shadow-sm">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-500" />
              <span>DocuAgent AI is analyzing documents and preparing response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-4 border-t border-theme-subtle header-bg backdrop-blur-md">
        <div className="flex items-center space-x-2 overflow-x-auto pb-2 mb-2 no-scrollbar">
          {quickPrompts.slice(0, 4).map((qp, i) => (
            <button
              key={i}
              onClick={() => onSendMessage(qp.prompt)}
              className="px-2.5 py-1 text-[11px] font-medium text-theme-secondary hover:text-theme-primary card-bg hover:bg-black/5 dark:hover:bg-white/10 border border-theme-subtle rounded-full whitespace-nowrap transition-colors shadow-sm"
            >
              {qp.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="relative flex items-center">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Ask a question or audit ${currentTarget.name}... (Press Enter to send, Shift+Enter for newline)`}
            rows={2}
            className="w-full pr-12 pl-4 py-3 text-xs text-theme-primary input-bg border border-theme-medium rounded-2xl focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder:text-theme-muted resize-none font-sans shadow-sm"
          />

          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-3 top-3 p-2 text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl shadow-md shadow-blue-600/30 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </main>
  );
};
