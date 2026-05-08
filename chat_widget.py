"""
AI 教练 Tab：只读历史区 + 多行输入框 + 发送；读写 user_data.json。

══════════════════════════════════════════════════════════════════════════════
 PyQt 初学者导读（与本控件相关的部分）
══════════════════════════════════════════════════════════════════════════════

【本控件在界面里的角色】
  ChatWidget 继承 QWidget，被放进 VersionPage 的 QTabWidget 里。它不操作主窗口，
  只负责：展示历史、收集输入、调用 ai_coach、把结果写回 data_manager。

【QTextEdit（历史区）】
  多行富文本只读区：setReadOnly(True)。setLineWrapMode(WidgetWidth) 按窗口宽度自动换行；
  对话以 HTML 表格 + 圆角气泡插入：用户消息靠右、助手靠左，窄列 Unicode 头像占位；正文经 html.escape 转义防注入。

【ComposerTextEdit（底部输入）】
  多行纯文本编辑：Enter 发送，Shift+Enter 换行；高度约为原先一半（min/max 减半），过长出现竖向滚动条。
  send_requested 信号与「发送」按钮均接入同一槽 _on_send。

【QPushButton + 信号】
  「发送」clicked → _on_send；「清空聊天记录」→ _on_clear_clicked（确认后调用 clear()）。

【QHBoxLayout / QVBoxLayout】
  历史区下方一排：左侧输入框拉伸，右侧竖排「清空聊天记录」+「发送」，顶对齐。

【QMessageBox】
  请求异常时用 warning；清空聊天记录前用 question 确认，避免误删本地持久化。

【与数据的边界】
  load_history / _on_send：读写在 data_manager；界面刷新用 append_message / clear。
  ai_coach.chat(...)：需要「旧历史」与「本轮用户句」分开传入，因此 hist[:-1] 见代码内注释。

类型标注：`from __future__ import annotations` 与其它模块一致。
"""

# 推迟解析类型注解，便于在类型里引用尚未定义的类名（与本项目其它文件一致）
from __future__ import annotations

from html import escape as html_escape
from typing import Any  # JSON 风格消息 dict 的值类型不定，hist 用 list[dict[str, Any]] 标注（见 _on_send）

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QPalette, QTextCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import ai_coach
import data_manager


class ComposerTextEdit(QTextEdit):
    """多行输入：Enter 发送，Shift+Enter 换行。"""

    send_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptRichText(False)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setMinimumHeight(44)
        self.setMaximumHeight(100)
        self.setPlaceholderText("Enter 发送 · Shift+Enter 换行。可粘贴代码片段或描述问题…")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.send_requested.emit()
                event.accept()
                return
        super().keyPressEvent(event)


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

    def __init__(self, version_id: str, task_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = version_id
        self._task_id = task_id

        # ---------- 上方：对话记录 ----------
        self._history_view = QTextEdit()
        self._history_view.setReadOnly(True)
        self._history_view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self._history_view.setAutoFillBackground(True)
        _hp = self._history_view.palette()
        _hp.setColor(QPalette.ColorRole.Base, self.palette().color(QPalette.ColorRole.Window))
        _hp.setColor(QPalette.ColorRole.Text, self.palette().color(QPalette.ColorRole.WindowText))
        self._history_view.setPalette(_hp)

        # ---------- 下方：输入 + 发送 ----------
        self._input = ComposerTextEdit()
        self._input.send_requested.connect(self._on_send)

        clear_btn = QPushButton("清空聊天记录")
        clear_btn.clicked.connect(self._on_clear_clicked)
        send = QPushButton("发送")
        send.clicked.connect(self._on_send)

        actions_col = QWidget()
        actions_layout = QVBoxLayout(actions_col)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        actions_layout.addWidget(clear_btn)
        actions_layout.addWidget(send)
        actions_layout.addStretch(1)

        row = QHBoxLayout()
        row.addWidget(self._input, stretch=1)
        row.addWidget(actions_col, stretch=0, alignment=Qt.AlignmentFlag.AlignTop)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"AI 教练 · {version_id} / {task_id}"))
        layout.addWidget(self._history_view)
        layout.addLayout(row)

        self.load_history()

    def set_task(self, task_id: str) -> None:
        """
        左侧任务列表切换时由 VersionPage 调用。

        更新内存中的 task_id 后立刻 load_history，使右侧文本与磁盘里该任务的记录一致。
        """
        self._task_id = task_id
        self.load_history()

    def load_history(self) -> None:
        """
        根据 self._version_id + self._task_id 从 user_data.json 读出 coach_history，刷新文本框。

        ensure_task_slot：
          若 JSON 里缺少对应版本/任务的嵌套字典，会在传入的 data 上就地创建键。
          此处「只读展示」仍会触发补键，但若最后没有 save_user_data，这些补键仅存在于本次内存里的 data，
          不会写盘——除非后续某操作 save 了同一份 data。
        """
        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        hist = slot.get("coach_history") or []
        self._history_view.clear()
        for m in hist:
            role = m.get("role", "")
            content = m.get("content", "")
            self._insert_history_html(role, content)
        self._scroll_history_to_bottom()

    def clear(self) -> None:
        """
        清空当前版本+任务在磁盘中的 coach_history，并清空界面。

        若仅需清屏不关磁盘，应另写方法或手动操作数据结构；当前 API 是「彻底清空持久化」。
        """
        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        slot["coach_history"] = []
        data_manager.save_user_data(data)
        self._history_view.clear()

    def _on_clear_clicked(self) -> None:
        ok = QMessageBox.question(
            self,
            "清空聊天记录",
            "确定清空当前版本与任务下的教练对话吗？将同步删除本地 data/user_data.json 中对应 coach_history，且不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if ok == QMessageBox.StandardButton.Yes:
            self.clear()

    def append_message(self, role: str, content: str) -> None:
        """在 QTextEdit 末尾追加气泡展示；不负责写入 JSON。"""
        self._insert_history_html(role, content)
        self._scroll_history_to_bottom()

    @staticmethod
    def _role_caption(role: str) -> str:
        return {"user": "用户", "assistant": "助手"}.get(role, role or "?")

    @staticmethod
    def _chat_bubble_inner(caption: str, body: str, bg: str, caption_color: str) -> str:
        """单条气泡内部 HTML（圆角块 + 小标题 + 正文）。"""
        return (
            f'<div style="padding:10px 14px;border-radius:14px;background:{bg};">'
            f'<div style="font-size:11px;color:{caption_color};margin-bottom:6px;">{caption}</div>'
            f'<div style="white-space:pre-wrap;font-family:inherit;color:#ececec;line-height:1.45;">{body}</div>'
            "</div>"
        )

    def _insert_history_html(self, role: str, content: str) -> None:
        caption = html_escape(self._role_caption(role))
        body = html_escape(content or "")
        if role == "user":
            bg, cap_col = "#1e4d6e", "#8ecae6"
            bubble = self._chat_bubble_inner(caption, body, bg, cap_col)
            block = (
                '<table width="100%" cellspacing="0" cellpadding="4" '
                'style="margin:10px 0;border-collapse:collapse;">'
                "<tr>"
                '<td align="right" valign="top">'
                '<div style="display:inline-block;max-width:82%;text-align:left;">'
                f"{bubble}</div></td>"
                '<td width="40" valign="top" align="center" '
                'style="font-size:17px;line-height:1.2;">👤</td>'
                "</tr></table>"
            )
        else:
            bg, cap_col = "#3d4450", "#c5cdd8"
            bubble = self._chat_bubble_inner(caption, body, bg, cap_col)
            block = (
                '<table width="100%" cellspacing="0" cellpadding="4" '
                'style="margin:10px 0;border-collapse:collapse;">'
                "<tr>"
                '<td width="40" valign="top" align="center" '
                'style="font-size:17px;line-height:1.2;">🤖</td>'
                '<td valign="top">'
                '<div style="display:inline-block;max-width:82%;text-align:left;">'
                f"{bubble}</div></td>"
                "</tr></table>"
            )
        cursor = self._history_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(block)
        # 连续 insertHtml 时 Qt 可能把相邻气泡接到同一行，插入新段落保证每条消息后换行
        cursor.insertBlock()

    def _scroll_history_to_bottom(self) -> None:
        bar = self._history_view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_send(self) -> None:
        """
        发送一轮对话：校验输入 → 持久化用户句 → 调 AI → 持久化助手句。

        顺序要点：
          先把用户消息追加到界面与列表 hist，再调用 ai_coach.chat(..., hist[:-1], text)，
          这样 API 收到的是「之前的消息」加单独的本轮用户句，而不是重复包含本轮 user 的列表。
        """
        text = self._input.toPlainText().strip()
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
