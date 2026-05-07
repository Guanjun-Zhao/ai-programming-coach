# AI 编程教练

魔兽世界 OJ 大作业辅助工具：版本化任务、AI 教练对照、样例库（骨架已就绪）。

## 环境

- Python 3.10+
- 依赖见 `requirements.txt`（PyQt6、OpenAI 兼容客户端用于 DeepSeek）

## 安装与运行

```bash
cd "程序设计 - AI编程教练"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## DeepSeek（可选）

```bash
set DEEPSEEK_API_KEY=你的密钥
```

未设置时，AI 教练返回占位回复，仍可调试界面与持久化。

可选：`DEEPSEEK_MODEL`（默认 `deepseek-chat`）。

## 仓库说明

- `problems/`：题目原文
- `answer/`：开发阶段参考实现（不打包进教学交付逻辑）
- `data/samples.json`：预置样例（程序只读）
- `data/user_data.json`：用户进度与聊天记录（默认忽略提交，见 `.gitignore`）
- `docs/MODULE_INTERFACES.md`：模块间冻结接口

## 分工对应文件

| 成员   | 主要文件 |
|--------|-----------|
| 赵冠钧 | `ai_coach.py`、`prompts/` |
| 李佳昱 | `data_manager.py`、`sample_library.py` |
| 师圣晴 | `main_window.py`、`version_page.py`、`chat_widget.py` |
