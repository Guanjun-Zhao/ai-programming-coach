# -*- coding: utf-8 -*-
"""Thin wrapper: build data/version1/sections.json."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_sections import write_version


def main() -> None:
    path = write_version("version1")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
