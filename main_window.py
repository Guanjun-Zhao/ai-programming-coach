"""
主窗口：主页四个版本按钮 + 栈式切换到对应 VersionPage。

初学者可以这样理解：
1. QMainWindow：带菜单栏/状态栏位的标准主窗口（这里只用了中央区域）。
2. QStackedWidget：像一摞卡片，每次只显示一页；索引 0 是主页，后面是各版本页。
3. lambda 里 `v=vid`：Python 闭包技巧，避免循环里所有按钮都指向最后一个 vid。
"""

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

# 单个版本的完整页面（左侧任务 + 右侧 Tab）
from version_page import VersionPage

# 常量：版本内部 id（与 prompts、JSON 键一致）和人类可读标题
VERSION_ENTRIES = (
    ("version1", "魔兽世界一 · 备战"),
    ("version2", "魔兽世界二 · 装备"),
    ("version3", "魔兽世界三 · 开战"),
    ("version4", "魔兽世界四 · 终极版"),
)


class MainWindow(QMainWindow):
    """应用顶层窗口：主页进入版本页，版本页可请求返回主页。"""

    def __init__(self) -> None:
        # 初始化 Qt 窗口对象
        super().__init__()
        self.setWindowTitle("AI 编程教练（骨架）")
        self.resize(960, 640)

        # 栈控件：以后每打开一个新版本就往里 addWidget 一页
        self._stack = QStackedWidget()
        # 主页：简单垂直布局，上面标题下面一排按钮
        home = QWidget()
        home_layout = QVBoxLayout(home)
        home_layout.addWidget(QLabel("选择题目版本"))
        row = QHBoxLayout()
        # 解包元组：vid 用于程序内部，label 显示在按钮上
        for vid, label in VERSION_ENTRIES:
            btn = QPushButton(label)
            # clicked 信号会带一个 checked 布尔参数；lambda 默认参数 v=vid「冻结」当前循环变量
            # 若写 lambda: self._open_version(vid)，可能四条按钮都指向最后一次的 vid（经典坑）
            btn.clicked.connect(lambda checked, v=vid: self._open_version(v))
            row.addWidget(btn)
        home_layout.addLayout(row)

        # 索引 0：主页
        self._stack.addWidget(home)
        # 缓存已创建的版本页，避免重复 new
        self._version_pages: dict[str, VersionPage] = {}
        # 把栈设为窗口中央部件（填满客户区）
        self.setCentralWidget(self._stack)

    def _open_version(self, version_id: str) -> None:
        """首次进入某版本时创建页面并连接返回信号；然后切换到该页。"""
        if version_id not in self._version_pages:
            page = VersionPage(version_id)
            # 子页面发信号要求回到主页（见 version_page 里返回按钮）
            page.back_requested.connect(self._go_home)
            self._version_pages[version_id] = page
            self._stack.addWidget(page)
        # 切换栈当前显示的控件
        self._stack.setCurrentWidget(self._version_pages[version_id])

    def _go_home(self) -> None:
        """版本页点返回：栈回到索引 0（主页）。"""
        self._stack.setCurrentIndex(0)
