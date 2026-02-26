from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_CONFLICT_START = re.compile(r"^<{7} ", re.MULTILINE)


@dataclass
class ConflictBlock:
    ours_label: str
    ours: str
    theirs_label: str
    theirs: str
    start: int  # 1-indexed line number of the opening marker
    end: int    # 1-indexed line number of the closing marker
    raw: str    # exact bytes from the file — used for in-place replacement


def parse_conflicts(content: str) -> list[ConflictBlock]:
    """Return every conflict block found in *content*."""
    conflicts: list[ConflictBlock] = []
    lines = content.splitlines(keepends=True)

    i = 0
    while i < len(lines):
        line = lines[i]

        if not line.startswith("<<<<<<<"):
            i += 1
            continue

        start_line = i + 1
        ours_label = line[8:].rstrip("\r\n")
        block_lines = [line]

        # Collect "ours" side
        ours_lines: list[str] = []
        i += 1
        while i < len(lines) and not lines[i].startswith("======="):
            ours_lines.append(lines[i])
            block_lines.append(lines[i])
            i += 1

        if i >= len(lines):
            break

        block_lines.append(lines[i])  # separator line
        i += 1

        # Collect "theirs" side
        theirs_lines: list[str] = []
        while i < len(lines) and not lines[i].startswith(">>>>>>>"):
            theirs_lines.append(lines[i])
            block_lines.append(lines[i])
            i += 1

        if i >= len(lines):
            break

        theirs_label = lines[i][8:].rstrip("\r\n")
        block_lines.append(lines[i])
        end_line = i + 1

        conflicts.append(
            ConflictBlock(
                ours_label=ours_label,
                ours="".join(ours_lines),
                theirs_label=theirs_label,
                theirs="".join(theirs_lines),
                start=start_line,
                end=end_line,
                raw="".join(block_lines),
            )
        )

        i += 1

    return conflicts


def has_conflicts(path: Path) -> bool:
    """Return True if *path* contains Git conflict markers."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return bool(_CONFLICT_START.search(content))
    except OSError:
        return False
