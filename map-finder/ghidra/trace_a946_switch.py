# -*- coding: utf-8 -*-
"""Writers / readers of D000A946 (rail B ld.bu index) + nearby bytes.

    python map-finder/ghidra/trace_a946_switch.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import CAL0, FLASH80, is32  # noqa: E402
from trace_ram_writers import BIN  # noqa: E402
from trace_rail_turbo_writers import lea_a0  # noqa: E402
from trace_rail_to_end import dump_ann  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "reports" / "map-switch-a946.md"
A0 = 0xD0010800
RAM = 0xD000A946
DISP = (RAM - A0) & 0xFFFF  # 0xA146  (signed -0x5EBA)


def is_stb_to(code: bytes, j: int, areg: int) -> bool:
    op = code[j]
    if op == 0x34:
        # st.b [A[b]], D[c]  SSR op0607=0 op0003=4 op0405=3
        db = code[j + 1] >> 4
        return db == areg
    if op == 0x2C:
        # st.b [A[b]+off4], d15
        db = code[j + 1] >> 4
        return db == areg
    if op == 0xE9:
        h0 = struct.unpack_from("<H", code, j)[0]
        rb = (h0 >> 12) & 0xF
        return rb == areg
    if op == 0x09:
        h0 = struct.unpack_from("<H", code, j)[0]
        h1 = struct.unpack_from("<H", code, j + 2)[0]
        rb = (h0 >> 12) & 0xF
        op2225 = (h1 >> 6) & 0xF
        op2627 = (h1 >> 10) & 3
        # st.b BO: op0607=2 (this is 16? 09 is BO 32-bit ld/st)
        if rb == areg and (op2225, op2627) == (0, 2):
            return True  # st.w actually (4,2)=st.w (5,2)=st.h
        if rb == areg and op0607_from(code, j) == 2 and op2225 == 0:
            return True
    return False


def op0607_from(code: bytes, j: int) -> int:
    return (code[j] >> 6) & 3


def classify_after_lea(code: bytes, lea_off: int, areg: int, window: int = 48) -> str:
    j = lea_off + 4
    end = min(len(code), lea_off + window)
    while j < end:
        op = code[j]
        n = 4 if is32(op) else 2
        if op == 0xD9:
            h0 = struct.unpack_from("<H", code, j)[0]
            if ((h0 >> 8) & 0xF) == areg:
                return "redef"
        if op == 0x14 and (code[j + 1] >> 4) == areg:
            return "ld.bu"
        if op == 0xB4 and (code[j + 1] >> 4) == areg:
            return "st.h"
        if op == 0x34 and (code[j + 1] >> 4) == areg:
            return "st.b"
        if op == 0x2C and (code[j + 1] >> 4) == areg:
            return "st.b+off"
        if op == 0x09:
            h0 = struct.unpack_from("<H", code, j)[0]
            h1 = struct.unpack_from("<H", code, j + 2)[0]
            rb = (h0 >> 12) & 0xF
            ra = (h0 >> 8) & 0xF
            op2225 = (h1 >> 6) & 0xF
            op2627 = (h1 >> 10) & 3
            if rb == areg:
                kind = {
                    (3, 2): "ld.hu",
                    (5, 2): "st.h",
                    (1, 2): "ld.b",
                    (2, 2): "ld.h",
                    (0, 2): "ld.w",
                    (4, 2): "st.w",
                }.get((op2225, op2627), "bo")
                return kind
        if op == 0xE9:
            h0 = struct.unpack_from("<H", code, j)[0]
            if ((h0 >> 12) & 0xF) == areg:
                return "st.b_bol"
        j += n
    return "none"


def main() -> None:
    code = BIN.read_bytes()
    leas = lea_a0(code, DISP if DISP < 0x8000 else struct.unpack("<h", struct.pack("<H", DISP))[0])
    # lea_a0 compares h1 == want as uint16
    leas = lea_a0(code, struct.unpack("<h", struct.pack("<H", (RAM - A0) & 0xFFFF))[0])

    counts = {}
    writes = []
    lines = [
        "# D000A946 + switch soft/RACE — 2026-08-23",
        "",
        "A0=`D0010800`. RAM=`D000A946` disp A0 `%+d` (`%#x`)."
        % (RAM - A0, (RAM - A0) & 0xFFFF),
        "",
        "Site rail B `800B5A96` : `ld.bu d5` = **index Y** de `interp_2d_B` grille `1E9BC8`.",
        "Ce n est **pas** un switch Stage1 entier (AccPed). C est un mode rail.",
        "",
        "## lea [a0+disp] : %d sites" % len(leas),
        "",
    ]
    for va, areg in leas:
        kind = classify_after_lea(code, va - FLASH80, areg)
        counts[kind] = counts.get(kind, 0) + 1
        if kind in ("st.b", "st.b+off", "st.b_bol", "st.h", "st.w"):
            writes.append((va, areg, kind))
            lines.append("### WRITE %s @ `%08X` a%d" % (kind, va, areg))
            lines.append("```")
            lines.extend(dump_ann(code, va, 24, 16))
            lines.append("```")
            lines.append("")

    lines.append("## Resume lectures vs ecritures")
    lines.append("")
    for k in sorted(counts, key=lambda x: (-counts[x], x)):
        lines.append("- `%s` : %d" % (k, counts[k]))
    lines.append("")
    lines.append("Writes stricts : **%d**" % len(writes))
    lines.append("")

    # flash flag near site B
    lines.append("## Flag flash cote site B (`A1+0x1872` = `192072`)")
    lines.append("")
    lines.append("```")
    lines.extend(dump_ann(code, 0x800B5A6C, 8, 20))
    lines.append("```")
    lines.append("")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("leas", len(leas), "counts", counts, "writes", len(writes))
    for va, areg, kind in writes[:12]:
        print("WRITE", kind, hex(va), "a%d" % areg)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
