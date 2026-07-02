"""Document loading from knowledge base directories.

Supports: .txt, .md, .pdf, .docx, .html
"""
import os, sys
from pathlib import Path
from backend.config import KNOWLEDGE_BASES_DIR, SUPPORTED_EXTENSIONS

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _read_txt(file_path: str) -> str:
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return ""


def _read_md(file_path: str) -> str:
    return _read_txt(file_path)


def _read_html(file_path: str) -> str:
    import re
    raw = _read_txt(file_path)
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def _read_pdf(file_path: str) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        parts = [p.extract_text() for p in reader.pages if p.extract_text()]
        return "\n".join(parts)
    except Exception as e:
        print(f"[WARN] PDF read failed {file_path}: {e}")
        return ""


def _read_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        print(f"[WARN] DOCX read failed {file_path}: {e}")
        return ""


_READERS = {
    ".txt": _read_txt, ".md": _read_md, ".html": _read_html,
    ".pdf": _read_pdf, ".docx": _read_docx,
}


def load_documents(kb_name: str) -> list[dict]:
    """Load all documents from a knowledge base directory.

    Returns:
        [{"content": str, "source": str, "filename": str}, ...]
    """
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    if not kb_dir.exists():
        print(f"[WARN] KB directory not found: {kb_dir}")
        return []

    documents = []
    for file_path in sorted(kb_dir.iterdir()):
        if not file_path.is_file():
            continue
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue
        reader = _READERS.get(suffix)
        if reader is None:
            continue
        try:
            content = reader(str(file_path))
            if not content or not content.strip():
                print(f"[SKIP] Empty document: {file_path.name}")
                continue
            documents.append({"content": content, "source": str(file_path), "filename": file_path.name})
            print(f"[OK] Loaded: {file_path.name} ({len(content)} chars)")
        except Exception as e:
            print(f"[ERROR] Failed to load {file_path.name}: {e}")

    print(f"[INFO] KB [{kb_name}]: {len(documents)} documents loaded")
    return documents


def list_knowledge_bases() -> list[str]:
    """List all available knowledge base names."""
    if not KNOWLEDGE_BASES_DIR.exists():
        return []
    return sorted(
        n for n in os.listdir(KNOWLEDGE_BASES_DIR)
        if (KNOWLEDGE_BASES_DIR / n).is_dir() and not n.startswith(".")
    )


if __name__ == "__main__":
    kbs = list_knowledge_bases()
    print(f"Found {len(kbs)} KBs: {kbs}")
    if kbs:
        docs = load_documents(kbs[0])
        if docs:
            print(f"\nSample: {docs[0]['filename']}")
            print(f"Preview: {docs[0]['content'][:200]}")
