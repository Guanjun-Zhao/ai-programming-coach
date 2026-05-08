"""
AI 教练 Tab：只读历史区 + 输入框 + 发送；读写 user_data.json。

初学者可以这样理解：
1. QTextEdit 显示多轮对话；setReadOnly(True) 禁止用户直接改历史。
2. 发送流程：读磁盘 → 追加用户消息 → 调 ai_coach.chat → 追加助手消息 → 写回磁盘。
3. chat(..., hist[:-1], text)：API 要「过去历史」和「本轮用户句」分开传，hist[:-1] 去掉刚追加的那条 user。

类型标注：见各文件统一的 `from __future__ import annotations` 说明。
"""

# 让当前文件里可以用「list[str]」这种写法标注类型（Python 3.9+ 也可不用这行；写上兼容旧习惯）
from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import ai_coach
import data_manager


class ChatWidget(QWidget):
    """
    当前版本 / 任务下的教练对话。
    切换任务时可调用 set_task(task_id) 再 load_history()。
    """

    def __init__(self, version_id: str, task_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = version_id
        self._task_id = task_id

        # 上方：对话记录（只读，防止误编辑）
        self._history_view = QTextEdit()
        self._history_view.setReadOnly(True)
        # 单行输入框：适合一行提问；多行可日后换成 QTextEdit
        self._input = QLineEdit()
        self._input.setPlaceholderText("粘贴代码片段或描述你的问题…")
        send = QPushButton("发送")
        send.clicked.connect(self._on_send)
        # 回车键也触发发送（和按钮同一槽函数）
        self._input.returnPressed.connect(self._on_send)

        row = QHBoxLayout()
        row.addWidget(self._input)
        row.addWidget(send)

        # QVBoxLayout(self)：把垂直布局挂到本控件上，由 Qt 管理子控件几何
        layout = QVBoxLayout(self)
        # 骨架占位：标题只在构造时写入 version_id/task_id；set_task 换任务后不会自动改这行文字（若需要可在 set_task 里同步 QLabel）
        layout.addWidget(QLabel(f"AI 教练 · {version_id} / {task_id}"))
        layout.addWidget(self._history_view)
        layout.addLayout(row)

        # 启动时从磁盘恢复该任务的聊天记录到界面
        self.load_history()

    def set_task(self, task_id: str) -> None:
        """左侧列表换了任务：更新内存里的 task_id（标题栏若要同步可在此扩展）。"""
        self._task_id = task_id
        self.load_history()

    def load_history(self) -> None:
        """
        根据 version_id + task_id 从 JSON 读出 coach_history，刷新文本框。

        只读路径：不把数据写回磁盘。ensure_task_slot 会在传入的 data 字典上就地补键，
        若随后没有 save_user_data，这些补键只存在于本次 load_history 里的局部变量 data 中。
        """
        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        # or []：键不存在或值为 None 时当作空列表
        hist = slot.get("coach_history") or []
        self._history_view.clear()
        for m in hist:
            role = m.get("role", "")
            content = m.get("content", "")
            # append 在 QTextEdit 末尾追加一段（自动换行）
            self._history_view.append(f"[{role}]\n{content}\n")

    def clear(self) -> None:
        """清空界面与持久化中当前任务的教练记录（可选调用）。"""
        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        slot["coach_history"] = []
        data_manager.save_user_data(data)
        self._history_view.clear()

    def append_message(self, role: str, content: str) -> None:
        """往界面追加一条消息（不负责写盘）。"""
        self._history_view.append(f"[{role}]\n{content}\n")

    def _on_send(self) -> None:
        """点击发送或按回车：完成一轮对话并持久化。"""
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()

        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        # 复制一份历史列表，后面会在内存里追加两条再写回
        hist: list[dict[str, Any]] = list(slot.get("coach_history") or [])

        # 先更新界面与内存中的用户消息
        self.append_message("user", text)
        hist.append({"role": "user", "content": text})

        try:
            # ai_coach.chat 期望：messages = 本轮发送「之前」的历史（不含本轮 user），
            # 本轮用户句单独放在 user_message 参数里。
            # 例：旧历史已有 2 条消息，append 用户后 hist 长度为 3，则 hist[:-1] 为前 2 条，与 API 约定一致。
            # 注意：ai_coach.chat 内部已对网络/API 异常做了捕获并返回 "[API 错误] ..." 字符串，一般不会向外抛；
            # 下面 except 主要防备极少数未预料异常（若走到 except，仍会写入一条 assistant 回复便于留痕）。
            reply = ai_coach.chat(
                self._version_id,
                self._task_id,
                hist[:-1],
                text,
            )
        except Exception as exc:
            reply = f"[错误] {exc}"
            # 弹出警告框；多数 API 问题已在 ai_coach 内转成字符串，不一定走到这里
            QMessageBox.warning(self, "教练请求失败", str(exc))

        self.append_message("assistant", reply)
        hist.append({"role": "assistant", "content": reply})
        slot["coach_history"] = hist
        data_manager.save_user_data(data)
