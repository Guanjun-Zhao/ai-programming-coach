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

import time

from PyQt6.QtCore import QEventLoop, QThread, QTimer, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# 同项目：某一魔兽版本的完整页面（左任务树 + 右 Tab）
from version_page import VersionPage

import ai_coach
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

MODEL_OPTIONS = (
    ("deepseek-v4-flash", "DeepSeek V4 Flash"),
    ("deepseek-v4-pro", "DeepSeek V4 Pro"),
    ("deepseek-chat", "deepseek-chat（兼容）"),
)

API_PING_UI_SECONDS = int(ai_coach.API_PING_TIMEOUT_SECONDS)


class ApiPingThread(QThread):
    """后台调用 ai_coach.ping_api，避免阻塞 UI。"""

    finished_with_result = pyqtSignal(object)

    def run(self) -> None:
        self.finished_with_result.emit(ai_coach.ping_api())


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
        self.setWindowTitle("AI 编程教练")
        self.resize(1200, 720)

        # ────────── 栈容器：所有「整页」界面都放在这里面 ──────────
        self._stack = QStackedWidget()

        # ────────── 第 0 页：主页（选版本）──────────
        home = QWidget()  # 无独立窗口边框，仅作为一页内容的根控件
        home_layout = QVBoxLayout(home)  # 把垂直布局绑定到 home：子控件自上而下排列

        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("模型 / API Key"))
        self._model_combo = QComboBox()
        for model_id, label in MODEL_OPTIONS:
            self._model_combo.addItem(label, model_id)
        api_row.addWidget(self._model_combo)
        api_key_wrap = QWidget()
        api_key_wrap_layout = QHBoxLayout(api_key_wrap)
        api_key_wrap_layout.setContentsMargins(0, 0, 0, 0)
        api_key_wrap_layout.setSpacing(4)
        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._api_key_input.setPlaceholderText(
            "未填写时使用环境变量 DEEPSEEK_API_KEY；均未配置则返回占位回复"
        )
        api_key_wrap_layout.addWidget(self._api_key_input, stretch=1)
        self._api_key_visibility_btn = QToolButton()
        self._api_key_visibility_btn.setText("👁")
        self._api_key_visibility_btn.setCheckable(True)
        self._api_key_visibility_btn.setToolTip("显示 / 隐藏 API Key")
        self._api_key_visibility_btn.toggled.connect(self._on_api_key_visibility_toggled)
        api_key_wrap_layout.addWidget(self._api_key_visibility_btn, stretch=0)
        api_row.addWidget(api_key_wrap, stretch=1)
        save_api_btn = QPushButton("保存")
        save_api_btn.clicked.connect(self._save_api_settings)
        api_row.addWidget(save_api_btn)
        self._save_api_btn = save_api_btn
        home_layout.addLayout(api_row)

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
        self._api_verified_ok = False

        # 把整个栈交给主窗口中央区域；此后可见内容完全由 _stack 当前页决定
        self.setCentralWidget(self._stack)
        self._apply_api_settings_from_disk()
        self._refresh_version_buttons_enabled()
        QTimer.singleShot(0, self._startup_api_verify_if_needed)

    def _model_id_from_combo(self) -> str:
        model_id = self._model_combo.currentData()
        if isinstance(model_id, str) and model_id.strip():
            return model_id.strip()
        return data_manager.DEFAULT_APP_MODEL

    def _set_model_combo(self, model_id: str) -> None:
        target = model_id.strip() or data_manager.DEFAULT_APP_MODEL
        for index in range(self._model_combo.count()):
            if self._model_combo.itemData(index) == target:
                self._model_combo.setCurrentIndex(index)
                return
        self._model_combo.setCurrentIndex(0)

    def _on_api_key_visibility_toggled(self, visible: bool) -> None:
        self._api_key_input.setEchoMode(
            QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        )

    def _apply_api_settings_from_disk(self) -> None:
        settings = data_manager.load_app_settings()
        self._set_model_combo(settings["model"])
        self._api_key_input.setText(settings["api_key"])
        if self._api_key_visibility_btn.isChecked():
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        ai_coach.set_runtime_config(settings["api_key"], settings["model"])

    def _set_home_api_controls_enabled(self, enabled: bool) -> None:
        self._model_combo.setEnabled(enabled)
        self._api_key_input.setEnabled(enabled)
        self._api_key_visibility_btn.setEnabled(enabled)
        self._save_api_btn.setEnabled(enabled)

    def _refresh_version_buttons_enabled(self) -> None:
        """有 Key 且已通过 ping 才可进版本；无 Key 时按钮可点，由 _open_version 提示填写。"""
        can_enter = (not ai_coach.has_api_key()) or self._api_verified_ok
        for _vid, btn in self._home_version_buttons:
            btn.setEnabled(can_enter)
        self._refresh_home_progress_labels()

    def _run_api_ping_modal(self) -> bool:
        """模态进度与倒计时；成功返回 True。无取消按钮，依赖客户端超时结束。"""
        dlg = QProgressDialog(self)
        dlg.setWindowTitle("验证 API")
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlg.setMinimumDuration(0)
        dlg.setRange(0, 0)
        dlg.setCancelButton(None)
        dlg.show()

        self._set_home_api_controls_enabled(False)

        t0 = time.monotonic()
        err_out: list[str | None] = [None]
        loop = QEventLoop()

        th = ApiPingThread(self)

        def on_result(res: object) -> None:
            err_out[0] = res if isinstance(res, str) else None
            loop.quit()

        th.finished_with_result.connect(on_result)

        timer = QTimer(self)

        def tick() -> None:
            elapsed = time.monotonic() - t0
            rem = max(0, API_PING_UI_SECONDS - int(elapsed))
            dlg.setLabelText(
                "正在连接 DeepSeek 并校验 API…\n"
                f"已用约 {elapsed:.0f} 秒；预计还需约 {rem} 秒"
                f"（单次上限 {API_PING_UI_SECONDS} 秒，为保守估计）。"
            )

        timer.timeout.connect(tick)
        tick()
        timer.start(200)
        th.start()
        loop.exec()
        timer.stop()
        th.wait()
        dlg.close()
        self._set_home_api_controls_enabled(True)

        err = err_out[0]
        if err is not None:
            QMessageBox.warning(self, "API 验证失败", err)
            return False
        return True

    def _startup_api_verify_if_needed(self) -> None:
        if not ai_coach.has_api_key():
            self._api_verified_ok = False
            self._refresh_version_buttons_enabled()
            return
        ok = self._run_api_ping_modal()
        self._api_verified_ok = ok
        self._refresh_version_buttons_enabled()
        if not ok:
            QMessageBox.information(
                self,
                "API 未就绪",
                "已保存的 API Key 未能通过连接验证，暂不能进入版本页。\n"
                "请检查网络与 Key 后点击「保存」重试。",
            )

    def _save_api_settings(self) -> None:
        model = self._model_id_from_combo()
        api_key = self._api_key_input.text().strip()
        data_manager.save_app_settings({"api_key": api_key, "model": model})
        ai_coach.set_runtime_config(api_key, model)
        self._api_verified_ok = False
        self._refresh_version_buttons_enabled()

        if ai_coach.has_api_key():
            ok = self._run_api_ping_modal()
            self._api_verified_ok = ok
            self._refresh_version_buttons_enabled()
            if ok:
                QMessageBox.information(
                    self,
                    "已保存",
                    "API 配置已保存到本机，连接验证通过。",
                )
            else:
                QMessageBox.warning(
                    self,
                    "已保存",
                    "配置已写入本机，但连接验证未通过，暂不能进入版本页。\n"
                    "请检查网络与 Key 后再次点击「保存」。",
                )
        else:
            QMessageBox.information(
                self,
                "已保存",
                "API 配置已保存到本机。（当前无可用 Key：进入版本页时会提示填写。）",
            )

    def _refresh_home_progress_labels(self) -> None:
        """主页按钮展示「已勾选 / 左侧全部复选框」计数（见 sections_loader）。"""
        for vid, btn in self._home_version_buttons:
            label = next(l for v, l in VERSION_ENTRIES if v == vid)
            state = data_manager.load_version_state(vid)
            den = sections_loader.progress_denominator(vid)
            num = sections_loader.progress_numerator(state, vid)
            btn.setText(f"{label}  [{num}/{den}]")

    def _open_version(self, version_id: str) -> None:
        """响应主页按钮：切换到对应版本的 VersionPage（必要时先创建）。"""
        self._apply_api_settings_from_disk()
        if not ai_coach.has_api_key():
            QMessageBox.information(
                self,
                "需要 API Key",
                "请先在主页顶部填写 API Key，并点击「保存」完成验证后再进入版本。",
            )
            return
        if not self._api_verified_ok:
            QMessageBox.information(
                self,
                "请完成验证",
                "请先点击「保存」并等待 API 连接验证通过后再进入版本。\n"
                "若刚启动应用，请等待自动验证结束或重新保存一次。",
            )
            return
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
        self._version_pages[version_id].refresh_bootstrap()

    def _go_home(self) -> None:
        """
        槽函数：由 VersionPage 的 back_requested 触发，回到主页。

        setCurrentIndex(0) 依赖 __init__ 中「第一个 addWidget 是 home」的约定；
        若将来调整 addWidget 顺序，必须同步修改这里的索引或改用按对象切换。
        """
        self._stack.setCurrentIndex(0)
        self._refresh_home_progress_labels()
