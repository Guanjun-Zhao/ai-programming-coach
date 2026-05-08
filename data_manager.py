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

# load_samples 缓存：(samples.json 的 st_mtime_ns, 解析结果)；文件变更后自动失效
_SAMPLES_FILE_CACHE: tuple[int, dict[str, Any]] | None = None


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
    """
    读取预置样例库；文件不存在或损坏时返回空字典。

    同一进程内按文件的修改时间（纳秒 mtime）缓存解析结果，避免界面反复刷新时重复读盘与 json.loads；
    保存或替换 samples.json 后 mtime 变化会重新读取。
    """
    global _SAMPLES_FILE_CACHE  # 声明后才能在函数内给模块级缓存变量赋值
    if not SAMPLES_PATH.is_file():  # Path.is_file()：路径存在且为普通文件时为 True
        _SAMPLES_FILE_CACHE = None  # 无文件则清空缓存，避免沿用上次进程内曾加载过的 dict
        return {}  # 调用方把「没有样例文件」与「空 JSON」都当成空 dict 处理
    try:
        # stat() 取文件元数据；st_mtime_ns 为上次修改时间的纳秒整数，用作缓存版本号
        mtime_ns = SAMPLES_PATH.stat().st_mtime_ns
        # 若缓存元组存在，且缓存里记录的 mtime 与磁盘当前一致，说明文件自上次解析后未改写
        if _SAMPLES_FILE_CACHE is not None and _SAMPLES_FILE_CACHE[0] == mtime_ns:
            return _SAMPLES_FILE_CACHE[1]  # 直接返回已解析好的 dict，不再读文件、不再 json.loads
        # 缓存未命中或首次加载：整文件读入 str（utf-8 与 samples.json 保存约定一致）
        text = SAMPLES_PATH.read_text(encoding="utf-8")
        if not text.strip():  # 文件只有空白或为空：等价于「空对象」，不必调用 json.loads("")
            parsed: dict[str, Any] = {}  # 显式类型标注，便于类型检查器推断分支后的 parsed 形状
        else:
            parsed = json.loads(text)  # 将 JSON 文本转为 Python dict（可嵌套 list/dict）
        _SAMPLES_FILE_CACHE = (mtime_ns, parsed)  # 记下本次 mtime 与解析结果，供下次快速命中
        return parsed  # 把内存中的样例库 dict 返回给 get_samples 等调用方
    except (json.JSONDecodeError, OSError):  # JSONDecodeError：语法错；OSError：权限、磁盘等读失败
        _SAMPLES_FILE_CACHE = None  # 解析失败不把半成品放进缓存，以免一直返回坏状态
        return {}  # 静默降级为空 dict（与文件不存在时一致），界面表现为「暂无样例配置」


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
