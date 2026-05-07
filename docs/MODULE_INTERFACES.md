# 模块接口冻结说明

本文与仓库根目录扁平模块一致；变更接口时请同步修改本文并通知组员。

**路径约定**：凡称「项目根目录」均指包含 `main.py` 的目录。

---

## 1. 标识符与 JSON 键名

| 概念 | 约定值 | 说明 |
|------|--------|------|
| 版本 ID | `version1` … `version4` | 与 `user_data.json`、`samples.json`、文件名 `prompts/versionN.txt` 一致 |
| 任务 ID | `task1`, `task2`, … | 字符串键；骨架阶段仅使用 `task1` |
| 对话消息 | `{"role": "user"\|"assistant", "content": str}` | 仅允许这两种 role |

### `user_data.json` 结构（示意）

```json
{
  "version1": {
    "task1": {
      "completed": false,
      "coach_history": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
      ]
    }
  }
}
```

### `samples.json` 结构（示意）

```json
{
  "version1": {
    "task1": [
      {
        "input": "字符串",
        "output": "字符串",
        "tags": ["标签1"],
        "source": "老师样例 | AI生成 | 骨架占位"
      }
    ]
  }
}
```

---

## 2. `data_manager.py`

| 符号 | 说明 |
|------|------|
| `ROOT_DIR` | `Path(__file__).resolve().parent` |
| `USER_DATA_PATH` | `ROOT_DIR / "data" / "user_data.json"` |
| `SAMPLES_PATH` | `ROOT_DIR / "data" / "samples.json"` |
| `load_user_data() -> dict` | 无文件或空文件返回 `{}` |
| `save_user_data(data: dict) -> None` | 覆盖写入 UTF-8 JSON |
| `load_samples() -> dict` | 无文件或解析失败返回 `{}` |
| `ensure_task_slot(data, version_id, task_id) -> dict` | 创建嵌套并返回 task 对象 |

---

## 3. `ai_coach.py`

| 符号 | 说明 |
|------|------|
| `PROMPTS_DIR` | `ROOT_DIR / "prompts"` |
| `get_system_prompt(version_id: str) -> str` | 读取 `prompts/{version_id}.txt`；缺失则返回占位字符串 |
| `chat(version_id, task_id, messages, user_message) -> str` | `messages` 为当前用户输入之前的 history（不含本轮 user）；同步返回助手文本 |
| 环境变量 | `DEEPSEEK_API_KEY` 必填方可调用 API；可选 `DEEPSEEK_MODEL`（默认 `deepseek-chat`） |
| API | `base_url=https://api.deepseek.com`，OpenAI 兼容 SDK |

---

## 4. `sample_library.py`

| 符号 | 说明 |
|------|------|
| `get_samples(version_id, task_id) -> list[dict]` | 基于 `load_samples()` 按键切片 |
| `SampleLibraryWidget` | PyQt `QWidget`；`set_context(version_id, task_id)` 刷新展示 |

---

## 5. `chat_widget.py`

| 方法 | 说明 |
|------|------|
| `ChatWidget(version_id, task_id)` | 构造时绑定版本与初始任务 |
| `set_task(task_id)` | 切换任务并应调用 `load_history()` |
| `load_history()` | 从 `user_data` 载入 `coach_history` 到界面 |
| `clear()` | 清空当前任务持久化记录与界面 |
| `append_message(role, content)` | 追加显示（内部调试可用） |

发送流程：读 `user_data` → `ensure_task_slot` → 调用 `ai_coach.chat(...)` → 写回 `coach_history` → `save_user_data`。

---

## 6. `version_page.py`

| 符号 | 说明 |
|------|------|
| `VersionPage(version_id)` | 左任务列表、右 `QStackedWidget`（`ChatWidget` + `SampleLibraryWidget`） |
| `back_requested` | 信号：请求返回主页 |

---

## 7. `main_window.py`

| 符号 | 说明 |
|------|------|
| `VERSION_ENTRIES` | `(version_id, 按钮文案)` 四元组列表 |
| `MainWindow` | `QStackedWidget`：主页四按钮 → 各 `VersionPage` |

---

## 8. `main.py`

唯一职责：创建 `QApplication`、`MainWindow`、`show`、`exec`。

---

## 依赖关系简图

```
main.py → main_window.py → version_page.py → chat_widget.py → ai_coach.py
                                           → sample_library.py → data_manager.py
chat_widget.py → data_manager.py
```

---

## 验收检查清单

- [ ] 新增任务 ID 时同时扩展 `samples.json` 键与左侧列表数据源。
- [ ] 修改 JSON 形状时同步更新本文与 `plan/AI编程教练_项目方案总结（组内版）.md` 中的示意（如有）。
- [ ] 不得在发布的程序资源中嵌入 `answer/` 下参考源码。
