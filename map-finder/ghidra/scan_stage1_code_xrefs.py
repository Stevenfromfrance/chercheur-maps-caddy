# -*- coding: utf-8 -*-
"""Offline: who consumes Stage1 HIGH maps on Golf 9980 (no Ghidra GUI).

Finds:
  1) LE 32-bit pointers in code (0x80xxxxxx and 0xA0xxxxxx)
  2) interp-hub call sites already recovered in golf9980_stage1_validated.csv
"""
from __future__ import annotations

import csv
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BIN = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
CSV = ROOT / "golf9980_stage1_validated.csv"
OUT = ROOT / "golf9980_stage1_code_xrefs.md"
CAL0 = 0x180000
FLASH80 = 0x80000000
PFLASH0 = 0xA0000000

CORE_CATS = {
    "AccPed",
    "clutch_prot",
    "tqlim",
    "smoke",
    "turbo",
    "rail",
    "duration",
    "speed_limiter",
    "egr_control",
}


def to_off(val: int) -> int:
    v = val & 0xFFFFFFFF
    if v >= PFLASH0:
        return v - PFLASH0
    if v >= FLASH80:
        return v - FLASH80
    return v


def main() -> None:
    blob = BIN.read_bytes()
    code = blob[:CAL0]

    maps: list[dict] = []
    with CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat = (row.get("category") or "").strip()
            conf = (row.get("confidence") or "").strip().lower()
            if cat not in CORE_CATS:
                continue
            winols = int(row["winols"], 16)
            length = int(row.get("atlas_length") or "0" or 0)
            if length <= 0:
                cols = int(row.get("atlas_cols") or "0" or 0)
                rows = int(row.get("atlas_rows") or "0" or 0)
                length = max(2, cols * rows * 2)
            maps.append(
                {
                    "cat": cat,
                    "conf": conf,
                    "id": row.get("id_name") or "",
                    "off": winols,
                    "len": length,
                    "hub": row.get("hub") or "",
                    "delta": row.get("delta") or "",
                    "fam": row.get("fam_label") or "",
                    "call": row.get("call_site") or "",
                    "ghidra": row.get("ghidra") or "",
                }
            )

    wanted = {m["off"] for m in maps if m["conf"] == "high"}
    ptrs: dict[int, list[int]] = defaultdict(list)
    for i in range(0, len(code) - 3, 2):
        val = struct.unpack_from("<I", code, i)[0]
        off = to_off(val)
        if off in wanted and (val >> 24) in (0x80, 0xA0):
            ptrs[off].append(FLASH80 + i)

    # Join hub call sites onto HIGH starts (inside-map hits)
    calls_by_start: dict[int, list[dict]] = defaultdict(list)
    for m in maps:
        start = m["off"] if m["conf"] == "high" and m["delta"] in ("", "0x0", "0") else None
        if start is None:
            # inside map: attribute to map_start if present, else to this off
            raw = m.get("call") or ""
            if not raw:
                continue
            parent = None
            for h in maps:
                if h["conf"] != "high":
                    continue
                if h["cat"] != m["cat"]:
                    continue
                if h["off"] <= m["off"] < h["off"] + max(h["len"], 4):
                    parent = h["off"]
                    break
            if parent is None:
                parent = m["off"]
            calls_by_start[parent].append(m)

    highs = [m for m in maps if m["conf"] == "high"]
    lines = [
        "# Golf 9980 — consommateurs Stage1 (code)",
        "",
        "Scan offline du fullflash + call-sites interp deja dans `golf9980_stage1_validated.csv`.",
        "Pointeurs code: little-endian `80xxxxxx` / `A0xxxxxx` dans `0x000000-0x180000`.",
        "",
        f"- HIGH maps scannees: **{len(highs)}**",
        f"- HIGH avec pointeur absolu dans le code: **{sum(1 for m in highs if m['off'] in ptrs)}**",
        "",
    ]

    order = [
        "clutch_prot",
        "AccPed",
        "tqlim",
        "smoke",
        "turbo",
        "rail",
        "duration",
        "speed_limiter",
        "egr_control",
    ]
    for cat in order:
        chunk = [m for m in highs if m["cat"] == cat]
        if not chunk:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |")
        lines.append("|---|---|---|---|---|")
        for m in chunk:
            p = ptrs.get(m["off"], [])
            ptxt = ", ".join(f"`{x:#010x}`" for x in p[:6]) or "—"
            if len(p) > 6:
                ptxt += f" (+{len(p) - 6})"
            cs = calls_by_start.get(m["off"], [])
            # also this row's own call if high+hub
            own = []
            if m["call"]:
                own.append(f"`{m['call']}` ({m['hub']}/{m['fam'] or '-'})")
            for c in cs:
                if c is m:
                    continue
                if c["call"]:
                    own.append(f"`{c['call']}` ({c['hub']} {c['delta']})")
            # unique
            seen = []
            for x in own:
                if x not in seen:
                    seen.append(x)
            ctxt = "<br>".join(seen[:8]) or "—"
            lines.append(
                f"| `{m['id']}` | `{m['off']:06X}` | `{m['ghidra']}` | {ptxt} | {ctxt} |"
            )
        lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"HIGH={len(highs)} with_abs_ptr={sum(1 for m in highs if m['off'] in ptrs)}")


if __name__ == "__main__":
    main()
