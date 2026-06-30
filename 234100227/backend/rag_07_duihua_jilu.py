# ==========================
# 模块 07：对话历史管理
# 功能：对话历史的增删查改、导出
#       以 JSON 文件持久化存储
# ==========================
import os
import json
import time
from datetime import datetime
from backend.config import HISTORY_DIR, MAX_HISTORY_ROUNDS


class ChatHistory:
    """单会话的对话历史管理器"""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.messages: list[dict] = []
        self._file_path = HISTORY_DIR / f"{session_id}.json"
        self._load()

    def _load(self):
        """从文件加载历史"""
        if self._file_path.exists():
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.messages = data.get("messages", [])
            except (json.JSONDecodeError, KeyError):
                self.messages = []

    def _save(self):
        """保存到文件"""
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        with open(self._file_path, "w", encoding="utf-8") as f:
            json.dump({
                "session_id": self.session_id,
                "updated_at": datetime.now().isoformat(),
                "messages": self.messages,
            }, f, ensure_ascii=False, indent=2)

    def add(self, question: str, answer_data: dict):
        """
        添加一轮对话

        Args:
            question: 用户问题
            answer_data: {text: str, score: float, sources: list}
        """
        record = {
            "id": len(self.messages) + 1,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer_data.get("text", ""),
            "score": answer_data.get("score", 0.0),
            "sources": answer_data.get("sources", []),
        }
        self.messages.append(record)

        # 只保留最近 N 轮
        if len(self.messages) > MAX_HISTORY_ROUNDS:
            self.messages = self.messages[-MAX_HISTORY_ROUNDS:]

        self._save()

    def get_history_text(self, max_rounds: int = 10) -> str:
        """
        获取格式化的对话历史文本（用于 Prompt 构建）

        Returns:
            "用户: xxx\n助手: xxx\n..."
        """
        recent = self.messages[-max_rounds:] if max_rounds > 0 else self.messages
        lines = []
        for r in recent:
            lines.append(f"用户: {r['question']}")
            lines.append(f"助手: {r['answer']}")
        return "\n".join(lines)

    def get_all(self) -> list[dict]:
        """获取全部历史"""
        return self.messages

    def get_recent(self, n: int = 10) -> list[dict]:
        """获取最近 N 轮"""
        return self.messages[-n:]

    def delete_message(self, msg_id: int) -> bool:
        """删除指定消息"""
        before = len(self.messages)
        self.messages = [m for m in self.messages if m["id"] != msg_id]
        if len(self.messages) < before:
            self._save()
            return True
        return False

    def clear(self):
        """清空历史"""
        self.messages = []
        self._save()

    def export(self) -> str:
        """导出为格式化的文本"""
        lines = [f"会话 ID: {self.session_id}"]
        lines.append(f"导出时间: {datetime.now().isoformat()}")
        lines.append(f"消息数量: {len(self.messages)}")
        lines.append("=" * 50)
        for r in self.messages:
            lines.append(f"\n[{r['timestamp']}]")
            lines.append(f"问: {r['question']}")
            lines.append(f"答: {r['answer']}")
            if r.get("sources"):
                lines.append("来源:")
                for s in r["sources"]:
                    lines.append(f"  - {s.get('filename', '未知')} (相似度: {s.get('score', 0):.2f})")
            lines.append("-" * 40)
        return "\n".join(lines)

    @property
    def count(self) -> int:
        return len(self.messages)


# ==========================
# 全局会话管理器
# ==========================
class SessionManager:
    """管理多个会话"""

    def __init__(self):
        self._sessions: dict[str, ChatHistory] = {}

    def get_session(self, session_id: str = "default") -> ChatHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatHistory(session_id)
        return self._sessions[session_id]

    def list_sessions(self) -> list[dict]:
        """列出所有会话"""
        sessions = []
        if HISTORY_DIR.exists():
            for f in sorted(HISTORY_DIR.iterdir(), reverse=True):
                if f.suffix == ".json":
                    try:
                        with open(f, "r", encoding="utf-8") as fp:
                            data = json.load(fp)
                        sessions.append({
                            "session_id": data.get("session_id", f.stem),
                            "updated_at": data.get("updated_at", ""),
                            "message_count": len(data.get("messages", [])),
                        })
                    except Exception:
                        pass
        return sessions

    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
        file_path = HISTORY_DIR / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()

    def clear_all(self):
        """清空所有会话"""
        self._sessions.clear()
        if HISTORY_DIR.exists():
            for f in HISTORY_DIR.iterdir():
                if f.suffix == ".json":
                    f.unlink()


# ────── 全局单例 ──────
session_manager = SessionManager()


# ==========================
# 测试入口
# ==========================
if __name__ == "__main__":
    # 测试单会话
    ch = ChatHistory("test_session")
    ch.add("什么是东巴文化？", {
        "text": "东巴文化是纳西族的传统文化...",
        "score": 0.92,
        "sources": [{"filename": "东巴文化.txt", "score": 0.92}],
    })
    print(f"消息数: {ch.count}")
    print(ch.get_history_text())