import ast
import base64
import json
import operator as op
import os
import zipfile
import xml.etree.ElementTree as ET

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    anthropic = None

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv()

# Client state variables
client = None
anthropic_client = None
MODEL_NAME = "None"
ACTIVE_PROVIDER = "None"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
GEMINI_QUOTA_EXHAUSTED = False


def is_likely_api_key(val: str) -> bool:
    if not val:
        return False
    v = val.strip()
    return v.startswith(("AQ.", "AIza", "gsk_", "sk-or-v1-", "sk-ant-", "sk-")) or len(v) > 35


def is_valid_gemini_key(val: str) -> bool:
    if not val:
        return False
    v = val.strip()
    # gen-lang-client- is a Google Cloud project/client ID, NOT an API key
    if v == "your_gemini_api_key_here" or v.startswith("gen-lang-client-"):
        return False
    return len(v) > 20


def switch_to_fallback(reason: str = ""):
    """Switches active provider to an alternate configured provider when the current one fails."""
    global client, anthropic_client, MODEL_NAME, ACTIVE_PROVIDER, GEMINI_QUOTA_EXHAUSTED
    current = ACTIVE_PROVIDER

    # If Claude failed
    if current == "Claude":
        if OPENROUTER_API_KEY and OPENROUTER_API_KEY.strip():
            print(f"[Agent Provider Switch] Claude failed ({reason}). Falling back to OpenRouter.")
            client = OpenAI(
                api_key=OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "http://127.0.0.1:8000",
                    "X-Title": "DocuAgent AI",
                },
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
            ACTIVE_PROVIDER = "OpenRouter"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER
        elif is_valid_gemini_key(GEMINI_API_KEY) and not GEMINI_QUOTA_EXHAUSTED:
            print(f"[Agent Provider Switch] Claude failed ({reason}). Falling back to Gemini.")
            client = OpenAI(
                api_key=GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
            ACTIVE_PROVIDER = "Gemini"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER
        elif GROQ_API_KEY and GROQ_API_KEY.strip():
            print(f"[Agent Provider Switch] Claude failed ({reason}). Falling back to Groq.")
            client = OpenAI(
                api_key=GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
            ACTIVE_PROVIDER = "Groq"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER

    # If OpenRouter failed (e.g. 402 Insufficient credits)
    elif current == "OpenRouter":
        if CLAUDE_API_KEY and CLAUDE_API_KEY.strip():
            print(f"[Agent Provider Switch] OpenRouter failed ({reason}). Falling back to Claude.")
            MODEL_NAME = os.environ.get("CLAUDE_MODEL", "claude-fable-5-1")
            ACTIVE_PROVIDER = "Claude"
            if CLAUDE_API_KEY.startswith("xpl_"):
                base_url = os.environ.get("CLAUDE_BASE_URL", "https://api.experientiallabs.ai/v1")
                client = OpenAI(api_key=CLAUDE_API_KEY, base_url=base_url, timeout=35.0)
                anthropic_client = None
                return client, MODEL_NAME, ACTIVE_PROVIDER
            elif HAS_ANTHROPIC:
                anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, timeout=30.0)
                client = None
                return anthropic_client, MODEL_NAME, ACTIVE_PROVIDER
        elif is_valid_gemini_key(GEMINI_API_KEY) and not GEMINI_QUOTA_EXHAUSTED:
            print(f"[Agent Provider Switch] OpenRouter failed ({reason}). Falling back to Gemini.")
            client = OpenAI(
                api_key=GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
            ACTIVE_PROVIDER = "Gemini"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER
        elif GROQ_API_KEY and GROQ_API_KEY.strip():
            print(f"[Agent Provider Switch] OpenRouter failed ({reason}). Falling back to Groq.")
            client = OpenAI(
                api_key=GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
            ACTIVE_PROVIDER = "Groq"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER

    # If Gemini failed (quota exceeded)
    elif current == "Gemini":
        GEMINI_QUOTA_EXHAUSTED = True
        if CLAUDE_API_KEY and CLAUDE_API_KEY.strip():
            print(f"[Agent Provider Switch] Gemini failed ({reason}). Falling back to Claude.")
            MODEL_NAME = os.environ.get("CLAUDE_MODEL", "claude-fable-5-1")
            ACTIVE_PROVIDER = "Claude"
            if CLAUDE_API_KEY.startswith("xpl_"):
                base_url = os.environ.get("CLAUDE_BASE_URL", "https://api.experientiallabs.ai/v1")
                client = OpenAI(api_key=CLAUDE_API_KEY, base_url=base_url, timeout=35.0)
                anthropic_client = None
                return client, MODEL_NAME, ACTIVE_PROVIDER
            elif HAS_ANTHROPIC:
                anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, timeout=30.0)
                client = None
                return anthropic_client, MODEL_NAME, ACTIVE_PROVIDER
        elif GROQ_API_KEY and GROQ_API_KEY.strip():
            print(f"[Agent Provider Switch] Gemini failed ({reason}). Falling back to Groq.")
            client = OpenAI(
                api_key=GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1",
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
            ACTIVE_PROVIDER = "Groq"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER

    # If Groq failed
    elif current == "Groq":
        if CLAUDE_API_KEY and CLAUDE_API_KEY.strip():
            print(f"[Agent Provider Switch] Groq failed ({reason}). Falling back to Claude.")
            MODEL_NAME = os.environ.get("CLAUDE_MODEL", "claude-fable-5-1")
            ACTIVE_PROVIDER = "Claude"
            if CLAUDE_API_KEY.startswith("xpl_"):
                base_url = os.environ.get("CLAUDE_BASE_URL", "https://api.experientiallabs.ai/v1")
                client = OpenAI(api_key=CLAUDE_API_KEY, base_url=base_url, timeout=35.0)
                anthropic_client = None
                return client, MODEL_NAME, ACTIVE_PROVIDER
            elif HAS_ANTHROPIC:
                anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, timeout=30.0)
                client = None
                return anthropic_client, MODEL_NAME, ACTIVE_PROVIDER
        elif OPENROUTER_API_KEY and OPENROUTER_API_KEY.strip():
            print(f"[Agent Provider Switch] Groq failed ({reason}). Falling back to OpenRouter.")
            client = OpenAI(
                api_key=OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "http://127.0.0.1:8000",
                    "X-Title": "DocuAgent AI",
                },
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
            ACTIVE_PROVIDER = "OpenRouter"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER
        elif is_valid_gemini_key(GEMINI_API_KEY) and not GEMINI_QUOTA_EXHAUSTED:
            print(f"[Agent Provider Switch] Groq failed ({reason}). Falling back to Gemini.")
            client = OpenAI(
                api_key=GEMINI_API_KEY,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                timeout=90.0,
            )
            MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
            ACTIVE_PROVIDER = "Gemini"
            anthropic_client = None
            return client, MODEL_NAME, ACTIVE_PROVIDER

    return None, None, None


def configure_client(
    gemini_key: str = None,
    groq_key: str = None,
    openrouter_key: str = None,
    claude_key: str = None,
    model: str = None,
    provider: str = None,
):
    """Dynamically configures or switches the active LLM client among OpenRouter, Claude, Gemini, and Groq."""
    global client, anthropic_client, MODEL_NAME, ACTIVE_PROVIDER, GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, CLAUDE_API_KEY, GEMINI_QUOTA_EXHAUSTED

    if gemini_key is not None:
        GEMINI_API_KEY = gemini_key.strip()
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        GEMINI_QUOTA_EXHAUSTED = False

    if groq_key is not None:
        GROQ_API_KEY = groq_key.strip()
        os.environ["GROQ_API_KEY"] = GROQ_API_KEY

    if openrouter_key is not None:
        OPENROUTER_API_KEY = openrouter_key.strip()
        os.environ["OPENROUTER_API_KEY"] = OPENROUTER_API_KEY

    if claude_key is not None:
        CLAUDE_API_KEY = claude_key.strip()
        os.environ["CLAUDE_API_KEY"] = CLAUDE_API_KEY
        os.environ["ANTHROPIC_API_KEY"] = CLAUDE_API_KEY

    target_prov = (provider or os.environ.get("ACTIVE_PROVIDER", "")).strip().lower()

    # Sanitize model name: ensure an API key wasn't accidentally passed as model
    chosen_model = model if (model and not is_likely_api_key(model)) else None

    # Priority 1: Explicit target provider selection
    if target_prov in ("claude", "anthropic") and CLAUDE_API_KEY and CLAUDE_API_KEY.strip():
        saved_model = os.environ.get("CLAUDE_MODEL", "claude-fable-5-1")
        MODEL_NAME = chosen_model or saved_model
        if CLAUDE_API_KEY.startswith("xpl_"):
            base_url = os.environ.get("CLAUDE_BASE_URL", "https://api.experientiallabs.ai/v1")
            client = OpenAI(
                api_key=CLAUDE_API_KEY,
                base_url=base_url,
                timeout=35.0,
            )
            anthropic_client = None
            ACTIVE_PROVIDER = "Claude"
            os.environ["ACTIVE_PROVIDER"] = "Claude"
            return
        else:
            if HAS_ANTHROPIC:
                anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, timeout=30.0)
            client = None
            ACTIVE_PROVIDER = "Claude"
            os.environ["ACTIVE_PROVIDER"] = "Claude"
            return

    if target_prov == "openrouter" and OPENROUTER_API_KEY and OPENROUTER_API_KEY.strip():
        saved_model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        MODEL_NAME = chosen_model or saved_model
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://127.0.0.1:8000",
                "X-Title": "DocuAgent AI",
            },
            timeout=90.0,
        )
        anthropic_client = None
        ACTIVE_PROVIDER = "OpenRouter"
        os.environ["ACTIVE_PROVIDER"] = "OpenRouter"
        return

    if target_prov == "groq" and GROQ_API_KEY and GROQ_API_KEY.strip():
        saved_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
        MODEL_NAME = chosen_model or saved_model
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            timeout=90.0,
        )
        anthropic_client = None
        ACTIVE_PROVIDER = "Groq"
        os.environ["ACTIVE_PROVIDER"] = "Groq"
        return

    if target_prov == "gemini" and not GEMINI_QUOTA_EXHAUSTED and is_valid_gemini_key(GEMINI_API_KEY):
        saved_model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
        MODEL_NAME = chosen_model or saved_model
        client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=90.0,
        )
        anthropic_client = None
        ACTIVE_PROVIDER = "Gemini"
        os.environ["ACTIVE_PROVIDER"] = "Gemini"
        return

    # Priority 2: Auto-detect available keys
    if CLAUDE_API_KEY and CLAUDE_API_KEY.strip() and target_prov in ("claude", "anthropic"):
        saved_model = os.environ.get("CLAUDE_MODEL", "claude-fable-5-1")
        MODEL_NAME = chosen_model or saved_model
        if CLAUDE_API_KEY.startswith("xpl_"):
            base_url = os.environ.get("CLAUDE_BASE_URL", "https://api.experientiallabs.ai/v1")
            client = OpenAI(
                api_key=CLAUDE_API_KEY,
                base_url=base_url,
                timeout=35.0,
            )
            anthropic_client = None
            ACTIVE_PROVIDER = "Claude"
            os.environ["ACTIVE_PROVIDER"] = "Claude"
        else:
            if HAS_ANTHROPIC:
                anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, timeout=30.0)
            client = None
            ACTIVE_PROVIDER = "Claude"
            os.environ["ACTIVE_PROVIDER"] = "Claude"
    elif OPENROUTER_API_KEY and OPENROUTER_API_KEY.strip():
        saved_model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        MODEL_NAME = chosen_model or saved_model
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://127.0.0.1:8000",
                "X-Title": "DocuAgent AI",
            },
            timeout=90.0,
        )
        anthropic_client = None
        ACTIVE_PROVIDER = "OpenRouter"
        os.environ["ACTIVE_PROVIDER"] = "OpenRouter"
    elif not GEMINI_QUOTA_EXHAUSTED and is_valid_gemini_key(GEMINI_API_KEY):
        saved_model = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
        MODEL_NAME = chosen_model or saved_model
        client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            timeout=90.0,
        )
        anthropic_client = None
        ACTIVE_PROVIDER = "Gemini"
        os.environ["ACTIVE_PROVIDER"] = "Gemini"
    elif GROQ_API_KEY and GROQ_API_KEY.strip():
        saved_model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
        MODEL_NAME = chosen_model or saved_model
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            timeout=90.0,
        )
        anthropic_client = None
        ACTIVE_PROVIDER = "Groq"
        os.environ["ACTIVE_PROVIDER"] = "Groq"
    elif CLAUDE_API_KEY and CLAUDE_API_KEY.strip():
        saved_model = os.environ.get("CLAUDE_MODEL", "claude-fable-5-1")
        MODEL_NAME = chosen_model or saved_model
        if HAS_ANTHROPIC:
            anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY, timeout=30.0)
        client = None
        ACTIVE_PROVIDER = "Claude"
        os.environ["ACTIVE_PROVIDER"] = "Claude"
    else:
        client = None
        anthropic_client = None
        ACTIVE_PROVIDER = "None"
        MODEL_NAME = "None"


def get_client_status():
    """Returns safe masked status of active client and configured keys."""
    def mask_key(k):
        if not k or len(k.strip()) < 8 or k == "your_gemini_api_key_here":
            return "Not Configured"
        k = k.strip()
        return f"{k[:7]}...{k[-4:]}"

    return {
        "active_provider": ACTIVE_PROVIDER,
        "active_model": MODEL_NAME,
        "is_active": (client is not None or (ACTIVE_PROVIDER == "Claude" and anthropic_client is not None)),
        "gemini_configured": bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here"),
        "groq_configured": bool(GROQ_API_KEY),
        "openrouter_configured": bool(OPENROUTER_API_KEY),
        "claude_configured": bool(CLAUDE_API_KEY),
        "masked_gemini_key": mask_key(GEMINI_API_KEY),
        "masked_groq_key": mask_key(GROQ_API_KEY),
        "masked_openrouter_key": mask_key(OPENROUTER_API_KEY),
        "masked_claude_key": mask_key(CLAUDE_API_KEY),
    }


# Initial setup on module load
configure_client()

# Supported extensions
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".tsv",
    ".json", ".xml", ".html", ".log", ".yaml", ".yml", ".py", ".sql",
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"
}

# A deliberately restricted calculator.
# Do not use unrestricted eval() with user input.
def calculate(expression: str) -> str:
    operations = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.Mod: op.mod,
    }

    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Exponent is too large")

            return operations[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = evaluate(node.operand)
            return -value if isinstance(node.op, ast.USub) else value

        raise ValueError("Only basic arithmetic is allowed")

    try:
        tree = ast.parse(expression, mode="eval")
        return str(evaluate(tree.body))
    except Exception as error:
        return f"Calculator error: {error}"


def run_python_code(code: str) -> str:
    """Executes Python code in an isolated environment and captures printed stdout and output."""
    import sys
    import io
    import traceback

    clean_code = code.strip()
    # Strip markdown code fences if provided
    if clean_code.startswith("```"):
        lines = clean_code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean_code = "\n".join(lines).strip()

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = io.StringIO()
    redirected_error = io.StringIO()
    sys.stdout = redirected_output
    sys.stderr = redirected_error

    exec_globals = {
        "math": __import__("math"),
        "datetime": __import__("datetime"),
        "json": __import__("json"),
        "re": __import__("re"),
        "os": __import__("os"),
    }

    try:
        exec(clean_code, exec_globals)
        stdout_val = redirected_output.getvalue()
        stderr_val = redirected_error.getvalue()
        output = stdout_val
        if stderr_val:
            output += f"\n[stderr]\n{stderr_val}"
        return output.strip() or "Code executed successfully (no printed output)."
    except Exception:
        return f"Python Execution Error:\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def read_pdf(file_path: str, start_page: int = 1, end_page: int = None) -> str:
    """Extracts readable text from a PDF file across all pages or a specified page range."""
    clean_path = file_path.strip().strip("'\"")
    if not os.path.exists(clean_path):
        alt_path = os.path.join("uploads", clean_path)
        if os.path.exists(alt_path):
            clean_path = alt_path
        else:
            return f"Error: File not found at '{clean_path}'. Please check the filename or path."

    try:
        reader = PdfReader(clean_path)
        total_pages = len(reader.pages)
        if total_pages == 0:
            return "Error: The PDF file has 0 pages."

        s_idx = max(0, start_page - 1)
        e_idx = min(total_pages, end_page) if end_page is not None else total_pages

        pages_text = []
        for idx in range(s_idx, e_idx):
            page = reader.pages[idx]
            text = page.extract_text() or ""
            if text.strip():
                pages_text.append(f"--- Page {idx + 1} of {total_pages} ---\n{text.strip()}")

        if not pages_text:
            return f"The PDF has {total_pages} page(s), but contains no extractable text. It might be scanned or image-based."

        combined = f"Document: {os.path.basename(clean_path)} (Total Pages: {total_pages})\n\n" + "\n\n".join(pages_text)
        max_chars = 80000
        if len(combined) > max_chars:
            combined = combined[:max_chars] + f"\n\n[Note: Output truncated to first {max_chars} characters. Use start_page and end_page to read specific sections.]"

        return combined
    except Exception as error:
        return f"Error reading PDF '{clean_path}': {error}"


def read_docx(file_path: str) -> str:
    """Extracts text content, headings, and tables from a Microsoft Word (.docx) document."""
    clean_path = file_path.strip().strip("'\"")
    if not os.path.exists(clean_path):
        alt = os.path.join("uploads", clean_path)
        if os.path.exists(alt):
            clean_path = alt
        else:
            return f"Error: File not found at '{clean_path}'."

    try:
        content = ""
        try:
            import docx
            doc = docx.Document(clean_path)
            text_parts = []
            for p in doc.paragraphs:
                if p.text.strip():
                    text_parts.append(p.text.strip())

            for table in doc.tables:
                table_lines = []
                for row in table.rows:
                    row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if row_cells:
                        table_lines.append(" | ".join(row_cells))
                if table_lines:
                    text_parts.append("\n".join(table_lines))
            content = "\n\n".join(text_parts)
        except ImportError:
            # Fallback using Python's built-in zipfile + XML (no external packages required)
            with zipfile.ZipFile(clean_path) as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for p in tree.iter(f"{{{ns['w']}}}p"):
                texts = [node.text for node in p.iter(f"{{{ns['w']}}}t") if node.text]
                if texts:
                    paragraphs.append("".join(texts))
            content = "\n\n".join(paragraphs)

        if not content.strip():
            return f"Word document '{os.path.basename(clean_path)}' contains no readable text content."

        max_chars = 80000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[Note: Output truncated to first {max_chars} characters.]"

        return f"Document: {os.path.basename(clean_path)} (Word Document)\n\n" + content
    except Exception as error:
        return f"Error reading Word document '{clean_path}': {error}"


def read_text_file(file_path: str) -> str:
    """Extracts content from plain text, CSV, Markdown, JSON, code, or log files."""
    clean_path = file_path.strip().strip("'\"")
    if not os.path.exists(clean_path):
        alt = os.path.join("uploads", clean_path)
        if os.path.exists(alt):
            clean_path = alt
        else:
            return f"Error: File not found at '{clean_path}'."

    try:
        with open(clean_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if not content.strip():
            return f"File '{os.path.basename(clean_path)}' is empty."

        max_chars = 80000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n[Note: Output truncated to first {max_chars} characters.]"

        return f"Document: {os.path.basename(clean_path)}\n\n" + content
    except Exception as error:
        return f"Error reading file '{clean_path}': {error}"


def inspect_image(file_path: str, instruction: str = "Analyze and extract all text, data tables, and key visual details from this image.") -> str:
    """Performs visual inspection and OCR on an image file (.png, .jpg, .jpeg, .webp, .bmp)."""
    clean_path = file_path.strip().strip("'\"")
    if not os.path.exists(clean_path):
        alt = os.path.join("uploads", clean_path)
        if os.path.exists(alt):
            clean_path = alt
        else:
            return f"Error: Image not found at '{clean_path}'."

    ext = os.path.splitext(clean_path)[1].lower().lstrip(".")
    img_format = "jpeg" if ext in ("jpg", "jpeg") else (ext if ext else "png")
    width, height = 0, 0

    if HAS_PIL and Image:
        try:
            with Image.open(clean_path) as img:
                width, height = img.size
                if img.format:
                    detected_format = img.format.lower()
                    img_format = "jpeg" if detected_format in ("jpg", "jpeg") else detected_format
        except Exception:
            pass

    try:
        with open(clean_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        mime_type = f"image/{img_format}"
        res_info = f" (Resolution: {width}x{height})" if width and height else ""

        if ACTIVE_PROVIDER == "Claude" and anthropic_client:
            media_type = mime_type if mime_type in ["image/jpeg", "image/png", "image/gif", "image/webp"] else "image/jpeg"
            claude_resp = anthropic_client.messages.create(
                model=MODEL_NAME,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"{instruction}\nFilename: {os.path.basename(clean_path)}{res_info}",
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": b64_data,
                                },
                            },
                        ],
                    }
                ],
            )
            analysis = "".join([b.text for b in claude_resp.content if getattr(b, "text", None)]) or "No content extracted."
            return f"Image Analysis: {os.path.basename(clean_path)} ({img_format.upper()}):\n\n{analysis}"

        vision_messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{instruction}\nFilename: {os.path.basename(clean_path)}{res_info}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_data}",
                        },
                    },
                ],
            }
        ]
        vision_kwargs = {
            "model": MODEL_NAME,
            "messages": vision_messages,
        }
        if "fable" not in MODEL_NAME.lower():
            vision_kwargs["temperature"] = 0.2
        vision_resp = client.chat.completions.create(**vision_kwargs)
        analysis = vision_resp.choices[0].message.content or "No content extracted."
        return f"Image Analysis: {os.path.basename(clean_path)} ({img_format.upper()}):\n\n{analysis}"
    except Exception as err:
        return f"Error inspecting image '{clean_path}': {err}"


def read_document(file_path: str, start_page: int = 1, end_page: int = None) -> str:
    """Universal reader: handles PDF, Word (.docx), Text/Data/CSV/JSON/Markdown, and Images (.png, .jpg, .webp)."""
    clean_path = file_path.strip().strip("'\"")
    ext = os.path.splitext(clean_path)[1].lower()

    if ext == ".pdf":
        return read_pdf(clean_path, start_page=start_page, end_page=end_page)
    elif ext in [".docx", ".doc"]:
        return read_docx(clean_path)
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]:
        return inspect_image(clean_path)
    else:
        return read_text_file(clean_path)


def list_available_documents() -> str:
    """Discovers all available documents and images in the uploads directory."""
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        return "No uploads directory found."
    files = [f for f in os.listdir(upload_dir) if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS]
    if not files:
        return "No files available in uploads directory."

    info = []
    for f in sorted(files):
        p = os.path.join(upload_dir, f)
        ext = os.path.splitext(f)[1].lower()
        try:
            size_kb = round(os.path.getsize(p) / 1024, 1)
            if ext == ".pdf":
                info.append(f"- 📕 {f} (PDF, {size_kb} KB)")
            elif ext in [".docx", ".doc"]:
                info.append(f"- 📘 {f} (Word Document, {size_kb} KB)")
            elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]:
                info.append(f"- 🖼️ {f} (Image, {size_kb} KB)")
            else:
                info.append(f"- 📄 {f} (Text/Data, {size_kb} KB)")
        except Exception:
            info.append(f"- {f}")
    return "Available Documents & Files:\n" + "\n".join(info)


def read_multiple_documents(file_paths: list, pages_per_doc: int = 3) -> str:
    """Reads starting content from multiple files simultaneously for comparison and QC (token-capped)."""
    results = []
    # Cap to at most 6 files at once to stay within token limits
    safe_paths = file_paths[:6]
    for path in safe_paths:
        clean = path.strip().strip("'\"")
        content = read_document(clean, start_page=1, end_page=min(pages_per_doc, 3))
        # Cap each document to 1500 chars for token efficiency
        if len(content) > 1500:
            content = content[:1500] + "\n... [Remaining content truncated for token limits] ..."
        results.append(f"=== {os.path.basename(clean)} ===\n{content}")
    return "\n\n" + ("=" * 40) + "\n\n".join(results)


# Aliases for seamless backwards compatibility
list_available_pdfs = list_available_documents
read_multiple_pdfs = read_multiple_documents


tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Calculate a basic arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "For example: (25 * 4) + 10",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_python_code",
            "description": "Executes Python code in an isolated environment and returns printed stdout and output. Use this whenever asked to run code, verify Python logic, perform complex math, data manipulation, or generate data dynamically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code snippet to execute. Use print() to output results.",
                    }
                },
                "required": ["code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_document",
            "description": "Extracts text content or visual details from any local file: PDF (.pdf), Word (.docx, .doc), Text/Data (.txt, .csv, .md, .json, .log), or Images (.png, .jpg, .webp). Use this whenever analyzing or answering questions about any uploaded file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path or filename (e.g., 'document.pdf', 'report.docx', 'data.csv', 'receipt.png').",
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "Optional 1-based start page for PDFs (defaults to 1).",
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "Optional 1-based end page for PDFs (defaults to all pages).",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_pdf",
            "description": "Universal document reader (PDF, Word, Text, Image). Alias for read_document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path or filename.",
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "Optional start page for PDFs.",
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "Optional end page for PDFs.",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_image",
            "description": "Inspects an image file (.png, .jpg, .jpeg, .webp, .bmp) using vision AI to read diagrams, charts, handwritten text, receipts, tables, or photo contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the image file.",
                    },
                    "instruction": {
                        "type": "string",
                        "description": "Optional question or instruction for the vision inspection.",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_documents",
            "description": "Lists all documents, spreadsheets, text files, and images currently uploaded and available in the workspace.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_pdfs",
            "description": "Lists all uploaded files (PDF, Word, Text, Images). Alias for list_available_documents.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_multiple_documents",
            "description": "Reads starting content from multiple files (PDFs, Word docs, CSV, Text, Images) simultaneously for fast cross-document comparison and QC audits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of filenames or paths to inspect together.",
                    },
                    "pages_per_doc": {
                        "type": "integer",
                        "description": "Number of preview pages/sections per document (default 5).",
                    },
                },
                "required": ["file_paths"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_multiple_pdfs",
            "description": "Alias for read_multiple_documents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of filenames to inspect together.",
                    },
                    "pages_per_doc": {
                        "type": "integer",
                        "description": "Number of preview pages/sections per document (default 5).",
                    },
                },
                "required": ["file_paths"],
            },
        },
    },
]


def execute_agent_tool(fname: str, args: dict) -> str:
    """Dispatches tool execution across all supported functions."""
    print(f"[Agent Tool] Calling '{fname}' with args={args}", flush=True)

    if fname == "calculate":
        return calculate(args.get("expression", ""))
    elif fname in ("run_python_code", "execute_code"):
        return run_python_code(args.get("code", ""))
    elif fname in ("read_document", "read_pdf"):
        return read_document(
            args.get("file_path", ""),
            start_page=args.get("start_page", 1),
            end_page=args.get("end_page", None),
        )
    elif fname == "inspect_image":
        return inspect_image(
            args.get("file_path", ""),
            instruction=args.get("instruction", "Analyze and extract all text and details from this image."),
        )
    elif fname in ("list_available_documents", "list_available_pdfs"):
        return list_available_documents()
    elif fname in ("read_multiple_documents", "read_multiple_pdfs"):
        return read_multiple_documents(
            args.get("file_paths", []),
            pages_per_doc=args.get("pages_per_doc", 5),
        )
    else:
        return f"Unknown tool '{fname}'."


def run_anthropic_agent(user_request: str, history: list = None) -> str:
    """Executes agent loop using Anthropic Claude with tool calling and fallback."""
    global anthropic_client, MODEL_NAME, ACTIVE_PROVIDER
    if not anthropic_client:
        raise ValueError("Anthropic Claude client is not initialized. Please configure your Claude API key.")

    system_prompt = (
        "You are an intelligent AI Assistant with expert Multi-Format Document Intelligence and Quality Control (QC) capabilities. "
        "You can answer general questions, solve math calculations, write code, explain concepts, and analyze uploaded files in ANY format: "
        "PDFs (.pdf), Word documents (.docx, .doc), plain text / code / CSV / JSON (.txt, .md, .csv, .json), and images (.png, .jpg, .webp). "
        "\n"
        "Guidelines:\n"
        "1. General Questions & Greetings: If the user asks general knowledge questions, math problems, greetings, or questions not tied to uploaded documents, answer directly, clearly, and helpfully without searching files.\n"
        "2. Arithmetic: Use the calculate tool whenever arithmetic is needed.\n"
        "3. Document Analysis & QC: When asked about uploaded documents or Quality Control, verify data across files (order numbers, parties, dates, addresses, amounts), check for discrepancies, and inspect files using read_document, inspect_image, or read_multiple_documents.\n"
        "4. Table Presentation: When presenting structured or multi-item records—such as Deed History / Chain of Title (with columns like #, Deed Type, Grantor, Grantee, Book / Page, Dated, Recorded), Tax Information, Fees/Invoices, Party Comparison, or Quality Control Audit checks—ALWAYS format them as a clean Markdown table with headers and row separators. Ensure each table has an empty line before and after it for proper rendering."
    )

    anthropic_tools = []
    for t in tools:
        func = t.get("function", {})
        anthropic_tools.append({
            "name": func.get("name"),
            "description": func.get("description", ""),
            "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
        })

    claude_messages = []
    if history:
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                role = "assistant" if msg["role"] == "assistant" else "user"
                claude_messages.append({"role": role, "content": msg["content"]})

    claude_messages.append({"role": "user", "content": user_request})

    for _ in range(10):
        try:
            response = anthropic_client.messages.create(
                model=MODEL_NAME,
                max_tokens=4096,
                system=system_prompt,
                messages=claude_messages,
                tools=anthropic_tools,
            )
        except Exception as err:
            err_str = str(err)
            new_client, new_model, new_provider = switch_to_fallback(err_str[:80])
            if new_client:
                return run_agent(user_request, history=history)
            raise err

        tool_use_blocks = [b for b in response.content if getattr(b, "type", None) == "tool_use"]
        text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text" or hasattr(b, "text")]

        if not tool_use_blocks or response.stop_reason != "tool_use":
            return "".join(text_blocks) or "No response was produced."

        claude_messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for b in tool_use_blocks:
            fname = b.name
            raw_args = b.input
            args = raw_args if isinstance(raw_args, dict) else {}
            result = execute_agent_tool(fname, args)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": b.id,
                "content": str(result),
            })
        claude_messages.append({"role": "user", "content": tool_results})

    return "The agent reached its tool-call limit while analyzing documents."


def run_agent(user_request: str, history: list = None) -> str:
    if ACTIVE_PROVIDER == "Claude" and anthropic_client is not None:
        return run_anthropic_agent(user_request, history=history)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an intelligent AI Assistant with expert Multi-Format Document Intelligence and Quality Control (QC) capabilities. "
                "You can answer general questions, solve math calculations, write code, explain concepts, and analyze uploaded files in ANY format: "
                "PDFs (.pdf), Word documents (.docx, .doc), plain text / code / CSV / JSON (.txt, .md, .csv, .json), and images (.png, .jpg, .webp). "
                "\n"
                "Guidelines:\n"
                "1. General Questions & Greetings: If the user asks general knowledge questions, math problems, greetings, or questions not tied to uploaded documents, answer directly, clearly, and helpfully without searching files.\n"
                "2. Arithmetic: Use the calculate tool whenever arithmetic is needed.\n"
                "3. Document Analysis & QC: When asked about uploaded documents or Quality Control, verify data across files (order numbers, parties, dates, addresses, amounts), check for discrepancies, and inspect files using read_document, inspect_image, or read_multiple_documents.\n"
                "4. Table Presentation: When presenting structured or multi-item records—such as Deed History / Chain of Title (with columns like #, Deed Type, Grantor, Grantee, Book / Page, Dated, Recorded), Tax Information, Fees/Invoices, Party Comparison, or Quality Control Audit checks—ALWAYS format them as a clean Markdown table with headers and row separators. Ensure each table has an empty line before and after it for proper rendering."
            ),
        },
    ]

    if history:
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append(
        {
            "role": "user",
            "content": user_request,
        }
    )

    if client is None and not (ACTIVE_PROVIDER == "Claude" and anthropic_client is not None):
        raise ValueError("No active AI API key found. Please enter your OpenRouter, Claude, Gemini, or Groq API key in the API Settings.")

    # Track active LLM engine for this session with fallback support
    active_client = client
    active_model = MODEL_NAME
    active_provider = ACTIVE_PROVIDER

    # Allow up to 10 tool iterations for comprehensive multi-document QC.
    for _ in range(10):
        create_kwargs = {
            "model": active_model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
        }
        if "fable" not in active_model.lower():
            create_kwargs["temperature"] = 0.2
        try:
            response = active_client.chat.completions.create(**create_kwargs)
        except Exception as err:
            err_str = str(err)
            # If current provider encounters failure, attempt cascading fallback
            while True:
                new_client, new_model, new_provider = switch_to_fallback(err_str[:80])
                if not new_client:
                    raise err
                if new_provider == "Claude" and anthropic_client is not None:
                    return run_anthropic_agent(user_request, history=history)
                active_client = new_client
                active_model = new_model
                active_provider = new_provider
                try:
                    retry_kwargs = {
                        "model": active_model,
                        "messages": messages,
                        "tools": tools,
                        "tool_choice": "auto",
                    }
                    if "fable" not in active_model.lower():
                        retry_kwargs["temperature"] = 0.2
                    response = active_client.chat.completions.create(**retry_kwargs)
                    break
                except Exception as retry_err:
                    err = retry_err
                    err_str = str(retry_err)

        message = response.choices[0].message

        # Save the assistant's response, including any tool calls.
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return message.content or "No response was produced."

        for tool_call in message.tool_calls:
            fname = tool_call.function.name
            raw_args = tool_call.function.arguments
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except Exception:
                args = {}

            result = execute_agent_tool(fname, args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )

    return "The agent reached its tool-call limit while analyzing documents."


if __name__ == "__main__":
    print("Type 'quit' to exit.")

    while True:
        request = input("\nYou: ")

        if request.lower() in {"quit", "exit"}:
            break

        print("Agent:", run_agent(request))