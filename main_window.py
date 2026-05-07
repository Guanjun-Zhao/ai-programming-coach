"""主页：四个版本入口，栈式切换到 VersionPage。"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from version_page import VersionPage

VERSION_ENTRIES = (
    ("version1", "魔兽世界一 · 备战"),
    ("version2", "魔兽世界二 · 装备"),
    ("version3", "魔兽世界三 · 开战"),
    ("version4", "魔兽世界四 · 终极版"),
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI 编程教练（骨架）")
        self.resize(960, 640)

        self._stack = QStackedWidget()
        home = QWidget()
        home_layout = QVBoxLayout(home)
        home_layout.addWidget(QLabel("选择题目版本"))
        row = QHBoxLayout()
        for vid, label in VERSION_ENTRIES:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, v=vid: self._open_version(v))
            row.addWidget(btn)
        home_layout.addLayout(row)

        self._stack.addWidget(home)
        self._version_pages: dict[str, VersionPage] = {}
        self.setCentralWidget(self._stack)

    def _open_version(self, version_id: str) -> None:
        if version_id not in self._version_pages:
            page = VersionPage(version_id)
            page.back_requested.connect(self._go_home)
            self._version_pages[version_id] = page
            self._stack.addWidget(page)
        self._stack.setCurrentWidget(self._version_pages[version_id])

    def _go_home(self) -> None:
        self._stack.setCurrentIndex(0)
