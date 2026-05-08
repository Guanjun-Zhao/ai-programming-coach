"""
样例库界面：从 samples.json 读出数据；左侧样例列表，右侧只读区域展示**当前选中条**的完整 input/output。

── PyQt 初学者可先对照下列概念读本文件 ──
1. QListWidget / QListWidgetItem
   - 纵向列表控件；每一行是一个 QListWidgetItem（本文件里文字为「样例 1」「样例 2」）。
   - currentRowChanged(int)：当前高亮行变化时发出信号，参数为新行号（无选中时可为 -1）。
2. QPlainTextEdit
   - 多行文本区；setReadOnly(True) 后仅供展示，配合滚动条阅读长输入输出。
3. 「列表 + 详情」与拉伸比例
   - 不把当前任务下所有样例正文一次性塞进一个控件（字符串过长会拖慢界面）。
   - QHBoxLayout.addWidget(..., 1) 与 addWidget(..., 3)：水平剩余空间按 1:3 分给列表与详情（左窄右宽）。
4. 信号槽与 blockSignals
   - currentRowChanged → `_on_sample_row_changed`：点到哪一行就刷新右侧全文。
   - 批量清空、重新 addItem 时先 blockSignals(True)，避免中间状态反复触发槽；收尾后再手动刷新第 0 行详情。
5. Python 小技巧（读数据）
   - dict.get(key, default) 避免缺键异常；`ver = x.get(vid) or {}` 在值为 None 时用空字典兜底。
   - `[x for x in raw if isinstance(x, dict)]`：列表推导，只保留 JSON 对象条目。

与其它文件的衔接：
- samples.json 里 version_id / task_id 必须与 VersionPage、user_data 等处命名一致。
- get_samples 依赖 data_manager.load_samples()（进程内按 samples.json 修改时间缓存）。

类型标注：`from __future__ import annotations` 与其它模块一致。
"""

# 让当前文件里可以用「list[str]」这种写法标注类型（Python 3.9+ 也可不用这行；写上兼容旧习惯）
from __future__ import annotations

from typing import Any  # 样例 dict 来自 JSON，值类型多样，用 Any 标注

# 第三方：PyQt6 字体与控件、布局
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,  # 水平布局：左列表 + 右详情
    QLabel,  # 顶部一句操作提示
    QListWidget,  # 样例条目列表
    QListWidgetItem,  # 列表中的一行（一项）
    QPlainTextEdit,  # 多行只读详情
    QVBoxLayout,  # 垂直布局：提示条 + 下方左右分栏
    QWidget,  # 通用控件基类；本类的父类
)

# 同项目：读取 data/samples.json（带 mtime 缓存）
import data_manager


def get_samples(version_id: str, task_id: str) -> list[dict[str, Any]]:
    """
    从嵌套结构 samples.json 中取出「某版本 → 某任务」下的样例数组。

    形状示意：{"version1": {"task1": [ {...}, ... ]}}；元素非 dict 的会被过滤。
    """
    # 整库 dict；同一进程内多次调用可能命中 data_manager 内的 mtime 缓存
    all_samples = data_manager.load_samples()
    # get 不到版本键时得到 None，or {} 避免后续对 None 再 .get
    ver = all_samples.get(version_id) or {}
    raw = ver.get(task_id)
    if raw is None:
        return []
    if isinstance(raw, list):
        # JSON 若被手改混入非对象元素，跳过以免下游假设每条都是 dict
        return [x for x in raw if isinstance(x, dict)]
    # task 对应的不是数组（例如误写成字符串）则视为无样例
    return []


def format_sample_detail(one_based_index: int, sample: dict[str, Any]) -> str:
    """将单条样例格式化为右侧详情用的纯文本（input/output 全文，不截断）。"""
    # .get 第二个参数为缺省值，避免 KeyError（JSON 里可能缺某个字段）
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
        str(inp),  # 统一转成字符串；若为数字等非 str 也能显示
        "",
        "输出:",
        str(out),
    ]
    return "\n".join(lines)


def format_sample_card(sample: dict[str, Any]) -> str:
    """调试或导出：按固定字段顺序拼接为纯文本，无标题行。"""
    parts = [
        str(sample.get("input", "")),
        str(sample.get("output", "")),
        str(sample.get("tags", [])),
        str(sample.get("source", "")),
    ]
    # 四段之间只用换行分隔，便于脚本 grep / 粘贴到别处
    return "\n".join(parts)


class SampleLibraryWidget(QWidget):
    """
    VersionPage 右侧 Tab「样例库」里嵌入的本控件。

    VersionPage 在用户切换任务时调用 set_context，本类据此刷新左侧列表与右侧详情。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        # parent 非空时本控件随父级一并参与 Qt 对象树析构（VersionPage 作为 Tab 子控件时常传入）
        super().__init__(parent)
        self._version_id = "version1"
        self._task_id = "task1"
        # 与 QListWidget 行下标一一对应：self._samples[i] 为第 i 条样例 dict
        self._samples: list[dict[str, Any]] = []

        # ────────── 左侧：样例列表 ──────────
        self._list = QListWidget()

        # ────────── 右侧：当前样例全文 ──────────
        self._detail = QPlainTextEdit()
        self._detail.setReadOnly(True)
        # 等宽字体便于对齐多行样例；名称不存在时 Qt 会选最接近的备用字体
        self._detail.setFont(QFont("Courier New", 10))

        # currentRowChanged：行变化时触发槽；不必对每一行 QListWidgetItem 单独 connect
        self._list.currentRowChanged.connect(self._on_sample_row_changed)

        hint = QLabel("左侧选择样例；右侧显示该条完整输入与输出（可滚动）。")
        hint.setWordWrap(True)

        # ────────── 布局：上提示 + 下左右分栏 ──────────
        split = QHBoxLayout()
        # stretch 1 : 3 → 列表窄、详情宽（与 main_window 里横向按钮排布同理，均为 QHBoxLayout）
        split.addWidget(self._list, 1)
        split.addWidget(self._detail, 3)

        # QVBoxLayout(self)：把布局绑在本控件上，self 即该 Tab 页的根 widget
        layout = QVBoxLayout(self)
        layout.addWidget(hint)
        layout.addLayout(split)

    def set_context(self, version_id: str, task_id: str) -> None:
        """VersionPage 切换版本或任务时调用：更新当前上下文并 _refresh。"""
        self._version_id = version_id
        self._task_id = task_id
        self._refresh()

    def _on_sample_row_changed(self, row: int) -> None:
        """
        槽函数：列表当前行变化时刷新详情。

        row 为 QListWidget 的零起始下标；展示给用户见「样例 {row+1}」。
        """
        # row == -1：列表被清空或暂无选中；>= len：与 self._samples 不同步时的防御
        if row < 0 or row >= len(self._samples):
            self._detail.setPlainText("")
            return
        text = format_sample_detail(row + 1, self._samples[row])
        # setPlainText 整段替换；适合大块文本，比 QLabel.setText 在此场景更常用
        self._detail.setPlainText(text)

    def _refresh(self) -> None:
        """重新读取当前版本/任务的样例列表；默认选中第一条并刷新详情。"""
        samples = get_samples(self._version_id, self._task_id)
        self._samples = samples

        # 下面会 clear / setCurrentRow；屏蔽信号可避免中间步骤反复进入 _on_sample_row_changed
        self._list.blockSignals(True)
        self._list.clear()
        if not samples:
            self._list.blockSignals(False)
            self._detail.setPlainText("（暂无样例，请在 data/samples.json 中配置）")
            return

        for i in range(len(samples)):
            self._list.addItem(QListWidgetItem(f"样例 {i + 1}"))
        # 默认第一行；因信号仍被 block，currentRowChanged 不会触发，故下面手动调一次槽
        self._list.setCurrentRow(0)
        self._list.blockSignals(False)
        self._on_sample_row_changed(0)
