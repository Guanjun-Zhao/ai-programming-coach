"""版本页：左侧任务列表 + 右侧教练/样例切换。"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from chat_widget import ChatWidget
from sample_library import SampleLibraryWidget


class VersionPage(QWidget):
    """单个魔兽世界版本的交互页。"""

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

        self._stack = QStackedWidget()
        self._chat = ChatWidget(version_id, "task1")
        self._samples = SampleLibraryWidget()
        self._samples.set_context(version_id, "task1")
        self._stack.addWidget(self._chat)
        self._stack.addWidget(self._samples)

        mode_row = QHBoxLayout()
        btn_coach = QPushButton("AI 教练")
        btn_samples = QPushButton("样例库")
        btn_coach.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        btn_samples.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        mode_row.addWidget(btn_coach)
        mode_row.addWidget(btn_samples)
        mode_row.addStretch()

        left = QVBoxLayout()
        left.addWidget(QLabel("任务清单"))
        left.addWidget(self._task_list)

        right = QVBoxLayout()
        right.addLayout(mode_row)
        right.addWidget(self._stack)

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
