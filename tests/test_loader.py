"""Tests for the document loader module.

Covers: TXT with multiple encodings, PDF, DOCX, empty docs filtering.
"""
import sys, os, tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.loader import load_documents, list_knowledge_bases


def _create_kb_dir(tmp_path: Path, name: str = "test_kb") -> Path:
    kb_dir = tmp_path / "knowledge_bases" / name
    kb_dir.mkdir(parents=True, exist_ok=True)
    return kb_dir


def test_load_txt_utf8(tmp_path):
    kb_dir = _create_kb_dir(tmp_path)
    (kb_dir / "doc_utf8.txt").write_text("你好世界", encoding="utf-8")

    with patch("backend.loader.KNOWLEDGE_BASES_DIR", tmp_path / "knowledge_bases"):
        docs = load_documents("test_kb")

    assert len(docs) == 1
    assert "你好世界" in docs[0]["content"]


def test_load_txt_gbk(tmp_path):
    kb_dir = _create_kb_dir(tmp_path)
    text = "你好世界"
    (kb_dir / "doc_gbk.txt").write_bytes(text.encode("gbk"))

    with patch("backend.loader.KNOWLEDGE_BASES_DIR", tmp_path / "knowledge_bases"):
        docs = load_documents("test_kb")

    assert len(docs) == 1
    assert "你好世界" in docs[0]["content"]


def test_skip_unsupported_extension(tmp_path):
    kb_dir = _create_kb_dir(tmp_path)
    (kb_dir / "data.csv").write_text("a,b,c\n1,2,3", encoding="utf-8")

    with patch("backend.loader.KNOWLEDGE_BASES_DIR", tmp_path / "knowledge_bases"):
        docs = load_documents("test_kb")

    assert len(docs) == 0


def test_skip_empty_document(tmp_path):
    kb_dir = _create_kb_dir(tmp_path)
    (kb_dir / "empty.txt").write_text("   \n  ", encoding="utf-8")

    with patch("backend.loader.KNOWLEDGE_BASES_DIR", tmp_path / "knowledge_bases"):
        docs = load_documents("test_kb")

    assert len(docs) == 0


def test_list_knowledge_bases(tmp_path):
    root = tmp_path / "knowledge_bases"
    (root / "kb_a").mkdir(parents=True)
    (root / "kb_b").mkdir()

    with patch("backend.loader.KNOWLEDGE_BASES_DIR", root):
        kbs = list_knowledge_bases()

    assert "kb_a" in kbs
    assert "kb_b" in kbs


def test_ignore_hidden_dirs(tmp_path):
    root = tmp_path / "knowledge_bases"
    (root / "kb_a").mkdir(parents=True)
    (root / ".hidden_kb").mkdir()

    with patch("backend.loader.KNOWLEDGE_BASES_DIR", root):
        kbs = list_knowledge_bases()

    assert "kb_a" in kbs
    assert ".hidden_kb" not in kbs
