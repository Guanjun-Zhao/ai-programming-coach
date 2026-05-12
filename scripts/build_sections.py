# -*- coding: utf-8 -*-
"""Build data/versionN/sections.json from warcraft chapter + code markdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANNING_TITLE = "\u529f\u80fd\u8bbe\u8ba1"

VERSIONS: dict[str, dict[str, object]] = {
    "version1": {
        "chapter": "warcraft1_chapter.md",
        "code": "warcraft1_code.md",
        "chapter_no": 1,
    },
    "version2": {
        "chapter": "warcraft2_chapter.md",
        "code": "warcraft2_code.md",
        "chapter_no": 2,
    },
    "version3": {
        "chapter": "warcraft3_chapter.md",
        "code": "warcraft3_code.md",
        "chapter_no": 3,
    },
}


def _strip_heading_line(block: str) -> str:
    lines = block.splitlines()
    if not lines:
        return ""
    if lines[0].startswith("#"):
        lines = lines[1:]
    return "\n".join(lines).strip()


def parse_chapter(text: str) -> dict[str, str]:
    parts: dict[str, str] = {}
    current_key: str | None = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf, current_key
        if current_key is not None:
            parts[current_key] = _strip_heading_line("\n".join(buf))
        buf = []

    for line in text.splitlines():
        m2 = re.match(r"^##\s+(\d+\.\d+)\s+(.+)$", line)
        m3 = re.match(r"^###\s+(\d+\.\d+\.\d+)\s+(.+)$", line)
        if m3:
            flush()
            current_key = m3.group(1)
            buf = [line]
            continue
        if m2:
            flush()
            current_key = m2.group(1)
            buf = [line]
            continue
        if current_key is not None:
            buf.append(line)
    flush()
    return parts


def parse_heading_titles(text: str) -> tuple[dict[str, str], dict[str, str]]:
    h2: dict[str, str] = {}
    h3: dict[str, str] = {}
    for line in text.splitlines():
        m2 = re.match(r"^##\s+(\d+\.\d+)\s+(.+)$", line)
        m3 = re.match(r"^###\s+(\d+\.\d+\.\d+)\s+(.+)$", line)
        if m2:
            h2[m2.group(1)] = m2.group(2).strip()
        if m3:
            h3[m3.group(1)] = m3.group(2).strip()
    return h2, h3


def parse_intro_and_planning(text: str, chapter_no: int) -> str:
    lines = text.splitlines()
    intro: list[str] = []
    planning: list[str] = []
    mode = "intro"
    planning_heading = re.compile(rf"^##\s+{chapter_no}\.1\s+")
    next_heading = re.compile(rf"^##\s+{chapter_no}\.2\s+")
    for line in lines:
        if line.startswith("# ") and not line.startswith("##"):
            continue
        if planning_heading.match(line):
            mode = "planning"
            continue
        if next_heading.match(line):
            break
        if mode == "intro":
            if line.strip():
                intro.append(line)
        else:
            if line.strip():
                planning.append(line)
    return "\n\n".join(["\n".join(intro).strip(), "\n".join(planning).strip()]).strip()


def parse_code_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for m in re.finditer(
        r"^##\s+\S+\s+(\d+(?:\.\d+)*(?:[a-z])?)\s+.+?\n+```cpp\n(.*?)```",
        text,
        flags=re.MULTILINE | re.DOTALL,
    ):
        blocks[m.group(1)] = m.group(2).rstrip("\n")
    return blocks


def _code_sort_key(key: str) -> tuple[tuple[int, ...], str]:
    m = re.match(r"^(\d+(?:\.\d+)*)([a-z]*)$", key)
    if not m:
        return ((0,), key)
    parts = tuple(int(part) for part in m.group(1).split("."))
    return (parts, m.group(2))


def collect_code(codes: dict[str, str], section_id: str) -> str:
    keys = [
        key
        for key in codes
        if key == section_id
        or (
            key.startswith(section_id)
            and key[len(section_id) :].isalpha()
            and key[len(section_id) :].isascii()
        )
    ]
    keys.sort(key=_code_sort_key)
    return "\n\n".join(codes[key] for key in keys)


def section_id_to_task_id(section_id: str) -> str:
    return "task_" + section_id.replace(".", "_")


def leaf_description(chapter_no: int, sections: dict[str, str], section_id: str) -> str:
    if chapter_no == 1 and section_id == "1.4.1":
        return "\n\n".join(
            part
            for part in (sections.get("1.4", "").strip(), sections.get("1.4.1", "").strip())
            if part
        ).strip()
    return sections.get(section_id, "").strip()


def ordered_h2_ids(chapter_text: str, chapter_no: int) -> list[str]:
    planning_id = f"{chapter_no}.1"
    ids: list[str] = []
    for line in chapter_text.splitlines():
        m2 = re.match(rf"^##\s+({chapter_no}\.\d+)\s+", line)
        if not m2:
            continue
        h2_id = m2.group(1)
        if h2_id != planning_id:
            ids.append(h2_id)
    return ids


def child_section_ids(h2_id: str, sections: dict[str, str]) -> list[str]:
    pattern = re.compile(rf"^{re.escape(h2_id)}\.\d+$")
    return sorted(
        (key for key in sections if pattern.match(key)),
        key=lambda key: [int(part) for part in key.split(".")],
    )


def build_groups(
    chapter_text: str,
    chapter_no: int,
    sections: dict[str, str],
    h2_titles: dict[str, str],
    h3_titles: dict[str, str],
    codes: dict[str, str],
) -> list[dict]:
    groups: list[dict] = []
    for h2_id in ordered_h2_ids(chapter_text, chapter_no):
        child_ids = child_section_ids(h2_id, sections)
        leaf_ids = child_ids if child_ids else [h2_id]
        group_sections: list[dict] = []
        for section_id in leaf_ids:
            group_sections.append(
                {
                    "section_id": section_id,
                    "task_id": section_id_to_task_id(section_id),
                    "title": h3_titles.get(section_id)
                    or h2_titles.get(section_id, section_id),
                    "description": leaf_description(chapter_no, sections, section_id),
                    "code": collect_code(codes, section_id),
                }
            )
        groups.append(
            {
                "h2_id": h2_id,
                "h2_title": h2_titles[h2_id],
                "sections": group_sections,
            }
        )
    return groups


def build_spec(version_id: str) -> dict:
    cfg = VERSIONS[version_id]
    chapter_no = int(cfg["chapter_no"])
    chapter_path = ROOT / str(cfg["chapter"])
    code_path = ROOT / str(cfg["code"])
    chapter_text = chapter_path.read_text(encoding="utf-8")
    code_text = code_path.read_text(encoding="utf-8")
    sections = parse_chapter(chapter_text)
    h2_titles, h3_titles = parse_heading_titles(chapter_text)
    codes = parse_code_blocks(code_text)
    planning_id = f"{chapter_no}.1"
    return {
        "planning": {
            "section_id": planning_id,
            "task_id": section_id_to_task_id(planning_id),
            "title": PLANNING_TITLE,
            "description": parse_intro_and_planning(chapter_text, chapter_no),
            "code": "",
            "skip_code_verify": True,
            "role": "planning",
        },
        "groups": build_groups(
            chapter_text, chapter_no, sections, h2_titles, h3_titles, codes
        ),
        "debug_task_id": "task_debug",
    }


def write_version(version_id: str) -> Path:
    out_path = ROOT / "data" / version_id / "sections.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(build_spec(version_id), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build version sections.json files.")
    parser.add_argument(
        "versions",
        nargs="*",
        default=["version2", "version3"],
        choices=sorted(VERSIONS),
        metavar="VERSION",
    )
    args = parser.parse_args()
    for version_id in args.versions:
        path = write_version(version_id)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
