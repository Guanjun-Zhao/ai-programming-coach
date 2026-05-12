"""
版本页：左侧任务树（导读 + 二级分组 + 三级叶子 + Debug）+ 右侧 Tab（AI 教练 / 样例库）。

左侧二级父节点：可勾选、可折叠，点击不切换右侧对话；三级与「功能设计」、Debug 为叶子，点击切换对话。
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from chat_widget import ChatWidget
from sample_library import SampleLibraryWidget

import data_manager
import sections_loader

# 自定义数据角色：task_id（叶子）与 h2_id（父节点）
ROLE_TASK = Qt.ItemDataRole.UserRole
ROLE_H2 = Qt.ItemDataRole.UserRole + 1


class VersionPage(QWidget):
    """单版本页面：任务树 + 教练 / 样例 Tab。"""

    back_requested = pyqtSignal()

    def __init__(self, version_id: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_id = version_id

        back = QPushButton("← 返回主页")
        back.clicked.connect(self.back_requested.emit)

        self._task_tree = QTreeWidget()
        self._task_tree.setHeaderHidden(True)
        self._task_tree.setAnimated(True)
        self._task_tree.setIndentation(16)
        self._task_tree.itemChanged.connect(self._on_tree_item_changed)
        self._task_tree.itemExpanded.connect(self._on_item_expanded_collapsed)
        self._task_tree.itemCollapsed.connect(self._on_item_expanded_collapsed)
        self._task_tree.currentItemChanged.connect(self._on_current_leaf_changed)

        first_tid = sections_loader.first_leaf_task_id(version_id) or "task1"
        self._chat = ChatWidget(version_id, first_tid)
        self._samples = SampleLibraryWidget()
        self._samples.set_context(version_id, first_tid)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._chat, "AI 教练")
        self._tabs.addTab(self._samples, "样例库")

        left = QVBoxLayout()
        left.addWidget(QLabel("任务清单"))
        left.addWidget(self._task_tree)

        right = QVBoxLayout()
        right.addWidget(self._tabs)

        body = QHBoxLayout()
        body.addLayout(left, 1)
        body.addLayout(right, 3)

        outer = QVBoxLayout(self)
        outer.addWidget(back)
        outer.addLayout(body)

        self._rebuild_task_tree()

    def _rebuild_task_tree(self) -> None:
        data = data_manager.load_user_data()
        tree_state = sections_loader.ensure_tree_state(data, self._version_id)
        exp = tree_state.setdefault("h2_expanded", {})
        h2_done = tree_state.setdefault("h2_completed", {})
        ver = data.setdefault(self._version_id, {})

        self._task_tree.blockSignals(True)
        self._task_tree.clear()

        spec = sections_loader.get_version_spec(self._version_id)
        first_select: QTreeWidgetItem | None = None

        if spec.get("planning"):
            p = spec["planning"]
            it = QTreeWidgetItem([str(p.get("title", "功能设计"))])
            it.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            tid = str(p.get("task_id", ""))
            it.setData(0, ROLE_TASK, tid)
            it.setData(0, ROLE_H2, "")
            done = bool((ver.get(tid) or {}).get("completed"))
            it.setCheckState(0, Qt.CheckState.Checked if done else Qt.CheckState.Unchecked)
            self._task_tree.addTopLevelItem(it)
            first_select = it

        for g in spec.get("groups") or []:
            h2_id = str(g.get("h2_id") or "")
            title = str(g.get("h2_title") or h2_id)
            parent = QTreeWidgetItem([title])
            parent.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            parent.setData(0, ROLE_TASK, "")
            parent.setData(0, ROLE_H2, h2_id)
            parent.setCheckState(
                0,
                Qt.CheckState.Checked if h2_done.get(h2_id) else Qt.CheckState.Unchecked,
            )
            self._task_tree.addTopLevelItem(parent)
            for sec in g.get("sections") or []:
                child = QTreeWidgetItem([str(sec.get("title", sec.get("task_id", "")))])
                child.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )
                ctid = str(sec.get("task_id", ""))
                child.setData(0, ROLE_TASK, ctid)
                child.setData(0, ROLE_H2, "")
                cdone = bool((ver.get(ctid) or {}).get("completed"))
                child.setCheckState(
                    0, Qt.CheckState.Checked if cdone else Qt.CheckState.Unchecked
                )
                parent.addChild(child)
            self._task_tree.setItemExpanded(parent, bool(exp.get(h2_id, True)))

        dt = spec.get("debug_task_id")
        if dt:
            dts = str(dt)
            dbg = QTreeWidgetItem(["Debug"])
            dbg.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            dbg.setData(0, ROLE_TASK, dts)
            dbg.setData(0, ROLE_H2, "")
            ddone = bool((ver.get(dts) or {}).get("completed"))
            dbg.setCheckState(0, Qt.CheckState.Checked if ddone else Qt.CheckState.Unchecked)
            self._task_tree.addTopLevelItem(dbg)

        if self._task_tree.topLevelItemCount() == 0:
            fb = QTreeWidgetItem(["示例任务（未找到 data/sections.json）"])
            fb.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            fb.setData(0, ROLE_TASK, "task1")
            fb.setData(0, ROLE_H2, "")
            fb.setCheckState(
                0,
                Qt.CheckState.Checked
                if bool((ver.get("task1") or {}).get("completed"))
                else Qt.CheckState.Unchecked,
            )
            self._task_tree.addTopLevelItem(fb)
            first_select = fb

        self._task_tree.blockSignals(False)

        if first_select is not None:
            self._task_tree.setCurrentItem(first_select)

    def _on_tree_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0:
            return
        data = data_manager.load_user_data()
        ver = data.setdefault(self._version_id, {})
        tree_state = sections_loader.ensure_tree_state(data, self._version_id)
        tid_raw = item.data(0, ROLE_TASK)
        h2_raw = item.data(0, ROLE_H2)
        tid = tid_raw if isinstance(tid_raw, str) else ""
        h2 = h2_raw if isinstance(h2_raw, str) else ""
        checked = item.checkState(0) == Qt.CheckState.Checked
        if tid:
            slot = data_manager.ensure_task_slot(data, self._version_id, tid)
            slot["completed"] = checked
        elif h2:
            tree_state.setdefault("h2_completed", {})[h2] = checked
        data_manager.save_user_data(data)

    def _on_item_expanded_collapsed(self, item: QTreeWidgetItem) -> None:
        h2_raw = item.data(0, ROLE_H2)
        h2 = h2_raw if isinstance(h2_raw, str) else ""
        if not h2:
            return
        data = data_manager.load_user_data()
        tree_state = sections_loader.ensure_tree_state(data, self._version_id)
        tree_state.setdefault("h2_expanded", {})[h2] = self._task_tree.isItemExpanded(item)
        data_manager.save_user_data(data)

    def _on_current_leaf_changed(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        if current is None:
            return
        tid_raw = current.data(0, ROLE_TASK)
        if not isinstance(tid_raw, str) or not tid_raw:
            return
        self._chat.set_task(tid_raw)
        self._samples.set_context(self._version_id, tid_raw)
