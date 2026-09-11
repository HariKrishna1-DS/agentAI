import React, { useState } from 'react';
import { Key, ShieldCheck, Cpu, X, Check, AlertCircle } from 'lucide-react';
import type { ApiKeyStatus } from '../services/api';
import { setApiKey } from '../services/api';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  status: ApiKeyStatus | null;
  onStatusUpdated: (newStatus: ApiKeyStatus) => void;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({
  isOpen,
  onClose,
  status,
  onStatusUpdated,
}) => {
  const [provider, setProvider] = useState<string>('openai');
  const [apiKey, setApiKeyInput] = useState<string>('');
  const [model, setModel] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isKeyConfigured = Boolean(status?.keys?.[provider as keyof typeof status.keys]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim() && !isKeyConfigured) {
      setError('Please enter a valid API key.');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await setApiKey(provider, apiKey.trim(), model.trim() || undefined);
      setSuccess(res.message);
      onStatusUpdated(res.status);
      setApiKeyInput('');
      setModel('');
      setTimeout(() => {
        setSuccess(null);
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err.message || 'Failed to set API key.');
    } finally {
      setLoading(false);
    }
  };

  const providers = [
    { id: 'openai', name: 'OpenAI', defaultModel: 'gpt-4o-mini', desc: 'GPT-4o, GPT-4o-mini, o1 models' },
    { id: 'groq', name: 'Groq API', defaultModel: 'openai/gpt-oss-20b', desc: 'Ultra-fast inference (Free Tier available)' },
    { id: 'gemini', name: 'Google Gemini', defaultModel: 'gemini-3.8-flash', desc: 'Gemini Flash & Pro models' },
    { id: 'openrouter', name: 'OpenRouter', defaultModel: 'openai/gpt-4o-mini', desc: 'Unified access to Claude, GPT-4o, Llama 3' },
    { id: 'claude', name: 'Anthropic Claude', defaultModel: 'claude-3-5-sonnet-20241022', desc: 'Claude 3.5 Sonnet & Haiku' },
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-md transition-opacity">
      <div className="relative w-full max-w-lg overflow-hidden glass-modal rounded-2xl border border-theme-subtle shadow-2xl animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-theme-subtle header-bg">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-theme-primary font-heading">AI Provider Settings</h3>
              <p className="text-xs text-theme-muted">Configure your API Key and active AI LLM model</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-theme-muted hover:text-theme-primary rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current Active Badge */}
        {status && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span className="text-theme-secondary">Active Provider:</span>
              <span className="font-semibold text-blue-600 dark:text-blue-400">{status.active_provider}</span>
            </div>
            <span className="text-[11px] font-mono bg-blue-600/15 px-2 py-0.5 rounded text-blue-600 dark:text-blue-300 border border-blue-500/30">
              {status.active_model}
            </span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          
          {error && (
            <div className="p-3 text-xs text-rose-600 dark:text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 text-xs text-emerald-600 dark:text-emerald-300 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center space-x-2">
              <Check className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <div>
            <label className="block mb-2 text-xs font-medium text-theme-secondary">Select Provider</label>
            <div className="grid grid-cols-2 gap-2">
              {providers.map((p) => (
                <button
                  type="button"
                  key={p.id}
                  onClick={() => {
                    setProvider(p.id);
                    setModel(p.defaultModel);
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    provider === p.id
                      ? 'bg-blue-600/15 border-blue-500 text-theme-primary shadow-sm'
                      : 'card-bg border-theme-subtle text-theme-muted hover:border-blue-500/40 hover:bg-black/5 dark:hover:bg-white/5'
                  }`}
                >
                  <div className="text-xs font-semibold text-theme-primary flex items-center justify-between">
                    {p.name}
                    {status?.keys?.[p.id as keyof typeof status.keys] && (
                      <span className="w-2 h-2 rounded-full bg-emerald-500" title="Key Configured"></span>
                    )}
                  </div>
                  <div className="text-[10px] text-theme-muted mt-1 line-clamp-1">{p.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block mb-1 text-xs font-medium text-theme-secondary">
              API Key {!isKeyConfigured && <span className="text-rose-500">*</span>}
              {isKeyConfigured && (
                <span className="text-emerald-500 text-[10px] ml-1.5 font-normal">
                  (Key already saved • Leave blank to keep existing key)
                </span>
              )}
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder={
                isKeyConfigured
                  ? `•••••••••••••••• (Saved. Enter new key to change)`
                  : `Enter your ${provider.toUpperCase()} API key...`
              }
              className="w-full px-3 py-2 text-xs text-theme-primary input-bg border border-theme-medium rounded-xl focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder:text-theme-muted font-mono"
            />
          </div>

          <div>
            <label className="block mb-1 text-xs font-medium text-theme-secondary">
              Custom Model Name <span className="text-theme-muted">(Optional)</span>
            </label>
            <div className="relative">
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder={`e.g. ${providers.find(p => p.id === provider)?.defaultModel}`}
                className="w-full px-3 py-2 pl-8 text-xs text-theme-primary input-bg border border-theme-medium rounded-xl focus:outline-none focus:border-blue-500 font-mono"
              />
              <Cpu className="w-3.5 h-3.5 text-theme-muted absolute left-2.5 top-2.5" />
            </div>
          </div>

          <div className="pt-3 flex justify-end space-x-2 border-t border-theme-subtle">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-theme-muted hover:text-theme-primary hover:bg-black/5 dark:hover:bg-white/5 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl shadow-md shadow-blue-600/30 transition-all flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  <span>{isKeyConfigured && !apiKey.trim() ? 'Switch Provider' : 'Activate Key'}</span>
                </>
              )}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
};
