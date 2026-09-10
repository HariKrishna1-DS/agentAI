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
  Sparkles
} from 'lucide-react';
import type { DocFile, ApiKeyStatus } from '../services/api';

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
    <aside className="w-80 bg-[#0d121f]/90 border-r border-white/10 flex flex-col h-screen shrink-0 select-none glass-panel">
      
      {/* Brand Header */}
      <div className="p-5 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-lg shadow-blue-500/30">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-white font-heading tracking-tight flex items-center gap-1.5">
              <span>DocuAgent</span>
              <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">AI</span>
            </h1>
            <p className="text-[11px] text-gray-400">QC & Intelligent Document Agent</p>
          </div>
        </div>
      </div>

      {/* AI Key & Provider Bar */}
      <div className="px-5 py-3 border-b border-white/10 bg-white/[0.02]">
        <button
          onClick={onOpenSettings}
          className="w-full p-2.5 rounded-xl bg-gray-900/80 hover:bg-gray-800 border border-gray-800 hover:border-blue-500/50 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center space-x-2 truncate">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="text-left truncate">
              <div className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">Active AI Engine</div>
              <div className="text-xs font-semibold text-gray-200 truncate">
                {status ? status.active_provider : 'Configuring...'}
                {status && <span className="text-gray-400 font-normal ml-1">({status.active_model})</span>}
              </div>
            </div>
          </div>
          <Key className="w-4 h-4 text-gray-500 group-hover:text-blue-400 transition-colors shrink-0" />
        </button>
      </div>

      {/* Scrollable Document & Mode Center */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        
        {/* Workspace Mode Selection */}
        <div>
          <label className="block text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">
            Target Focus Mode
          </label>
          <div className="space-y-1.5">
            
            {/* All Documents Mode */}
            <button
              onClick={() => onSelectTarget('__all__')}
              className={`w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all ${
                activeTarget === '__all__'
                  ? 'bg-blue-600/20 border-blue-500 text-white font-medium shadow-md shadow-blue-950/30'
                  : 'bg-gray-900/40 border-gray-800/80 text-gray-300 hover:bg-gray-800/60 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2.5 truncate">
                <Files className="w-4 h-4 text-blue-400 shrink-0" />
                <span className="text-xs truncate">All Documents (QC Mode)</span>
              </div>
              <span className="text-[10px] bg-blue-900/60 text-blue-300 font-mono px-1.5 py-0.5 rounded border border-blue-700/50 shrink-0">
                {files.length}
              </span>
            </button>

            {/* General Assistant Mode */}
            <button
              onClick={() => onSelectTarget('__general__')}
              className={`w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all ${
                activeTarget === '__general__'
                  ? 'bg-purple-600/20 border-purple-500 text-white font-medium shadow-md shadow-purple-950/30'
                  : 'bg-gray-900/40 border-gray-800/80 text-gray-300 hover:bg-gray-800/60 hover:text-white'
              }`}
            >
              <div className="flex items-center space-x-2.5 truncate">
                <Globe className="w-4 h-4 text-purple-400 shrink-0" />
                <span className="text-xs truncate">General Assistant</span>
              </div>
            </button>

          </div>
        </div>

        {/* 1-Click QC Audit Banner */}
        <div className="p-3.5 rounded-2xl bg-gradient-to-r from-blue-950/80 to-indigo-950/80 border border-blue-500/30 shadow-lg relative overflow-hidden">
          <div className="relative z-10 space-y-2">
            <div className="flex items-center space-x-2 text-blue-300">
              <Zap className="w-4 h-4 text-amber-400 fill-amber-400 animate-pulse" />
              <span className="text-xs font-bold font-heading">Automated Order Audit</span>
            </div>
            <p className="text-[11px] text-gray-300 leading-tight">
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
            <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
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
                : 'border-gray-800 hover:border-gray-600 bg-gray-900/30'
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
            <UploadCloud className="w-7 h-7 text-blue-400 mx-auto mb-1.5" />
            <p className="text-xs font-medium text-gray-300">Drop PDFs or click to upload</p>
            <p className="text-[10px] text-gray-500 mt-0.5">PDF, Word, Images, Text supported</p>
          </div>
        </div>

        {/* Uploaded Document List */}
        <div className="space-y-1.5">
          {files.length === 0 ? (
            <div className="p-4 text-center text-xs text-gray-500 bg-gray-900/20 rounded-xl border border-gray-800/40">
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
                      ? 'bg-blue-600/20 border-blue-500 shadow-sm'
                      : 'bg-gray-900/50 border-gray-800/80 hover:bg-gray-800/60'
                  }`}
                >
                  <div
                    onClick={() => onSelectTarget(file.name)}
                    className="flex items-center space-x-2.5 min-w-0 cursor-pointer flex-1 mr-2"
                  >
                    {renderFileIcon(file)}
                    <div className="min-w-0 flex-1">
                      <p className={`text-xs truncate font-medium ${isSelected ? 'text-white' : 'text-gray-300'}`}>
                        {file.name}
                      </p>
                      <p className="text-[10px] text-gray-500">{file.size_kb} KB</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1 opacity-80 group-hover:opacity-100 transition-opacity shrink-0">
                    <button
                      onClick={() => onPreviewFile(file)}
                      title="View File Preview"
                      className="p-1 text-gray-400 hover:text-blue-400 hover:bg-white/10 rounded-lg transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onDeleteFile(file.name)}
                      title="Delete Document"
                      className="p-1 text-gray-400 hover:text-rose-400 hover:bg-white/10 rounded-lg transition-colors"
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
      <div className="p-3 border-t border-white/10 text-center text-[10px] text-gray-500 bg-black/20">
        DocuAgent AI v2.0 • Powered by FastAPI & Groq/Gemini/Claude
      </div>
    </aside>
  );
};
