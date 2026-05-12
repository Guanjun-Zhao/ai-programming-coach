"""
AI 教练 Tab：只读历史区 + 多行输入框 + 发送；读写 data/versionN/history/*.json。
"""

# 推迟解析类型注解，便于在类型里引用尚未定义的类名（与本项目其它文件一致）
from __future__ import annotations

from collections.abc import Callable

from html import escape as html_escape
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QPalette, QTextCursor
from PyQt6.QtWidgets import (  # 本文件用到的界面类
    QHBoxLayout,  # 水平布局
    QLabel,  # 静态文字
    QMessageBox,  # 模态消息框
    QPushButton,  # 可点击按钮
    QTextEdit,  # 多行富文本编辑/只读
    QVBoxLayout,  # 垂直布局
    QWidget,  # 所有控件的基类
)

import ai_coach  # 调用大模型/占位回复
import data_manager
import sections_loader


class ComposerTextEdit(QTextEdit):
    """多行输入：Enter 发送，Shift+Enter 换行。"""

    send_requested = pyqtSignal()  # 无参信号：用户按 Enter 要求发送

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)  # 构造基类，挂到父控件对象树
        self.setAcceptRichText(False)  # 只收纯文本，避免粘贴进 HTML 隐患
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # 按控件宽度自动换行
        self.setMinimumHeight(44)  # 输入区最小高度（约原设计一半）
        self.setMaximumHeight(100)  # 输入区最大高度，超出出竖向滚动条
        self.setPlaceholderText("Enter 发送 · Shift+Enter 换行。可粘贴代码片段或描述问题…")  # 空时灰色提示

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):  # 主键盘或数字区回车
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:  # 按住 Shift
                super().keyPressEvent(event)  # 默认行为：插入换行
            else:  # 未按 Shift 的单独回车
                self.send_requested.emit()  # 通知外层执行发送
                event.accept()  # 事件已处理，不再向下传
                return  # 不调用 super，避免再插入换行
        super().keyPressEvent(event)  # 其它键走默认（字符、退格等）


class ChatWidget(QWidget):
    """
    当前版本（version_id）与任务（task_id）下的教练对话区。

    典型用法（见 VersionPage）：
      - 构造时传入初始 task_id，并 load_history()；
      - 左侧列表切换任务时调用 set_task(new_id)，内部会更新 self._task_id 并重新 load_history。

    线程说明：
      _on_send 里直接调用 ai_coach.chat（同步）。若接口很慢，界面会短暂卡住；
      以后要优化可改为线程/QTimer/worker，但那是架构升级，本文件保持简单直观。
    """

    def __init__(
        self,
        version_id: str,
        task_id: str,
        program_loader: Callable[[], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._version_id = version_id
        self._task_id = task_id
        self._program_loader = program_loader or (
            lambda: data_manager.load_version_code(version_id)
        )

        # ---------- 上方：对话记录 ----------
        self._history_view = QTextEdit()  # 只读区，展示历史气泡
        self._history_view.setReadOnly(True)  # 禁止用户直接改历史文本
        self._history_view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)  # 历史按宽度换行
        self._history_view.setAutoFillBackground(True)  # 用调色板铺背景，避免露底
        _hp = self._history_view.palette()  # 取历史区当前调色板副本
        _hp.setColor(QPalette.ColorRole.Base, self.palette().color(QPalette.ColorRole.Window))  # 背景与窗口色一致
        _hp.setColor(QPalette.ColorRole.Text, self.palette().color(QPalette.ColorRole.WindowText))  # 前景与窗口文字色一致
        self._history_view.setPalette(_hp)  # 应用调色板，深色主题下不刺眼

        # ---------- 下方：输入 + 发送 ----------
        self._input = ComposerTextEdit()  # 多行输入框
        self._input.send_requested.connect(self._on_send)  # Enter 发送与按钮共用槽

        clear_btn = QPushButton("清空聊天记录")  # 清当前任务持久化与界面
        clear_btn.clicked.connect(self._on_clear_clicked)  # 先确认再清
        send = QPushButton("发送")  # 显式发送
        send.clicked.connect(self._on_send)  # 与 Enter 行为一致

        actions_col = QWidget()  # 承载右侧竖排按钮的容器
        actions_layout = QVBoxLayout(actions_col)  # 上下叠放清空与发送
        actions_layout.setContentsMargins(0, 0, 0, 0)  # 与输入行贴齐，不额外留边
        actions_layout.setSpacing(6)  # 两钮间距 6 像素
        actions_layout.addWidget(clear_btn)  # 上：清空
        actions_layout.addWidget(send)  # 下：发送
        actions_layout.addStretch(1)  # 下方弹性空白，两钮顶对齐

        row = QHBoxLayout()  # 底行：输入 + 右侧操作列
        row.addWidget(self._input, stretch=1)  # 输入区占满剩余宽
        row.addWidget(actions_col, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)  # 右侧列不拉伸、顶对齐

        layout = QVBoxLayout(self)  # 本控件根布局
        self._ctx_label = QLabel("")  # 版本 / 任务 / 小节标题
        layout.addWidget(self._ctx_label)  # 标题行
        layout.addWidget(self._history_view)  # 中间：历史
        layout.addLayout(row)  # 底：输入行

        self._update_ctx_label()
        self.load_history()
        self._bootstrap_if_needed()

    def _debug_task_id(self) -> str | None:
        spec = sections_loader.get_version_spec(self._version_id)
        tid = spec.get("debug_task_id")
        return str(tid) if tid else None

    def _is_debug_task(self) -> bool:
        dt = self._debug_task_id()
        return bool(dt and self._task_id == dt)

    def _bootstrap_if_needed(self) -> None:
        if self._is_debug_task():
            self._bootstrap_debug_if_needed()
        else:
            self._bootstrap_planning_if_needed()

    def _update_ctx_label(self) -> None:
        sec = sections_loader.get_leaf_section(self._version_id, self._task_id)
        title = sec.get("title") if sec else None
        suffix = f" · {title}" if title else ""
        self._ctx_label.setText(f"AI 教练 · {self._version_id} / {self._task_id}{suffix}")

    def _bootstrap_planning_if_needed(self) -> None:
        sec = sections_loader.get_leaf_section(self._version_id, self._task_id)
        if not sec or sec.get("role") != "planning":
            return
        hist = data_manager.load_task_history(self._version_id, self._task_id)
        if hist:
            return
        trigger = "请开始本节导读讲解。"
        reply = ai_coach.chat(self._version_id, self._task_id, [], trigger)
        data_manager.save_task_history(
            self._version_id,
            self._task_id,
            [
                {"role": "user", "content": trigger},
                {"role": "assistant", "content": reply},
            ],
        )
        self.load_history()

    def _bootstrap_debug_if_needed(self) -> None:
        hist = data_manager.load_task_history(self._version_id, self._task_id)
        if hist:
            return
        samples = data_manager.load_version_samples(self._version_id)
        if not samples:
            intro = "（暂无样例，请在 data/versionN/samples.json 中配置。）"
            data_manager.save_task_history(
                self._version_id,
                self._task_id,
                [{"role": "assistant", "content": intro}],
            )
            self.load_history()
            return
        state = data_manager.load_version_state(self._version_id)
        data_manager.ensure_task_state(state, self._task_id)
        state[self._task_id]["current_sample_index"] = 0
        data_manager.save_version_state(self._version_id, state)
        lines = ["所有编码节已完成，现在开始调试。"]
        if not sections_loader.all_coding_leaves_completed(
            state, self._version_id
        ):
            lines.append("提示：建议先完成左侧各编码小节的勾选后再系统调试。")
        lines.append(
            "请在本地用中列完整程序运行，并将**完整**程序输出粘贴回对话框。"
        )
        lines.append(f"这是第 1 条样例输入：\n{samples[0].get('input', '')}")
        intro = "\n".join(lines)
        data_manager.save_task_history(
            self._version_id,
            self._task_id,
            [{"role": "assistant", "content": intro}],
        )
        self.load_history()

    def set_task(self, task_id: str) -> None:
        """
        左侧任务列表切换时由 VersionPage 调用。
        更新内存中的 task_id 后立刻 load_history，使右侧文本与磁盘里该任务的记录一致。
        """
        self._task_id = task_id  # 更新当前任务
        self._update_ctx_label()
        self.load_history()
        self._bootstrap_if_needed()

    def load_history(self) -> None:
        hist = data_manager.load_task_history(self._version_id, self._task_id)
        self._history_view.clear()
        for m in hist:
            role = m.get("role", "")
            content = m.get("content", "")
            self._insert_history_html(role, content)
        self._scroll_history_to_bottom()

    def clear(self) -> None:
        data_manager.clear_task_history(self._version_id, self._task_id)
        if self._is_debug_task():
            state = data_manager.load_version_state(self._version_id)
            slot = data_manager.ensure_task_state(state, self._task_id)
            slot["current_sample_index"] = 0
            data_manager.save_version_state(self._version_id, state)
        self._history_view.clear()
        self._bootstrap_if_needed()

    def _on_clear_clicked(self) -> None:
        ok = QMessageBox.question(
            self,
            "清空聊天记录",
            "确定清空当前版本与任务下的教练对话吗？将同步删除本地 history 中对应记录，且不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ok == QMessageBox.StandardButton.Yes:  # 用户确认
            self.clear()  # 执行持久化清空

    def append_message(self, role: str, content: str) -> None:
        """在 QTextEdit 末尾追加气泡展示；不负责写入 JSON。"""
        self._insert_history_html(role, content)  # 插入对应角色的气泡
        self._scroll_history_to_bottom()  # 新消息始终可见

    @staticmethod
    def _role_caption(role: str) -> str:
        return {"user": "用户", "assistant": "助手"}.get(role, role or "?")  # 界面展示用中文角色名

    @staticmethod
    def _chat_bubble_inner(caption: str, body: str, bg: str, caption_color: str) -> str:
        """单条气泡内部 HTML（圆角块 + 小标题 + 正文）。"""
        # 圆括号里多段引号字面值上下相邻时，Python 会拼成**一个**长字符串，中间可插 # 注释行。
        # 下面按「开标签 / 小标题 / 正文 / 闭标签」四段写，每段上一行用 # 解释 HTML 与 style 里各关键词。
        return (
            # <div>：块级容器（division）。style="…"：内联 CSS，属性间用分号；双引号包住整段样式字串。
            # padding:10px 14px：内边距；两值时=上下 10px、左右 14px，字不贴边。
            # border-radius:14px：圆角，px=像素，数值越大角越圆。
            # background:{bg}：背景色；{bg} 为 f-string 把参数 bg 填进 HTML，一般是 # 开头的十六进制颜色。
            f'<div style="padding:10px 14px;border-radius:14px;background:{bg};">'
            # 仍是一个 <div>。font-size:11px：字高 11 像素。color:{caption_color}：字色，来自参数插值。
            # margin-bottom:6px：本块下缘与下一块（正文）之间再空 6px。{caption} 为已转义的小标题文本。末尾 </div> 结束本层。
            f'<div style="font-size:11px;color:{caption_color};margin-bottom:6px;">{caption}</div>'
            # white-space:pre-wrap：保留用户输入里的换行与缩进，同时仍按窗口宽度自动折行（与 pre 纯预格式化不同）。
            # font-family:inherit：字体继承父级，与界面其它字一致。color:#ececec：写死为浅灰字色。
            # line-height:1.45：行高为字高的 1.45 倍，多行时更易读。{body} 为已转义的正文。末尾 </div> 结束正文层。
            f'<div style="white-space:pre-wrap;font-family:inherit;color:#ececec;line-height:1.45;">{body}</div>'
            # "</div>"：非 f-string；只闭合最外层 <div>，与第一段开标签配对；不加 f 是因为这里没有 {变量}。
            "</div>"
        )

    def _insert_history_html(self, role: str, content: str) -> None:
        caption = html_escape(self._role_caption(role))  # 标题防 XSS
        body = html_escape(content or "")  # 正文防 XSS

        if role == "user":  # 用户消息：右对齐气泡
            bg, cap_col = "#1e4d6e", "#8ecae6"  # 深蓝气泡 + 浅青标题色
            bubble = self._chat_bubble_inner(caption, body, bg, cap_col)  # 内层 HTML
            # 下列相邻字符串会拼成一段 HTML；# 行解释标签名与属性（名=值，布尔属性可单独出现）。
            block = (
                # <table>：表格根；width="100%" 相对上层容器占满宽（百分比）。
                # cellspacing="0"：相邻单元格间隙为 0（否则默认有缝）。
                # cellpadding="4"：格子内线与内容的内边距各约 4px。
                '<table width="100%" cellspacing="0" cellpadding="4" '
                # style：margin:10px 0 = 表格外上下外边距 10px、左右 0；border-collapse:collapse 合并格子边框避免双线。
                'style="margin:10px 0;border-collapse:collapse;">'
                # <tr>：table row，一行；本行含两个 <td> = 两列（左气泡列 | 右头像列）。
                "<tr>"
                # <td>：table data，一格；align="right" 格内水平靠右（气泡贴右侧）；valign="top" 垂直顶端对齐。
                '<td align="right" valign="top">'
                # <div style="…">：display:inline-block 使盒子宽度随内容；max-width:82% 限制不超过父宽约 82%；
                # text-align:left 气泡内文字仍从左读（只是整块气泡在右）。
                '<div style="display:inline-block;max-width:82%;text-align:left;">'
                # f"{bubble}"：插入 _chat_bubble_inner；</div> 结束 div；</td> 结束左列。
                f"{bubble}</div></td>"
                # 第二列：width="40" 固定列宽约 40px；valign="top"；align="center" 水平居中放 emoji。
                # font-size:17px 控制符号大小；line-height:1.2 行高相对字号；👤 为用户头像占位（Unicode）。
                '<td width="40" valign="top" align="center" '
                'style="font-size:17px;line-height:1.2;">👤</td>'
                # </tr> 结束行；</table> 结束表。
                "</tr></table>"
            )
        else:  # 助手或其它角色：左对齐气泡
            bg, cap_col = "#3d4450", "#c5cdd8"  # 灰气泡 + 浅灰标题
            bubble = self._chat_bubble_inner(caption, body, bg, cap_col)
            # 与用户分支同一套 <table>/<tr>，仅两列顺序对调：先窄头像列，再气泡列（常见「对方消息在左」）。
            block = (
                # 表格外壳与用户侧相同：拉满宽、格子间距、合并边框、上下外边距。
                '<table width="100%" cellspacing="0" cellpadding="4" '
                'style="margin:10px 0;border-collapse:collapse;">'
                "<tr>"
                # 第一列：窄列放助手头像；width="40"、居中、顶对齐；emoji 🤖 占位。
                '<td width="40" valign="top" align="center" '
                'style="font-size:17px;line-height:1.2;">🤖</td>'
                # 第二列：仅 valign="top"（文本默认左对齐），内层 div 同样限制 max-width:82%。
                '<td valign="top">'
                '<div style="display:inline-block;max-width:82%;text-align:left;">'
                f"{bubble}</div></td>"
                "</tr></table>"
            )

        cursor = self._history_view.textCursor()  # 取文档光标
        cursor.movePosition(QTextCursor.MoveOperation.End)  # 移到文末再插
        cursor.insertHtml(block)  # 插入富文本片段
        # 连续 insertHtml 时 Qt 可能把相邻气泡接到同一行，插入新段落保证每条消息后换行
        cursor.insertBlock()  # 新段落，分隔两条消息

    def _scroll_history_to_bottom(self) -> None:
        bar = self._history_view.verticalScrollBar()  # 历史区竖直滚动条
        bar.setValue(bar.maximum())  # 滚到最底

    def _on_send(self) -> None:
        text = self._input.toPlainText().strip()
        if not text:
            return
        self._input.clear()
        if self._is_debug_task():
            self._on_send_debug(text)
            return
        hist = data_manager.load_task_history(self._version_id, self._task_id)
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
        data_manager.save_task_history(self._version_id, self._task_id, hist)

    def _on_send_debug(self, text: str) -> None:
        samples = data_manager.load_version_samples(self._version_id)
        state = data_manager.load_version_state(self._version_id)
        slot = data_manager.ensure_task_state(state, self._task_id)
        index = int(slot.get("current_sample_index", 0))
        hist = data_manager.load_task_history(self._version_id, self._task_id)
        self.append_message("user", text)
        hist.append({"role": "user", "content": text})
        if index >= len(samples):
            reply = "所有样例已测试完成。若尚未勾选左侧 Debug，请手动勾选。"
            self.append_message("assistant", reply)
            hist.append({"role": "assistant", "content": reply})
            data_manager.save_task_history(self._version_id, self._task_id, hist)
            return
        sample = samples[index]
        expected = data_manager.normalize_program_output(
            str(sample.get("output", ""))
        )
        actual = data_manager.normalize_program_output(text)
        if actual == expected:
            n = index + 1
            reply = f"样例 {n} 通过。"
            slot["current_sample_index"] = index + 1
            data_manager.save_version_state(self._version_id, state)
            if index + 1 < len(samples):
                nxt = index + 2
                reply += f"\n下面是第 {nxt} 条样例输入：\n{samples[index + 1].get('input', '')}"
            else:
                reply += (
                    "\n所有样例已通过。请在左侧手动勾选 Debug 复选框标记完成。"
                )
        else:
            program = self._program_loader()
            reply = ai_coach.analyze_debug_mismatch(
                self._version_id, sample, text, program
            )
        self.append_message("assistant", reply)
        hist.append({"role": "assistant", "content": reply})
        data_manager.save_task_history(self._version_id, self._task_id, hist)
