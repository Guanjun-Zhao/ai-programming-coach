"""
本模块：调用 DeepSeek 的聊天接口（兼容 OpenAI SDK），并挂上「系统提示词」。

初学者可以这样理解整个文件：
1. get_system_prompt：从磁盘读取某个版本题目对应的「教练人设 + 规则」长文本。
2. chat：把「系统提示 + 历史对话 + 本轮用户输入」发给模型，拿回模型回复字符串。

类型标注：`from __future__ import annotations` 与其它模块一致。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = ROOT_DIR / "prompts"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


def get_system_prompt(version_id: str) -> str:
    """
    读取 prompts/{version_id}.txt（例如 version1 -> prompts/version1.txt）。
    缺失时返回占位说明，避免崩溃。
    """
    path = PROMPTS_DIR / f"{version_id}.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return (
        f"[占位] 未找到 {path.name}，请在 prompts/ 下添加该版本的 System Prompt 文本。"
    )


def chat(
    version_id: str,
    task_id: str,
    messages: list[dict[str, Any]],
    user_message: str,
) -> str:
    """
    发送一轮用户消息，返回助手回复文本（同步）。
    messages：此前多轮历史，每项为 {"role":"user"|"assistant","content": str}。
    未配置 DEEPSEEK_API_KEY 时返回占位字符串，便于无密钥联调界面。

    task_id：界面侧当前左侧任务，用于占位回复里标注上下文；将来若做「按任务的 Prompt」也会用到。
    当前发往模型的 payload 只由 version_id 决定 System Prompt，不把 task_id 单独塞进 API。
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    system = get_system_prompt(version_id)

    payload_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for m in messages:
        role = m.get("role")
        content = m.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            payload_messages.append({"role": role, "content": content})
    payload_messages.append({"role": "user", "content": user_message})

    if not api_key:
        return (
            "[占位回复] 未设置环境变量 DEEPSEEK_API_KEY。"
            f"（当前版本={version_id}，任务={task_id}）"
        )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        completion = client.chat.completions.create(
            model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
            messages=payload_messages,
        )
        choice = completion.choices[0].message
        return (choice.content or "").strip()
    except Exception as exc:
        return f"[API 错误] {type(exc).__name__}: {exc}"
