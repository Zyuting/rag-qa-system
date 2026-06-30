# ==========================
# 模块 02：知识库文档加载
# 功能：加载指定知识库目录下的所有文档
#       支持 .txt / .md / .pdf / .docx / .html
# ==========================
import os
import sys
from pathlib import Path
from backend.config import KNOWLEDGE_BASES_DIR, SUPPORTED_EXTENSIONS

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _read_txt(file_path: str) -> str:
    """读取纯文本文件"""
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return ""


def _read_md(file_path: str) -> str:
    """读取 Markdown 文件"""
    return _read_txt(file_path)


def _read_html(file_path: str) -> str:
    """读取 HTML 文件（简单去标签）"""
    import re
    raw = _read_txt(file_path)
    # 去除 script/style 标签
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    # 去除 HTML 标签
    raw = re.sub(r"<[^>]+>", " ", raw)
    # 合并空白
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def _read_pdf(file_path: str) -> str:
    """读取 PDF 文件"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except Exception as e:
        print(f"[WARN] PDF 读取失败 {file_path}: {e}")
        return ""


def _read_docx(file_path: str) -> str:
    """读取 Word 文档"""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"[WARN] DOCX 读取失败 {file_path}: {e}")
        return ""


# ─────────── 读取器映射 ───────────
_READERS = {
    ".txt": _read_txt,
    ".md": _read_md,
    ".html": _read_html,
    ".pdf": _read_pdf,
    ".docx": _read_docx,
}


def load_documents(kb_name: str) -> list[dict]:
    """
    加载指定知识库的所有文档

    Args:
        kb_name: 知识库目录名（如 "dongba"）

    Returns:
        [{"content": str, "source": str, "filename": str}, ...]
    """
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name

    if not kb_dir.exists():
        print(f"[WARN] 知识库目录不存在: {kb_dir}")
        return []

    documents = []
    files = sorted(kb_dir.iterdir())

    for file_path in files:
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
                print(f"[SKIP] 空文档: {file_path.name}")
                continue

            documents.append({
                "content": content,
                "source": str(file_path),
                "filename": file_path.name,
            })
            print(f"[OK] 加载成功: {file_path.name} ({len(content)} 字符)")

        except Exception as e:
            print(f"[ERROR] 加载失败 {file_path.name}: {e}")

    print(f"[INFO] 知识库 [{kb_name}] 共加载 {len(documents)} 个文档")
    return documents


def list_knowledge_bases() -> list[str]:
    """
    获取所有可用知识库名称列表

    Returns:
        ["dongba", "puercha", ...]
    """
    if not KNOWLEDGE_BASES_DIR.exists():
        return []

    kb_names = []
    for name in sorted(os.listdir(KNOWLEDGE_BASES_DIR)):
        kb_path = KNOWLEDGE_BASES_DIR / name
        if not kb_path.is_dir():
            continue
        # 排除隐藏目录
        if name.startswith('.'):
            continue
        kb_names.append(name)

    return kb_names


# ==========================
# 测试入口
# ==========================
if __name__ == "__main__":
    kbs = list_knowledge_bases()
    print(f"发现 {len(kbs)} 个知识库: {kbs}")

    if kbs:
        docs = load_documents(kbs[0])
        if docs:
            print(f"\n示例文档: {docs[0]['filename']}")
            print(f"内容预览 (前200字): {docs[0]['content'][:200]}")
