"""
Per-version persistence under data/versionN/: state.json, code.cpp, history/*.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
SAMPLES_PATH = ROOT_DIR / "data" / "samples.json"
APP_SETTINGS_PATH = ROOT_DIR / "data" / "app_settings.json"
DEFAULT_APP_MODEL = "deepseek-v4-flash"

_SAMPLES_FILE_CACHE: tuple[int, dict[str, Any]] | None = None
_VERSION_SAMPLES_CACHE: dict[str, tuple[int, list[dict[str, Any]]]] = {}


def load_app_settings() -> dict[str, str]:
    defaults = {"api_key": "", "model": DEFAULT_APP_MODEL}
    path = APP_SETTINGS_PATH
    if not path.is_file():
        return defaults
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return defaults
        raw = json.loads(text)
        if not isinstance(raw, dict):
            return defaults
        api_key = raw.get("api_key", "")
        model = raw.get("model", DEFAULT_APP_MODEL)
        return {
            "api_key": api_key if isinstance(api_key, str) else "",
            "model": model if isinstance(model, str) and model.strip() else DEFAULT_APP_MODEL,
        }
    except (json.JSONDecodeError, OSError):
        return defaults


def save_app_settings(settings: dict[str, str]) -> None:
    model = settings.get("model", DEFAULT_APP_MODEL)
    if not isinstance(model, str) or not model.strip():
        model = DEFAULT_APP_MODEL
    api_key = settings.get("api_key", "")
    if not isinstance(api_key, str):
        api_key = ""
    payload = {"api_key": api_key, "model": model.strip()}
    APP_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    APP_SETTINGS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def version_dir(version_id: str) -> Path:
    return ROOT_DIR / "data" / version_id


def version_state_path(version_id: str) -> Path:
    return version_dir(version_id) / "state.json"


def version_code_path(version_id: str) -> Path:
    return version_dir(version_id) / "code.cpp"


def version_history_dir(version_id: str) -> Path:
    return version_dir(version_id) / "history"


def version_samples_path(version_id: str) -> Path:
    return version_dir(version_id) / "samples.json"


def history_filename(task_id: str) -> str:
    if task_id == "task_debug":
        return "debug.json"
    return f"{task_id}.json"


def history_path(version_id: str, task_id: str) -> Path:
    return version_history_dir(version_id) / history_filename(task_id)


def load_version_state(version_id: str) -> dict[str, Any]:
    path = version_state_path(version_id)
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    return json.loads(text)


def save_version_state(version_id: str, state: dict[str, Any]) -> None:
    path = version_state_path(version_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ensure_tree_state(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("_tree", {"h2_expanded": {}, "h2_completed": {}})
    tree = state["_tree"]
    tree.setdefault("h2_expanded", {})
    tree.setdefault("h2_completed", {})
    return tree


def ensure_task_state(state: dict[str, Any], task_id: str) -> dict[str, Any]:
    state.setdefault(task_id, {"completed": False})
    slot = state[task_id]
    slot.setdefault("completed", False)
    if task_id == "task_debug":
        slot.setdefault("current_sample_index", 0)
    return slot


def load_task_history(version_id: str, task_id: str) -> list[dict[str, Any]]:
    path = history_path(version_id, task_id)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return []
        raw = json.loads(text)
        if not isinstance(raw, list):
            return []
        return [
            m
            for m in raw
            if isinstance(m, dict)
            and m.get("role") in ("user", "assistant")
            and isinstance(m.get("content"), str)
        ]
    except (json.JSONDecodeError, OSError):
        return []


def save_task_history(
    version_id: str, task_id: str, messages: list[dict[str, Any]]
) -> None:
    path = history_path(version_id, task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(messages, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_task_history(version_id: str, task_id: str) -> None:
    path = history_path(version_id, task_id)
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


def load_version_code(version_id: str) -> str:
    path = version_code_path(version_id)
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def save_version_code(version_id: str, text: str) -> None:
    path = version_code_path(version_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_program_output(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return ""
    return "\n".join(line.rstrip() for line in normalized.split("\n"))


def load_samples() -> dict[str, Any]:
    global _SAMPLES_FILE_CACHE
    if not SAMPLES_PATH.is_file():
        _SAMPLES_FILE_CACHE = None
        return {}
    try:
        mtime_ns = SAMPLES_PATH.stat().st_mtime_ns
        if _SAMPLES_FILE_CACHE is not None and _SAMPLES_FILE_CACHE[0] == mtime_ns:
            return _SAMPLES_FILE_CACHE[1]
        text = SAMPLES_PATH.read_text(encoding="utf-8")
        if not text.strip():
            parsed: dict[str, Any] = {}
        else:
            parsed = json.loads(text)
        _SAMPLES_FILE_CACHE = (mtime_ns, parsed)
        return parsed
    except (json.JSONDecodeError, OSError):
        _SAMPLES_FILE_CACHE = None
        return {}


def load_version_samples(version_id: str) -> list[dict[str, Any]]:
    global _VERSION_SAMPLES_CACHE
    path = version_samples_path(version_id)
    if not path.is_file():
        _VERSION_SAMPLES_CACHE.pop(version_id, None)
        return []
    try:
        mtime_ns = path.stat().st_mtime_ns
        cached = _VERSION_SAMPLES_CACHE.get(version_id)
        if cached is not None and cached[0] == mtime_ns:
            return cached[1]
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            parsed: list[dict[str, Any]] = []
        else:
            raw = json.loads(text)
            if not isinstance(raw, list):
                parsed = []
            else:
                parsed = [x for x in raw if isinstance(x, dict)]
        _VERSION_SAMPLES_CACHE[version_id] = (mtime_ns, parsed)
        return parsed
    except (json.JSONDecodeError, OSError):
        _VERSION_SAMPLES_CACHE.pop(version_id, None)
        return []
