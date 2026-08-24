# -*- coding: utf-8 -*-
"""SOFT/RACE pedal-combo plan: AccPed sites, caves, RAM gaps. Offline, no patch.

    python map-finder/ghidra/plan_map_switch_combo.py
"""
from __future__ import annotations

import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import (  # noqa: E402
    CAL0,
    FLASH80,
    HUBS,
    emulate_site,
    find_calls,
    is32,
)
from trace_ram_writers import BIN, find_lea_abs  # noqa: E402
from trace_rail_to_end import dump_ann  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "reports" / "map-switch-combo-scan.txt"

# AccPed family tiles (Golf 9980 Ghidra). 8x16 u16 = 256 B each.
ACCPED_TILES = (
    0x1CFFC0,  # main wish @ 800CC4AA
    0x1CFAC0,
    0x1CFBC0,
    0x1CFCC0,
    0x1CFDC0,
    0x1CFEC0,
    0x1D0640,
)
# Interior pointers used by some hubs (tile+0x24).
ACCPED_PTRS = set()
for t in ACCPED_TILES:
    ACCPED_PTRS.add(0xA0000000 + t)
    ACCPED_PTRS.add(0xA0000000 + t + 0x24)

RACE_HOLE = 0x1CB064  # ~3.4 KB FF in cal


def code_caves(code: bytes, min_len: int = 64) -> list[tuple[int, int, int]]:
    region = code[0x20000:CAL0]
    caves = []
    i = 0
    while i < len(region):
        b = region[i]
        if b in (0x00, 0xFF):
            j = i
            while j < len(region) and region[j] == b:
                j += 1
            n = j - i
            if n >= min_len:
                caves.append((FLASH80 + 0x20000 + i, n, b))
            i = j
        else:
            i += 1
    return caves


def cal_ff_holes(code: bytes, min_len: int = 256) -> list[tuple[int, int]]:
    cal = code[0x180000:0x200000]
    holes = []
    i = 0
    while i < len(cal):
        if cal[i] == 0xFF:
            j = i
            while j < len(cal) and cal[j] == 0xFF:
                j += 1
            n = j - i
            if n >= min_len:
                holes.append((0x180000 + i, n))
            i = j
        else:
            i += 1
    return holes


def collect_lea_abs_ram(code: bytes) -> set[int]:
    """All lea-ABS destinations in D000xxxx (one pass)."""
    hit: set[int] = set()
    i = 0
    end = min(len(code), CAL0) - 3
    while i <= end:
        op = code[i]
        if is32(op):
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            if op == 0xC5 and ((h1 >> 10) & 3) == 0:
                from scan_interp_families import off18

                addr = off18(h0, h1) & 0xFFFFFFFF
                if 0xD0000000 <= addr <= 0xD001FFFF:
                    hit.add(addr)
            i += 4
        else:
            i += 2
    return hit


def accped_sites(code: bytes) -> list[tuple[int, str, int, int]]:
    rows = []
    for hub, info in HUBS.items():
        for va in find_calls(code, info["addr"]):
            emu = emulate_site(code, va)
            a4 = emu.A[4] or 0
            if a4 in ACCPED_PTRS:
                rows.append((va, hub, a4, emu.A[14] or 0))
    return rows


def main() -> None:
    code = BIN.read_bytes()
    lines: list[str] = []
    lines.append("SOFT/RACE combo scan — Golf 9980 offline")
    lines.append("bin: %s" % BIN)
    lines.append("")

    sites = accped_sites(code)
    lines.append("## AccPed interp sites (a4 in AccPed tiles)")
    lines.append("count %d" % len(sites))
    for va, hub, a4, a14 in sites:
        lines.append(
            "  %08X  %-14s  a4=%08X  a14=%08X"
            % (va, hub, a4, a14)
        )
    lines.append("")

    lines.append("## AccPed tile bytes (copy candidates)")
    for t in ACCPED_TILES:
        chunk = code[t : t + 256]
        uniq = len(set(struct.unpack("<%dH" % 128, chunk)))
        lines.append("  %06X  uniq_u16=%d  head=%s" % (t, uniq, chunk[:8].hex()))
    lines.append("")

    hole = code[RACE_HOLE : RACE_HOLE + 0xD80]
    ff = sum(1 for b in hole if b == 0xFF)
    lines.append("## RACE hole %06X" % RACE_HOLE)
    lines.append("  first 0xD80 bytes, FF=%d/%d" % (ff, len(hole)))
    lines.append("")

    caves = code_caves(code)
    lines.append("## code caves >=64 B in 0x80020000..cal")
    for va, n, b in sorted(caves, key=lambda x: -x[1])[:12]:
        lines.append("  %08X  %5d  fill=%02X" % (va, n, b))
    lines.append("")

    holes = cal_ff_holes(code)
    lines.append("## cal FF holes >=256")
    for off, n in sorted(holes, key=lambda x: -x[1])[:10]:
        lines.append("  %06X  %5d" % (off, n))
    lines.append("")

    ram_leas = collect_lea_abs_ram(code)
    lines.append("## lea ABS RAM D000-D001 count %d" % len(ram_leas))
    # gap near A946 (known used) and after interp rams
    candidates = []
    for addr in range(0xD000A948, 0xD000A970):
        if addr not in ram_leas:
            candidates.append(addr)
    lines.append("unused lea-ABS near A946: %s" % (" ".join("%04X" % (a & 0xFFFF) for a in candidates[:20]) or "(none)"))
    # 8-byte aligned gap in 0xD0003xxx unused looking
    gap_start = None
    gap_len = 0
    best: tuple[int, int] | None = None
    for addr in range(0xD0002000, 0xD0004000):
        used = addr in ram_leas or (addr - 1) in ram_leas
        if not used:
            if gap_start is None:
                gap_start = addr
                gap_len = 1
            else:
                gap_len += 1
        else:
            if gap_start is not None and gap_len >= 16:
                if best is None or gap_len > best[1]:
                    best = (gap_start, gap_len)
            gap_start = None
            gap_len = 0
    if best:
        lines.append("biggest D0002000-4000 lea-ABS gap: %08X len=%d" % best)
    lines.append("")

    # speed / APP writers (already known)
    lines.append("## proven combo inputs")
    lines.append("  APP_r   D0002198  AccPed X @ 800CC4AA")
    lines.append("  nmot    D000219A")
    lines.append("  vfzg?   D0002810  X of tqlim_speed2A @ 800A6B86 (atlas: vehicle speed km/h)")
    lines.append("  brake   NOT PROVEN (skip V1)")
    lines.append("")

    lines.append("## D0002810 writer")
    leas = find_lea_abs(code, 0xD0002810)
    for va, areg in leas:
        lines.append("  lea a%d @ %08X" % (areg, va))
        lines.extend(dump_ann(code, va, 16, 12))
    lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
