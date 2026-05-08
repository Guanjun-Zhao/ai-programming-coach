"""
版本页：左侧任务列表 + 右侧 Tab（AI 教练 / 样例库）。

初学者可以这样理解：
1. QListWidget：一条条可选中的列表项；隐藏的 UserRole 里存真正的 task_id 字符串。
2. currentItemChanged：用户改选任务时触发，用来同步聊天区与样例区。
3. pyqtSignal：子控件「通知」父窗口的信号槽机制（这里返回按钮发给 MainWindow）。
"""

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

    # 无参数信号：点击返回按钮时发射，MainWindow 监听后切回主页
    back_requested = pyqtSignal()

    def __init__(self, version_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = version_id

        back = QPushButton("← 返回主页")
        # clicked 连接 emit：一点击就发 back_requested
        back.clicked.connect(self.back_requested.emit)

        self._task_list = QListWidget()
        # 骨架只列一条占位任务；以后可换成读配置文件或写死多行
        for tid, title in (
            ("task1", "示例任务（占位）"),
        ):
            item = QListWidgetItem(title)
            # 用户看到的是 title；程序_read 时用 UserRole 取 tid（约定接口）
            item.setData(Qt.ItemDataRole.UserRole, tid)
            self._task_list.addItem(item)
        # 当前行变化：参数是当前项、上一项（上一项这里用 _ 前缀表示故意不用）
        self._task_list.currentItemChanged.connect(self._on_task_changed)

        # 聊天与样例都绑定初始任务 task1
        self._chat = ChatWidget(version_id, "task1")
        self._samples = SampleLibraryWidget()
        self._samples.set_context(version_id, "task1")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._chat, "AI 教练")
        self._tabs.addTab(self._samples, "样例库")

        # 左侧窄条：任务清单
        left = QVBoxLayout()
        left.addWidget(QLabel("任务清单"))
        left.addWidget(self._task_list)

        # 右侧宽：Tab
        right = QVBoxLayout()
        right.addWidget(self._tabs)

        # 水平比例 1:3（第二个 stretch 因子更大）
        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 3)

        outer = QVBoxLayout(self)
        outer.addWidget(back)
        outer.addLayout(body)

        # 初始化选中第一行，触发一次同步（若信号已连接，也会跑 _on_task_changed）
        self._task_list.setCurrentRow(0)

    def _on_task_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        """用户点击另一条任务：切换聊天历史上下文与样例列表。"""
        if current is None:
            return
        # 取出之前塞进 UserRole 的 task_id
        task_id = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(task_id, str):
            return
        self._chat.set_task(task_id)
        self._chat.load_history()
        self._samples.set_context(self._version_id, task_id)
