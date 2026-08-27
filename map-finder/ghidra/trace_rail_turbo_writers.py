# -*- coding: utf-8 -*-
"""Writers: rail D000B6AE / D000E6E8 + turbo table D0011D74.

    python map-finder/ghidra/trace_rail_turbo_writers.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import CAL0, FLASH80, is32, off16_bol, parse_movha  # noqa: E402
from trace_ram_writers import BIN, find_lea_abs, next_is_sth_to_areg  # noqa: E402
from trace_turbo_rail import dump, hint  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "reports" / "rail-turbo-writers.md"
A0 = 0xD0010800

TARGETS = [
    (0xD000B6AE, "rail X (site 2d d4)", -0x5152),
    (0xD000E6E8, "rail Y / partage (d5 2d, d4 D)", -0x2118),
    (0xD0011D74, "turbo table base (SP+4)", 0x1574),
]


def store_to_areg(code: bytes, lea_off: int, areg: int, window: int = 40) -> list[str]:
    hits = []
    j = lea_off + 4
    end = min(len(code), lea_off + window)
    while j < end:
        op = code[j]
        n = 4 if is32(op) else 2
        h = hint(code, j)
        # st.h [aR],  st.w, st.b, st.h BOL
        if op == 0xB4 and (code[j + 1] >> 4) == areg:
            hits.append(h)
        elif op == 0xF9:
            rb = (struct.unpack_from("<H", code, j)[0] >> 12) & 0xF
            if rb == areg:
                hits.append(h)
        elif op == 0x09:
            h0 = struct.unpack_from("<H", code, j)[0]
            h1 = struct.unpack_from("<H", code, j + 2)[0]
            rb = (h0 >> 12) & 0xF
            op2225 = (h1 >> 6) & 0xF
            op2627 = (h1 >> 10) & 3
            if rb == areg and (op2225, op2627) in ((5, 2), (4, 2)):
                hits.append(h)
        j += n
    return hits


def lea_a0(code: bytes, disp: int) -> list[tuple[int, int]]:
    """lea aR, [a0+disp]  op D9 rb=0 off16=disp."""
    want = disp & 0xFFFF
    hits = []
    i = 0
    end = min(len(code), CAL0) - 3
    while i <= end:
        if code[i] == 0xD9:
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            rb = (h0 >> 12) & 0xF
            if rb == 0 and (h1 & 0xFFFF) == want:
                ra = (h0 >> 8) & 0xF
                hits.append((FLASH80 + i, ra))
            i += 4
        else:
            i += 4 if is32(code[i]) else 2
    return hits


def sth_a0_bol(code: bytes, disp: int) -> list[int]:
    """st.h [a0+disp], dR   op F9 rb=0."""
    want = disp & 0xFFFF
    hits = []
    i = 0
    end = min(len(code), CAL0) - 3
    while i <= end:
        if code[i] == 0xF9:
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            rb = (h0 >> 12) & 0xF
            if rb == 0 and (h1 & 0xFFFF) == want:
                hits.append(FLASH80 + i)
            i += 4
        else:
            i += 4 if is32(code[i]) else 2
    return hits


def sth_bo_a0(code: bytes, disp: int) -> list[int]:
    """st.h [a0+off10], *  op 09, rb=0, off10=disp (if fits)."""
    hits = []
    i = 0
    end = min(len(code), CAL0) - 3
    while i <= end:
        if code[i] == 0x09:
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            rb = (h0 >> 12) & 0xF
            op2225 = (h1 >> 6) & 0xF
            op2627 = (h1 >> 10) & 3
            if rb == 0 and (op2225, op2627) == (5, 2):
                from scan_interp_families import off10_bo

                if off10_bo(h1) == disp:
                    hits.append(FLASH80 + i)
            i += 4
        else:
            i += 4 if is32(code[i]) else 2
    return hits


def movha_lea(code: bytes, target: int) -> list[tuple[int, int]]:
    hits = []
    last: dict[int, int] = {}
    i = 0
    end = min(len(code), CAL0) - 7
    while i <= end:
        op = code[i]
        n = 4 if is32(op) else 2
        if n == 4:
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            if op == 0x91:
                mh = parse_movha(h0, h1)
                if mh:
                    last[mh[0]] = mh[1]
            elif op == 0xD9:
                ra = (h0 >> 8) & 0xF
                rb = (h0 >> 12) & 0xF
                base = last.get(rb)
                if base is not None and ((base + off16_bol(h1)) & 0xFFFFFFFF) == target:
                    hits.append((FLASH80 + i, ra))
        i += n
    return hits


def section(code: bytes, addr: int, name: str, disp: int) -> list[str]:
    lines = ["## `%08X`  %s" % (addr, name), ""]
    lines.append("disp vs A0 : `%+d` (`%04X`)" % (disp, disp & 0xFFFF))
    lines.append("")

    abs_leas = find_lea_abs(code, addr)
    lines.append("lea ABS : **%d**" % len(abs_leas))
    for va, areg in abs_leas:
        wr = next_is_sth_to_areg(code, va - FLASH80, areg)
        more = store_to_areg(code, va - FLASH80, areg, 48)
        tag = "WRITE" if wr or more else "read"
        lines.append("- `%08X` lea a%d  [%s] %s" % (va, areg, tag, more or ""))
        if wr or more:
            lines.append("```")
            lines.extend(dump(code, va, 28, 16))
            lines.append("```")

    a0s = lea_a0(code, disp)
    lines.append("lea [a0%+#x] : **%d**" % (disp, len(a0s)))
    writes = 0
    for va, areg in a0s:
        more = store_to_areg(code, va - FLASH80, areg, 48)
        if more:
            writes += 1
            lines.append("- **WRITE** `%08X` lea a%d  puis %s" % (va, areg, more))
            lines.append("```")
            lines.extend(dump(code, va, 32, 20))
            lines.append("```")
    if writes == 0:
        lines.append("- aucun `st.h/st.w` dans les 48 o (lectures seules, comme les call-sites rail)")

    bol = sth_a0_bol(code, disp)
    lines.append("st.h BOL [a0%+#x] : **%d**" % (disp, len(bol)))
    for va in bol[:8]:
        lines.append("```")
        lines.extend(dump(code, va, 24, 12))
        lines.append("```")

    bo = sth_bo_a0(code, disp)
    lines.append("st.h BO [a0%+#x] : **%d**" % (disp, len(bo)))
    for va in bo[:6]:
        lines.append("```")
        lines.extend(dump(code, va, 20, 10))
        lines.append("```")

    ml = movha_lea(code, addr)
    lines.append("movh.a+lea → cible : **%d**" % len(ml))
    for va, areg in ml[:8]:
        more = store_to_areg(code, va - FLASH80, areg, 48)
        lines.append("- `%08X` a%d  store=%s" % (va, areg, more or "non"))
        if more:
            lines.append("```")
            lines.extend(dump(code, va, 24, 16))
            lines.append("```")
    lines.append("")
    return lines


def table_neighbors(code: bytes) -> list[str]:
    """Any A0-lea into D0011D74 .. D0011D74+64 with a nearby store."""
    lines = ["## Table turbo — voisins `D0011D74`+0..64", ""]
    n_wr = 0
    for off in range(0, 66, 2):
        addr = 0xD0011D74 + off
        disp = addr - A0
        for va, areg in lea_a0(code, disp):
            more = store_to_areg(code, va - FLASH80, areg, 48)
            if more:
                n_wr += 1
                lines.append("- **WRITE** `%08X`  ram `%04X`  a%d  %s" % (va, addr & 0xFFFF, areg, more))
                if n_wr <= 8:
                    lines.append("```")
                    lines.extend(dump(code, va, 20, 16))
                    lines.append("```")
        for va in sth_a0_bol(code, disp):
            n_wr += 1
            lines.append("- **st.h BOL** `%08X` ram `%04X`" % (va, addr & 0xFFFF))
            if n_wr <= 8:
                lines.append("```")
                lines.extend(dump(code, va, 16, 10))
                lines.append("```")
    lines.append("total stores dans la fenetre table : **%d**" % n_wr)
    lines.append("")
    return lines


def main() -> None:
    code = BIN.read_bytes()
    out = [
        "# Writers rail + table turbo — 2026-08-23",
        "",
        "A0 = `D0010800`. Offline Golf 9980.",
        "",
    ]
    for addr, name, disp in TARGETS:
        out.extend(section(code, addr, name, disp))
    out.extend(table_neighbors(code))
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(out))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
