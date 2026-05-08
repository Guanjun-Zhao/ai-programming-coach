"""
样例库界面：从 samples.json 读出数据，在右侧用 QLabel + 滚动条展示。

初学者可以这样理解：
1. get_samples：按「版本 id + 任务 id」从嵌套 JSON 里取出样例列表。
2. SampleLibraryWidget：一块可放在 Tab 里的控件，切换任务时刷新文字内容。
"""

from __future__ import annotations

from typing import Any

# QLabel 显示富文本/纯文本；QScrollArea 让内容过高时可以滚动
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

# 同项目里的数据加载模块
import data_manager


def get_samples(version_id: str, task_id: str) -> list[dict[str, Any]]:
    """返回某版本某任务下的样例列表（每项为 JSON 对象）。"""
    # 一次性载入整个样例库（中等规模 JSON，骨架阶段足够）
    all_samples = data_manager.load_samples()
    # .get(version_id) 没有则 None；or {} 把 None 变成空字典，后面 .get 更安全
    ver = all_samples.get(version_id) or {}
    # 当前任务对应的原始值（期望是 list，但也可能是别的）
    raw = ver.get(task_id)
    if raw is None:
        return []
    # 类型检查：必须是列表；列表里只保留「字典」类型的元素（过滤脏数据）
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


class SampleLibraryWidget(QWidget):
    """样例模式右侧面板：根据 version_id / task_id 刷新展示。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        # 调用 Qt 父类初始化，挂上对象树（内存管理由 Qt 负责一部分）
        super().__init__(parent)
        # 默认上下文：骨架只有一个示例任务；后续 set_context 会改
        self._version_id = "version1"
        self._task_id = "task1"
        # QLabel 用来塞 Markdown 风格的纯文本（这里没用 QTextBrowser，骨架够用）
        self._label = QLabel()
        # 长文本自动换行
        self._label.setWordWrap(True)
        # 滚动区域：内部放一个「内容控件」，超出可视区域出现滚动条
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._label)
        # 垂直布局：从上到下只放滚动区域，填满 SampleLibraryWidget
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

    def set_context(self, version_id: str, task_id: str) -> None:
        """左侧切换任务时调用：记住当前版本/任务并刷新界面。"""
        self._version_id = version_id
        self._task_id = task_id
        self._refresh()

    def _refresh(self) -> None:
        """根据数据库里的样例列表生成展示字符串。"""
        samples = get_samples(self._version_id, self._task_id)
        if not samples:
            self._label.setText("（暂无样例，请在 data/samples.json 中配置）")
            return
        lines: list[str] = []
        # enumerate(..., start=1)：下标从 1 开始，方便显示「样例 1、样例 2」
        for i, s in enumerate(samples, start=1):
            # .get 第二个参数是默认值：缺少键时用空字符串或 []，避免 KeyError
            inp = s.get("input", "")
            out = s.get("output", "")
            tags = s.get("tags", [])
            src = s.get("source", "")
            lines.append(f"### 样例 {i}")
            lines.append(f"- 来源: {src}")
            lines.append(f"- 标签: {tags}")
            # 用 Markdown 代码块包一层，等宽字体显示输入输出
            lines.append("输入:\n```\n" + str(inp).strip() + "\n```")
            lines.append("输出:\n```\n" + str(out).strip() + "\n```")
            lines.append("")
        # 把多行合成一个大字符串塞给 QLabel
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
