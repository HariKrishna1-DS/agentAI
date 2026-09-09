import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import agent logic
from agent import run_agent, SUPPORTED_EXTENSIONS, configure_client, get_client_status, run_python_code

app = FastAPI(
    title="DocuAgent API",
    description="FastAPI service with OpenRouter / Gemini / Groq Agent for Multi-Format Document Intelligence and Code Execution",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
STATIC_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static files for marked.js and assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_file_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in [".docx", ".doc"]:
        return "word"
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]:
        return "image"
    else:
        return "text"


def update_env_file(key_name: str, key_val: str, model_val: str = None, active_provider: str = None):
    """Safely updates or appends keys in the .env file."""
    env_path = ".env"
    lines = []
    found_key = False
    prefix = key_name.replace("_API_KEY", "")
    model_key_name = f"{prefix}_MODEL"
    found_model = False
    found_provider = False

    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key_name}="):
            new_lines.append(f"{key_name}={key_val}\n")
            found_key = True
        elif model_val and stripped.startswith(f"{model_key_name}="):
            new_lines.append(f"{model_key_name}={model_val}\n")
            found_model = True
        elif active_provider and stripped.startswith("ACTIVE_PROVIDER="):
            new_lines.append(f"ACTIVE_PROVIDER={active_provider}\n")
            found_provider = True
        else:
            new_lines.append(line)

    if not found_key:
        new_lines.append(f"{key_name}={key_val}\n")
    if model_val and not found_model:
        new_lines.append(f"{model_key_name}={model_val}\n")
    if active_provider and not found_provider:
        new_lines.append(f"ACTIVE_PROVIDER={active_provider}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


class ApiKeyConfigRequest(BaseModel):
    provider: str  # "claude", "openrouter", "gemini", or "groq"
    api_key: str
    model: Optional[str] = None


class RunCodeRequest(BaseModel):
    code: str


class ChatMessage(BaseModel):
    role: str
    content: str


class AskDocumentRequest(BaseModel):
    filename: Optional[str] = None  # None or "__all__" triggers cross-document QC mode
    question: str
    history: Optional[List[ChatMessage]] = None


class GeneralChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None


# --- API Key Management Endpoints ---

@app.get("/api-key-status")
async def api_key_status():
    """Returns the currently active AI provider, model, and key status."""
    return get_client_status()


@app.post("/set-api-key")
async def set_api_key(req: ApiKeyConfigRequest):
    """Updates the active API key and model from the web UI and writes to .env."""
    key = req.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    prov = req.provider.strip().lower()
    if prov in ("claude", "anthropic"):
        model = req.model.strip() if req.model and req.model.strip() else "claude-fable-5-1"
        configure_client(provider="claude", claude_key=key, model=model)
        update_env_file("CLAUDE_API_KEY", key, model_val=model, active_provider="Claude")
    elif prov == "openrouter":
        model = req.model.strip() if req.model and req.model.strip() else "openai/gpt-4o-mini"
        configure_client(provider="openrouter", openrouter_key=key, model=model)
        update_env_file("OPENROUTER_API_KEY", key, model_val=model, active_provider="OpenRouter")
    elif prov == "gemini":
        if key.startswith("gen-lang-client-"):
            raise HTTPException(
                status_code=400,
                detail="'gen-lang-client-...' is a Google Cloud project name, not an API key. Your Gemini API key starts with 'AIzaSy...' or 'AQ.'."
            )
        model = req.model.strip() if req.model and req.model.strip() else "gemini-3.6-flash"
        configure_client(provider="gemini", gemini_key=key, model=model)
        update_env_file("GEMINI_API_KEY", key, model_val=model, active_provider="Gemini")
    elif prov == "groq":
        model = req.model.strip() if req.model and req.model.strip() else "openai/gpt-oss-20b"
        configure_client(provider="groq", groq_key=key, model=model)
        update_env_file("GROQ_API_KEY", key, model_val=model, active_provider="Groq")
    else:
        raise HTTPException(status_code=400, detail="Provider must be 'claude', 'openrouter', 'gemini', or 'groq'.")

    return {
        "message": f"Successfully activated {prov.title()} API Key!",
        "status": get_client_status(),
    }


@app.post("/run-code")
async def run_code_endpoint(req: RunCodeRequest):
    """Safely executes Python code snippet and returns stdout."""
    if not req.code or not req.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")
    output = run_python_code(req.code)
    return {"output": output}


# --- Web Page Route ---
@app.get("/", response_class=HTMLResponse)
async def serve_webpage():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>DocuAgent API is running. static/index.html not found.</h1>"


# --- File Management Endpoints ---

@app.get("/files")
async def list_files():
    """Lists all uploaded files (PDF, Word, Text, Images) with metadata."""
    file_list = []
    if os.path.exists(UPLOAD_DIR):
        for f in sorted(os.listdir(UPLOAD_DIR)):
            ext = os.path.splitext(f)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(UPLOAD_DIR, f)
                try:
                    size_kb = round(os.path.getsize(full_path) / 1024, 1)
                except Exception:
                    size_kb = 0
                file_list.append({
                    "name": f,
                    "size_kb": size_kb,
                    "type": get_file_type(f),
                    "ext": ext,
                })
    return {"files": file_list}


@app.get("/raw-file/{filename}")
async def get_raw_file(filename: str):
    """Serves the raw file content or image for previews."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{safe_name}' not found.")
    return FileResponse(file_path)


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Uploads one or multiple documents or images and saves them to uploads/."""
    saved_files = []
    skipped_files = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            safe_name = os.path.basename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, safe_name)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(safe_name)
        else:
            skipped_files.append(file.filename)

    if not saved_files:
        raise HTTPException(
            status_code=400,
            detail=f"No supported documents or images provided. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    return {
        "uploaded": saved_files,
        "count": len(saved_files),
        "skipped": skipped_files,
        "filename": saved_files[0],
        "message": f"Successfully uploaded {len(saved_files)} file(s)!",
    }


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Deletes an uploaded document or image by filename."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{safe_name}' not found.")

    try:
        os.remove(file_path)
        return {
            "message": f"File '{safe_name}' has been deleted.",
            "filename": safe_name,
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to delete '{safe_name}': {err}")


# --- Agent Q&A & QC Endpoints ---

@app.post("/ask")
async def ask_document(req: AskDocumentRequest):
    """
    Asks a question about a specific document or image, conducts cross-document analysis/QC,
    or answers general questions and greetings naturally.
    """
    all_files = (
        [f for f in os.listdir(UPLOAD_DIR) if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
        if os.path.exists(UPLOAD_DIR)
        else []
    )

    # Case 1: Explicit General Assistant Mode
    if req.filename == "__general__":
        prompt = req.question
        target_name = "General Assistant"

    # Case 2: Cross-Document / QC Mode or Default
    elif not req.filename or req.filename == "__all__":
        if all_files:
            file_summary = ", ".join(all_files[:8]) + (f" and {len(all_files)-8} more" if len(all_files) > 8 else "")
            prompt = (
                f"User Question: {req.question}\n\n"
                f"[Workspace Context: {len(all_files)} document(s) uploaded ({file_summary})]\n\n"
                "INSTRUCTIONS:\n"
                "1. If this is a general knowledge question (e.g. 'what is INA', abbreviations, history, definitions, math, coding, or greetings), "
                "ANSWER DIRECTLY from your knowledge. DO NOT invoke document tools.\n"
                "2. If the user explicitly asks about their uploaded documents, files, reports, QC, or discrepancies, "
                "then inspect the relevant files with the document tools.\n"
                "3. When the user requests a Deed History, Chain of Title, Tax records, Fees, or structured comparisons, "
                "ALWAYS present the output in a clean, comprehensive Markdown table with standard column headers (e.g. | # | Deed Type | Grantor | Grantee | Book / Page | Dated | Recorded |). "
                "Ensure there is an empty line before and after the table so it renders properly."
            )
            target_name = "All Documents & General Assistant"
        else:
            prompt = req.question
            target_name = "General Assistant"

    # Case 3: Specific Document Focused
    else:
        file_path = os.path.join(UPLOAD_DIR, req.filename)
        if os.path.exists(file_path):
            prompt = (
                f"The user has selected the file '{req.filename}' located at '{file_path}'.\n\n"
                f"User Question: {req.question}\n\n"
                "- If this question relates to the document or image, use the read_document or inspect_image tool to answer.\n"
                "- If this is a general greeting or general question, answer directly.\n"
                "- When the user requests a Deed History, Chain of Title, Tax records, Fees, or structured comparisons, "
                "ALWAYS present the output in a clean, comprehensive Markdown table with standard column headers (e.g. | # | Deed Type | Grantor | Grantee | Book / Page | Dated | Recorded |). "
                "Ensure there is an empty line before and after the table so it renders properly."
            )
            target_name = req.filename
        else:
            prompt = (
                f"Note: The user specified file '{req.filename}', but it is not found on disk.\n"
                f"User Question: {req.question}\n\n"
                "Answer the user's question helpfully, and if it specifically required that file, let them know it was not found."
            )
            target_name = "General Assistant"

    history_dicts = [m.model_dump() for m in req.history] if req.history else None
    try:
        answer = run_agent(prompt, history=history_dicts)
    except Exception as err:
        answer = f"⚠️ An error occurred while communicating with the AI service:\n\n`{err}`\n\nPlease check your API key and model settings in `.env`."

    return {
        "filename": target_name,
        "question": req.question,
        "answer": answer,
    }


@app.post("/qc-audit")
async def run_qc_audit():
    """Runs a complete automatic Quality Control (QC) audit across all uploaded files."""
    all_files = (
        [f for f in os.listdir(UPLOAD_DIR) if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
        if os.path.exists(UPLOAD_DIR)
        else []
    )
    if not all_files:
        raise HTTPException(status_code=404, detail="No documents or images uploaded yet to audit.")

    prompt = (
        f"Perform a comprehensive Quality Control (QC) Audit across all {len(all_files)} documents in the order package:\n"
        f"Files to audit: {', '.join(all_files)}\n\n"
        "Audit Requirements:\n"
        "1. Order ID Verification: Confirm that all documents share the same order number.\n"
        "2. Parties & Names Check: Cross-verify borrower / owner / grantor / grantee names across the Search Package, Tax Snapshot, PA Snapshot, PACER, and Patriot.\n"
        "3. PACER & Patriot Check: Check PACER for bankruptcy records and Patriot for SDN / OFAC hits.\n"
        "4. Tax Snapshot Verification: Check whether property taxes are paid, open, or delinquent.\n"
        "5. Fee Reconciliation: Check the Cost Worksheet for all recorded charges, fees, and invoiced totals.\n"
        "6. Final QC Verdict: Conclude with PASS, FAIL, or REVIEW NEEDED, listing any flags clearly."
    )

    try:
        answer = run_agent(prompt)
    except Exception as err:
        answer = f"⚠️ An error occurred while generating the QC audit:\n\n`{err}`"

    return {
        "audit_type": "Full Order Package QC Audit",
        "documents_audited": all_files,
        "report": answer,
    }


@app.post("/chat")
async def general_chat(req: GeneralChatRequest):
    """General conversation with the agent."""
    history_dicts = [m.model_dump() for m in req.history] if req.history else None
    try:
        response = run_agent(req.message, history=history_dicts)
    except Exception as err:
        response = f"⚠️ Error: {err}"
    return {"reply": response}


@app.post("/ask-pdf")
async def ask_pdf(
    question: str = Form(...),
    file: UploadFile = File(...),
):
    """One-step endpoint: Upload a PDF and ask a question in a single request."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    prompt = f"Please read the uploaded file at '{file_path}' and answer this: {question}"
    answer = run_agent(prompt)

    return {"filename": file.filename, "question": question, "answer": answer}
