# -*- coding: utf-8 -*-
"""Offline: find who WRITES interp RAM cells (lea ABS + st.h), no Ghidra.

Also writes golf9980_parent_seeds.txt for KickParents.py (auto-D in Ghidra).

    python map-finder/ghidra/trace_ram_writers.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import (  # noqa: E402
    CAL0,
    FLASH80,
    HUBS,
    is32,
    off18,
    parse_movha,
)

ROOT = Path(__file__).resolve().parent
BIN = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
SEEDS_OUT = ROOT / "golf9980_parent_seeds.txt"
REPORT_OUT = ROOT / "golf9980_ram_writers.txt"

# Stage1 axes we actually follow (clutch / AccPed / smoke).
TARGETS = {
    0xD000273C: "ram_273C clutch X (launch/hardcut)",
    0xD0002754: "ram_2754 clutch Y",
    0xD0002198: "APP_r AccPed X",
    0xD000219A: "nmot",
    0xD0001D60: "ram_1D60 smoke X",
    0xD0001D62: "ram_1D62 smoke Y",
    0xD0002780: "ram_2780 SOI X (near clutch)",
    0xD0001AB8: "ram_1AB8 duration X",
}


def hint16(op: int, b1: int) -> str:
    dc, db = b1 & 0xF, b1 >> 4
    if op == 0x02:
        return "mov d%d, d%d" % (dc, db)
    if op == 0x42:
        return "add d%d, d%d" % (dc, db)
    if op == 0x52:
        return "sub d%d, d%d" % (dc, db)
    if op == 0xB4:
        return "st.h [a%d], d%d" % (db, dc)
    if op == 0x14:
        return "ld.bu d%d, [a%d]" % (dc, db)
    if op == 0x40:
        return "mov.aa a%d, a%d" % (dc, db)
    if op == 0x58:
        return "ld.w d15, [a10]+%#x" % (b1 * 4)
    if op == 0x54:
        return "st.w [a10]+%#x, d15" % (b1 * 4)
    if op == 0xD8:
        return "ld.a a15, [a10]+%#x" % (b1 * 4)
    if op == 0x82:
        return "mov d%d, #%d" % (dc, db)
    if op == 0x6E:
        return "jz"
    return "op16 %02x %02x" % (op, b1)


def hint32(code: bytes, i: int) -> str:
    op = code[i]
    h0 = struct.unpack_from("<H", code, i)[0]
    h1 = struct.unpack_from("<H", code, i + 2)[0]
    ra = (h0 >> 8) & 0xF
    rb = (h0 >> 12) & 0xF
    if op == 0x6D:
        b1, b2, b3 = code[i + 1], code[i + 2], code[i + 3]
        disp = ((b2 | (b3 << 8)) | ((b1 if b1 < 128 else b1 - 256) << 16)) * 2
        tgt = (FLASH80 + i + disp) & 0xFFFFFFFF
        name = ""
        for hn, info in HUBS.items():
            if info["addr"] == tgt:
                name = " " + hn
        return "call %#010x%s" % (tgt, name)
    if op == 0x91:
        mh = parse_movha(h0, h1)
        if mh:
            return "movh.a a%d, %#010x" % (mh[0], mh[1])
        return "movh.a"
    if op == 0xC5 and ((h1 >> 10) & 3) == 0:
        return "lea a%d, %#010x" % (ra, off18(h0, h1) & 0xFFFFFFFF)
    if op == 0x09:
        op2225 = (h1 >> 6) & 0xF
        op2627 = (h1 >> 10) & 3
        off = (h1 & 0x3F) | (((h1 >> 12) & 0xF) << 6)
        if off & 0x200:
            off -= 0x400
        kind = {
            (3, 2): "ld.hu",
            (5, 2): "st.h",
            (0, 2): "ld.w",
            (4, 2): "st.w",
        }.get((op2225, op2627), "bo")
        return "%s d%d, [a%d%+#x]" % (kind, ra, rb, off)
    if op == 0x37:
        return "extr"
    if op == 0x7F:
        return "jge/jlt"
    if op == 0x0B:
        return "min/max/sat"
    return "op32 %02x" % op


def dump_window(code: bytes, va: int, before: int = 24, after: int = 20) -> list[str]:
    lines = []
    off = va - FLASH80
    start = max(0, off - before) & ~1
    end = min(len(code), off + after)
    i = start
    while i < end:
        n = 4 if is32(code[i]) else 2
        hx = code[i : i + n].hex(" ")
        h = hint32(code, i) if n == 4 else hint16(code[i], code[i + 1])
        mark = ">>" if i == off else "  "
        lines.append("%s %08X  %-11s  %s" % (mark, FLASH80 + i, hx, h))
        i += n
    return lines


def find_lea_abs(code: bytes, target: int) -> list[tuple[int, int]]:
    """Return (va, dest_areg) for lea aR, target."""
    hits = []
    i = 0
    end = min(len(code), CAL0) - 3
    while i <= end:
        op = code[i]
        if is32(op):
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            if op == 0xC5 and ((h1 >> 10) & 3) == 0:
                addr = off18(h0, h1) & 0xFFFFFFFF
                if addr == target:
                    ra = (h0 >> 8) & 0xF
                    hits.append((FLASH80 + i, ra))
            i += 4
        else:
            i += 2
    return hits


def next_is_sth_to_areg(code: bytes, lea_off: int, areg: int) -> bool:
    """st.h [aR], * within ~20 bytes after lea (not always the next instr)."""
    j = lea_off + 4
    end = min(len(code), lea_off + 24)
    while j < end:
        op = code[j]
        n = 4 if is32(op) else 2
        if op == 0xB4 and j + 1 < len(code):
            db = code[j + 1] >> 4
            if db == areg:
                return True
        j += n
    return False


def main() -> None:
    code = BIN.read_bytes()
    seeds: dict[int, str] = {}
    report: list[str] = []
    report.append("Golf 9980 — writers RAM interp (offline, pas OEM)")
    report.append("bin: %s" % BIN)
    report.append("")

    for addr, name in TARGETS.items():
        leas = find_lea_abs(code, addr)
        writers = []
        readers = []
        for va, areg in leas:
            off = va - FLASH80
            if next_is_sth_to_areg(code, off, areg):
                writers.append((va, areg))
                seeds[va] = "WRITE %s" % name
            else:
                readers.append((va, areg))
                seeds[va] = "LEA %s" % name
        report.append("## %s  (%#010x)" % (name, addr))
        report.append("  lea ABS: %d   st.h juste apres: %d" % (len(leas), len(writers)))
        if not leas:
            report.append("  (pas de lea ABS — ptr via pile / A14)")
            report.append("")
            continue
        for va, areg in writers:
            report.append("  WRITE lea a%d @ %#010x" % (areg, va))
            report.extend(dump_window(code, va, 28, 16))
            report.append("")
        for va, areg in readers[:8]:
            report.append("  READ  lea a%d @ %#010x" % (areg, va))
        if len(readers) > 8:
            report.append("  ... +%d reads" % (len(readers) - 8))
        report.append("")

    extra = {
        0x800FB7B4: "clutch writer context (a10+0x88)",
        0x800FC2EE: "clutch sibling CALL parent",
        0x800FC314: "clutch map_interp_C",
        0x800CC4AA: "AccPed interp_2d",
        0x8008736E: "tqlim interp_2d_B",
        0x800F4A38: "smoke ram_1D60 first lea",
        0x800F4A48: "smoke ram_1D60 first st.h",
        0x800F4AFA: "smoke ram_1D62 lea",
        0x800F4B06: "smoke ram_1D62 st.h",
        0x800F4BA8: "smoke interp_2d_B",
        0x80074EBE: "duration interp_2d",
        0x800FC2C8: "SOI map_interp_C (clutch block)",
        0x800FB4CC: "SOI interp_2d ram_2780",
    }
    for va, why in extra.items():
        seeds.setdefault(va, why)

    lines = ["# VA seeds for KickParents.py (auto D)", "# generated by trace_ram_writers.py", ""]
    for va in sorted(seeds):
        lines.append("%#010x  %s" % (va, seeds[va]))
    SEEDS_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print("wrote %s" % REPORT_OUT)
    print("wrote %s (%d seeds)" % (SEEDS_OUT, len(seeds)))


if __name__ == "__main__":
    main()
