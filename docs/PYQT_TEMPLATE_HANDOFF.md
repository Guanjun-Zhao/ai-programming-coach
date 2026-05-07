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
| [main_window.py](../main_window.py) | 主页：四个版本按钮；`QStackedWidget` 切换主页与各 `VersionPage`。可改按钮样式、布局、后续加「进度」显示。 |
| [version_page.py](../version_page.py) | 版本页：**左侧**任务列表（`QListWidget`）；**右侧** `QTabWidget` 两个 Tab：「AI 教练」「样例库」。可改左右比例、Tab 样式、任务列表数据源。 |
| [chat_widget.py](../chat_widget.py) | 教练 Tab 内：只读历史 + 输入框 + 发送。可换 QTextBrowser、气泡样式、快捷键等；**保留** `set_task` / `load_history` 或与组长约定的接口。 |
| [sample_library.py](../sample_library.py) | 样例 Tab 内：当前为 QLabel + 滚动区展示文本。可改为卡片网格（方案里是「三列卡片」）；数据仍来自 `get_samples()` / `load_samples()`。 |

请**不要轻易改动**（除非与组长对齐接口）：

- [data_manager.py](../data_manager.py) —— JSON 路径与键名
- [ai_coach.py](../ai_coach.py) —— API 调用与 Prompt 路径

## 版本 ID 与界面文案

代码里版本键为 `version1` … `version4`，按钮中文见 `main_window.VERSION_ENTRIES`。左侧任务目前仅有占位 `task1`，后续由内容与 JSON 扩展。

## 联调约定

- 持久化格式见仓库根目录 `docs/MODULE_INTERFACES.md`。
- 遇到问题先在群里 @赵冠钧 确认是否涉及接口变更。
