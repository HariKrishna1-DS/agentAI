import React, { useState } from 'react';
import { Terminal, Play, X, Copy, Check } from 'lucide-react';
import { runCodeSnippet } from '../services/api';

interface CodeSandboxModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialCode?: string;
}

export const CodeSandboxModal: React.FC<CodeSandboxModalProps> = ({
  isOpen,
  onClose,
  initialCode = '# Write Python code here...\nprint("Hello from DocuAgent Python Engine!")',
}) => {
  const [code, setCode] = useState<string>(initialCode);
  const [output, setOutput] = useState<string | null>(null);
  const [running, setRunning] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleRun = async () => {
    if (!code.trim()) return;
    setRunning(true);
    try {
      const res = await runCodeSnippet(code);
      setOutput(res.output);
    } catch (err: any) {
      setOutput(`Error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-md transition-opacity">
      <div className="relative w-full max-w-3xl flex flex-col glass-modal rounded-2xl border border-theme-subtle shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-theme-subtle header-bg">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-theme-primary font-heading">Python Code Sandbox</h3>
              <p className="text-[11px] text-theme-muted">Execute Python code directly in DocuAgent AI engine</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="p-1.5 text-xs text-theme-muted hover:text-theme-primary card-bg hover:bg-black/5 dark:hover:bg-white/10 border border-theme-subtle rounded-lg transition-colors flex items-center space-x-1 shadow-sm"
              title="Copy Code"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-theme-muted hover:text-theme-primary rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4 app-bg">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-theme-secondary flex items-center space-x-1.5">
                <span>Code Editor</span>
                <span className="text-[10px] bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/30 font-mono">
                  Python 3.13
                </span>
              </span>
              <button
                onClick={handleRun}
                disabled={running}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-xl shadow-md shadow-emerald-600/30 flex items-center space-x-1.5 transition-all"
              >
                {running ? (
                  <>
                    <div className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    <span>Executing...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Run Code</span>
                  </>
                )}
              </button>
            </div>
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              rows={8}
              spellCheck={false}
              className="w-full p-4 text-xs font-mono text-emerald-700 dark:text-emerald-300 input-bg border border-theme-medium rounded-xl focus:outline-none focus:border-emerald-500 font-medium leading-relaxed resize-none shadow-sm"
            />
          </div>

          {output !== null && (
            <div>
              <span className="block mb-1 text-xs font-medium text-theme-secondary">Execution Output</span>
              <pre className="p-4 text-xs font-mono text-slate-100 bg-slate-900 border border-slate-700 rounded-xl max-h-48 overflow-y-auto whitespace-pre-wrap shadow-inner">
                {output || '<No output returned>'}
              </pre>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
