"""
本地 JSON 持久化模块。

初学者可以这样理解：
1. user_data.json：存用户的勾选进度、AI 聊天记录等「可读写」状态。
2. samples.json：题目预置样例，程序只读，一般不在这里写回。
3. json.loads / dumps：Python 字典 ↔ JSON 文本互转。
"""

from __future__ import annotations

# 读写 JSON 字符串
import json
# 跨操作系统安全地拼路径
from pathlib import Path
# dict 的值可能是任意结构，这里用 Any 简化类型标注
from typing import Any

# 本文件所在目录 = 项目根目录（与 main.py 同级）
ROOT_DIR = Path(__file__).resolve().parent
# data 文件夹下的两个 JSON 路径
USER_DATA_PATH = ROOT_DIR / "data" / "user_data.json"
SAMPLES_PATH = ROOT_DIR / "data" / "samples.json"


def load_user_data() -> dict[str, Any]:
    """读取用户状态；文件不存在时返回空字典。"""
    # 第一次运行可能还没有文件，直接当作「没有任何记录」
    if not USER_DATA_PATH.is_file():
        return {}
    # 整个文件读成一个大字符串
    text = USER_DATA_PATH.read_text(encoding="utf-8")
    # 空文件或只有空格：当作空数据，避免 json.loads 报错
    if not text.strip():
        return {}
    # 把 JSON 解析成 Python 的 dict（里面可以再嵌套 list、dict）
    return json.loads(text)


def save_user_data(data: dict[str, Any]) -> None:
    """写入用户状态（覆盖写入）。"""
    # parents=True：若 data 文件夹不存在则逐级创建；exist_ok=True：已存在不报错
    USER_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    # dumps：字典 → 字符串；ensure_ascii=False 保留中文；indent=2 便于人用记事本查看
    USER_DATA_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_samples() -> dict[str, Any]:
    """读取预置样例库；文件不存在或损坏时返回空字典。"""
    if not SAMPLES_PATH.is_file():
        return {}
    try:
        text = SAMPLES_PATH.read_text(encoding="utf-8")
        if not text.strip():
            return {}
        return json.loads(text)
    # JSON 格式坏了，或读文件权限失败：宁可返回空字典也不要让程序崩溃
    except (json.JSONDecodeError, OSError):
        return {}


def ensure_task_slot(data: dict[str, Any], version_id: str, task_id: str) -> dict[str, Any]:
    """保证嵌套路径存在，返回 task 对应字典。"""
    # setdefault：若还没有 version_id 这个键，就先设为 {}，并返回该键的值
    data.setdefault(version_id, {})
    # 同理：保证 version_id 下有 task_id，默认是一条「任务记录」模板
    data[version_id].setdefault(
        task_id,
        {"completed": False, "coach_history": []},
    )
    # 返回「当前任务」那一小段字典，调用方可以直接改 coach_history 再 save_user_data
    return data[version_id][task_id]
