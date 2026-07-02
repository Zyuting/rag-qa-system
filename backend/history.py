"""Session and conversation history management with JSON persistence."""
import os, json
from datetime import datetime
from backend.config import HISTORY_DIR, MAX_HISTORY_ROUNDS


class ChatHistory:
    """Persistent conversation history for a single session."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.messages: list[dict] = []
        self._file_path = HISTORY_DIR / f"{session_id}.json"
        self._load()

    def _load(self):
        if self._file_path.exists():
            try:
                data = json.loads(self._file_path.read_text(encoding="utf-8"))
                self.messages = data.get("messages", [])
            except (json.JSONDecodeError, KeyError):
                self.messages = []

    def _save(self):
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        self._file_path.write_text(
            json.dumps({
                "session_id": self.session_id,
                "updated_at": datetime.now().isoformat(),
                "messages": self.messages,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add(self, question: str, answer_data: dict):
        record = {
            "id": len(self.messages) + 1,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer_data.get("text", ""),
            "score": answer_data.get("score", 0.0),
            "sources": answer_data.get("sources", []),
        }
        self.messages.append(record)
        if len(self.messages) > MAX_HISTORY_ROUNDS:
            self.messages = self.messages[-MAX_HISTORY_ROUNDS:]
        self._save()

    def get_history_text(self, max_rounds: int = 10) -> str:
        recent = self.messages[-max_rounds:] if max_rounds > 0 else self.messages
        return "\n".join(f"User: {r['question']}\nAssistant: {r['answer']}" for r in recent)

    def get_all(self) -> list[dict]:
        return self.messages

    def get_recent(self, n: int = 10) -> list[dict]:
        return self.messages[-n:]

    def delete_message(self, msg_id: int) -> bool:
        before = len(self.messages)
        self.messages = [m for m in self.messages if m["id"] != msg_id]
        if len(self.messages) < before:
            self._save()
            return True
        return False

    def clear(self):
        self.messages = []
        self._save()

    def export(self) -> str:
        lines = [f"Session: {self.session_id}"]
        lines.append(f"Exported: {datetime.now().isoformat()}")
        lines.append(f"Messages: {len(self.messages)}")
        lines.append("=" * 50)
        for r in self.messages:
            lines.append(f"\n[{r['timestamp']}]")
            lines.append(f"Q: {r['question']}")
            lines.append(f"A: {r['answer']}")
            if r.get("sources"):
                lines.append("Sources:")
                for s in r["sources"]:
                    lines.append(f"  - {s.get('filename', '?')} (score: {s.get('score', 0):.2f})")
            lines.append("-" * 40)
        return "\n".join(lines)

    @property
    def count(self) -> int:
        return len(self.messages)


class SessionManager:
    """Manages multiple chat sessions."""

    def __init__(self):
        self._sessions: dict[str, ChatHistory] = {}

    def get_session(self, session_id: str = "default") -> ChatHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatHistory(session_id)
        return self._sessions[session_id]

    def list_sessions(self) -> list[dict]:
        if not HISTORY_DIR.exists():
            return []
        sessions = []
        for f in sorted(HISTORY_DIR.iterdir(), reverse=True):
            if f.suffix != ".json":
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sessions.append({
                    "session_id": data.get("session_id", f.stem),
                    "updated_at": data.get("updated_at", ""),
                    "message_count": len(data.get("messages", [])),
                })
            except Exception:
                pass
        return sessions

    def delete_session(self, session_id: str):
        self._sessions.pop(session_id, None)
        path = HISTORY_DIR / f"{session_id}.json"
        if path.exists():
            path.unlink()

    def clear_all(self):
        self._sessions.clear()
        if HISTORY_DIR.exists():
            for f in HISTORY_DIR.iterdir():
                if f.suffix == ".json":
                    f.unlink()


session_manager = SessionManager()


if __name__ == "__main__":
    ch = ChatHistory("test_session")
    ch.add("What is Dongba?", {
        "text": "Dongba culture is the traditional culture of the Naxi people...",
        "score": 0.92,
        "sources": [{"filename": "dongba.txt", "score": 0.92}],
    })
    print(f"Messages: {ch.count}")
    print(ch.get_history_text())
