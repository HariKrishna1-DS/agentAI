import ast
import json
import operator as op
import os

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv()

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

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


def list_available_pdfs() -> str:
    """Discovers all available PDF documents in the uploads directory with page counts."""
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        return "No uploads directory found."
    files = [f for f in os.listdir(upload_dir) if f.lower().endswith(".pdf")]
    if not files:
        return "No PDF files available in uploads directory."

    info = []
    for f in sorted(files):
        p = os.path.join(upload_dir, f)
        try:
            reader = PdfReader(p)
            info.append(f"- {f} ({len(reader.pages)} pages)")
        except Exception:
            info.append(f"- {f} (page count unavailable)")
    return "Available Documents:\n" + "\n".join(info)


def read_multiple_pdfs(file_paths: list, pages_per_doc: int = 5) -> str:
    """Reads starting pages from multiple PDF files simultaneously for comparison and QC."""
    results = []
    for path in file_paths:
        clean = path.strip().strip("'\"")
        content = read_pdf(clean, start_page=1, end_page=pages_per_doc)
        results.append(f"=== {os.path.basename(clean)} ===\n{content}")
    return "\n\n" + ("=" * 40) + "\n\n".join(results)


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
            "name": "read_pdf",
            "description": "Extracts text content from a local PDF file path across all pages or specific page ranges. Use this tool whenever the user wants to read, analyze, summarize, or ask questions about a specific PDF document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the PDF file (e.g., 'sample.pdf' or 'documents/report.pdf').",
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "Optional 1-based start page to read from (defaults to 1).",
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "Optional 1-based end page to read up to (defaults to all pages).",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_pdfs",
            "description": "Lists all PDF documents currently uploaded and available in the workspace, along with their page counts. Use this first when performing cross-document analysis or QC audits.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_multiple_pdfs",
            "description": "Reads the first few pages of multiple PDF files at once. Essential for fast cross-document comparison and QC audits across files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of PDF filenames or paths to inspect together.",
                    },
                    "pages_per_doc": {
                        "type": "integer",
                        "description": "Number of pages to read from each document (default 5).",
                    },
                },
                "required": ["file_paths"],
            },
        },
    },
]


def run_agent(user_request: str, history: list = None) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an intelligent AI Assistant with expert Document Intelligence and Quality Control (QC) capabilities. "
                "You can answer general questions, solve math calculations, write code, explain concepts, and analyze uploaded PDF documents. "
                "\n"
                "Guidelines:\n"
                "1. General Questions & Greetings: If the user asks general knowledge questions, math problems, greetings, or questions not tied to uploaded documents, answer directly, clearly, and helpfully without searching files.\n"
                "2. Arithmetic: Use the calculate tool whenever arithmetic is needed.\n"
                "3. Document Analysis & QC: When asked about uploaded documents or Quality Control, verify data across files (order numbers, parties, dates, addresses, amounts), check for discrepancies, and inspect files using read_pdf or read_multiple_pdfs."
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

    # Allow up to 10 tool iterations for comprehensive multi-document QC.
    for _ in range(10):
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,
        )

        message = response.choices[0].message

        # Save the assistant's response, including any tool calls.
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return message.content or "No response was produced."

        for tool_call in message.tool_calls:
            if tool_call.function.name == "calculate":
                arguments = json.loads(tool_call.function.arguments)
                result = calculate(arguments["expression"])

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
            elif tool_call.function.name == "read_pdf":
                arguments = json.loads(tool_call.function.arguments)
                result = read_pdf(
                    arguments["file_path"],
                    start_page=arguments.get("start_page", 1),
                    end_page=arguments.get("end_page", None),
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
            elif tool_call.function.name == "list_available_pdfs":
                result = list_available_pdfs()
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
            elif tool_call.function.name == "read_multiple_pdfs":
                arguments = json.loads(tool_call.function.arguments)
                result = read_multiple_pdfs(
                    arguments["file_paths"],
                    pages_per_doc=arguments.get("pages_per_doc", 5),
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
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