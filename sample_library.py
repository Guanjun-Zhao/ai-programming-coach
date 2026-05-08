"""
样例库界面：从 samples.json 读出数据；左侧样例列表，右侧只读多行区展示**当前条**的完整 input/output。

初学者可以这样理解：
1. get_samples：按「版本 id + 任务 id」从嵌套 JSON 里取出样例列表（load_samples 在 data_manager 中带 mtime 缓存）。
2. SampleLibraryWidget：列表 + 详情，避免把所有样例全文拼进一个控件；详情区不截断 input/output 正文。

类型标注：见 `from __future__ import annotations`（与其它模块一致）。
"""

# 推迟解析类型注解（与本项目其它模块一致；详见模块 docstring）
from __future__ import annotations

from typing import Any  # 样例条目为 JSON 对象，list[dict[str, Any]] 表示「键多为 str、值类型不定」

# 第三方：PyQt6 控件与布局
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPlainTextEdit, QVBoxLayout, QWidget

# 同项目：读取 data/samples.json
import data_manager


def get_samples(version_id: str, task_id: str) -> list[dict[str, Any]]:
    """返回某版本某任务下的样例列表（每项为 JSON 对象）。"""
    all_samples = data_manager.load_samples()
    ver = all_samples.get(version_id) or {}
    raw = ver.get(task_id)
    if raw is None:
        return []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


def format_sample_detail(one_based_index: int, sample: dict[str, Any]) -> str:
    """将单条样例格式化为纯文本：来源、标签、输入与输出均为全文（不截断）。"""
    inp = sample.get("input", "")
    out = sample.get("output", "")
    tags = sample.get("tags", [])
    src = sample.get("source", "")
    lines = [
        f"样例 {one_based_index}",
        f"来源: {src}",
        f"标签: {tags}",
        "",
        "输入:",
        "```",
        str(inp),
        "```",
        "",
        "输出:",
        "```",
        str(out),
        "```",
    ]
    return "\n".join(lines)


def format_sample_card(sample: dict[str, Any]) -> str:
    """调试或后续卡片 UI 复用：将单条样例格式化为纯文本。"""
    parts = [
        str(sample.get("input", "")),
        str(sample.get("output", "")),
        str(sample.get("tags", [])),
        str(sample.get("source", "")),
    ]
    return "\n".join(parts)


class SampleLibraryWidget(QWidget):
    """样例模式右侧面板：根据 version_id / task_id 刷新列表；选中条目后在右侧显示全文 input/output。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = "version1"
        self._task_id = "task1"
        self._samples: list[dict[str, Any]] = []

        self._list = QListWidget()
        self._detail = QPlainTextEdit()
        self._detail.setReadOnly(True)
        # 等宽字体便于对齐长输入输出；系统无该族名时 Qt 会回退默认字体
        self._detail.setFont(QFont("Courier New", 10))

        self._list.currentRowChanged.connect(self._on_sample_row_changed)

        hint = QLabel("左侧选择样例；右侧显示该条完整输入与输出（可滚动）。")
        hint.setWordWrap(True)

        split = QHBoxLayout()
        split.addWidget(self._list, 1)
        split.addWidget(self._detail, 3)

        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(split)

    def set_context(self, version_id: str, task_id: str) -> None:
        """左侧切换任务时调用：记住当前版本/任务并刷新界面。"""
        self._version_id = version_id
        self._task_id = task_id
        self._refresh()

    def _on_sample_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._samples):
            self._detail.setPlainText("")
            return
        text = format_sample_detail(row + 1, self._samples[row])
        self._detail.setPlainText(text)

    def _refresh(self) -> None:
        """载入当前版本/任务下的样例列表；仅详情区渲染选中条的全文。"""
        samples = get_samples(self._version_id, self._task_id)
        self._samples = samples

        self._list.blockSignals(True)
        self._list.clear()
        if not samples:
            self._list.blockSignals(False)
            self._detail.setPlainText("（暂无样例，请在 data/samples.json 中配置）")
            return

        for i in range(len(samples)):
            self._list.addItem(QListWidgetItem(f"样例 {i + 1}"))
        self._list.setCurrentRow(0)
        self._list.blockSignals(False)
        self._on_sample_row_changed(0)
