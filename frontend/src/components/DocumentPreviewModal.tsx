import React, { useState, useEffect } from 'react';
import { FileText, Image, FileCode, X, Download, ExternalLink, RefreshCw } from 'lucide-react';
import type { DocFile } from '../services/api';
import { getRawFileUrl } from '../services/api';

interface DocumentPreviewModalProps {
  file: DocFile | null;
  onClose: () => void;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({ file, onClose }) => {
  const [textContent, setTextContent] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!file) return;

    if (file.type === 'text' || file.ext === '.txt' || file.ext === '.docx') {
      setLoading(true);
      setError(null);
      fetch(getRawFileUrl(file.name))
        .then((res) => {
          if (!res.ok) throw new Error('Could not load text preview.');
          return res.text();
        })
        .then((text) => {
          setTextContent(text);
        })
        .catch((err) => {
          setError(err.message);
        })
        .finally(() => setLoading(false));
    } else {
      setTextContent(null);
    }
  }, [file]);

  if (!file) return null;

  const rawUrl = getRawFileUrl(file.name);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 dark:bg-black/80 backdrop-blur-md transition-opacity">
      <div className="relative w-full max-w-4xl max-h-[85vh] flex flex-col glass-modal rounded-2xl border border-theme-subtle shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-theme-subtle header-bg shrink-0">
          <div className="flex items-center space-x-3 truncate pr-4">
            <div className="p-2 rounded-lg bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
              {file.type === 'image' ? (
                <Image className="w-5 h-5" />
              ) : file.type === 'pdf' ? (
                <FileText className="w-5 h-5 text-rose-500" />
              ) : (
                <FileCode className="w-5 h-5 text-emerald-500" />
              )}
            </div>
            <div className="truncate">
              <h3 className="text-sm font-semibold text-theme-primary font-heading truncate">{file.name}</h3>
              <p className="text-[11px] text-theme-muted">{file.size_kb} KB • {file.ext.toUpperCase()}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <a
              href={rawUrl}
              target="_blank"
              rel="noreferrer"
              className="p-2 text-xs font-medium text-theme-secondary hover:text-theme-primary card-bg hover:bg-black/5 dark:hover:bg-white/10 border border-theme-subtle rounded-lg flex items-center space-x-1.5 transition-colors shadow-sm"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Open Raw</span>
            </a>
            <button
              onClick={onClose}
              className="p-1.5 text-theme-muted hover:text-theme-primary rounded-lg hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Viewer Body */}
        <div className="flex-1 overflow-y-auto p-6 app-bg min-h-[300px]">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 space-y-3">
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
              <p className="text-xs text-theme-muted">Loading document preview...</p>
            </div>
          ) : error ? (
            <div className="p-4 text-xs text-rose-600 dark:text-rose-300 bg-rose-500/10 border border-rose-500/30 rounded-xl">
              {error}
            </div>
          ) : file.type === 'image' ? (
            <div className="flex items-center justify-center p-4">
              <img
                src={rawUrl}
                alt={file.name}
                className="max-h-[60vh] max-w-full rounded-xl border border-theme-subtle card-bg shadow-xl object-contain"
              />
            </div>
          ) : file.type === 'pdf' ? (
            <iframe
              src={rawUrl}
              title={file.name}
              className="w-full h-[60vh] rounded-xl border border-theme-subtle card-bg"
            />
          ) : textContent ? (
            <pre className="p-4 text-xs font-mono text-theme-primary card-bg rounded-xl border border-theme-subtle overflow-x-auto whitespace-pre-wrap shadow-sm">
              {textContent}
            </pre>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <FileText className="w-12 h-12 text-theme-muted mb-2 opacity-50" />
              <p className="text-xs text-theme-primary font-medium">Binary document preview</p>
              <p className="text-[11px] text-theme-muted max-w-xs mt-1">
                You can inspect this document using DocuAgent AI chat prompts or open it in a new window.
              </p>
              <a
                href={rawUrl}
                download
                className="mt-4 px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-xl flex items-center space-x-2 shadow-md shadow-blue-600/30 transition-all"
              >
                <Download className="w-4 h-4" />
                <span>Download File</span>
              </a>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};
