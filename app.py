import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import agent logic
from agent import run_agent

app = FastAPI(
    title="DocuAgent API",
    description="FastAPI service with Groq Agent for multi-page PDF Question Answering, Document Management, and Cross-Document QC",
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
    """Lists all uploaded PDF files with metadata."""
    file_list = []
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if f.lower().endswith(".pdf"):
                full_path = os.path.join(UPLOAD_DIR, f)
                try:
                    size_kb = round(os.path.getsize(full_path) / 1024, 1)
                except Exception:
                    size_kb = 0
                file_list.append({"name": f, "size_kb": size_kb})
    return {"files": file_list}


@app.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Uploads one or multiple PDF documents and saves them to uploads/."""
    saved_files = []
    for file in files:
        if file.filename.lower().endswith(".pdf"):
            safe_name = os.path.basename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, safe_name)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(safe_name)

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid PDF documents provided.")

    return {
        "uploaded": saved_files,
        "count": len(saved_files),
        "filename": saved_files[0],
        "message": f"Successfully uploaded {len(saved_files)} document(s)!",
    }


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Deletes an uploaded PDF document by filename."""
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Document '{safe_name}' not found.")

    try:
        os.remove(file_path)
        return {
            "message": f"Document '{safe_name}' has been deleted.",
            "filename": safe_name,
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to delete '{safe_name}': {err}")


# --- Agent Q&A & QC Endpoints ---

@app.post("/ask")
async def ask_document(req: AskDocumentRequest):
    """
    Asks a question about a specific document, conducts a cross-document QC analysis,
    or answers general questions and greetings naturally.
    """
    all_files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")] if os.path.exists(UPLOAD_DIR) else []

    # Case 1: Explicit General Assistant Mode
    if req.filename == "__general__":
        prompt = req.question
        target_name = "General Assistant"

    # Case 2: Cross-Document / QC Mode or Default
    elif not req.filename or req.filename == "__all__":
        if all_files:
            prompt = (
                f"Workspace Context: The user has {len(all_files)} uploaded PDF document(s): {', '.join(all_files)}.\n\n"
                f"User Message/Question: {req.question}\n\n"
                "Instructions:\n"
                "- If the user's message is asking about the uploaded documents, cross-referencing information, or requesting a Quality Control (QC) check, "
                "use the read_pdf or read_multiple_pdfs tools to inspect the relevant documents and provide an accurate answer.\n"
                "- If the user's message is a general greeting (e.g. 'hi', 'hello'), a general knowledge query, a math calculation, "
                "or something unrelated to the documents, answer directly, politely, and conversationally without searching files."
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
                f"The user has selected the document '{req.filename}' located at '{file_path}'.\n\n"
                f"User Question: {req.question}\n\n"
                "- If this question relates to the document, use the read_pdf tool to answer.\n"
                "- If this is a general greeting or general question, answer directly."
            )
            target_name = req.filename
        else:
            prompt = (
                f"Note: The user specified document '{req.filename}', but it is not found on disk.\n"
                f"User Question: {req.question}\n\n"
                "Answer the user's question helpfully, and if it specifically required that file, let them know it was not found."
            )
            target_name = "General Assistant"

    history_dicts = [m.model_dump() for m in req.history] if req.history else None
    answer = run_agent(prompt, history=history_dicts)

    return {
        "filename": target_name,
        "question": req.question,
        "answer": answer,
    }


@app.post("/qc-audit")
async def run_qc_audit():
    """Runs a complete automatic Quality Control (QC) audit across all uploaded files."""
    all_files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")] if os.path.exists(UPLOAD_DIR) else []
    if not all_files:
        raise HTTPException(status_code=404, detail="No PDF documents uploaded yet to audit.")

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

    answer = run_agent(prompt)
    return {
        "audit_type": "Full Order Package QC Audit",
        "documents_audited": all_files,
        "report": answer,
    }


@app.post("/chat")
async def general_chat(req: GeneralChatRequest):
    """General conversation with the agent."""
    history_dicts = [m.model_dump() for m in req.history] if req.history else None
    response = run_agent(req.message, history=history_dicts)
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
