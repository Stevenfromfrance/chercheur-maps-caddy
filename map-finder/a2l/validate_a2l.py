# -*- coding: utf-8 -*-
"""Quick A2L syntax checker for WinOLS compatibility issues."""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

A2L = Path(__file__).resolve().parent / "PCR21_Golf9980_REVERSE.a2l"
GOOD = Path(__file__).resolve().parents[1] / "ghidra" / "golf9980_interp_families_HIGH.a2l"


def analyze(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    print(f"\n=== {path.name} ({len(text)} bytes, {len(lines)} lines) ===")

    begins = re.findall(r"/begin\s+(\w+)", text)
    ends = re.findall(r"/end\s+(\w+)", text)
    cb, ce = Counter(begins), Counter(ends)
    for k in sorted(set(cb) | set(ce)):
        d = cb[k] - ce[k]
        if d:
            print(f"  BLOCK IMBALANCE {k}: begin={cb[k]} end={ce[k]} diff={d}")

    issues: list[str] = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith("/*") or s.startswith("*") or s.endswith("*/"):
            continue
        # non-ascii outside comments
        if re.search(r"[^\x00-\x7F]", line):
            issues.append(f"L{i}: non-ASCII: {line[:100]!r}")
        if "PROJECT_NO" in line and not re.search(r'PROJECT_NO\s+"', line):
            issues.append(f"L{i}: PROJECT_NO unquoted: {s}")
        if "FIX_AXIS_PAR" in line:
            issues.append(f"L{i}: FIX_AXIS_PAR (often invalid): {s}")
        if "AXIS_PTS_X" in line:
            issues.append(f"L{i}: AXIS_PTS_X in RECORD_LAYOUT: {s}")
        if re.search(r"RL_AXIS\b", line):
            issues.append(f"L{i}: RL_AXIS ref: {s[:90]}")
        if re.search(r"/begin CHARACTERISTIC.*\bMAP\b.*0 65535", line):
            issues.append(f"L{i}: CHAR extra min/max: {s[:100]}")
        if re.search(r"/begin MEASUREMENT.*65535", line):
            issues.append(f"L{i}: MEAS extra min/max: {s[:100]}")
        if re.search(r'FORMAT "%5\.0"', line):
            issues.append(f"L{i}: FORMAT missing %% escape: {s}")
        if s.count('"') % 2 == 1 and "/begin" in s:
            issues.append(f"L{i}: odd quotes: {s[:120]}")

    # duplicate identifiers
    chars = re.findall(r"/begin CHARACTERISTIC (\w+)", text)
    axes = re.findall(r"/begin AXIS_PTS (\w+)", text)
    meas = re.findall(r"/begin MEASUREMENT (\w+)", text)
    for label, names in [("CHAR", chars), ("AXIS", axes), ("MEAS", meas)]:
        c = Counter(names)
        dups = [n for n, v in c.items() if v > 1]
        if dups:
            issues.append(f"DUPLICATE {label}: {dups[:5]}")

    print(f"  issues found: {len(issues)}")
    for x in issues[:60]:
        print(f"    {x}")
    if len(issues) > 60:
        print(f"    ... +{len(issues)-60} more")


def main() -> None:
    paths = [
        Path(r"C:\Users\theda\ghidra_scripts\PCR21_Golf9980_REVERSE.a2l"),
        A2L,
        GOOD,
    ]
    for p in paths:
        if p.exists():
            try:
                analyze(p)
            except PermissionError:
                print(f"LOCKED {p}")
        else:
            print(f"MISSING {p}")


if __name__ == "__main__":
    main()
