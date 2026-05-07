"""版本页：左侧任务清单 + 右侧「AI 教练 / 样例库」Tab。"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from chat_widget import ChatWidget
from sample_library import SampleLibraryWidget


class VersionPage(QWidget):
    """单个题目版本的交互页（师圣晴主要负责美化与交互深化）。"""

    back_requested = pyqtSignal()

    def __init__(self, version_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = version_id

        back = QPushButton("← 返回主页")
        back.clicked.connect(self.back_requested.emit)

        self._task_list = QListWidget()
        for tid, title in (
            ("task1", "示例任务（占位）"),
        ):
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, tid)
            self._task_list.addItem(item)
        self._task_list.currentItemChanged.connect(self._on_task_changed)

        self._chat = ChatWidget(version_id, "task1")
        self._samples = SampleLibraryWidget()
        self._samples.set_context(version_id, "task1")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._chat, "AI 教练")
        self._tabs.addTab(self._samples, "样例库")

        left = QVBoxLayout()
        left.addWidget(QLabel("任务清单"))
        left.addWidget(self._task_list)

        right = QVBoxLayout()
        right.addWidget(self._tabs)

        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 3)

        outer = QVBoxLayout(self)
        outer.addWidget(back)
        outer.addLayout(body)

        self._task_list.setCurrentRow(0)

    def _on_task_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        task_id = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(task_id, str):
            return
        self._chat.set_task(task_id)
        self._chat.load_history()
        self._samples.set_context(self._version_id, task_id)
