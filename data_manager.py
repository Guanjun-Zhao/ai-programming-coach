"""本地 JSON 持久化：user_data 读写、samples 只读。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
USER_DATA_PATH = ROOT_DIR / "data" / "user_data.json"
SAMPLES_PATH = ROOT_DIR / "data" / "samples.json"


def load_user_data() -> dict[str, Any]:
    """读取用户状态；文件不存在时返回空字典。"""
    if not USER_DATA_PATH.is_file():
        return {}
    text = USER_DATA_PATH.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)


def save_user_data(data: dict[str, Any]) -> None:
    """写入用户状态（覆盖写入）。"""
    USER_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    except (json.JSONDecodeError, OSError):
        return {}


def ensure_task_slot(data: dict[str, Any], version_id: str, task_id: str) -> dict[str, Any]:
    """保证嵌套路径存在，返回 task 对应字典。"""
    data.setdefault(version_id, {})
    data[version_id].setdefault(
        task_id,
        {"completed": False, "coach_history": []},
    )
    return data[version_id][task_id]
