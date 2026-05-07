"""样例库：从 samples.json 查询 + PyQt 展示占位。"""
from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

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


class SampleLibraryWidget(QWidget):
    """样例模式右侧面板：根据 version_id / task_id 刷新展示。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = "version1"
        self._task_id = "task1"
        self._label = QLabel()
        self._label.setWordWrap(True)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._label)
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

    def set_context(self, version_id: str, task_id: str) -> None:
        self._version_id = version_id
        self._task_id = task_id
        self._refresh()

    def _refresh(self) -> None:
        samples = get_samples(self._version_id, self._task_id)
        if not samples:
            self._label.setText("（暂无样例，请在 data/samples.json 中配置）")
            return
        lines: list[str] = []
        for i, s in enumerate(samples, start=1):
            inp = s.get("input", "")
            out = s.get("output", "")
            tags = s.get("tags", [])
            src = s.get("source", "")
            lines.append(f"### 样例 {i}")
            lines.append(f"- 来源: {src}")
            lines.append(f"- 标签: {tags}")
            lines.append("输入:\n```\n" + str(inp).strip() + "\n```")
            lines.append("输出:\n```\n" + str(out).strip() + "\n```")
            lines.append("")
        self._label.setText("\n".join(lines))


def format_sample_card(sample: dict[str, Any]) -> str:
    """调试或后续卡片 UI 复用：将单条样例格式化为纯文本。"""
    parts = [
        str(sample.get("input", "")),
        str(sample.get("output", "")),
        str(sample.get("tags", [])),
        str(sample.get("source", "")),
    ]
    return "\n".join(parts)
