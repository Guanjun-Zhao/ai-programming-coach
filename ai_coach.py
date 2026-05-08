"""
本模块：调用 DeepSeek 的聊天接口（兼容 OpenAI SDK），并挂上「系统提示词」。

初学者可以这样理解整个文件：
1. get_system_prompt：从磁盘读取某个版本题目对应的「教练人设 + 规则」长文本。
2. chat：把「系统提示 + 历史对话 + 本轮用户输入」发给模型，拿回模型回复字符串。
"""

# 让当前文件里可以用「list[str]」这种写法标注类型（Python 3.9+ 也可不用这行；写上兼容旧习惯）
from __future__ import annotations

# os：读取环境变量（例如 DEEPSEEK_API_KEY）、合并默认模型名时用
import os
# Path：用面向对象的方式拼路径、判断文件是否存在，比手写字符串斜杠更安全
from pathlib import Path
# Any：在类型标注里表示「任意类型」，这里用于历史消息字典里除了 str 以外暂不细究的值
from typing import Any

# __file__ 是当前这个 .py 文件的路径字符串；Path(...) 包装成路径对象
# .resolve() 变成绝对路径并解析掉 .. 等符号
# .parent 表示「所在文件夹」，即项目根目录（因为 ai_coach.py 就在根目录）
ROOT_DIR = Path(__file__).resolve().parent
# / 在 Path 上表示拼接子路径，得到「项目根目录下的 prompts 文件夹」
PROMPTS_DIR = ROOT_DIR / "prompts"

# DeepSeek 提供的 OpenAI 兼容接口的基础网址（SDK 会把具体请求路径接在后面）
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
# 若不设置环境变量 DEEPSEEK_MODEL，就用这个默认模型名
DEFAULT_MODEL = "deepseek-chat"


def get_system_prompt(version_id: str) -> str:
    """
    读取 prompts/{version_id}.txt（例如 version1 -> prompts/version1.txt）。
    缺失时返回占位说明，避免崩溃。
    """
    # 用 f-string 把版本号嵌进文件名：例如 version_id 为 "version1" 则得到 prompts/version1.txt
    path = PROMPTS_DIR / f"{version_id}.txt"
    # is_file()：存在且是普通文件（不是文件夹）时为 True
    if path.is_file():
        # read_text：一次性读出整个文本文件；encoding 指定 UTF-8 避免中文乱码
        # strip()：去掉开头结尾空白，避免空行影响模型
        return path.read_text(encoding="utf-8").strip()
    # 找不到文件时，不抛异常，返回一段固定中文提示，界面仍可调试
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
    """
    # os.environ 像字典一样保存环境变量；get 第二个参数是「不存在时用的默认值」
    # DEEPSEEK_API_KEY 需要在系统或终端里事先设置，这里读出来；strip 去掉首尾空格
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    # 根据当前选的魔兽版本，取出对应的长系统提示词（教练规则）
    system = get_system_prompt(version_id)

    # API 要求第一条消息往往是 role=system，后面才是 user/assistant 交替
    # 显式写出类型 list[dict[str, str]]：列表里每个元素是「角色 + 文本」
    payload_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    # 遍历调用方传入的历史记录（不包含本轮用户输入）
    for m in messages:
        # dict.get("role")：取键 role，没有则返回 None
        role = m.get("role")
        content = m.get("content")
        # 只接受角色为 user 或 assistant、且 content 确实是字符串的条目，其它忽略（防止脏数据）
        if role in ("user", "assistant") and isinstance(content, str):
            # 构造一条 Chat API 认识的字典，追加到待发列表末尾（保持时间顺序）
            payload_messages.append({"role": role, "content": content})
    # 本轮用户新说的话放在列表最后，表示「最新一条提问」
    payload_messages.append({"role": "user", "content": user_message})

    # 若用户没有配置密钥，不调网络，直接返回占位字符串，方便先做界面与本地 JSON
    if not api_key:
        return (
            "[占位回复] 未设置环境变量 DEEPSEEK_API_KEY。"
            # f-string 里用 {...} 嵌入变量，便于调试时看出是哪个版本/任务触发的
            f"（当前版本={version_id}，任务={task_id}）"
        )

    # 真正请求 API 时可能出现网络错误、密钥错误等，用 try/except 包住，避免程序崩溃
    try:
        # 延迟导入：只有真的要请求时才加载 openai 库；没装库时至少占位分支还能跑
        from openai import OpenAI

        # OpenAI 官方客户端类；这里把 base_url 换成 DeepSeek，就能复用同一套调用代码
        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        # chat.completions.create：发起一次「聊天补全」请求；返回对象里含模型生成的文本
        completion = client.chat.completions.create(
            # 模型名可从环境变量覆盖，否则用文件顶部的 DEFAULT_MODEL
            model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
            # messages 即上面拼好的：system + 历史 + 最新 user
            messages=payload_messages,
        )
        # completion.choices 是候选回复列表，通常取第一个；.message 里有 content（正文）
        choice = completion.choices[0].message
        # content 有时可能为 None，用 or "" 变成空字符串再 strip，避免返回 None 类型
        return (choice.content or "").strip()
    # as exc：把捕获到的异常对象存到变量 exc，下面字符串里要用
    except Exception as exc:
        # type(exc).__name__ 得到异常类名（如 ConnectionError），便于用户截图排查
        return f"[API 错误] {type(exc).__name__}: {exc}"
