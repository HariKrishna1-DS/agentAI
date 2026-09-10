export interface ApiKeyStatus {
  active_provider: string;
  active_model: string;
  keys: {
    openai: boolean;
    claude: boolean;
    openrouter: boolean;
    gemini: boolean;
    groq: boolean;
  };
}

export interface DocFile {
  name: string;
  size_kb: number;
  type: 'pdf' | 'word' | 'image' | 'text';
  ext: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  targetFile?: string;
  isAudit?: boolean;
}

export interface AskResponse {
  filename: string;
  question: string;
  answer: string;
}

export interface QCAuditResponse {
  audit_type: string;
  documents_audited: string[];
  report: string;
}

export interface RunCodeResponse {
  output: string;
}

export async function fetchApiKeyStatus(): Promise<ApiKeyStatus> {
  const res = await fetch('/api-key-status');
  if (!res.ok) throw new Error(`Status error: ${res.statusText}`);
  return res.json();
}

export async function setApiKey(provider: string, apiKey: string, model?: string): Promise<{ message: string; status: ApiKeyStatus }> {
  const res = await fetch('/set-api-key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, api_key: apiKey, model }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to set API key');
  }
  return res.json();
}

export async function fetchFiles(): Promise<DocFile[]> {
  const res = await fetch('/files');
  if (!res.ok) throw new Error(`Failed to list files: ${res.statusText}`);
  const data = await res.json();
  return data.files || [];
}

export async function uploadFiles(files: FileList | File[]): Promise<{ uploaded: string[]; count: number; message: string }> {
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  const res = await fetch('/upload', {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Upload failed');
  }
  return res.json();
}

export async function deleteFile(filename: string): Promise<{ message: string; filename: string }> {
  const res = await fetch(`/files/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Delete failed');
  }
  return res.json();
}

export async function askDocument(
  question: string,
  targetFilename?: string,
  history?: { role: string; content: string }[]
): Promise<AskResponse> {
  const res = await fetch('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: targetFilename,
      question,
      history,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Question failed');
  }
  return res.json();
}

export async function runQCAudit(): Promise<QCAuditResponse> {
  const res = await fetch('/qc-audit', {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'QC audit failed');
  }
  return res.json();
}

export async function runCodeSnippet(code: string): Promise<RunCodeResponse> {
  const res = await fetch('/run-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Code execution failed');
  }
  return res.json();
}

export function getRawFileUrl(filename: string): string {
  return `/raw-file/${encodeURIComponent(filename)}`;
}
