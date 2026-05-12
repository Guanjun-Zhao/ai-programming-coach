"""
本模块：调用 DeepSeek 的聊天接口（兼容 OpenAI SDK），并挂上「系统提示词」。

初学者可以这样理解整个文件：
1. get_system_prompt：从磁盘读取某个版本题目对应的「教练人设 + 规则」长文本。
2. chat：把「系统提示 + 历史对话 + 本轮用户输入」发给模型，拿回模型回复字符串。

类型标注：`from __future__ import annotations` 与其它模块一致。
"""

# 推迟注解求值，便于在类型里引用尚未定义的类名等（与本项目其它文件一致）
from __future__ import annotations

# 用于读取环境变量 DEEPSEEK_API_KEY、DEEPSEEK_MODEL
import os
# 表示路径，便于拼接 prompts 目录与版本文件名
from pathlib import Path
# 历史消息列表里每条是 dict，用 Any 兼容额外字段
from typing import Any

import sections_loader

# 本文件所在目录，作为项目根下的相对路径锚点
ROOT_DIR = Path(__file__).resolve().parent
# 存放各版本系统提示词文本的目录（如 prompts/version1.txt）
PROMPTS_DIR = ROOT_DIR / "prompts"

# DeepSeek 官方 API 基地址（OpenAI 兼容接口）
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
# 未设置 DEEPSEEK_MODEL 时使用的默认模型名
DEFAULT_MODEL = "deepseek-chat"


def get_system_prompt(version_id: str) -> str:
    """
    读取 prompts/{version_id}.txt（例如 version1 -> prompts/version1.txt）。
    缺失时返回占位说明，避免崩溃。
    """
    # 按版本 id 拼出对应的提示词文件路径
    path = PROMPTS_DIR / f"{version_id}.txt"
    # 若文件存在，则按 UTF-8 读取并去掉首尾空白
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    # 缺少文件时返回中文占位串，提示用户在 prompts/ 下补充
    return (
        f"[占位] 未找到 {path.name}，请在 prompts/ 下添加该版本的 System Prompt 文本。"
    )


def _looks_like_code_snippet(text: str) -> bool:
    """Heuristic: multi-line snippet that looks like C/C++ source."""
    t = text.strip()
    if len(t) < 40:
        return False
    if "\n" not in t:
        return False
    return ";" in t or "{" in t or "#include" in t


def build_task_system(version_id: str, task_id: str) -> str:
    """Base coach prompt + current leaf section description from sections.json."""
    base = get_system_prompt(version_id)
    sec = sections_loader.get_leaf_section(version_id, task_id)
    if not sec:
        return base
    title = str(sec.get("title", task_id))
    desc = str(sec.get("description", ""))
    role = sec.get("role")
    if role == "planning":
        return (
            base
            + f"\n\n【当前任务：{title}（导读/功能设计）】\n{desc}\n\n"
            + "教学要求：只讲解题意与模块分工，不要输出代码块，不要要求用户在本节粘贴代码验证；"
            + "结尾用一两句自然口语建议用户点击左侧下一节开始具体编码。"
        )
    if role == "debug":
        return base
    sid = str(sec.get("section_id", ""))
    return (
        base
        + f"\n\n【当前编码小节：{title}（{sid}）】\n{desc}\n\n"
        + "教学要求：用中文描述要实现什么、逻辑如何流动；不要输出代码块；"
        + "用户若索要完整代码，引导其自己动手完成。"
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

    task_id：当前叶子任务 id；与 `sections.json` 组合为 `build_task_system` 注入本节说明。
    """
    sec = sections_loader.get_leaf_section(version_id, task_id)
    if sec and sec.get("skip_code_verify") and _looks_like_code_snippet(user_message):
        return (
            "【提示】当前小节不需要在这里粘贴大段代码做验证（导读或未开放本节验证）。"
            "请切换到左侧具体编码小节后再粘贴代码，或继续用文字提问。"
        )

    # 从环境变量读取密钥，缺省为空串；strip 去掉无意中的空格换行
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    system = build_task_system(version_id, task_id)

    # 发给模型的消息列表：先放一条 system，角色与内容均为字符串（API 要求）
    payload_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    # 把界面传入的多轮历史逐条规范化后加入 payload
    for m in messages:
        # 每条历史期望含 role
        role = m.get("role")
        # 每条历史期望含 content
        content = m.get("content")
        # 只接受 user/assistant 且 content 为 str，避免脏数据打进请求
        if role in ("user", "assistant") and isinstance(content, str):
            payload_messages.append({"role": role, "content": content})
    # 本轮用户新输入作为最后一条 user 消息
    payload_messages.append({"role": "user", "content": user_message})

    # 没有 API 密钥时不请求网络，返回可读的占位说明（含版本与任务便于调试）
    if not api_key:
        return (
            "[占位回复] 未设置环境变量 DEEPSEEK_API_KEY。"
            f"（当前版本={version_id}，任务={task_id}）"
        )

    try:
        # 延迟导入：无密钥跑界面时可以不装 openai 包也能启动（直到真正调用 chat）
        from openai import OpenAI

        # 使用 OpenAI 兼容客户端连接 DeepSeek 基地址
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        # 发起聊天补全请求；模型名可由环境变量覆盖
        completion = client.chat.completions.create(
            model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
            messages=payload_messages,
        )
        # 取第一条候选里的助手消息对象
        choice = completion.choices[0].message
        # content 可能为 None，统一转成字符串并去掉首尾空白
        return (choice.content or "").strip()
    except Exception as exc:
        # 网络、鉴权、解析等任一环节出错时，把错误类型与信息返回给界面展示
        return f"[API 错误] {type(exc).__name__}: {exc}"
