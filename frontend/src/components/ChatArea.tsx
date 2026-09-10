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
  RefreshCw
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { ChatMessage, DocFile } from '../services/api';

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
    if (activeTarget === '__general__') return { name: 'General Assistant Mode', icon: Globe, color: 'text-purple-400' };
    if (activeTarget === '__all__') return { name: `All Documents QC Mode (${files.length} files)`, icon: Files, color: 'text-blue-400' };
    return { name: `Document Focus: ${activeTarget}`, icon: FileText, color: 'text-emerald-400' };
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
    <main className="flex-1 flex flex-col h-screen overflow-hidden bg-[#0b0f19]">
      <header className="h-16 px-6 border-b border-white/10 bg-[#0d121f]/60 backdrop-blur-md flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-white/5 border border-white/10">
            <currentTarget.icon className={`w-5 h-5 ${currentTarget.color}`} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white font-heading flex items-center gap-2">
              <span>{currentTarget.name}</span>
            </h2>
            <p className="text-[11px] text-gray-400">Ask questions, generate chain of title tables, or audit QC records</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onOpenSandbox}
            className="px-3 py-1.5 text-xs font-semibold text-emerald-300 bg-emerald-950/60 hover:bg-emerald-900/80 border border-emerald-800/60 rounded-xl transition-colors flex items-center space-x-1.5"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>Python Sandbox</span>
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] max-w-2xl mx-auto text-center space-y-6">
            <div className="p-4 rounded-3xl bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-blue-500/30 shadow-2xl">
              <Bot className="w-12 h-12 text-blue-400 animate-pulse" />
            </div>

            <div className="space-y-2">
              <h3 className="text-2xl font-bold text-white font-heading">
                DocuAgent <span className="gradient-text">AI QC Intelligence</span>
              </h3>
              <p className="text-xs text-gray-400 max-w-md mx-auto leading-relaxed">
                Upload your title orders, tax snapshots, PACER & Patriot documents, or cost worksheets to get instant Quality Control audits.
              </p>
            </div>

            <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
              {quickPrompts.map((qp, i) => (
                <button
                  key={i}
                  onClick={() => onSendMessage(qp.prompt)}
                  className="p-3 text-left rounded-2xl glass-panel glass-panel-hover border border-white/10 group flex items-start space-x-3 transition-all"
                >
                  <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                  <div>
                    <span className="text-xs font-semibold text-white block">{qp.label}</span>
                    <span className="text-[11px] text-gray-400 line-clamp-1">{qp.prompt}</span>
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
                <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400 h-fit shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-3xl rounded-2xl p-4 space-y-2 shadow-xl ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'glass-panel border border-white/10 text-gray-200 rounded-bl-none'
                }`}
              >
                {msg.role === 'assistant' && msg.targetFile && (
                  <div className="flex items-center justify-between text-[10px] text-blue-300 border-b border-white/10 pb-2 mb-2">
                    <span className="flex items-center space-x-1">
                      <FileText className="w-3 h-3" />
                      <span>Context: {msg.targetFile}</span>
                    </span>
                    <button
                      onClick={() => handleCopy(msg.content, index)}
                      className="text-gray-400 hover:text-white flex items-center space-x-1 transition-colors"
                    >
                      {copiedIndex === index ? (
                        <Check className="w-3 h-3 text-emerald-400" />
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
                  <div className="prose prose-invert prose-xs max-w-none prose-table:border prose-table:border-gray-800 prose-th:bg-gray-900 prose-th:p-2 prose-td:p-2 prose-td:border-t prose-td:border-gray-800">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div className="p-2 rounded-xl bg-purple-600/20 border border-purple-500/30 text-purple-400 h-fit shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30 text-blue-400">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="glass-panel p-3 rounded-2xl border border-white/10 flex items-center space-x-2 text-xs text-blue-300">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400" />
              <span>DocuAgent AI is analyzing documents and preparing response...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-white/10 bg-[#0d121f]/90 backdrop-blur-md">
        <div className="flex items-center space-x-2 overflow-x-auto pb-2 mb-2 no-scrollbar">
          {quickPrompts.slice(0, 4).map((qp, i) => (
            <button
              key={i}
              onClick={() => onSendMessage(qp.prompt)}
              className="px-2.5 py-1 text-[11px] font-medium text-gray-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-full whitespace-nowrap transition-colors"
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
            className="w-full pr-12 pl-4 py-3 text-xs text-white bg-gray-950/80 border border-gray-800 rounded-2xl focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-gray-500 resize-none font-sans"
          />

          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-3 top-3 p-2 text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl shadow-lg shadow-blue-600/30 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </main>
  );
};
