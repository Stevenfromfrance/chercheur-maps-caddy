# -*- coding: utf-8 -*-
"""Diff chaque fichier DaVinci 1-DTC vs ORI FLS → catalogue CSV + MD (même méthode Caddy)."""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

ORI = Path(__file__).with_name("ORI_FLS.fls")
DTC_DIR = Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off")
OUT_CSV = Path(__file__).with_name("DTC_OFF_catalog.csv")
OUT_MD = Path(__file__).with_name("DTC_OFF_catalog.md")

CODE_RE = re.compile(r"DTC\s+([PU][0-9A-Fa-f]{4})", re.I)


def regions(a: bytes, b: bytes, merge_gap: int = 8) -> list[tuple[int, int]]:
    diffs = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    if not diffs:
        return []
    regs: list[tuple[int, int]] = []
    s = e = diffs[0]
    for i in diffs[1:]:
        if i <= e + merge_gap:
            e = i
        else:
            regs.append((s, e + 1))
            s = e = i
    regs.append((s, e + 1))
    return regs


def hexdump(data: bytes, max_len: int = 32) -> str:
    chunk = data[:max_len]
    h = chunk.hex()
    spaced = " ".join(h[i : i + 2] for i in range(0, len(h), 2))
    if len(data) > max_len:
        spaced += " …"
    return spaced


ori = ORI.read_bytes()
n = len(ori)
assert n == 2_097_152, n

rows: list[dict] = []
md_lines: list[str] = [
    "# DTC OFF — A5 EDC17CP14 516657 / 0008",
    "",
    f"ORI: `{ORI}` ({n} bytes)",
    f"Source: `{DTC_DIR}`",
    "",
    "| DTC | Octets changés | Régions | Première zone |",
    "|-----|---------------:|--------:|---------------|",
]

files = sorted(
    p
    for p in DTC_DIR.iterdir()
    if p.is_file() and p.suffix.lower() in {".bin", ".fls", ".ols"}
)
files = [p for p in files if p.read_bytes() != ori]

if not files:
    print("Aucun fichier DaVinci 1-DTC dans:")
    print(f"  {DTC_DIR}")
    print("Dans DaVinci: 1 code → Save as dans ce dossier → suivant.")
    raise SystemExit(0)

for path in files:
    m = CODE_RE.search(path.name)
    code = m.group(1).upper() if m else path.stem[:24]
    data = path.read_bytes()
    if len(data) != n:
        md_lines.append(f"| {code} | ERR size {len(data)} | - | `{path.name}` |")
        continue

    regs = regions(ori, data)
    total = sum(e - s for s, e in regs)
    md_lines.append(
        f"| **{code}** | {total} | {len(regs)} | "
        + (f"`0x{regs[0][0]:06X}`–`0x{regs[0][1]-1:06X}`" if regs else "*(aucun)*")
        + " |"
    )
    md_lines.append("")
    md_lines.append(f"## {code}")
    md_lines.append("")
    md_lines.append(f"Fichier: `{path.name}`")
    md_lines.append("")
    if not regs:
        md_lines.append("Aucun octet différent de l'ORI.")
        md_lines.append("")
        continue

    md_lines.append("| # | Start | End | Size | ORI | MOD |")
    md_lines.append("|--:|------:|----:|-----:|-----|-----|")
    for i, (s, e) in enumerate(regs, 1):
        o = ori[s:e]
        d = data[s:e]
        rows.append(
            {
                "dtc": code,
                "region_i": i,
                "start": f"0x{s:06X}",
                "end": f"0x{e-1:06X}",
                "size": e - s,
                "ori_hex": o.hex(),
                "mod_hex": d.hex(),
                "file": path.name,
            }
        )
        md_lines.append(
            f"| {i} | `0x{s:06X}` | `0x{e-1:06X}` | {e - s} | "
            f"`{hexdump(o)}` | `{hexdump(d)}` |"
        )
    md_lines.append("")

with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(
        f,
        fieldnames=["dtc", "region_i", "start", "end", "size", "ori_hex", "mod_hex", "file"],
    )
    w.writeheader()
    w.writerows(rows)

OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
print(f"files={len(files)} regions={len(rows)}")
print(f"CSV={OUT_CSV}")
print(f"MD={OUT_MD}")

by = defaultdict(list)
for r in rows:
    by[r["dtc"]].append(r)
for code in sorted(by):
    rs = by[code]
    total = sum(int(r["size"]) for r in rs)
    starts = ", ".join(r["start"] for r in rs[:4])
    more = f" (+{len(rs) - 4})" if len(rs) > 4 else ""
    print(f"{code}: {total} B in {len(rs)} region(s) @ {starts}{more}")
