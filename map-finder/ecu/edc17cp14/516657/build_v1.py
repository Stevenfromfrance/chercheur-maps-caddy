# -*- coding: utf-8 -*-
"""Build A5 Bertin V1: conservative Stage1 + DaVinci DPF/EGR/FLAPS (no TVA, no lambda).

Rules (verified before write):
- Start from ORI FLS 2 Mo
- Apply DaVinci DPF+EGR+FLAPS fully (related DTCs included)
- Stage1: 16-bit LE in cal (0x180000-0x1EFFFF), skip flag band 0x185000-0x1861FF
- Only raise cells already used (ori > 0)
- Follow A4 Stage2 direction, but cap +12% (0AW / 256k km)
- Skip empty-cell fill (ori==0 -> Stage2 max) and huge ratios
- Skip Stage2 low-flash (0x000000-0x17FFFF) except DaVinci
- Do not copy A4 Stage2
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORI = ROOT / "ORI_FLS.fls"
S2 = ROOT / "ref-a4-516657-stage2" / "A4_516657_STAGE2.fls"
DAV = Path(
    r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off\A5_516657_DPF-EGR-FLAPS_noCHK.bin"
)
CLIENT = Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN")
OUT_NAME = "A5_516657_V1_S1cons_DPF_EGR_noCHK.fls"

CAP = 1.12
CAL_LO, CAL_HI = 0x180000, 0x1F0000
FLAG_LO, FLAG_HI = 0x185000, 0x186200
IDS = [b"516657", b"8K1907401K", b"0008", b"B3UX", b"CGKA", b"1037516657"]
PROTECT = [
    (0x000000, 0x000100),
    (0x001A00, 0x001B00),  # bosch id window
    (0x1A6EA0, 0x1A6F20),
    (0x183000, 0x183080),
]


def in_range(i: int, lo: int, hi: int) -> bool:
    return lo <= i < hi


def protected(i: int) -> bool:
    return any(lo <= i < hi for lo, hi in PROTECT)


def u16(b: bytes, i: int) -> int:
    return b[i] | (b[i + 1] << 8)


def put_u16(buf: bytearray, i: int, v: int) -> None:
    v = max(0, min(0xFFFF, int(round(v))))
    buf[i] = v & 0xFF
    buf[i + 1] = (v >> 8) & 0xFF


def cal_runs(s2_only: set[int], merge: int = 6, min_len: int = 16) -> list[tuple[int, int]]:
    diffs = sorted(i for i in s2_only if CAL_LO <= i < CAL_HI and not in_range(i, FLAG_LO, FLAG_HI))
    if not diffs:
        return []
    regs = []
    s = e = diffs[0]
    for i in diffs[1:]:
        if i <= e + merge:
            e = i
        else:
            if e - s + 1 >= min_len:
                regs.append((s, e + 1))
            s = e = i
    if e - s + 1 >= min_len:
        regs.append((s, e + 1))
    return regs


def main() -> None:
    ori = ORI.read_bytes()
    s2 = S2.read_bytes()
    dav = DAV.read_bytes()
    n = len(ori)
    assert n == 2_097_152 == len(s2) == len(dav)

    dav_set = {i for i in range(n) if ori[i] != dav[i]}
    s2_set = {i for i in range(n) if ori[i] != s2[i]}
    overlap = dav_set & s2_set
    conflicts = [i for i in overlap if dav[i] != s2[i]]
    if conflicts:
        raise SystemExit(f"DaVinci vs Stage2 conflicts: {len(conflicts)}")

    out = bytearray(ori)
    for i in dav_set:
        out[i] = dav[i]

    s1_cells = []
    skipped = {"ori0": 0, "decrease": 0, "ratio": 0, "flag": 0, "protect": 0, "no_s2": 0, "tiny": 0, "outside_run": 0}
    runs = cal_runs(s2_set - dav_set)
    in_run = [False] * n
    for a, b in runs:
        for i in range(a, b):
            in_run[i] = True

    i = CAL_LO
    while i + 1 < CAL_HI:
        if in_range(i, FLAG_LO, FLAG_HI) or in_range(i + 1, FLAG_LO, FLAG_HI):
            skipped["flag"] += 1
            i += 2
            continue
        if protected(i) or protected(i + 1):
            skipped["protect"] += 1
            i += 2
            continue
        if i in dav_set or (i + 1) in dav_set:
            skipped["protect"] += 1
            i += 2
            continue
        if not in_run[i]:
            skipped["outside_run"] += 1
            i += 2
            continue
        o = u16(ori, i)
        t = u16(s2, i)
        if o == t:
            skipped["no_s2"] += 1
            i += 2
            continue
        if t < o:
            skipped["decrease"] += 1
            i += 2
            continue
        if o == 0:
            skipped["ori0"] += 1
            i += 2
            continue
        ratio = t / o
        if ratio > 1.20:
            skipped["ratio"] += 1
            i += 2
            continue
        if ratio < 1.02:
            skipped["tiny"] += 1
            i += 2
            continue
        new = min(t, math.floor(o * CAP))
        if new <= o:
            i += 2
            continue
        put_u16(out, i, new)
        s1_cells.append({"addr": i, "ori": o, "s2": t, "v1": new, "pct": round(100 * (new / o - 1), 2)})
        i += 2

    # Verify DaVinci fully applied
    missing_dav = [i for i in dav_set if out[i] != dav[i]]
    extra_low = [
        i
        for i in range(0x180000)
        if out[i] != ori[i] and i not in dav_set
    ]
    tva_path = Path(
        r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off\DaVinci (A5_CGKA_8K1907401K_0008_BACKUP_MICRO.FLS(_TVA_))__noCHK.BIN"
    )
    tva = tva_path.read_bytes()
    tva_only = {i for i in range(n) if ori[i] != tva[i] and i not in dav_set}
    tva_hit = [i for i in tva_only if out[i] == tva[i] and out[i] != ori[i]]

    id_ok = all(out.find(x) >= 0 for x in IDS)
    id_moved = any(out.find(x) != ori.find(x) for x in IDS)

    changed = [i for i in range(n) if out[i] != ori[i]]
    s1_bytes = len({c["addr"] for c in s1_cells} | {c["addr"] + 1 for c in s1_cells})
    dav_bytes = len(dav_set)
    pcts = [c["pct"] for c in s1_cells]
    max_pct = max(pcts) if pcts else 0
    max_raw = max((c["v1"] / c["ori"] for c in s1_cells), default=1)

    errors = []
    if len(out) != n:
        errors.append("size")
    if missing_dav:
        errors.append(f"davinci_missing {len(missing_dav)}")
    if extra_low:
        errors.append(f"extra_lowflash {len(extra_low)}")
    if tva_hit:
        errors.append(f"tva_applied {len(tva_hit)}")
    if not id_ok:
        errors.append("ids_missing")
    if id_moved:
        errors.append("ids_moved")
    if max_raw > CAP + 0.0005:
        errors.append(f"cap_exceeded {max_raw}")
    if any(c["ori"] == 0 for c in s1_cells):
        errors.append("filled_zero")
    if len(s1_cells) < 20:
        errors.append(f"too_few_s1_cells {len(s1_cells)}")

    dest = ROOT / OUT_NAME
    dest_client = CLIENT / OUT_NAME
    report = {
        "file": OUT_NAME,
        "ori": str(ORI),
        "size": n,
        "ok": not errors,
        "errors": errors,
        "bytes_changed": len(changed),
        "davinci_dpf_egr_flaps_bytes": dav_bytes,
        "stage1_u16_cells": len(s1_cells),
        "stage1_bytes": s1_bytes,
        "stage1_pct_min": min(pcts) if pcts else None,
        "stage1_pct_max": max_pct,
        "stage1_cap": CAP,
        "cal_runs": len(runs),
        "cal_run_bytes": sum(b - a for a, b in runs),
        "skipped": skipped,
        "davinci_stage2_overlap": len(overlap),
        "davinci_stage2_conflicts": len(conflicts),
        "ids_ok": id_ok,
        "ids_unmoved": not id_moved,
        "tva_bytes_not_applied": len(tva_only),
        "lambda_not_applied": True,
        "note": (
            "noCHK — checksum WinOLS/K-TAG avant flash. "
            "Pas de TVA, pas de lambda, pas de copie Stage2 A4. "
            "Ne pas flasher si G83 123C / EGT S3 / FAP 55g non traites."
        ),
        "cells_top": sorted(s1_cells, key=lambda c: -c["pct"])[:15],
        "cells_addr_sample": s1_cells[:20],
        "s1_banks": {
            f"{(c['addr']//0x10000):02X}0000": sum(1 for x in s1_cells if x["addr"] // 0x10000 == c["addr"] // 0x10000)
            for c in s1_cells
        },
        "cal_run_count": len(runs),
    }
    (ROOT / "A5_516657_V1_manifest.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: report[k] for k in report if k not in ("cells_top", "cells_addr_sample", "ori")}, indent=2))
    if errors:
        raise SystemExit("VERIFY FAIL: " + ", ".join(errors))
    dest.write_bytes(out)
    dest_client.write_bytes(out)
    print(f"wrote {dest}")
    print(f"wrote {dest_client}")


if __name__ == "__main__":
    main()
