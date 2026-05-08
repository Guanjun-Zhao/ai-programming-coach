"""
样例库界面：从 samples.json 读出数据，在右侧用 QLabel + 滚动条展示。

初学者可以这样理解：
1. get_samples：按「版本 id + 任务 id」从嵌套 JSON 里取出样例列表。
2. SampleLibraryWidget：一块可放在 Tab 里的控件，切换任务时刷新文字内容。

类型标注：见 `from __future__ import annotations`（与其它模块一致）。
"""

# 推迟解析类型注解（与本项目其它模块一致；详见模块 docstring）
from __future__ import annotations

from typing import Any  # 样例条目为 JSON 对象，list[dict[str, Any]] 表示「键多为 str、值类型不定」

# 第三方：PyQt6 控件与布局
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

# 同项目：读取 data/samples.json
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
    # 必须是列表；列表推导过滤掉非 dict 的元素（JSON 手滑写成字符串等脏数据）
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


class SampleLibraryWidget(QWidget):
    """样例模式右侧面板：根据 version_id / task_id 刷新展示。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        # 必须先初始化 QWidget；Qt 才能在对象树里正确布置子控件
        super().__init__(parent)
        # 默认上下文：骨架只有一个示例任务；后续 set_context 会改
        self._version_id = "version1"
        self._task_id = "task1"
        # QLabel 默认按纯文本显示；下文用 ``` 只是排版习惯，不会像 Markdown 那样渲染标题样式
        self._label = QLabel()
        # 长文本自动换行
        self._label.setWordWrap(True)
        # 滚动区域：内部放一个「内容控件」，超出可视区域出现滚动条
        scroll = QScrollArea()
        # True：内部 QLabel 随滚动区域宽度拉伸换行；False 则可能横向裁切或出现横向滚动条
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._label)
        # QVBoxLayout(self)：把布局绑定到本控件，作为唯一顶层布局
        layout = QVBoxLayout(self)
        layout.addWidget(scroll)

    def set_context(self, version_id: str, task_id: str) -> None:
        """左侧切换任务时调用：记住当前版本/任务并刷新界面。"""
        self._version_id = version_id
        self._task_id = task_id
        self._refresh()

    def _refresh(self) -> None:
        """根据 samples.json 里的样例列表生成展示字符串。"""
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
            # 用 ``` 包住输入输出便于肉眼区分；仍是 QLabel 纯文本，不是 Markdown 渲染器
            lines.append("输入:\n```\n" + str(inp).strip() + "\n```")
            lines.append("输出:\n```\n" + str(out).strip() + "\n```")
            lines.append("")
        # 把多行合成一个大字符串塞给 QLabel
        self._label.setText("\n".join(lines))


def format_sample_card(sample: dict[str, Any]) -> str:
    """调试或后续卡片 UI 复用：将单条样例格式化为纯文本。"""
    # 按固定字段顺序拼接，便于日志或与卡片控件字段一一对应
    parts = [
        str(sample.get("input", "")),  # 样例输入
        str(sample.get("output", "")),  # 期望输出
        str(sample.get("tags", [])),  # 标签列表
        str(sample.get("source", "")),  # 来源（老师 / AI 生成等）
    ]
    return "\n".join(parts)
