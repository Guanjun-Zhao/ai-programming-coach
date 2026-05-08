"""
版本页：左侧任务列表 + 右侧 Tab（AI 教练 / 样例库）。

══════════════════════════════════════════════════════════════════════════════
 PyQt 初学者导读（读代码前先看这一段）
══════════════════════════════════════════════════════════════════════════════

【控件树 Object tree】
  Qt 里几乎所有界面元素都是 QObject 的子类；带“界面”的是 QWidget。
  父子关系很重要：你创建子控件时通常传入 parent（或在布局里挂上去），Qt 会在父控件销毁时一起删掉子控件，
  避免手动泄漏。“先有父（或顶层窗口），再往上面摆子控件”。

【布局 Layout】
  不要用固定像素坐标硬编码按钮位置（除非特殊理由）。用 QVBoxLayout（纵向一排）、QHBoxLayout（横向一排）
  告诉 Qt：谁先谁后、谁先拉伸。布局可以嵌套：左边一列 + 右边一列，放进一个横向 body，再和顶部按钮放进纵向 outer。

【拉伸系数 stretch】
  addLayout(left, 1) 与 addLayout(right, 3) 里的 1 和 3 表示“多余水平空间按 1:3 分给左右”。
  所以左侧任务栏窄、右侧内容区宽。

【信号 Signal / 槽 Slot】
  用户点击、键盘、列表换行等都会“发信号”。你用 connect(信号, 槽) 把处理函数接上去。
  槽就是普通 Python 可调用对象（函数、方法、lambda）。这是事件驱动：你不用死循环问“用户点了没”。

【自定义信号 pyqtSignal】
  子页面不应直接 import MainWindow 去改窗口——耦合太紧。做法是：子页面定义自己的 pyqtSignal，
  在合适时机 emit()；主窗口在创建页面时 connect 信号到“切回主页”的方法。这样分工清晰。

【QListWidget 与 QListWidgetItem】
  列表里“一行”是一个 QListWidgetItem。显示文字用构造函数或 setText；额外数据用 setData(角色, 值)。
  Qt.ItemDataRole.UserRole 是预留给应用自定义数据的槽位（任务 id 等与界面文案无关的信息放这里）。

【QTabWidget】
  同一区域叠多个子页面，用户点标签切换。addTab(widget, "标签文字") 会把 widget 交给 Tab 管理显示/隐藏。

本文件里三类协作：
- QListWidget + currentItemChanged：换左侧任务时，刷新右侧聊天与样例的数据上下文。
- pyqtSignal back_requested：子页面只发信号；MainWindow connect 到 _go_home，负责切回栈首页。
- ChatWidget / SampleLibraryWidget：项目封装；分别负责对话与读 samples.json。

类型标注：`from __future__ import annotations` 与其它模块一致。
"""

# 推迟解析类型注解：这样类里写「QWidget | None」等无需在文件顶部先 import 那些类（Python 3.7+）。
from __future__ import annotations

# QtCore：与“画在屏幕上的控件”无关的核心机制——对象、信号槽、枚举常量（如 ItemDataRole）。
from PyQt6.QtCore import Qt, pyqtSignal
# QtWidgets：按钮、列表、布局等可视控件（PyQt6 里 GUI 类大多在此）。
from PyQt6.QtWidgets import (
    QHBoxLayout,  # 水平盒子布局：子控件从左到右排
    QLabel,  # 纯文本/简单富文本标签，常作标题或说明
    QListWidget,  # 带列表项的列表控件（比 QListView 更易上手）
    QListWidgetItem,  # 列表中的一行数据 + 显示
    QPushButton,  # 可点击按钮
    QTabWidget,  # 标签页容器
    QVBoxLayout,  # 垂直盒子布局：子控件从上到下排
    QWidget,  # 所有控件的基类之一；本页的 VersionPage 就是一个 QWidget 子类
)

from chat_widget import ChatWidget
from sample_library import SampleLibraryWidget


class VersionPage(QWidget):
    """
    单个题目版本下的整页 UI：上方返回钮 + 中间分左右栏。

    为什么是 QWidget 子类？
      主窗口需要“一整块可以塞进 QStackedWidget 的页面”。自定义页面就是做一个 QWidget，
      在里面用布局组合现有控件（按钮、列表、Tab）。

    生命周期（与 MainWindow 的配合）：
      用户第一次进入某版本时，MainWindow 会 `VersionPage(version_id)` 创建本实例并缓存；
      返回主页时通常只是隐藏本页、不销毁，所以 __init__ 只做一次，不要在页面里假设“每次显示都会重新构造”。
    """

    # ── 自定义信号（必须在类体里声明；不能写在 __init__ 里）──
    # pyqtSignal() 无参数：表示“发出时不附带数据”。若需要可写成 pyqtSignal(str)。
    # MainWindow：page.back_requested.connect(self._go_home)
    # 用户点返回 → clicked → 这里间接 emit back_requested → 主窗口收到后切页。
    back_requested = pyqtSignal()

    def __init__(self, version_id: str, parent: QWidget | None = None) -> None:
        # parent 传给 QWidget：若不为 None，本页析构随父级；也是 Qt 对象树的一环。
        super().__init__(parent)
        self._version_id = version_id

        # ---------- 顶部：返回主页 ----------
        back = QPushButton("← 返回主页")
        # clicked：bool 型信号（Qt6 里点击参数略有差异，这里不关心）
        # connect(self.back_requested.emit)：点击时直接调用信号的 emit，等价于发“返回”广播，不写 lambda。
        back.clicked.connect(self.back_requested.emit)

        # ---------- 左侧：任务列表 ----------
        self._task_list = QListWidget()
        # 每条 (tid, title)：title 展示给用户；tid 与数据文件里的任务键一致（如 user_data / coach_history）
        for tid, title in (
            ("task1", "示例任务（占位）"),
        ):
            # 列表项可以先用标题构造，再附加自定义数据
            item = QListWidgetItem(title)
            # UserRole：Qt 预留的“应用自定义数据”角色；同一条还可以用别的 Role 存图标等
            item.setData(Qt.ItemDataRole.UserRole, tid)
            self._task_list.addItem(item)

        # currentItemChanged(current, previous)：选中行变化即触发（鼠标、键盘都会）
        # 连接到自己的槽，里面根据 current 的 UserRole 更新右侧两个子控件
        self._task_list.currentItemChanged.connect(self._on_task_changed)

        # ---------- 右侧 Tab：AI 教练 + 样例库 ----------
        # version_id 决定读哪套 prompts / 哪份用户数据目录；初始任务 "task1" 与列表第一项一致
        self._chat = ChatWidget(version_id, "task1")
        self._samples = SampleLibraryWidget()
        self._samples.set_context(version_id, "task1")

        self._tabs = QTabWidget()
        # addTab：第一个参数是页面本体，第二个是标签文字；TabWidget 负责切换时显示哪一个子控件
        self._tabs.addTab(self._chat, "AI 教练")
        self._tabs.addTab(self._samples, "样例库")

        # ---------- 布局：嵌套思想 —— 先小组件，再拼成大布局 ----------
        # 左栏：标题 + 列表，纵向堆叠
        left = QVBoxLayout()
        left.addWidget(QLabel("任务清单"))
        left.addWidget(self._task_list)

        # 右栏：只有 Tab（Tab 里面已经包了 chat / samples）
        right = QVBoxLayout()
        right.addWidget(self._tabs)

        # 中间一行：左 : 右 = 1 : 3（数字是相对比例，不是像素）
        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 3)

        # QVBoxLayout(self)：把布局直接设到本 VersionPage 上（等价于 setLayout），self 就是这一页的根
        outer = QVBoxLayout(self)
        outer.addWidget(back)
        outer.addLayout(body)

        # 程序启动时列表可能尚无“当前项”；设第 0 行会触发 currentItemChanged，从而加载对应任务的聊天记录
        self._task_list.setCurrentRow(0)

    def _on_task_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        """
        槽函数：左侧任务切换时，同步右侧「当前任务」上下文。

        参数说明（Qt 约定）：
          current：当前选中项；可能为 None（例如列表被清空时）。
          previous：之前选中项；本页逻辑不需要，参数名前加 _ 表示有意忽略，避免 IDE 报未使用变量。

        数据流：
          从 item 取出 UserRole → 得到 task_id → 更新 Chat（换任务会 load_history）与 SampleLibrary 的过滤上下文。
        """
        # 无选中项时不更新（避免 startup 或清空列表时的无效状态）
        if current is None:
            return
        # data(role) 取 setData 时写入的值；类型可能是 QVariant 解包后的对象，这里要做运行时校验
        task_id = current.data(Qt.ItemDataRole.UserRole)
        if not isinstance(task_id, str):
            return
        # ChatWidget.set_task 内部会按新版本/任务路径 load_history；样例库按同一 task_id 过滤展示
        self._chat.set_task(task_id)
        self._samples.set_context(self._version_id, task_id)
