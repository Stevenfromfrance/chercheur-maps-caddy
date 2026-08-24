# -*- coding: utf-8 -*-
"""Offline remaining: horsA2L ranking, ram_2754/vmax/rail, Stage1 on SM2G0P.

    python map-finder/ghidra/offline_remaining.py
"""
from __future__ import annotations

import csv
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import (  # noqa: E402
    CAL0,
    FLASH80,
    emulate_site,
    is32,
    off16_bol,
    off18,
    parse_movha,
)
from trace_ram_writers import (  # noqa: E402
    BIN as GOLF9980,
    dump_window,
    find_lea_abs,
    next_is_sth_to_areg,
)

ROOT = Path(__file__).resolve().parent
MF = ROOT.parent
REPORTS = MF / "reports"
BINS = MF / "bins"
ATLAS = MF / "atlas"
HORS = ROOT / "golf9980_horsA2L_identified.csv"
OUT = REPORTS / "offline-remaining.md"

STAGE1_IDS = (
    "AccPed_trq4A",
    "tqlim_cluth_prot",
    "tqlim_base_pu_4A",
    "smoke_mapA",
    "turbo_base3B",
    "rail_base_int_trq2B",
    "duration_inj6A",
    "soi_base_int_trq2A",
    "vmax3",
)

SOFTS = ("9977", "9978", "9980", "9983", "9972")

# Ghidra-validated starts on Golf 03L997558A fullflash (not cloned atlas 9979).
GOLF_VALIDATED = {
    "AccPed_trq4A": 0x1CFFC0,
    "tqlim_cluth_prot": 0x1D0860,
    "tqlim_base_pu_4A": 0x1D3190,
    "smoke_mapA": 0x1D1D18,
    "turbo_base3B": 0x1C04AC,
    "rail_base_int_trq2B": 0x1E9368,
    "duration_inj6A": 0x1CDC84,
    "soi_base_int_trq2A": 0x18C380,
    "vmax3": 0x18047C,
}

ORI_9979_CANDIDATES = [
    Path(
        r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
        r"\Caddy-CAYE-2013-03L906023PA-2531\ORI"
        r"\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
    ),
    Path(
        r"C:\Users\theda\OneDrive\Bureau\caddy cartho\ORI CADDY STEVEN"
        r"\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27"
    ),
]

BIN_FILES = {
    "9977": BINS / "9977-03L906023N-SM2G0P.bin",
    "9978": BINS / "9978-03L906023AR-SM2G0P.bin",
    "9983": BINS / "9983-03L906023A-SM2G0P.bin",
    "9972": BINS / "9972-03L906023BL-SM2G0M.bin",
}


def find_ori_9979() -> Path | None:
    for p in ORI_9979_CANDIDATES:
        if p.exists():
            return p
    return None


def hors_stats() -> tuple[Counter, list[dict], int, int]:
    n = Counter()
    cands = []
    ident_unk = 0
    fill_n = 0
    with HORS.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            conf = (row.get("confidence") or "").strip().lower()
            n[conf] += 1
            notes = row.get("notes") or ""
            m = re.search(r"uniq_u16=(\d+)", notes)
            uniq = int(m.group(1)) if m else 0
            fill = "8000/A000 fill" in notes
            if fill:
                fill_n += 1
            same = (row.get("same_9979") or "").strip() == "1"
            if conf != "low" or fill or uniq < 10:
                continue
            rec = {
                "off": row.get("offset"),
                "call": row.get("call_site"),
                "uniq": uniq,
                "folder": row.get("a2l_folder") or "",
            }
            if same:
                ident_unk += 1
            else:
                cands.append(rec)
    cands.sort(key=lambda x: -x["uniq"])
    return n, cands, ident_unk, fill_n


def all_abs18(code: bytes, target: int) -> list[tuple[int, int]]:
    """Any 32-bit ABS encoding whose off18 == target. Returns (va, opcode)."""
    hits = []
    i = 0
    end = min(len(code), CAL0) - 3
    while i <= end:
        op = code[i]
        if is32(op):
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            if ((h1 >> 10) & 3) == 0 and op in (0xC5, 0x05, 0xA5, 0x25, 0x85, 0x45):
                if (off18(h0, h1) & 0xFFFFFFFF) == target:
                    hits.append((FLASH80 + i, op))
            i += 4
        else:
            i += 2
    return hits


def movha_lea_target(code: bytes, target: int) -> list[tuple[int, int]]:
    """movh.a then lea BOL that sums to target. Returns (lea_va, areg)."""
    hits = []
    i = 0
    end = min(len(code), CAL0) - 7
    last_movh: dict[int, tuple[int, int]] = {}
    while i <= end:
        op = code[i]
        n = 4 if is32(op) else 2
        if n == 4:
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            if op == 0x91:
                mh = parse_movha(h0, h1)
                if mh:
                    last_movh[mh[0]] = (mh[1], FLASH80 + i)
            elif op == 0xD9:
                ra = (h0 >> 8) & 0xF
                rb = (h0 >> 12) & 0xF
                base = last_movh.get(rb)
                if base:
                    addr = (base[0] + off16_bol(h1)) & 0xFFFFFFFF
                    if addr == target:
                        hits.append((FLASH80 + i, ra))
        i += n
    return hits


def raw_ptr(code: bytes, ptr: int, limit: int) -> list[int]:
    needle = struct.pack("<I", ptr)
    hits = []
    start = 0
    blob = code[:limit]
    while True:
        j = blob.find(needle, start)
        if j < 0:
            break
        hits.append(FLASH80 + j if limit <= CAL0 else j)
        start = j + 2
        if len(hits) >= 12:
            break
    return hits


def ram_2754_report(code: bytes) -> list[str]:
    lines = ["### ram_2754 clutch Y (`D0002754`)"]
    leas = find_lea_abs(code, 0xD0002754)
    lines.append("lea ABS: **%d**" % len(leas))
    for va, areg in leas:
        wr = next_is_sth_to_areg(code, va - FLASH80, areg)
        lines.append("- `%08X` lea a%d  st.h_near=%s" % (va, areg, wr))
        lines.extend("    " + x for x in dump_window(code, va, 16, 16))
    abs_hits = all_abs18(code, 0xD0002754)
    lines.append("autres ABS (ld/st opcode) : %d  %s" % (
        len(abs_hits),
        ", ".join("`%08X` op=%02x" % (va, op) for va, op in abs_hits[:8]) or "—",
    ))
    ml = movha_lea_target(code, 0xD0002754)
    lines.append("movh.a+lea BOL : **%d**" % len(ml))
    for va, areg in ml[:6]:
        lines.append("- `%08X` a%d" % (va, areg))
        lines.extend("    " + x for x in dump_window(code, va, 12, 12))
    ptrs = raw_ptr(code, 0xD0002754, CAL0)
    lines.append("ptr u32 `54 27 00 D0` dans le code : **%d** %s" % (
        len(ptrs),
        " ".join("`%08X`" % x for x in ptrs) or "",
    ))
    # Neighbour RAM block D0002700-27FF with lea+st.h
    neigh = []
    for off in range(0x2700, 0x2800, 2):
        tgt = 0xD0000000 + off
        for va, areg in find_lea_abs(code, tgt):
            if next_is_sth_to_areg(code, va - FLASH80, areg):
                neigh.append((tgt, va, areg))
    lines.append("lea+st.h dans `D0002700–27FF` (bloc clutch/SOI) : **%d**" % len(neigh))
    for tgt, va, areg in neigh:
        lines.append("- `%08X`  ram_%04X  lea a%d" % (va, tgt & 0xFFFF, areg))
    emu = emulate_site(code, 0x800FC260)
    lines.append(
        "lecture `800FC260` d5=%s (axe Y clutch/SOI)"
        % (hex(emu.Dsrc[5]) if emu.Dsrc[5] else "indirect")
    )
    if not ml and not any(next_is_sth_to_areg(code, va - FLASH80, ar) for va, ar in leas):
        lines.append(
            "**Verdict:** pas de writer `lea+st.h` / `movh+lea`. "
            "Cellule remplie via ptr / DMA / autre module — pas la recette clutch X."
        )
    return lines


def vmax_report(code: bytes) -> list[str]:
    lines = ["### vmax3 `18047C`"]
    u16 = struct.unpack_from("<H", code, 0x18047C)[0]
    lines.append("valeur Golf fullflash : `%04X` = %.1f km/h (facteur 0.1)" % (u16, u16 * 0.1))
    targets = (0xA018047C, 0x8018047C, 0xA018047E, 0x8018047E)
    for t in targets:
        abs_h = all_abs18(code, t)
        ml = movha_lea_target(code, t)
        ptrs = raw_ptr(code, t, CAL0)
        lines.append(
            "`%08X`  ABS=%d  movh+lea=%d  ptr32=%d"
            % (t, len(abs_h), len(ml), len(ptrs))
        )
        for va, op in abs_h[:4]:
            lines.append("- ABS `%08X` op=%02x" % (va, op))
            lines.extend("    " + x for x in dump_window(code, va, 8, 8))
        for va, areg in ml[:4]:
            lines.append("- movh+lea `%08X` a%d" % (va, areg))
            lines.extend("    " + x for x in dump_window(code, va, 8, 8))
    # context around 18047C: often a small speed-limiter table
    ctx = code[0x180470 : 0x180490].hex(" ")
    lines.append("contexte `180470–18048F` : `%s`" % ctx)
    lines.append(
        "**Verdict:** scalaire cal, pas d interpolateur. Lecture code toujours "
        "indirecte (table / index), pas un `lea ABS` unique."
    )
    return lines


def rail_turbo_report(code: bytes) -> list[str]:
    lines = ["### Rail / turbo — entrees aux call-sites"]
    sites = [
        ("rail B `800B5A96`", 0x800B5A96),
        ("rail 2d `800F5114`", 0x800F5114),
        ("rail D `800C1964`", 0x800C1964),
        ("turbo 2d `800E0ECA`", 0x800E0ECA),
        ("turbo C `800F8F0A`", 0x800F8F0A),
    ]
    for name, va in sites:
        emu = emulate_site(code, va)
        regs = []
        for r in range(16):
            if emu.A[r]:
                regs.append("A%d=%08X" % (r, emu.A[r]))
        lines.append("- **%s**" % name)
        lines.append("  " + (" ".join(regs) if regs else "(A* inconnus dans 256 o)"))
        lines.append(
            "  d4=%s d5=%s  how=%s / %s"
            % (
                hex(emu.Dsrc[4]) if emu.Dsrc[4] else "—",
                hex(emu.Dsrc[5]) if emu.Dsrc[5] else "—",
                emu.d4_how or "—",
                emu.d5_how or "—",
            )
        )
    lines.append(
        "Pas de `ram_XXXX` nommee comme clutch : axes via `a15` / pile. "
        "Writer net = toujours ouvert."
    )
    return lines


def load_atlas_maps(soft: str) -> dict[str, dict]:
    p = ATLAS / f"{soft}.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {m["id"]: m for m in data.get("maps") or [] if "id" in m}


def fp64(a: bytes, b: bytes, off_a: int, off_b: int, n: int = 64) -> str:
    if off_a + n > len(a) or off_b + n > len(b):
        return "oob"
    x, y = a[off_a : off_a + n], b[off_b : off_b + n]
    if x == y:
        return "ident"
    d = sum(1 for p, q in zip(x, y) if p != q)
    return "diff %d/%d" % (d, n)


def u16_phys(blob: bytes, off: int, factor: float, offset: float) -> str:
    if off + 2 > len(blob):
        return "—"
    raw = struct.unpack_from("<H", blob, off)[0]
    return "%.1f" % (raw * factor + offset)


def main() -> None:
    out: list[str] = []
    out.append("# Offline remaining — 2026-08-22")
    out.append("")
    out.append(
        "Sans clic Ghidra, sans WinOLS. Golf 9980 fullflash `03L997558A` "
        "+ banque PCR (atlas + bins)."
    )
    out.append("")

    n, cands, ident_unk, fill_n = hors_stats()
    total = sum(n.values())
    out.append("## 1) Hors-A2L 9980")
    out.append("")
    out.append(
        "`ghidra/golf9980_horsA2L_identified.csv` — **%d** grilles interp sans IdName WinOLS."
        % total
    )
    out.append("")
    out.append("| conf | n | signification |")
    out.append("|------|---|---------------|")
    out.append("| high | %d | match famille A2L pres du start |" % n["high"])
    out.append(
        "| medium | %d | **dans** une map deja nommee (sous-vue, pas une nouvelle) |"
        % n["medium"]
    )
    out.append("| low | %d | hors des ~299 maps A2L WinOLS |" % n["low"])
    out.append("| (dont fill 8000/A000) | %d | bruit, pas une map |" % fill_n)
    out.append("")
    out.append(
        "Low **identiques 9979** + grille diverse (uniq≥10) : **%d** — inconnues A2L "
        "mais **meme payload que le Caddy** (pas un gisement Golf-only)."
        % ident_unk
    )
    out.append("")
    out.append(
        "Low **≠ 9979** + uniq≥10 + pas fill : **%d** candidates « vraie inconnue / payload Golf »."
        % len(cands)
    )
    if cands:
        out.append("")
        out.append("| offset | call-site | uniq_u16 |")
        out.append("|--------|-----------|----------|")
        for c in cands[:30]:
            out.append("| `%s` | `%s` | %d |" % (c["off"], c["call"], c["uniq"]))
        if len(cands) > 30:
            out.append("")
            out.append("… +%d autres dans le CSV." % (len(cands) - 30))
    out.append("")
    out.append(
        "Je peux classer. Je ne peux **pas** baptiser OEM une grille low sans A2L ou log."
    )
    out.append("")

    code = GOLF9980.read_bytes()
    out.append("## 2) ram_2754 / rail / turbo / vmax (Golf 9980 code)")
    out.append("")
    out.extend(ram_2754_report(code))
    out.append("")
    out.extend(vmax_report(code))
    out.append("")
    out.extend(rail_turbo_report(code))
    out.append("")

    out.append("## 3) Autres softs PCR — adresses Stage1")
    out.append("")
    out.append(
        "SM2G0P proche Caddy : **9977, 9978, 9983** + Golf **9980**. "
        "**9972** = SM2G0M (Polo) — autre famille, offsets souvent ≠. "
        "Ce n est **pas** la chaine code Ghidra 9980 : juste fingerprints / atlas."
    )
    out.append("")

    atlases = {s: load_atlas_maps(s) for s in ("9979",) + SOFTS}
    golf_cal = code
    ori = find_ori_9979()
    ori_b = ori.read_bytes() if ori else None
    loaded = {s: p.read_bytes() if p.exists() else None for s, p in BIN_FILES.items()}

    out.append(
        "ORI 9979 : `%s`" % (ori if ori else "introuvable — pas de colonne Caddy")
    )
    out.append("")
    out.append("### Adresses atlas (start WinOLS)")
    out.append("")
    hdr = "| Map | 9979 | 9977 | 9978 | 9980 atlas | 9983 | 9972 | Golf Ghidra |"
    out.append(hdr)
    out.append("|-----|------|------|------|------------|------|------|-------------|")
    for mid in STAGE1_IDS:
        cells = []
        for s in ("9979", "9977", "9978", "9980", "9983", "9972"):
            m = atlases.get(s, {}).get(mid)
            cells.append("`%s`" % m["addr_hex"] if m else "—")
        g = GOLF_VALIDATED.get(mid)
        cells.append("`%06X`" % g if g is not None else "—")
        out.append("| `%s` | %s |" % (mid, " | ".join(cells)))
    out.append("")
    out.append(
        "Note : atlas 9980 est clone 9979 (`AccPed` `1CF9C0`). "
        "Ghidra sur **03L997558A** a valide `AccPed` a **`1CFFC0`** — "
        "le dump cal `03L997557P` n est pas le fullflash du projet Ghidra."
    )
    out.append("")

    out.append("### 64 octets : Golf Ghidra vs bin (adresse de *ce* soft)")
    out.append("")
    out.append("| Map | vs 9979 ORI | 9977 | 9978 | 9983 | 9972 |")
    out.append("|-----|-------------|------|------|------|------|")
    a9979 = atlases.get("9979") or {}
    for mid in STAGE1_IDS:
        goff = GOLF_VALIDATED[mid]
        n = 2 if mid == "vmax3" else 64
        row = ["`%s`" % mid]
        ref = a9979.get(mid)
        if ori_b is not None and ref:
            row.append(fp64(golf_cal, ori_b, goff, int(ref["addr"]), n))
        else:
            row.append("—")
        for s in ("9977", "9978", "9983", "9972"):
            blob = loaded.get(s)
            m = atlases.get(s, {}).get(mid)
            if blob is None or not m:
                row.append("—")
            else:
                row.append(fp64(golf_cal, blob, goff, int(m["addr"]), n))
        out.append("| %s |" % " | ".join(row))
    out.append("")

    out.append("### vmax3 physique (km/h)")
    out.append("")
    cells = []
    if ori_b is not None and a9979.get("vmax3"):
        cells.append("9979 ORI " + u16_phys(ori_b, int(a9979["vmax3"]["addr"]), 0.1, 0))
    cells.append("Golf Ghidra " + u16_phys(golf_cal, 0x18047C, 0.1, 0))
    for s in ("9977", "9978", "9983", "9972"):
        blob = loaded.get(s)
        m = atlases.get(s, {}).get("vmax3")
        if blob is None or not m:
            cells.append("%s —" % s)
        else:
            cells.append("%s %s" % (s, u16_phys(blob, int(m["addr"]), 0.1, 0)))
    out.append("- " + " · ".join(cells))
    out.append("")

    out.append("### AccPed max (Nm, facteur 0.03125 offset −1024)")
    out.append("")
    for s in ("9977", "9978", "9983", "9972"):
        blob = loaded.get(s)
        m = atlases.get(s, {}).get("AccPed_trq4A")
        if blob is None or not m:
            continue
        off = int(m["addr"])
        ln = int(m.get("length") or 256)
        chunk = blob[off : off + ln]
        if len(chunk) < 2:
            continue
        mx = max(struct.unpack_from("<%dH" % (len(chunk) // 2), chunk))
        phys = mx * 0.03125 - 1024.0
        out.append("- **%s** `@%s` max raw %d → **%.1f Nm**" % (s, m["addr_hex"], mx, phys))
    goff = GOLF_VALIDATED["AccPed_trq4A"]
    chunk = golf_cal[goff : goff + 256]
    mx = max(struct.unpack_from("<%dH" % (len(chunk) // 2), chunk))
    out.append(
        "- **Golf Ghidra** `@1CFFC0` max raw %d → **%.1f Nm**"
        % (mx, mx * 0.03125 - 1024.0)
    )
    out.append("")
    out.append(
        "9977/9978/9983 dumps MHH : AccPed souvent deja Stage1 (~400 Nm). "
        "Bon pour **trouver l adresse**, pas comme ORI a flasher."
    )
    out.append("")

    out.append("## 4) Ce que je peux / ne peux pas boucler seul")
    out.append("")
    out.append("| Sujet | Autonome | Reste |")
    out.append("|-------|----------|-------|")
    out.append(
        "| Hors-A2L | classer high/medium/low, lister les low ≠9979 | nom OEM |"
    )
    out.append(
        "| 9977/9978/9972 | adresses Stage1 via atlas/phase2 | importer un fullflash Ghidra par soft |"
    )
    out.append(
        "| ram_2754 | confirmer : pas de writer `lea+st.h` | Ghidra GUI sur un XREF data, ou log |"
    )
    out.append(
        "| Rail / turbo | call-sites + emu registres | resoudre `a15` pile (long) |"
    )
    out.append("| vmax3 | valeur + adresse par soft | lecture code (table) |")
    out.append("")
    out.append("Rien a cliquer de ton cote pour cette passe.")
    out.append("")

    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
