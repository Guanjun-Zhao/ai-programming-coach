"""
本地 JSON 持久化模块。

初学者可以这样理解：
1. user_data.json：存用户的勾选进度、AI 聊天记录等「可读写」状态。
2. samples.json：题目预置样例，程序只读，一般不在这里写回。
3. json.loads / dumps：Python 字典 ↔ JSON 文本互转。

类型标注：`from __future__ import annotations` 让 `dict[str, Any]` 等写法在运行时延后求值，
避免类型名与类定义顺序纠缠；不写也不影响程序运行。
"""

# 推迟解析类型注解，便于写 dict[str, Any] 等而不必顾虑书写顺序（详见模块 docstring）
from __future__ import annotations

import json  # 标准库：loads/dumps，把 dict/list 与 JSON 文本互转
from pathlib import Path  # 路径对象：拼 data/*.json、判断是否存在；比字符串拼接更安全可读
from typing import Any  # 标注「任意 JSON 兼容值」；本文件多处 dict[str, Any] 表示嵌套用户数据结构

# 本文件所在目录 = 项目根目录（与 main.py 同级）
ROOT_DIR = Path(__file__).resolve().parent
# data 文件夹下的两个 JSON 路径
USER_DATA_PATH = ROOT_DIR / "data" / "user_data.json"
SAMPLES_PATH = ROOT_DIR / "data" / "samples.json"


def load_user_data() -> dict[str, Any]:
    """
    读取用户状态；文件不存在或为空时返回空字典。

    注意：若文件存在但内容不是合法 JSON，`json.loads` 会抛出异常（程序会退出）。
    这与 load_samples（损坏时返回 {}）故意不同：用户数据损坏时应人工修复文件，
    而不是静默当成「无数据」。若你希望两者行为一致，需在代码层外加 try（属行为变更）。
    """
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
    """
    写入用户状态。

    write_text 会整文件覆盖：磁盘上旧 JSON 会被本次内容完全替换（不是追加补丁）。
    """
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
    except (json.JSONDecodeError, OSError):
        return {}


def ensure_task_slot(data: dict[str, Any], version_id: str, task_id: str) -> dict[str, Any]:
    """
    保证嵌套路径存在，返回「当前任务」对应的那一小段字典。

    `data` 会被就地修改（不是拷贝一份新字典）：缺少的键会用 setdefault 补上。

    持久化后的形状示意（与 MODULE_INTERFACES.md 一致）::

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
    """
    # setdefault：若还没有 version_id 这个键，就先设为 {}，并返回该键的值（就地写入 data）
    data.setdefault(version_id, {})
    # 同理：保证 version_id 下有 task_id，默认是一条「任务记录」模板
    data[version_id].setdefault(
        task_id,
        {"completed": False, "coach_history": []},
    )
    # 返回「当前任务」那一小段字典，调用方可以直接改 coach_history 再 save_user_data
    return data[version_id][task_id]
