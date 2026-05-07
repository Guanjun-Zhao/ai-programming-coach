"""AI 教练模式：聊天区 + 与 user_data 同步。"""
from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import ai_coach
import data_manager


class ChatWidget(QWidget):
    """
    当前版本 / 任务下的教练对话。
    切换任务时可调用 set_task(task_id) 再 load_history()。
    """

    def __init__(self, version_id: str, task_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = version_id
        self._task_id = task_id

        self._history_view = QTextEdit()
        self._history_view.setReadOnly(True)
        self._input = QLineEdit()
        self._input.setPlaceholderText("粘贴代码片段或描述你的问题…")
        send = QPushButton("发送")
        send.clicked.connect(self._on_send)
        self._input.returnPressed.connect(self._on_send)

        row = QHBoxLayout()
        row.addWidget(self._input)
        row.addWidget(send)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"AI 教练 · {version_id} / {task_id}"))
        layout.addWidget(self._history_view)
        layout.addLayout(row)

        self.load_history()

    def set_task(self, task_id: str) -> None:
        self._task_id = task_id
        self.load_history()

    def load_history(self) -> None:
        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        hist = slot.get("coach_history") or []
        self._history_view.clear()
        for m in hist:
            role = m.get("role", "")
            content = m.get("content", "")
            self._history_view.append(f"[{role}]\n{content}\n")

    def clear(self) -> None:
        """清空界面与持久化中当前任务的教练记录（可选调用）。"""
        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        slot["coach_history"] = []
        data_manager.save_user_data(data)
        self._history_view.clear()

    def append_message(self, role: str, content: str) -> None:
        self._history_view.append(f"[{role}]\n{content}\n")

    def _on_send(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()

        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        hist: list[dict[str, Any]] = list(slot.get("coach_history") or [])

        self.append_message("user", text)
        hist.append({"role": "user", "content": text})

        try:
            reply = ai_coach.chat(
                self._version_id,
                self._task_id,
                hist[:-1],
                text,
            )
        except Exception as exc:
            reply = f"[错误] {exc}"
            QMessageBox.warning(self, "教练请求失败", str(exc))

        self.append_message("assistant", reply)
        hist.append({"role": "assistant", "content": reply})
        slot["coach_history"] = hist
        data_manager.save_user_data(data)
