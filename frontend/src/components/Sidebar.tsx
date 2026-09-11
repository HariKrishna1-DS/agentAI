import React, { useRef, useState } from 'react';
import {
  FileText,
  UploadCloud,
  Trash2,
  Eye,
  Zap,
  Globe,
  Files,
  ShieldCheck,
  Key,
  Image,
  FileCode,
  Sparkles,
  Sun,
  Moon
} from 'lucide-react';
import type { DocFile, ApiKeyStatus } from '../services/api';
import { useTheme } from '../context/ThemeContext';

interface SidebarProps {
  files: DocFile[];
  activeTarget: string;
  onSelectTarget: (target: string) => void;
  onUpload: (files: FileList | File[]) => void;
  onDeleteFile: (filename: string) => void;
  onPreviewFile: (file: DocFile) => void;
  onRunAudit: () => void;
  isAuditing: boolean;
  status: ApiKeyStatus | null;
  onOpenSettings: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  files,
  activeTarget,
  onSelectTarget,
  onUpload,
  onDeleteFile,
  onPreviewFile,
  onRunAudit,
  isAuditing,
  status,
  onOpenSettings,
}) => {
  const { isNight, toggleTheme, theme } = useTheme();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onUpload(e.dataTransfer.files);
    }
  };

  const renderFileIcon = (file: DocFile) => {
    if (file.type === 'image') return <Image className="w-4 h-4 text-purple-400" />;
    if (file.type === 'pdf') return <FileText className="w-4 h-4 text-rose-400" />;
    return <FileCode className="w-4 h-4 text-emerald-400" />;
  };

  return (
    <aside className="w-80 sidebar-bg border-r border-theme-subtle flex flex-col h-screen shrink-0 select-none transition-colors duration-200">
      
      {/* Brand Header */}
      <div className="p-4 border-b border-theme-subtle flex items-center justify-between header-bg">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-md shadow-blue-500/30">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-extrabold text-theme-primary font-heading tracking-tight flex items-center gap-1.5">
              <span>DocuAgent</span>
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-600 dark:text-blue-400 border border-blue-500/30">
                AI
              </span>
            </h1>
            <p className="text-[11px] text-theme-muted">QC & Document Intelligence</p>
          </div>
        </div>

        {/* Theme Toggle Button (White & Night Mode) */}
        <button
          onClick={toggleTheme}
          title={isNight ? "Switch to White Mode" : "Switch to Night Mode"}
          className="p-2 rounded-xl card-bg border border-theme-subtle hover:border-blue-500/40 text-theme-secondary hover:text-theme-primary transition-all flex items-center justify-center group shadow-sm"
          aria-label="Toggle Theme Mode"
        >
          {isNight ? (
            <Sun className="w-4 h-4 text-amber-400 group-hover:rotate-45 transition-transform" />
          ) : (
            <Moon className="w-4 h-4 text-indigo-600 group-hover:-rotate-12 transition-transform" />
          )}
        </button>
      </div>

      {/* AI Key & Provider Bar */}
      <div className="px-4 py-3 border-b border-theme-subtle bg-black/[0.02] dark:bg-white/[0.02]">
        <button
          onClick={onOpenSettings}
          className="w-full p-2.5 rounded-xl card-bg hover:bg-black/5 dark:hover:bg-white/5 border border-theme-subtle hover:border-blue-500/50 transition-all flex items-center justify-between group shadow-sm"
        >
          <div className="flex items-center space-x-2 truncate">
            <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
            <div className="text-left truncate">
              <div className="text-[10px] text-theme-muted uppercase tracking-wider font-semibold">Active AI Engine</div>
              <div className="text-xs font-semibold text-theme-primary truncate">
                {status ? status.active_provider : 'Configuring...'}
                {status && <span className="text-theme-muted font-normal ml-1">({status.active_model})</span>}
              </div>
            </div>
          </div>
          <Key className="w-4 h-4 text-theme-muted group-hover:text-blue-500 transition-colors shrink-0" />
        </button>
      </div>

      {/* Scrollable Document & Mode Center */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        
        {/* Workspace Mode Selection */}
        <div>
          <label className="block text-[10px] font-bold text-theme-muted uppercase tracking-wider mb-2">
            Target Focus Mode
          </label>
          <div className="space-y-1.5">
            
            {/* All Documents Mode */}
            <button
              onClick={() => onSelectTarget('__all__')}
              className={`w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all ${
                activeTarget === '__all__'
                  ? 'bg-blue-600/15 border-blue-500 text-blue-600 dark:text-blue-300 font-semibold shadow-sm'
                  : 'card-bg border-theme-subtle text-theme-secondary hover:bg-black/5 dark:hover:bg-white/5 hover:text-theme-primary'
              }`}
            >
              <div className="flex items-center space-x-2.5 truncate">
                <Files className="w-4 h-4 text-blue-500 shrink-0" />
                <span className="text-xs truncate">All Documents (QC Mode)</span>
              </div>
              <span className="text-[10px] bg-blue-500/15 text-blue-600 dark:text-blue-300 font-mono px-1.5 py-0.5 rounded border border-blue-500/30 shrink-0">
                {files.length}
              </span>
            </button>

            {/* General Assistant Mode */}
            <button
              onClick={() => onSelectTarget('__general__')}
              className={`w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all ${
                activeTarget === '__general__'
                  ? 'bg-purple-600/15 border-purple-500 text-purple-600 dark:text-purple-300 font-semibold shadow-sm'
                  : 'card-bg border-theme-subtle text-theme-secondary hover:bg-black/5 dark:hover:bg-white/5 hover:text-theme-primary'
              }`}
            >
              <div className="flex items-center space-x-2.5 truncate">
                <Globe className="w-4 h-4 text-purple-500 shrink-0" />
                <span className="text-xs truncate">General Assistant</span>
              </div>
            </button>

          </div>
        </div>

        {/* 1-Click QC Audit Banner */}
        <div className="p-3.5 rounded-2xl bg-gradient-to-r from-blue-600/15 to-indigo-600/15 dark:from-blue-950/80 dark:to-indigo-950/80 border border-blue-500/30 shadow-sm relative overflow-hidden">
          <div className="relative z-10 space-y-2">
            <div className="flex items-center space-x-2 text-blue-600 dark:text-blue-300">
              <Zap className="w-4 h-4 text-amber-500 fill-amber-500 animate-pulse" />
              <span className="text-xs font-bold font-heading">Automated Order Audit</span>
            </div>
            <p className="text-[11px] text-theme-secondary leading-tight">
              Cross-verify Order IDs, Names, Taxes, PACER, Patriot & Costs across all files.
            </p>
            <button
              onClick={onRunAudit}
              disabled={isAuditing || files.length === 0}
              className="w-full mt-2 py-2 px-3 text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-md transition-all flex items-center justify-center space-x-2"
            >
              {isAuditing ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Running QC Audit...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Run 1-Click QC Audit</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Multi-file Upload Zone */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-[10px] font-bold text-theme-muted uppercase tracking-wider">
              Document Workspace ({files.length})
            </label>
          </div>

          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-4 text-center cursor-pointer transition-all ${
              dragOver
                ? 'border-blue-500 bg-blue-500/10 scale-[0.99]'
                : 'border-theme-medium hover:border-blue-500/50 card-bg'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => e.target.files && onUpload(e.target.files)}
              multiple
              className="hidden"
              accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.txt"
            />
            <UploadCloud className="w-7 h-7 text-blue-500 mx-auto mb-1.5" />
            <p className="text-xs font-medium text-theme-primary">Drop PDFs or click to upload</p>
            <p className="text-[10px] text-theme-muted mt-0.5">PDF, Word, Images, Text supported</p>
          </div>
        </div>

        {/* Uploaded Document List */}
        <div className="space-y-1.5">
          {files.length === 0 ? (
            <div className="p-4 text-center text-xs text-theme-muted card-bg rounded-xl border border-theme-subtle">
              No files uploaded yet. Drag and drop order files above to begin QC.
            </div>
          ) : (
            files.map((file) => {
              const isSelected = activeTarget === file.name;
              return (
                <div
                  key={file.name}
                  className={`p-2.5 rounded-xl border transition-all flex items-center justify-between group ${
                    isSelected
                      ? 'bg-blue-600/15 border-blue-500 shadow-sm'
                      : 'card-bg border-theme-subtle hover:bg-black/5 dark:hover:bg-white/5'
                  }`}
                >
                  <div
                    onClick={() => onSelectTarget(file.name)}
                    className="flex items-center space-x-2.5 min-w-0 cursor-pointer flex-1 mr-2"
                  >
                    {renderFileIcon(file)}
                    <div className="min-w-0 flex-1">
                      <p className={`text-xs truncate font-medium ${isSelected ? 'text-blue-600 dark:text-blue-300' : 'text-theme-primary'}`}>
                        {file.name}
                      </p>
                      <p className="text-[10px] text-theme-muted">{file.size_kb} KB</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1 opacity-80 group-hover:opacity-100 transition-opacity shrink-0">
                    <button
                      onClick={() => onPreviewFile(file)}
                      title="View File Preview"
                      className="p-1 text-theme-muted hover:text-blue-500 hover:bg-black/5 dark:hover:bg-white/10 rounded-lg transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onDeleteFile(file.name)}
                      title="Delete Document"
                      className="p-1 text-theme-muted hover:text-rose-500 hover:bg-black/5 dark:hover:bg-white/10 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-theme-subtle text-center text-[10px] text-theme-muted header-bg flex items-center justify-between px-4">
        <span>DocuAgent AI v2.0</span>
        <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/5 border border-theme-subtle">
          {theme} mode
        </span>
      </div>
    </aside>
  );
};
