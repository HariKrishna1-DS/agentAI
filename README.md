# ⚡ DocuAgent AI — Document QC & Intelligent Agent

Here the Link : https://docagent-ai.onrender.com/
A powerful, full-stack AI Document Intelligence and Quality Control (QC) Agent built with **FastAPI**, **Groq API**, and **Python**.

DocuAgent allows you to chat with a general AI assistant, upload multiple PDF documents, extract text across multi-page files, cross-verify records across different documents, and run automated **Quality Control (QC) audits** (such as cross-checking property records, names, addresses, PACER bankruptcies, Patriot Act SDN lists, and cost worksheets).

---

## 🌟 Key Features

- **💬 Dual-Mode Agent Intelligence**:
  - **General Assistant Mode**: Ask general knowledge questions, solve math calculations, generate code, or have conversational chats without needing any documents.
  - **All Documents (QC Mode)**: Cross-references information across all uploaded PDFs simultaneously to spot inconsistencies, mismatches, or negative flags.
  - **Single Document Focus**: Click any specific PDF in the sidebar to ask questions focused entirely on that file.
- **📑 Multi-Page PDF Extraction**:
  - Powered by `pypdf` with page tracking (`--- Page X of Y ---`).
  - Supports reading complete documents or targeted page ranges with safe context window management.
- **📥 Multiple PDF Upload & Drag-and-Drop**:
  - Drag and drop multiple PDF documents simultaneously into the upload zone.
- **🗑️ Document Lifecycle Management**:
  - List uploaded documents with live file sizes in KB.
  - Delete past or unwanted PDFs instantly using the trash button or REST API.
- **🔍 One-Click Full QC Audit**:
  - Instantly audit all order files for:
    1. **Order ID Consistency** across all files.
    2. **Party Names & Address Verification** across Search Packages, Tax Snapshots, and Appraisal records.
    3. **PACER Bankruptcy & Patriot (OFAC/SDN) Screening**.
    4. **Tax Status Verification** (paid, open, or delinquent).
    5. **Fee Reconciliation** against Cost Worksheets.
    6. **Final QC Verdict** (`PASS` / `FAIL` / `REVIEW NEEDED`).
- **🎨 Modern Glassmorphic Web Interface**:
  - Responsive, dark-themed UI built with Vanilla CSS and Google Fonts (`Outfit` & `Inter`).
  - Served directly by FastAPI at `http://127.0.0.1:8000/`.

---

## 🏗️ Architecture & Project Structure

```
Agentic-folder/
├── agent.py              # Core LLM Agent with multi-provider tool-calling capabilities
├── app.py                # FastAPI REST API, routing, static serving, and file management
├── frontend/             # Modern React + TypeScript + Tailwind CSS Frontend Application
│   ├── src/
│   │   ├── components/   # Sidebar, ChatArea, ApiKeyModal, DocumentPreviewModal, CodeSandboxModal
│   │   ├── services/     # API client service (FastAPI integration)
│   │   ├── App.tsx       # Main React application workspace
│   │   └── main.tsx      # React entrypoint
│   ├── dist/             # Production build served directly by FastAPI at http://127.0.0.1:8000
│   ├── vite.config.ts    # Vite dev server and proxy configuration
│   └── package.json      # Node dependencies (React 19, TypeScript, Tailwind CSS v4, Lucide React)
├── static/               # Legacy static fallbacks
├── uploads/              # Storage directory for uploaded PDF, Word, Image & Text documents
├── .env                  # Environment variables (API Keys: Groq, Gemini, OpenRouter, Claude)
├── README.md             # Project documentation
└── .venv/                # Python Virtual Environment
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- A free [Groq API Key](https://console.groq.com/keys)

---

### 2. Setup Virtual Environment

#### On Windows (PowerShell):
```powershell
# Activate virtual environment:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

#### On Linux / macOS / Git Bash:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install openai python-dotenv pypdf fastapi uvicorn python-multipart
```

---

### 4. Configure Environment Variables

Create a `.env` file in the root folder:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

---

### 5. Run the Application

Start the FastAPI development server with auto-reload:

```powershell
python -m uvicorn app:app --reload
```

- 🌐 **Web Interface**: Open your browser at **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**
- 📚 **Interactive Swagger API Docs**: Open **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

### 6. (Optional) Run Agent via Terminal CLI

You can also run the agent as a standalone command-line chatbot:

```powershell
python agent.py
```

---

## 📡 REST API Reference

| Endpoint | Method | Description | Request Body |
| :--- | :---: | :--- | :--- |
| `/` | `GET` | Serves the interactive web interface | None |
| `/files` | `GET` | Lists all uploaded PDFs with file sizes | None |
| `/upload` | `POST` | Uploads one or multiple PDF documents | `multipart/form-data` (`files`) |
| `/files/{filename}` | `DELETE` | Deletes a specific PDF from storage | None |
| `/ask` | `POST` | Asks a question (general, specific PDF, or all PDFs QC) | `{"filename": "__all__", "question": "..."}` |
| `/qc-audit` | `POST` | Triggers a full automated Quality Control audit | None |
| `/chat` | `POST` | General conversation endpoint | `{"message": "Hello"}` |
| `/ask-pdf` | `POST` | One-shot upload and question answering | `multipart/form-data` (`file`, `question`) |

---

## 🛠️ Tool Calling Mechanism (`agent.py`)

The Groq Agent utilizes the following built-in functions:

1. **`calculate(expression)`**: Evaluates arithmetic safely using Python's Abstract Syntax Tree (`ast`).
2. **`read_pdf(file_path, start_page, end_page)`**: Extracts text from a local PDF with optional page range slicing.
3. **`list_available_pdfs()`**: Dynamically lists all files in `uploads/` with page counts.
4. **`read_multiple_pdfs(file_paths, pages_per_doc)`**: Reads initial pages from multiple files in parallel for cross-document comparisons.

---

## 🛡️ License

This project is open-source and available under the MIT License.
