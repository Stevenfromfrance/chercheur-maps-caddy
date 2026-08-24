# -*- coding: utf-8 -*-
"""Trace turbo ram_2D8C d15 source + rail a15. Offline, no Ghidra.

    python map-finder/ghidra/trace_turbo_rail.py
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
    emulate_site,
    is32,
    off10_bo,
    off16_bol,
    off18,
    parse_movha,
    sx,
)
from trace_ram_writers import BIN, find_lea_abs, next_is_sth_to_areg  # noqa: E402

MF = Path(__file__).resolve().parent.parent
OUT = MF / "reports" / "turbo-rail-trace.md"
B9977 = MF / "bins" / "9977-03L906023N-SM2G0P.bin"


def s4(v: int) -> int:
    return v - 16 if v >= 8 else v


def hint(code: bytes, i: int) -> str:
    op = code[i]
    if not is32(op):
        b1 = code[i + 1]
        dc, db = b1 & 0xF, b1 >> 4
        if op == 0x02:
            return "mov d%d, d%d" % (dc, db)
        if op == 0x42:
            return "add d%d, d%d" % (dc, db)
        if op == 0x52:
            return "sub d%d, d%d" % (dc, db)
        if op == 0xA2:
            return "sub d%d, d%d" % (dc, db)
        if op == 0xB4:
            return "st.h [a%d], d%d" % (db, dc)
        if op == 0x14:
            return "ld.bu d%d, [a%d]" % (dc, db)
        if op == 0x40:
            return "mov.aa a%d, a%d" % (dc, db)
        if op == 0x30:
            return "add.a a%d, a%d" % (dc, db)
        if op == 0x58:
            return "ld.w d15, [a10]+%#x" % (b1 * 4)
        if op == 0x54:
            return "st.w [a10]+%#x, d15" % (b1 * 4)
        if op == 0xD8:
            return "ld.a a15, [a10]+%#x" % (b1 * 4)
        if op == 0xF8:
            return "st.a [a10]+%#x, a15" % (b1 * 4)
        if op == 0xD4:
            return "ld.a a%d, [a%d]" % (dc, db)
        if op == 0x82:
            return "mov d%d, #%d" % (dc, s4(db) if False else db)
        if op == 0x86:
            return "sha d%d, #%d" % (dc, s4(db))
        if op == 0xC2:
            return "add d%d, #%d" % (dc, s4(db))
        if op == 0x6E:
            return "jz d15, +%d" % b1
        if op == 0xEE:
            return "jnz d15"
        if (op & 0x3F) == 0x10:
            n = (op >> 6) & 3
            return "addsc.a a%d, a%d, d15, #%d" % (dc, db, n)
        if (op & 0x0F) == 0x4 and ((op >> 6) & 3) == 2:
            return "ld.h d%d, [a%d]" % (dc, db)
        if (op & 0x0F) == 0x4 and ((op >> 6) & 3) == 3:
            return "st.a [a%d], a%d" % (db, dc)
        if op == 0xEC:
            return "st.a [a%d]+%d, a15" % (db, dc)
        return "op16 %02x %02x" % (op, b1)

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
    if op == 0xD9:
        return "lea a%d, [a%d%+#x]" % (ra, rb, off16_bol(h1))
    if op == 0x49:
        off = off10_bo(h1)
        op2227 = (h1 >> 6) & 0x3F
        if op2227 == 0x28:
            return "lea a%d, [a%d%+#x]" % (ra, rb, off)
        return "op49 a%d [a%d%+#x] sub=%#x" % (ra, rb, off, op2227)
    if op == 0x01:
        dest = (h1 >> 12) & 0xF
        op1827 = (h1 >> 2) & 0x3FF
        n = h1 & 3
        if op1827 == 0x180:
            return "addsc.a a%d, a%d, d%d, #%d" % (dest, rb, ra, n)
        return "op01 dest=a%d a%d d%d n=%d aux=%#x" % (dest, rb, ra, n, op1827)
    if op == 0x09:
        op2225 = (h1 >> 6) & 0xF
        op2627 = (h1 >> 10) & 3
        off = off10_bo(h1)
        kind = {
            (3, 2): "ld.hu",
            (5, 2): "st.h",
            (0, 2): "ld.w",
            (4, 2): "st.w",
            (1, 2): "ld.b",
            (2, 2): "ld.h",
        }.get((op2225, op2627), "bo")
        return "%s d%d, [a%d%+#x]" % (kind, ra, rb, off)
    if op == 0xB9:
        return "ld.hu d%d, [a%d%+#x]" % (ra, rb, off16_bol(h1))
    if op == 0x99:
        return "ld.a a%d, [a%d%+#x]" % (ra, rb, off16_bol(h1))
    if op == 0xB5:
        return "st.a [a%d%+#x], a%d" % (rb, off16_bol(h1), ra)
    if op == 0xF9:
        return "st.h [a%d%+#x], d%d" % (rb, off16_bol(h1), ra)
    if op == 0x37:
        return "extr"
    if op == 0x3C:
        return "j %+d" % sx(code[i + 1], 8)
    return "op32 %02x" % op


def dump(code: bytes, va: int, before: int, after: int) -> list[str]:
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


def stack_stores(code: bytes, va: int, lookback: int = 0x200) -> list[str]:
    """st.a / st.w to a10 slots in lookback."""
    off = va - FLASH80
    start = max(0, off - lookback) & ~1
    hits = []
    i = start
    while i < off:
        op = code[i]
        n = 4 if is32(op) else 2
        h = hint(code, i)
        if "a10" in h and ("st.a" in h or "st.w" in h or "st.h" in h):
            hits.append("%08X  %s" % (FLASH80 + i, h))
        i += n
    return hits


def lea_abs_near(code: bytes, va: int, lookback: int = 0x180) -> list[str]:
    off = va - FLASH80
    start = max(0, off - lookback) & ~1
    hits = []
    i = start
    while i < off:
        op = code[i]
        n = 4 if is32(op) else 2
        if op == 0xC5:
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            if ((h1 >> 10) & 3) == 0:
                addr = off18(h0, h1) & 0xFFFFFFFF
                ra = (h0 >> 8) & 0xF
                hits.append("%08X  lea a%d, %#010x" % (FLASH80 + i, ra, addr))
        elif op == 0x91:
            mh = parse_movha(
                struct.unpack_from("<H", code, i)[0],
                struct.unpack_from("<H", code, i + 2)[0],
            )
            if mh:
                hits.append("%08X  movh.a a%d, %#010x" % (FLASH80 + i, mh[0], mh[1]))
        i += n
    return hits


def bin_kind(p: Path) -> str:
    if not p.exists():
        return "absent"
    b = p.read_bytes()
    n = len(b)
    code = b[:CAL0]
    ff = code.count(b"\xff") / max(1, len(code))
    # TriCore 32-bit CALL 0x6D density in first 64k
    calls = sum(1 for i in range(0, min(65536, n) - 1, 2) if b[i] == 0x6D)
    leas = sum(1 for i in range(0, min(65536, n) - 4) if b[i] == 0xC5)
    return "size=%d  ff_in_0-cal=%.0f%%  call_6D_64k=%d  lea_C5_64k=%d" % (
        n,
        100 * ff,
        calls,
        leas,
    )


def main() -> None:
    code = BIN.read_bytes()
    out: list[str] = []
    out.append("# Turbo ram_2D8C + rail a15 — 2026-08-23")
    out.append("")
    out.append("Offline, Golf 9980 fullflash. Pas de clic Ghidra.")
    out.append("")

    out.append("## 1) Turbo — qui nourrit d15")
    out.append("")
    out.append(
        "Writer `800E0EA2` `st.h [a14], d15` dans `ram_2D8C`. "
        "Ce n est **pas** un capteur calcule : `d15` est un **ld.h [a15]** "
        "juste avant le store. `a15` est un pointeur indexe."
    )
    out.append("")
    out.append("```")
    out.extend(dump(code, 0x800E0E9C, 48, 28))
    out.append("```")
    out.append("")
    out.append("Lecture de la sequence (encodages Ghidra `tricore.sinc`) :")
    out.append("")
    out.append("| VA | Quoi |")
    out.append("|----|------|")
    out.append("| `800E0E80` | `ld.a a15, [SP+0x14]` puis `ld.bu d15, [a15]` — **index A** (octet) |")
    out.append("| `800E0E84` | `ld.a a15, [SP+0x1C]` puis `ld.bu d0, [a15]` — **index B** |")
    out.append("| `800E0E88` | `sha d0, #4` → B*16 |")
    out.append("| `800E0E8A` | `ld.a a15, [SP+0x04]` — **base table** |")
    out.append("| `800E0E8C` | `sha d15, #1` → A*2 |")
    out.append("| `800E0E8E` | `lea a15, [a15-16]` |")
    out.append("| `800E0E92` | `add d15, #-2` |")
    out.append("| `800E0E96` | `addsc.a a15, a15, d0, #0` → base + B*16 |")
    out.append("| `800E0E9A` | `addsc.a a15, a15, d15, #0` → + A*2 - 2 |")
    out.append("| `800E0EA0` | **`ld.h d15, [a15]`** cellule u16 |")
    out.append("| `800E0EA2` | `st.h ram_2D8C, d15` |")
    out.append("")
    out.append(
        "**Formule :** `ram_2D8C = *(u16*)( table[SP+4] - 16 + (idxB<<4) + (idxA*2 - 2) )`"
    )
    out.append("")
    out.append("Meme recette que smoke (`1D3FB4` → `ram_1D60`) : copie d une **case cal** dans la RAM, puis l interp turbo `800E0ECA` lit cette RAM comme axe X (grille `1C0714` dans `turbo_base3B`).")
    out.append("")
    stores = stack_stores(code, 0x800E0E80, 0x280)
    out.append("Stores pile vers `a10` dans les ~0x280 o avant :")
    if stores:
        for s in stores[-16:]:
            out.append("- `%s`" % s)
    else:
        out.append("- (aucun `st.a/st.w [a10]` dans la fenetre — slots remplis par l appelant)")
    out.append("")
    leas = lea_abs_near(code, 0x800E0E80, 0x200)
    out.append("lea ABS / movh.a dans les ~0x200 o avant le bloc :")
    if leas:
        for s in leas[-20:]:
            out.append("- `%s`" % s)
    else:
        out.append("- aucun — la **base table** arrive par la pile (appelant).")
    out.append("")

    emu = emulate_site(code, 0x800E0ECA)
    out.append(
        "Au CALL interp `800E0ECA` : A4=`%s` A5=`%s` A6=`%s` A14=`%s`"
        % (
            "%08X" % emu.A[4] if emu.A[4] else "—",
            "%08X" % emu.A[5] if emu.A[5] else "—",
            "%08X" % emu.A[6] if emu.A[6] else "—",
            "%08X" % emu.A[14] if emu.A[14] else "—",
        )
    )
    out.append(
        "A4 grille = WinOLS `%06X` (dans turbo_base3B). Axes flash A5/A6 = `%06X` / `%06X`."
        % (
            (emu.A[4] or 0) & 0xFFFFFF,
            (emu.A[5] or 0) & 0xFFFFFF,
            (emu.A[6] or 0) & 0xFFFFFF,
        )
    )
    out.append("")

    out.append("## 2) Rail — resoudre a15")
    out.append("")
    sites = [
        ("B `800B5A96` grille `1E9BC8`", 0x800B5A96),
        ("2d `800F5114` grille `1E9DE0`", 0x800F5114),
        ("D `800C1964` grille `1E98C0`", 0x800C1964),
    ]
    for name, va in sites:
        out.append("### %s" % name)
        out.append("")
        out.append("```")
        out.extend(dump(code, va, 64, 8))
        out.append("```")
        out.append("")
        emu = emulate_site(code, va)
        regs = ["A%d=%08X" % (r, emu.A[r]) for r in range(16) if emu.A[r]]
        out.append("emu A* : " + (" ".join(regs) if regs else "(vides)"))
        out.append(
            "d4=%s (%s)  d5=%s (%s)"
            % (
                hex(emu.Dsrc[4]) if emu.Dsrc[4] else "indirect",
                emu.d4_how or "—",
                hex(emu.Dsrc[5]) if emu.Dsrc[5] else "indirect",
                emu.d5_how or "—",
            )
        )
        leas = lea_abs_near(code, va, 0x100)
        out.append("lea/movh avant :")
        for s in leas[-12:] or ["- (aucun ABS — ptr pile / a15)"]:
            out.append("- `%s`" % s if not s.startswith("-") else s)
        sts = stack_stores(code, va, 0x180)
        if sts:
            out.append("stores pile :")
            for s in sts[-8:]:
                out.append("- `%s`" % s)
        out.append("")

    # rail ram_0414 already known at 800F5114
    out.append("### Writer `ram_0414` (vu a A13 sur le site 2d)")
    out.append("")
    for va, areg in find_lea_abs(code, 0xD0000414):
        wr = next_is_sth_to_areg(code, va - FLASH80, areg)
        out.append("- `%08X` lea a%d  st.h_near=%s" % (va, areg, wr))
        if wr:
            out.append("```")
            out.extend(dump(code, va, 16, 12))
            out.append("```")
    out.append("")

    out.append("## 3) Bin 9977 — code ou cal seule ?")
    out.append("")
    out.append("- Golf fullflash : `%s`" % bin_kind(BIN))
    out.append("- 9977 `03L906023N` : `%s`" % bin_kind(B9977))
    out.append("")
    out.append(
        "Si 9977 a ~0 CALL dans les 64k, c est une **image cal 2 Mo** (pas de chaine code). "
        "Un import Ghidra n aiderait pas : il n y a rien a desassembler. "
        "Il faudrait un dump **fullflash** (boot+app) comme le Golf `03L997558A`."
    )
    out.append("")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(out))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
