# PyQt 模板交接说明（师圣晴）

赵冠钧提供的**可运行空白壳**，你只需专注**界面布局、样式与交互细节**；业务规则与 API 见 [MODULE_INTERFACES.md](MODULE_INTERFACES.md)。

## 运行方式

```bash
pip install -r requirements.txt
python main.py
```

## 当前已实现结构

| 文件 | 职责（你可修改的范围） |
|------|------------------------|
| [main_window.py](../main_window.py) | 主页：四个版本按钮；`QStackedWidget` 切换主页与各 `VersionPage`。可改按钮样式、布局、**主页进度**（已勾选复选框数 / 左侧树全部复选框数，数据来自 `user_data.json` + `sections.json`）。 |
| [version_page.py](../version_page.py) | 版本页：**左侧**为 **`QTreeWidget` 任务树**（首条「功能设计」叶子、`##` 二级父节点 + `###` 子叶子、末尾 Debug）；父节点有复选框与折叠，**点击父节点不切换**右侧教练对话；**仅叶子**切换 `ChatWidget` / 样例上下文。右侧 `QTabWidget`：「AI 教练」「样例库」。 |
| [chat_widget.py](../chat_widget.py) | 教练 Tab：`set_task` / `load_history`；**「功能设计」叶子且历史为空**时自动请求一轮导读回复并持久化。可换气泡样式等。 |
| [sections_loader.py](../sections_loader.py)（若已添加） | 只读加载 `data/sections.json`：分组、`task_id`、是否 `skip_code_verify`；供版本页建树与 `ai_coach` 组装按任务的系统提示。 |
| [sample_library.py](../sample_library.py) | 样例 Tab：`get_samples(version_id, task_id)`；`task_id` 与左侧叶子一致（如 `task_debug`）。 |

请**不要轻易改动**（除非与组长对齐接口）：

- [data_manager.py](../data_manager.py) —— `user_data.json` / `samples.json` 路径与 `ensure_task_slot` 等基础读写
- [ai_coach.py](../ai_coach.py) —— API 调用；可按 `sections_loader` 注入当前叶子 `description`/`code`

## 版本 ID 与界面文案

代码里版本键为 `version1` … `version4`，按钮中文见 `main_window.VERSION_ENTRIES`。左侧为 **树形任务栏**（见项目方案总结 §2.3）：`data/sections.json` 定义每版本的 `planning`、`groups[]`、`debug_task_id`；`user_data.json` 中 `_tree.h2_expanded` / `h2_completed` 存二级折叠与勾选，各 `task_*` 存叶子勾选与 `coach_history`。

## 左侧任务树与信号约定（实现要点）

- **控件**：推荐 `QTreeWidget`；父项 = 二级标题（`h2_id`），子项 = 三级叶子（`task_id`）；最上「功能设计」与最末「Debug」为**顶层叶子项**（无子项）。
- **UserRole**：子项 `Qt.ItemDataRole.UserRole` 存 `task_id`（`str`）；父项该角色为空或不用，用 `childCount()>0` 或另设 `UserRole+1` 存 `h2_id`。
- **复选框**：`QTreeWidgetItem` 设 `Qt.ItemFlag.ItemIsUserCheckable`，`setCheckState(0, …)`；`itemChanged` 里区分父/子写回 `user_data`（父 → `_tree.h2_completed[h2_id]`，子 → `slot["completed"]`）；批量建树时 `blockSignals(True)` 避免级联。
- **折叠**：监听 `itemExpanded` / `itemCollapsed` 写回 `_tree.h2_expanded[h2_id]`；或父行旁单独按钮切换 `setItemExpanded`。
- **点击语义**：`currentItemChanged` 或 `itemClicked`：仅当当前项为**叶子且含 `task_id`** 时调用 `ChatWidget.set_task(task_id)` 与 `SampleLibraryWidget.set_context`；点到父项**不调用** `set_task`（右侧保持上一个叶子上下文）。
- **初始选中**：进入版本页后选中第一条「功能设计」叶子并加载其历史。

## 联调约定

- 持久化与任务 ID 约定见仓库根目录 `plan/AI编程教练_项目方案总结.md` 与 `plan/AI陪练教练_上下文管理方案.md`。
- 遇到问题先在群里 @赵冠钧 确认是否涉及接口变更。
