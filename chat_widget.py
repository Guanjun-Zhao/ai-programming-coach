"""
AI 教练 Tab：只读历史区 + 输入框 + 发送；读写 user_data.json。

══════════════════════════════════════════════════════════════════════════════
 PyQt 初学者导读（与本控件相关的部分）
══════════════════════════════════════════════════════════════════════════════

【本控件在界面里的角色】
  ChatWidget 继承 QWidget，被放进 VersionPage 的 QTabWidget 里。它不操作主窗口，
  只负责：展示历史、收集输入、调用 ai_coach、把结果写回 data_manager。

【QTextEdit】
  多行富文本编辑区。这里 setReadOnly(True)：用户只能看历史，不能像记事本那样随便改，
  避免误删对话。append(...) 在末尾追加文本（会自动换行）。

【QLineEdit】
  单行输入框。适合一句提问或粘贴一小段代码说明；若以后要「多行代码框」可换成 QTextEdit 并改发送逻辑。

【QPushButton + 信号】
  clicked 信号连到槽函数 _on_send。同一槽也可被别的信号触发——下面用 returnPressed 实现「回车发送」。

【QHBoxLayout / QVBoxLayout】
  输入框与按钮横向一排（H）；标题 + 历史区 + 输入行纵向叠（V）。最外层 QVBoxLayout(self) 表示布局挂在本控件上。

【QMessageBox】
  模态对话框：请求异常时在界面中央提示用户（程序会阻塞到用户点确定为止）。本文件仅在极少未捕获异常时使用。

【与数据的边界】
  load_history / _on_send：读写在 data_manager；界面刷新用 append_message / clear。
  ai_coach.chat(...)：需要「旧历史」与「本轮用户句」分开传入，因此 hist[:-1] 见代码内注释。

类型标注：`from __future__ import annotations` 与其它模块一致。
"""

# 推迟解析类型注解，便于在类型里引用尚未定义的类名（与本项目其它文件一致）
from __future__ import annotations

from typing import Any  # JSON 风格消息 dict 的值类型不定，hist 用 list[dict[str, Any]] 标注（见 _on_send）

from PyQt6.QtWidgets import (
    QHBoxLayout,  # 横向布局：输入框 + 按钮同一行
    QLabel,  # 顶部标题行（版本 / 任务提示）
    QLineEdit,  # 单行输入
    QMessageBox,  # 错误提示框
    QPushButton,  # 发送按钮
    QTextEdit,  # 多行显示历史（只读）
    QVBoxLayout,  # 纵向布局：标题、历史、输入区自上而下
    QWidget,  # 本控件的基类
)

import ai_coach
import data_manager


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

        # ---------- 下方：输入 + 发送 ----------
        self._input = QLineEdit()
        self._input.setPlaceholderText("粘贴代码片段或描述你的问题…")
        send = QPushButton("发送")
        send.clicked.connect(self._on_send)
        # returnPressed：单行编辑框里按回车时发出；与按钮共用同一槽，行为一致
        self._input.returnPressed.connect(self._on_send)

        row = QHBoxLayout()
        row.addWidget(self._input)
        row.addWidget(send)

        # QVBoxLayout(self)：根布局装在整个 ChatWidget 上；stretch 默认 0，历史区会随窗口变大而拉伸（由 QTextEdit 默认尺寸策略决定）
        layout = QVBoxLayout(self)
        # 标题仅构造时拼一次；若需在 set_task 里同步改成新 task_id，可在此处把 QLabel 存成 self._title 再在 set_task 里 setText
        layout.addWidget(QLabel(f"AI 教练 · {version_id} / {task_id}"))
        layout.addWidget(self._history_view)
        layout.addLayout(row)

        # 进入界面时从磁盘恢复该版本+任务的 coach_history
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
        # 整份 user_data.json 读入内存（dict）；后续若 ensure 出新键但未 save，不会自动写盘
        data = data_manager.load_user_data()
        # 按 version_id / task_id 向下钻取到「该任务」那一层 dict；缺键会在 data 上就地创建
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        # coach_history 应为消息列表；键不存在或值为 None 时当作空列表，避免 None 进入 for
        hist = slot.get("coach_history") or []
        # 先清空文本框，避免多次 load_history 时把同一段内容重复追加
        self._history_view.clear()
        for m in hist:
            # 单条消息约定为 {"role": "...", "content": "..."}；缺键时用空串以免界面报错
            role = m.get("role", "")
            content = m.get("content", "")
            self._history_view.append(f"[{role}]\n{content}\n")

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

    def append_message(self, role: str, content: str) -> None:
        """仅在 QTextEdit 末尾追加一行展示；不负责写入 JSON。"""
        self._history_view.append(f"[{role}]\n{content}\n")

    def _on_send(self) -> None:
        """
        发送一轮对话：校验输入 → 持久化用户句 → 调 AI → 持久化助手句。

        顺序要点：
          先把用户消息追加到界面与列表 hist，再调用 ai_coach.chat(..., hist[:-1], text)，
          这样 API 收到的是「之前的消息」加单独的本轮用户句，而不是重复包含本轮 user 的列表。
        """
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()

        data = data_manager.load_user_data()
        slot = data_manager.ensure_task_slot(data, self._version_id, self._task_id)
        # 从 slot 取出已有记录；or [] 防止 None；list(...) 浅拷贝一份新列表，后面 append 用户/助手消息时不与原引用纠缠
        hist: list[dict[str, Any]] = list(slot.get("coach_history") or [])

        self.append_message("user", text)
        hist.append({"role": "user", "content": text})

        try:
            # hist[:-1]：去掉刚 append 的本轮 user，避免「历史里两条 user」与 user_message 参数语义重复
            reply = ai_coach.chat(
                self._version_id,
                self._task_id,
                hist[:-1],
                text,
            )
        except Exception as exc:
            reply = f"[错误] {exc}"
            # 极少数未被 ai_coach 内部消化的异常才弹框；多数 API 错误已在 ai_coach 内变成字符串 reply
            QMessageBox.warning(self, "教练请求失败", str(exc))

        self.append_message("assistant", reply)
        hist.append({"role": "assistant", "content": reply})
        slot["coach_history"] = hist
        data_manager.save_user_data(data)
