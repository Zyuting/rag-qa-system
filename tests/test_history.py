"""Tests for the history/session management module."""
import sys, os, json, tempfile, shutil
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.history import ChatHistory, SessionManager


@pytest.fixture
def temp_history_dir(tmp_path):
    return tmp_path / "history"


def test_chat_history_roundtrip(temp_history_dir):
    with patch("backend.history.HISTORY_DIR", temp_history_dir):
        ch = ChatHistory("test_session")
        ch.add("What is Dongba?", {
            "text": "Dongba culture is ...",
            "score": 0.92,
            "sources": [{"filename": "dongba.txt", "score": 0.92}],
        })
        assert ch.count == 1

        # Re-load from disk
        ch2 = ChatHistory("test_session")
        assert ch2.count == 1
        assert ch2.get_all()[0]["question"] == "What is Dongba?"


def test_chat_history_max_rounds(temp_history_dir):
    with patch("backend.history.HISTORY_DIR", temp_history_dir):
        ch = ChatHistory("test_session")
        # Add more than MAX_HISTORY_ROUNDS
        n = 25  # MAX_HISTORY_ROUNDS is 20
        for i in range(n):
            ch.add(f"Q{i}", {"text": f"A{i}", "score": 0.5, "sources": []})
        assert ch.count == 20  # trimmed to MAX_HISTORY_ROUNDS


def test_session_manager(temp_history_dir):
    with patch("backend.history.HISTORY_DIR", temp_history_dir):
        sm = SessionManager()
        s1 = sm.get_session("session_a")
        s1.add("Q1", {"text": "A1", "score": 0.5, "sources": []})

        s2 = sm.get_session("session_b")
        s2.add("Q2", {"text": "A2", "score": 0.5, "sources": []})

        sessions = sm.list_sessions()
        assert len(sessions) >= 2

        sm.delete_session("session_a")
        sessions = sm.list_sessions()
        session_ids = [s["session_id"] for s in sessions]
        assert "session_a" not in session_ids
        assert "session_b" in session_ids


def test_chat_history_clear(temp_history_dir):
    with patch("backend.history.HISTORY_DIR", temp_history_dir):
        ch = ChatHistory("clear_test")
        ch.add("Q", {"text": "A", "score": 0.5, "sources": []})
        ch.clear()
        assert ch.count == 0


def test_chat_history_export(temp_history_dir):
    with patch("backend.history.HISTORY_DIR", temp_history_dir):
        ch = ChatHistory("export_test")
        ch.add("Q", {"text": "A", "score": 0.9, "sources": [{"filename": "doc.txt", "score": 0.9}]})
        exported = ch.export()
        assert "Q" in exported
        assert "A" in exported
        assert "doc.txt" in exported
