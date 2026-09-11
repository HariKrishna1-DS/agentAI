import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatArea } from './components/ChatArea';
import { ApiKeyModal } from './components/ApiKeyModal';
import { DocumentPreviewModal } from './components/DocumentPreviewModal';
import { CodeSandboxModal } from './components/CodeSandboxModal';
import { ThemeProvider, useTheme } from './context/ThemeContext';
import type {
  DocFile,
  ChatMessage,
  ApiKeyStatus
} from './services/api';
import {
  fetchFiles,
  fetchApiKeyStatus,
  uploadFiles,
  deleteFile,
  askDocument,
  runQCAudit
} from './services/api';

function AppContent() {
  useTheme();
  const [files, setFiles] = useState<DocFile[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activeTarget, setActiveTarget] = useState<string>('__all__');
  const [status, setStatus] = useState<ApiKeyStatus | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [isAuditing, setIsAuditing] = useState<boolean>(false);

  // Modals
  const [previewFile, setPreviewFile] = useState<DocFile | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const [isSandboxOpen, setIsSandboxOpen] = useState<boolean>(false);

  // Initial Load
  useEffect(() => {
    loadFiles();
    loadStatus();
  }, []);

  const loadFiles = async () => {
    try {
      const list = await fetchFiles();
      setFiles(list);
    } catch (err) {
      console.error('Failed to load files:', err);
    }
  };

  const loadStatus = async () => {
    try {
      const s = await fetchApiKeyStatus();
      setStatus(s);
    } catch (err) {
      console.error('Failed to load status:', err);
    }
  };

  const handleUpload = async (fileList: FileList | File[]) => {
    try {
      setLoading(true);
      const res = await uploadFiles(fileList);
      await loadFiles();
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `📥 **Uploaded ${res.count} file(s) successfully!**\nFiles added: ${res.uploaded.join(', ')}`,
          targetFile: 'Upload System',
        },
      ]);
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFile = async (filename: string) => {
    if (!confirm(`Are you sure you want to delete '${filename}'?`)) return;
    try {
      await deleteFile(filename);
      if (activeTarget === filename) {
        setActiveTarget('__all__');
      }
      await loadFiles();
    } catch (err: any) {
      alert(`Failed to delete file: ${err.message}`);
    }
  };

  const handleSendMessage = async (question: string) => {
    const userMsg: ChatMessage = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const historyPayload = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await askDocument(question, activeTarget, historyPayload);

      const botMsg: ChatMessage = {
        role: 'assistant',
        content: res.answer,
        targetFile: res.filename,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error processing request: ${err.message}`,
          targetFile: activeTarget,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRunAudit = async () => {
    if (files.length === 0) {
      alert('Please upload order documents before running a QC audit.');
      return;
    }

    setIsAuditing(true);
    setLoading(true);

    const promptMsg: ChatMessage = {
      role: 'user',
      content: '⚡ Triggered 1-Click QC Audit across all workspace order documents.',
    };
    setMessages((prev) => [...prev, promptMsg]);

    try {
      const res = await runQCAudit();
      const auditMsg: ChatMessage = {
        role: 'assistant',
        content: res.report,
        targetFile: `Full QC Audit (${res.documents_audited.length} files)`,
        isAudit: true,
      };
      setMessages((prev) => [...prev, auditMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ QC Audit failed: ${err.message}`,
          targetFile: 'QC Engine',
        },
      ]);
    } finally {
      setIsAuditing(false);
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden app-bg text-theme-primary font-sans transition-colors duration-200">
      <Sidebar
        files={files}
        activeTarget={activeTarget}
        onSelectTarget={setActiveTarget}
        onUpload={handleUpload}
        onDeleteFile={handleDeleteFile}
        onPreviewFile={setPreviewFile}
        onRunAudit={handleRunAudit}
        isAuditing={isAuditing}
        status={status}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <ChatArea
        messages={messages}
        activeTarget={activeTarget}
        files={files}
        onSendMessage={handleSendMessage}
        onOpenSandbox={() => setIsSandboxOpen(true)}
        loading={loading}
      />

      <ApiKeyModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        status={status}
        onStatusUpdated={setStatus}
      />

      <DocumentPreviewModal
        file={previewFile}
        onClose={() => setPreviewFile(null)}
      />

      <CodeSandboxModal
        isOpen={isSandboxOpen}
        onClose={() => setIsSandboxOpen(false)}
      />
    </div>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;

