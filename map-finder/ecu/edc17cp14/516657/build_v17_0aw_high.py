# -*- coding: utf-8 -*-
"""Build A5 Bertin V1.7 0AW HIGH — Stage1 gain biased to high RPM, Multitronic-safe.

Base: V1.6 SAFE (no PCR wish/gear fill, no redline raise, turbo atm floor ORI).

Rules (EDC17 methodology, no PCR2.1 AccPed errors):
- NEVER touch Torque Request Standard / Gear 1-5 (0AW shift safety)
- NEVER raise RPM limiters
- NEVER raise turbo cells where ORI == 1000 hPa (0-boost / ~1000 rpm)
- Gain shape: low RPM soft → high RPM more (Lesson 21 soft increments)
- Caps: InjTime ≤ +8%, IQ ≤ +4%, Turbo ≤ +6%, Smoke ≤ +6%, SOI ≤ +5%
- Keep DaVinci DPF/EGR/FLAPS + rail soft from V1.6

python build_v17_0aw_high.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORI = ROOT / "ORI_FLS.fls"
V16 = ROOT / "A5_516657_V1.6_0AW_SAFE_noPCR_wish_noRPMup_injtime_turbo_DPF_EGR_noCHK.fls"
OUT_NAME = "A5_516657_V1.7_0AW_HIGH_rpm_safe_noPCR_wish_DPF_EGR_noCHK.fls"
OUT = ROOT / OUT_NAME
MANIFEST = ROOT / "A5_516657_V1.7_0AW_HIGH_manifest.json"
LIVRAISON = ROOT / "LIVRAISON-V1.7-0AW-HIGH.txt"

IDS = [b"516657", b"8K1907401K", b"0008", b"B3UX", b"CGKA", b"1037516657"]
ATM = 1000

# (name, addr, cols, rows, rpm_axis 'row'|'col', gain_lo, gain_hi, cap)
# rpm_axis inferred from ORI gradients (see build comments)
SHAPED = [
    # IQ #1 family — rows ≈ RPM (IQ drops toward high rows in ORI)
    ("IQ1_1", 0x1A8E7C, 16, 16, "row", 1.008, 1.040, 1.040),
    ("IQ1_2", 0x1A90C0, 16, 16, "row", 1.008, 1.040, 1.040),
    ("IQ1_3", 0x1A9348, 16, 16, "row", 1.008, 1.040, 1.040),
    ("IQ1_4", 0x1A9858, 16, 16, "row", 1.008, 1.040, 1.040),
    # Injection Time — rows ≈ RPM
    ("InjTime", 0x1D1496, 17, 21, "row", 1.010, 1.075, 1.080),
    # Smoke Higher Lambda
    ("Smoke_1", 0x1E325E, 16, 16, "row", 1.030, 1.060, 1.060),
    ("Smoke_2", 0x1E345E, 16, 16, "row", 1.030, 1.060, 1.060),
    ("Smoke_3", 0x1E365E, 16, 16, "row", 1.030, 1.060, 1.060),
    ("Smoke_4", 0x1E385E, 16, 16, "row", 1.030, 1.060, 1.060),
    ("Smoke_5", 0x1E3A5E, 16, 16, "row", 1.030, 1.060, 1.060),
    # SOI main banks
    ("SOI_1_1", 0x1B7E54, 10, 10, "row", 1.020, 1.050, 1.050),
    ("SOI_1_2", 0x1B7F74, 10, 10, "row", 1.020, 1.050, 1.050),
    ("SOI_1_3", 0x1B8094, 10, 10, "row", 1.020, 1.050, 1.050),
    ("SOI_1_4", 0x1B81B4, 10, 10, "row", 1.020, 1.050, 1.050),
    ("SOI_1_5", 0x1B82D4, 10, 10, "row", 1.020, 1.050, 1.050),
]

TURBO = [
    ("Turbo_1", 0x1D5D7C, 16, 10),
    ("Turbo_2", 0x1D5EF4, 16, 10),
    ("Turbo_3", 0x1D606C, 16, 10),
    ("Turbo_4", 0x1D61E4, 16, 10),
    ("Turbo_5", 0x1D635C, 16, 10),
    ("Turbo_6", 0x1D64D4, 16, 10),
    ("Turbo_7", 0x1D67C4, 16, 10),
]
TURBO_LIM = ("Turbo_Lim", 0x1D6DF8, 7, 15)

# Forbidden — must stay ORI (0AW)
FORBIDDEN = [
    (0x183FFE, 128),
    (0x19AE94, 256),
    (0x19AFC8, 256),
    (0x19B0FC, 256),
    (0x19B230, 256),
    (0x19B4BA, 256),
]
RPM_LIM = [0x1917C0, 0x191810, 0x191814, 0x1AFD70, 0x1AFD72]


def u16(b: bytes | bytearray, i: int) -> int:
    return b[i] | (b[i + 1] << 8)


def put_u16(buf: bytearray, i: int, v: int) -> None:
    v = max(0, min(0xFFFF, int(round(v))))
    buf[i] = v & 0xFF
    buf[i + 1] = (v >> 8) & 0xFF


def rpm_norm(r: int, c: int, rows: int, cols: int, axis: str) -> float:
    if axis == "row":
        return r / max(1, rows - 1)
    return c / max(1, cols - 1)


def shaped_gain(t: float, lo: float, hi: float) -> float:
    # ease-in toward high RPM
    t = max(0.0, min(1.0, t))
    w = t**1.35
    return lo + (hi - lo) * w


def apply_grid(
    out: bytearray,
    ori: bytes,
    addr: int,
    cols: int,
    rows: int,
    axis: str,
    lo: float,
    hi: float,
    cap: float,
    skip_atm: bool = False,
) -> dict:
    cells = raised = skipped0 = skipped_atm = 0
    pcts = []
    for r in range(rows):
        for c in range(cols):
            i = addr + (r * cols + c) * 2
            o = u16(ori, i)
            cells += 1
            if o == 0:
                skipped0 += 1
                continue
            if skip_atm and o == ATM:
                put_u16(out, i, o)
                skipped_atm += 1
                continue
            g = min(cap, shaped_gain(rpm_norm(r, c, rows, cols, axis), lo, hi))
            nv = min(0xFFFF, math.floor(o * g))
            if nv > o:
                put_u16(out, i, nv)
                raised += 1
                pcts.append(100 * (nv / o - 1))
            else:
                put_u16(out, i, o)
    return {
        "cells": cells,
        "raised": raised,
        "skipped0": skipped0,
        "skipped_atm": skipped_atm,
        "pct_med": round(sorted(pcts)[len(pcts) // 2], 2) if pcts else 0,
        "pct_max": round(max(pcts), 2) if pcts else 0,
        "pct_min": round(min(pcts), 2) if pcts else 0,
    }


def main() -> None:
    ori = ORI.read_bytes()
    v16 = V16.read_bytes()
    n = len(ori)
    assert n == 2_097_152 == len(v16)

    out = bytearray(v16)  # keep DaVinci + rail + restores

    stats = {}
    for name, addr, cols, rows, axis, lo, hi, cap in SHAPED:
        stats[name] = apply_grid(out, ori, addr, cols, rows, axis, lo, hi, cap)
        stats[name].update(
            {"addr_hex": f"{addr:06X}", "gain_lo": lo, "gain_hi": hi, "cap": cap, "rpm_axis": axis}
        )

    for name, addr, cols, rows in TURBO:
        # col ≈ mild RPM trend; use max(row,col) bias so high load+rpm gets more
        # implement: rpm_norm = max(r/(rows-1), c/(cols-1))
        cells = raised = atm = 0
        pcts = []
        for r in range(rows):
            for c in range(cols):
                i = addr + (r * cols + c) * 2
                o = u16(ori, i)
                cells += 1
                if o == ATM:
                    put_u16(out, i, ATM)
                    atm += 1
                    continue
                if o == 0:
                    continue
                t = max(r / max(1, rows - 1), c / max(1, cols - 1))
                g = min(1.060, shaped_gain(t, 1.020, 1.060))
                nv = min(0xFFFF, math.floor(o * g))
                if nv > o:
                    put_u16(out, i, nv)
                    raised += 1
                    pcts.append(100 * (nv / o - 1))
                else:
                    put_u16(out, i, o)
        stats[name] = {
            "addr_hex": f"{addr:06X}",
            "cells": cells,
            "raised": raised,
            "atm_floor_kept": atm,
            "pct_med": round(sorted(pcts)[len(pcts) // 2], 2) if pcts else 0,
            "pct_max": round(max(pcts), 2) if pcts else 0,
            "gain": "2%..6% shaped, atm 1000 kept",
        }

    # Turbo limiter same rule (7x15)
    name, addr, cols, rows = TURBO_LIM
    cells = raised = atm = 0
    pcts = []
    for r in range(rows):
        for c in range(cols):
            i = addr + (r * cols + c) * 2
            o = u16(ori, i)
            cells += 1
            if o == ATM:
                put_u16(out, i, ATM)
                atm += 1
                continue
            if o == 0:
                continue
            t = max(r / max(1, rows - 1), c / max(1, cols - 1))
            g = min(1.060, shaped_gain(t, 1.020, 1.060))
            nv = min(0xFFFF, math.floor(o * g))
            if nv > o:
                put_u16(out, i, nv)
                raised += 1
                pcts.append(100 * (nv / o - 1))
            else:
                put_u16(out, i, o)
    stats[name] = {
        "addr_hex": f"{addr:06X}",
        "raised": raised,
        "atm_floor_kept": atm,
        "pct_med": round(sorted(pcts)[len(pcts) // 2], 2) if pcts else 0,
        "pct_max": round(max(pcts), 2) if pcts else 0,
    }

    # Verify forbidden regions still ORI
    errors = []
    for addr, size in FORBIDDEN:
        if out[addr : addr + size] != ori[addr : addr + size]:
            errors.append(f"wish_touched_{addr:06X}")
    for addr in RPM_LIM:
        if u16(out, addr) != u16(ori, addr):
            errors.append(f"rpm_lim_touched_{addr:06X}")

    id_ok = all(bytes(out).find(x) >= 0 for x in IDS)
    id_unmoved = all(bytes(out).find(x) == ori.find(x) for x in IDS)
    if not id_ok:
        errors.append("ids_missing")
    if not id_unmoved:
        errors.append("ids_moved")

    # atm floor still clean on turbo1
    for i in range(0, 320, 2):
        if u16(ori, 0x1D5D7C + i) == ATM and u16(out, 0x1D5D7C + i) != ATM:
            errors.append("turbo_atm_raised")
            break

    bytes_vs_ori = sum(1 for i in range(n) if out[i] != ori[i])
    bytes_vs_v16 = sum(1 for i in range(n) if out[i] != v16[i])

    report = {
        "file": OUT_NAME,
        "ok": not errors,
        "errors": errors,
        "based_on": "V1.6_0AW_SAFE",
        "goal": "stage1_0aw_high_rpm_bias_no_pcr_wish",
        "bytes_changed_vs_ori": bytes_vs_ori,
        "bytes_changed_vs_v16": bytes_vs_v16,
        "maps": stats,
        "guarantees": [
            "Torque Request Standard + Gear1-5 = ORI (0AW)",
            "RPM limiters = ORI",
            "Turbo 1000 hPa floor = ORI",
            "No launch",
            "InjTime max gain <= +8%",
            "IQ max gain <= +4%",
            "Turbo max gain <= +6% (active cells only)",
        ],
        "ids_ok": id_ok,
        "note": (
            "noCHK. V1.7 = V1.6 SAFE + high-RPM shaped Stage1 on IQ/InjTime/SOI/Smoke/Turbo. "
            "0AW: wish/gear untouched. Gain felt more at high rpm, soft at low."
        ),
    }
    MANIFEST.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "maps"}, indent=2))
    for k, v in stats.items():
        print(k, {x: v[x] for x in v if x in ("addr_hex", "raised", "pct_med", "pct_max", "atm_floor_kept", "gain_lo", "gain_hi")})

    if errors:
        raise SystemExit("VERIFY FAIL: " + ", ".join(errors))

    OUT.write_bytes(out)
    LIVRAISON.write_text(
        f"""A5 Bertin — V1.7 0AW HIGH (Stage1 haut regime, Multitronic-safe)

Fichier :
  {OUT_NAME}

Pour qui
  Stage 1 qui RESPECTE la 0AW : gain surtout haut regime,
  sans erreurs PCR2.1 (pas de fill wish/gear, pas de hausse redline).

Base
  V1.6 SAFE (DaVinci DPF/EGR, wish/gear ORI, RPM lim ORI, turbo floor 1000 OK)

Ajoute (forme haut regime)
  - IQ #1 : ~+0.8 % bas → ~+4 % haut
  - Injection Time : ~+1 % bas → ~+7.5 % haut (cap +8 %)
  - SOI : ~+2 % → ~+5 %
  - Smoke lambda : ~+3 % → ~+6 %
  - Turbo + limiteur : ~+2 % → ~+6 % (cellules actives)
  - Plancher turbo 1000 hPa : INCHANGE (ORI)

JAMAIS touche (0AW)
  - Torque Request Standard + Gear 1..5
  - RPM limiters
  - Launch

Obligatoire avant flash
  1. CHK WinOLS/KESS
  2. G83 / EGT / FAP physiques
  3. KESS OBD read 516657 + 2 Mo puis write V1.7 CHK

Octets ≠ ORI : {bytes_vs_ori}
Octets ≠ V1.6 : {bytes_vs_v16}
""",
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    print(f"wrote {MANIFEST}")
    print(f"wrote {LIVRAISON}")


if __name__ == "__main__":
    main()
