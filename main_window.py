"""
主窗口：应用只有一个 MainWindow；主页选版本 → 栈切换到 VersionPage → 返回再切回主页。

── PyQt 初学者可先对照下列概念读本文件 ──
1. QMainWindow（本类继承它）
   - 比 QWidget 多了「菜单栏 / 工具栏 / 状态栏 / 停靠区」等预留位置；最少也要设一个 centralWidget。
   - 本骨架没用菜单栏，只把 QStackedWidget 塞进中央区域，占满客户区。
2. QStackedWidget（核心容器）
   - 多个子页面叠在同一矩形区域，**任意时刻只显示其中一个**；像一摞扑克牌只翻开一张。
   - 用「索引」或「控件指针」切换当前页：setCurrentIndex / setCurrentWidget。
   - **顺序很重要**：本文件约定索引 **0 = 主页**，必须先 addWidget(home)，再往栈里追加各 VersionPage；
     `_go_home` 里写 setCurrentIndex(0) 才能稳定回到主页。
3. 布局（QVBoxLayout / QHBoxLayout）
   - 主页由竖排（标题 + 一整行按钮）拼出来；那一行按钮又用横排布局承载。
4. 信号槽（配合 version_page）
   - 主页按钮：`clicked` → lambda → `_open_version`。
   - 版本页：`VersionPage.back_requested` → `_go_home`（子页面不直接操作栈，只发信号）。
5. Python 闭包（按钮 lambda）
   - 循环里创建多个按钮时，用 `lambda checked, v=vid: ...` 把当前的 vid「冻结」进默认参数，
     避免四个按钮都指向最后一次循环的 vid（详见下方循环内注释）。

与其它文件的衔接：
- VERSION_ENTRIES 里的 vid（version1…）必须与 prompts/version*.txt、data/*.json 键名一致。
- VersionPage 构造后缓存在 `_version_pages`，避免重复创建、保留聊天记录所在控件不被销毁。

类型标注：`from __future__ import annotations` 与其它模块一致。
"""

# 让当前文件里可以用「list[str]」这种写法标注类型（Python 3.9+ 也可不用这行；写上兼容旧习惯）
from __future__ import annotations

# 第三方：PyQt6 窗口与布局控件
from PyQt6.QtWidgets import (
    QHBoxLayout,  # 水平布局：子控件从左到右排列
    QLabel,  # 静态文字标签
    QMainWindow,  # 标准主窗口框架（本类的基类）
    QPushButton,  # 可点击按钮，发出 clicked 信号
    QStackedWidget,  # 多页叠放、只显示一页的切换容器
    QVBoxLayout,  # 垂直布局：子控件从上到下排列
    QWidget,  # 通用矩形控件基类；可作为一页的「根容器」
)

# 同项目：某一魔兽版本的完整页面（左任务树 + 右 Tab）
from version_page import VersionPage

import data_manager
import sections_loader

# 主页四个按钮的数据源：每项 (内部 id, 按钮上显示的中文)。
# 内部 id 必须稳定（字符串），供 OpenAI/DeepSeek、路径 prompts、JSON 使用；中文 label 仅展示。
VERSION_ENTRIES = (
    ("version1", "魔兽世界一 · 备战"),
    ("version2", "魔兽世界二 · 装备"),
    ("version3", "魔兽世界三 · 开战"),
    ("version4", "魔兽世界四 · 终极版"),
)


class MainWindow(QMainWindow):
    """
    应用程序唯一的顶层窗口实例（main.py 里创建并 show）。

    主要职责：
    - 搭建「主页」UI，并为每个版本缓存一个 VersionPage；
    - 维护 QStackedWidget 的页面栈与「当前显示哪一页」。
    """

    def __init__(self) -> None:
        # QMainWindow 必须先初始化，才能使用 setCentralWidget 等 API
        super().__init__()
        # 窗口标题栏显示的字符串（操作系统任务栏、窗口左上角可见）
        self.setWindowTitle("AI 编程教练（骨架）")
        # 初始客户区宽高（像素）；用户仍可拖拽边缘改变大小，内部布局会随之伸缩
        self.resize(960, 640)

        # ────────── 栈容器：所有「整页」界面都放在这里面 ──────────
        self._stack = QStackedWidget()

        # ────────── 第 0 页：主页（选版本）──────────
        home = QWidget()  # 无独立窗口边框，仅作为一页内容的根控件
        home_layout = QVBoxLayout(home)  # 把垂直布局绑定到 home：子控件自上而下排列
        home_layout.addWidget(QLabel("选择题目版本"))  # 顶部提示文字；QLabel 默认不接收点击
        row = QHBoxLayout()  # 下一行将容纳四个并排按钮；此时还未 attach 到 home

        self._home_version_buttons: list[tuple[str, QPushButton]] = []

        for vid, label in VERSION_ENTRIES:
            btn = QPushButton(label)  # 按钮文字为用户可读标题；vid 保存在闭包里

            # --- clicked.connect(lambda ...) 语法拆解 ---
            # clicked：按钮点击时发出的信号；connect：注册回调。
            # lambda checked, v=vid: ...：匿名函数。clicked 会传入 checked（是否处于勾选态），
            #   lambda 必须留出第一个参数接住，否则 Qt 传参与函数签名不匹配。
            # v=vid：在「定义 lambda 的这一轮循环」把 vid 复制进默认参数，四个按钮各绑定自己的版本；
            #   若误写 lambda: self._open_version(vid)，四条按钮常会全部指向最后一次循环的 vid。
            # 函数体：调用 _open_version，切换栈到对应 VersionPage。
            btn.clicked.connect(lambda checked, v=vid: self._open_version(v))

            row.addWidget(btn)  # 从左到右依次放入四个按钮
            self._home_version_buttons.append((vid, btn))

        self._refresh_home_progress_labels()

        # 把横向布局整体作为「第二行」塞进竖向布局（第一行是 QLabel）
        home_layout.addLayout(row)

        # 主页必须是栈里第一个 addWidget，从而索引恒为 0，供 _go_home 使用
        self._stack.addWidget(home)

        # version_id → 已创建的 VersionPage 实例；首次进入某版本时创建并缓存，返回主页不销毁
        # self._version_pages：实例属性；前导 _ 表示约定「类内部使用」。
        # dict[str, VersionPage]：类型标注（键为版本字符串，值为页面对象）；运行时不强制检查。
        self._version_pages: dict[str, VersionPage] = {}

        # 把整个栈交给主窗口中央区域；此后可见内容完全由 _stack 当前页决定
        self.setCentralWidget(self._stack)

    def _refresh_home_progress_labels(self) -> None:
        """主页按钮展示「已勾选 / 左侧全部复选框」计数（见 sections_loader）。"""
        data = data_manager.load_user_data()
        for vid, btn in self._home_version_buttons:
            label = next(l for v, l in VERSION_ENTRIES if v == vid)
            den = sections_loader.progress_denominator(vid)
            num = sections_loader.progress_numerator(data, vid)
            btn.setText(f"{label}  [{num}/{den}]")

    def _open_version(self, version_id: str) -> None:
        """响应主页按钮：切换到对应版本的 VersionPage（必要时先创建）。"""
        # version_id 与 VERSION_ENTRIES、prompts、JSON 中的键一致，例如 "version1"
        if version_id not in self._version_pages:
            page = VersionPage(version_id)
            # 用户在该页点「← 返回主页」时，VersionPage 发射 back_requested；这里订阅并转到首页
            page.back_requested.connect(self._go_home)
            self._version_pages[version_id] = page
            # 为新页面分配栈中的下一个索引（跟在已有所有页后面）；索引 0 永远是主页
            self._stack.addWidget(page)

        # 已创建则直接切换可见页；setCurrentWidget 不重复添加控件，仅改变当前显示的子控件
        self._stack.setCurrentWidget(self._version_pages[version_id])

    def _go_home(self) -> None:
        """
        槽函数：由 VersionPage 的 back_requested 触发，回到主页。

        setCurrentIndex(0) 依赖 __init__ 中「第一个 addWidget 是 home」的约定；
        若将来调整 addWidget 顺序，必须同步修改这里的索引或改用按对象切换。
        """
        self._stack.setCurrentIndex(0)
        self._refresh_home_progress_labels()
