# -*- coding: utf-8 -*-
"""Go to the end: FUN_8004d15c + E6E8 d2 (division) until flash/sensor.

    python map-finder/ghidra/trace_rail_to_end.py
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
    find_calls,
    is32,
    off16_bol,
    parse_movha,
    sx,
)
from trace_ram_writers import BIN  # noqa: E402
from trace_turbo_rail import dump, hint as hint0  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "reports" / "rail-to-the-end.md"
A0 = 0xD0010800
A1 = 0xA0190800
FN = 0x8004D15C
E6 = 0x80080FE4


def hint(code: bytes, i: int) -> str:
    op = code[i]
    if op == 0x00 and i + 1 < len(code) and code[i + 1] == 0x90:
        return "ret"
    if op == 0xFC:
        return "loop a%d" % (code[i + 1] >> 4)
    if op == 0x4B:
        h0 = struct.unpack_from("<H", code, i)[0]
        h1 = struct.unpack_from("<H", code, i + 2)[0]
        da, db = (h0 >> 8) & 0xF, (h0 >> 12) & 0xF
        dc = (h1 >> 12) & 0xF
        aux = h1 & 0xFFF
        if aux == 0xA0:
            return "dvinit.u E%d, d%d, d%d" % (dc, da, db)
        if aux == 0x201:
            return "div E%d, d%d, d%d" % (dc, da, db)
        if aux == 0x211:
            return "div.u E%d, d%d, d%d" % (dc, da, db)
        if aux == 0x41:
            return "mul.f d%d, d%d, d%d" % (dc, da, db)
        return "op4b d%d,d%d ->E/d%d aux=%#x" % (da, db, dc, aux)
    if op == 0x6B:
        h0 = struct.unpack_from("<H", code, i)[0]
        h1 = struct.unpack_from("<H", code, i + 2)[0]
        db = (h0 >> 12) & 0xF
        dc = (h1 >> 12) & 0xF
        aux = h1 & 0xFFF
        return "dvstep/op6b E%d ... d%d aux=%#x" % (dc, db, aux)
    if op == 0x0B:
        return "min/max/sat " + hint0(code, i)[5:]
    h = hint0(code, i)
    if h.startswith("lea a") and "[a0" in h:
        # annotate A0-relative
        pass
    return h


def dump2(code: bytes, va: int, before: int, after: int) -> list[str]:
    off = va - FLASH80
    start = max(0, off - before) & ~1
    end = min(len(code), off + after)
    lines, i = [], start
    while i < end:
        n = 4 if is32(code[i]) else 2
        mark = ">>" if i == off else "  "
        lines.append(
            "%s %08X  %-11s  %s" % (mark, FLASH80 + i, code[i : i + n].hex(" "), hint(code, i))
        )
        i += n
    return lines


def fn_end(code: bytes, va: int, limit: int = 0x200) -> int:
    off = va - FLASH80
    i = off
    end = min(len(code), off + limit)
    while i < end:
        if code[i] == 0x00 and i + 1 < len(code) and code[i + 1] == 0x90:
            return FLASH80 + i
        i += 4 if is32(code[i]) else 2
    return FLASH80 + end


def fn_start(code: bytes, va: int, limit: int = 0x300) -> int:
    """Walk back to previous ret, next instr is start (approx)."""
    off = va - FLASH80
    i = max(0, off - limit) & ~1
    last_ret = None
    while i < off:
        n = 4 if is32(code[i]) else 2
        if n == 2 and code[i] == 0x00 and code[i + 1] == 0x90:
            last_ret = i
        i += n
    if last_ret is None:
        return va - limit
    return FLASH80 + last_ret + 2


def a0_abs(disp: int) -> int:
    return (A0 + disp) & 0xFFFFFFFF


def annotate_lea(h: str) -> str:
    # lea aN, [a0+0xHEX]
    import re

    m = re.search(r"lea a(\d+), \[a0([+-])0x([0-9a-fA-F]+)\]", h)
    if not m:
        m = re.search(r"lea a(\d+), \[a1([+-])0x([0-9a-fA-F]+)\]", h)
        if m:
            sign = 1 if m.group(2) == "+" else -1
            disp = sign * int(m.group(3), 16)
            addr = (A1 + disp) & 0xFFFFFFFF
            return h + "  ; %08X winols %06X" % (addr, addr & 0xFFFFFF)
        return h
    sign = 1 if m.group(2) == "+" else -1
    disp = sign * int(m.group(3), 16)
    addr = a0_abs(disp)
    return h + "  ; ram %08X" % addr


def dump_ann(code: bytes, va: int, before: int, after: int) -> list[str]:
    lines = []
    for line in dump2(code, va, before, after):
        # split hint part
        if "  " in line:
            pre, h = line[:22], line[22:].lstrip()
            # actually format is ">> VA  bytes  hint"
            parts = line.split("  ", 2)
            if len(parts) >= 3:
                lines.append(parts[0] + "  " + parts[1] + "  " + annotate_lea(parts[2].strip()))
            else:
                lines.append(line)
        else:
            lines.append(line)
    return lines


def main() -> None:
    """Dump helpers only. The verdict lives in reports/rail-to-the-end.md (do not clobber)."""
    code = BIN.read_bytes()
    callers = find_calls(code, FN)
    end = fn_end(code, FN, 0x180)
    st = fn_start(code, E6, 0x280)
    sys.stdout.reconfigure(encoding="utf-8")
    print("FUN_8004d15c callers", len(callers), "ret", hex(end), "len", hex(end - FN))
    print("E6E8 fn start", hex(st))
    print("hand-written report:", OUT)
    print("--- FUN_8004d15c ---")
    print("\n".join(dump_ann(code, FN, 0, end - FN + 4)))
    print("--- FUN_80080f4c ---")
    print("\n".join(dump_ann(code, st, 0, 0xA0)))


if __name__ == "__main__":
    main()
