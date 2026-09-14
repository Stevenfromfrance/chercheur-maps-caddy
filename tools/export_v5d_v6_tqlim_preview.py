# -*- coding: utf-8 -*-
"""Export tqlim_base_pu_4A V5d vs V6f preview.

Confidence (honest):
  HIGH — cliff RPM 3750→4000 (370→278) is real in V5d; will clip wish ≥4000.
  MED  — soft @3814 TQI~255 not explained by this map alone (~346 still allowed).
  LOW  — won't fix MAP_SP holes / tegt if EGT≥780.

V6f policy (ATM≈900–1050, rpm 3800–4600):
  Lift toward gentle decay from mid plateau (~370), NOT flat 370 to hardcut.
  Targets @ATM1000: 4000→350, 4200→335, 4400→310, 4600→280.
  Keep rpm≥4800 near V5d (cut / safety).
  Never exceed 370. Preview only — not a flashable NOCS.

  python tools/export_v5d_v6_tqlim_preview.py
"""
from __future__ import annotations

import json
from pathlib import Path

VEH = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
    r"\Caddy-CAYE-2013-03L906023PA-2531"
)
REPO = Path(r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy")

V5D = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5d_tegtORI_launch110.NOCS"
ACE = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_ACE_stage1_dpf_egr.NOCS"
ORI = VEH / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
OUT = REPO / "compare-v5d-v6-tqlim-data.json"

ADDR = 0x1D3190
COLS, ROWS = 8, 26
NM_F, NM_O = 0.03125, -1024.0
ATM_AXIS = 0x1A42BA  # factor 0.0829187
RPM_AXIS = None  # read from atlas via file — will decode from known pattern after ATM

# Hardcoded from atlas 9979 / prior probe (rpm axis of tqlim_base)
# Will overwrite by reading if we find axis addr from atlas json
ATM_F = 0.0829187


def u16(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def decode_nm(raw: int) -> float:
    return raw * NM_F + NM_O


def encode_nm(val: float) -> int:
    return max(0, min(0xFFFF, int(round((val - NM_O) / NM_F))))


def read_axis(buf: bytes, addr: int, n: int, factor: float, offset: float = 0.0) -> list[float]:
    return [round(u16(buf, addr + i * 2) * factor + offset, 3) for i in range(n)]


def read_grid(buf: bytes, addr: int) -> list[list[float]]:
    return [
        [round(decode_nm(u16(buf, addr + (r * COLS + c) * 2)), 2) for c in range(COLS)]
        for r in range(ROWS)
    ]


def find_rpm_axis(atlas_path: Path) -> tuple[int, float]:
    data = json.loads(atlas_path.read_text(encoding="utf-8"))
    m = next(x for x in data["maps"] if x["id"] == "tqlim_base_pu_4A")
    ay = m["axis_y"]
    return ay["addr"], ay["factor"]


def target_at_rpm(rpm: float, plateau: float) -> float | None:
    """
    Desired tqlim ceiling vs rpm (Nm). None = leave V5d.
    Gentle decay — not flat plateau to cut.
    """
    if rpm < 3800:
        return None
    if rpm >= 4700:
        return None  # leave hardcut / near-cut stock
    # 3800→4000 : plateau → 0.96*plateau (~355 if 370)
    if rpm <= 4000:
        t = (rpm - 3800) / 200.0
        return plateau * (1.0 - t * 0.04)
    # 4000→4400 : 0.96 → 0.88 (~355→326)
    if rpm <= 4400:
        t = (rpm - 4000) / 400.0
        return plateau * (0.96 - t * 0.08)
    # 4400→4700 : 0.88 → 0.78 (~326→289)
    t = (rpm - 4400) / 300.0
    return plateau * (0.88 - min(1.0, t) * 0.10)


def build_v6f(v5: list[list[float]], atm: list[float], rpm: list[float]) -> tuple[list[list[float]], dict]:
    # Plateau = typical sea-level midband (ATM≥950, rpm 2500–3500)
    plate_vals = []
    for r, rv in enumerate(rpm):
        if 2500 <= rv <= 3500:
            for c, av in enumerate(atm):
                if av >= 950:
                    plate_vals.append(v5[r][c])
    plateau = max(plate_vals) if plate_vals else 370.0

    out = [row[:] for row in v5]
    stats = {
        "version": "v6f_tqlim_hi_rpm_fill",
        "plateau_nm": round(plateau, 1),
        "cells": 0,
        "max_d": 0.0,
        "confidence": "high_for_ge4000_med_for_3814",
    }

    for r, rv in enumerate(rpm):
        tgt = target_at_rpm(rv, plateau)
        if tgt is None:
            continue
        for c, av in enumerate(atm):
            # Only lift usable ATM band (altitude / sea-level drive)
            if av < 850:
                continue
            cur = v5[r][c]
            # Only raise if below target (don't lower anything)
            if cur >= tgt - 0.5:
                continue
            # Cap: never above plateau, never above 370
            nv = min(plateau, 370.0, tgt)
            # Blend 90% toward target (strong fill — this IS the limiter)
            nv = round(cur + 0.90 * (nv - cur), 2)
            if nv > cur + 0.5:
                out[r][c] = nv
                d = nv - cur
                stats["cells"] += 1
                stats["max_d"] = max(stats["max_d"], d)

    stats["max_d"] = round(stats["max_d"], 1)
    return out, stats


def slice_atm1000(grid: list[list[float]], atm: list[float], rpm: list[float]) -> dict:
    ci = min(range(len(atm)), key=lambda i: abs(atm[i] - 1000.0))
    return {
        "atm_col": atm[ci],
        "rpm": rpm,
        "v5d": [grid[r][ci] for r in range(len(rpm))],
        "col_index": ci,
    }


def main() -> None:
    atlas = REPO / "map-finder" / "atlas" / "9979.json"
    rpm_addr, rpm_f = find_rpm_axis(atlas)

    v5d = V5D.read_bytes()
    ace = ACE.read_bytes()
    ori = ORI.read_bytes()

    atm = read_axis(v5d, ATM_AXIS, COLS, ATM_F)
    rpm = read_axis(v5d, rpm_addr, ROWS, rpm_f)

    g5 = read_grid(v5d, ADDR)
    ga = read_grid(ace, ADDR)
    go = read_grid(ori, ADDR)
    g6, st = build_v6f(g5, atm, rpm)

    delta = [[round(g6[r][c] - g5[r][c], 2) for c in range(COLS)] for r in range(ROWS)]

    sl5 = slice_atm1000(g5, atm, rpm)
    sl6 = slice_atm1000(g6, atm, rpm)
    sla = slice_atm1000(ga, atm, rpm)
    slo = slice_atm1000(go, atm, rpm)

    # Log-style probes
    probes = []
    for src, prpm, tq in [
        ("hold", 3832, 333.4),
        ("soft", 3814, 255.4),
        ("soft", 3865, 226.0),
        ("soft", 4006, 230.6),
        ("soft", 4236, 214.0),
    ]:
        # interp along ATM1000 slice
        def at(grid_slice, r):
            ys = rpm
            xs = grid_slice
            if r <= ys[0]:
                return xs[0]
            if r >= ys[-1]:
                return xs[-1]
            for i in range(1, len(ys)):
                if ys[i] >= r:
                    t = (r - ys[i - 1]) / (ys[i] - ys[i - 1])
                    return xs[i - 1] + t * (xs[i] - xs[i - 1])
            return xs[-1]

        v5 = at(sl5["v5d"], prpm)
        v6 = at(sl6["v5d"] if False else [g6[r][sl5["col_index"]] for r in range(ROWS)], prpm)
        # fix: rebuild
        v6 = at([g6[r][sl5["col_index"]] for r in range(ROWS)], prpm)
        probes.append(
            {
                "src": src,
                "rpm": prpm,
                "log_tq": tq,
                "wish_approx": 333.0,
                "tqlim_v5d": round(v5, 1),
                "tqlim_v6f": round(v6, 1),
                "headroom_wish_v5d": round(v5 - 333.0, 1),
                "headroom_wish_v6f": round(v6 - 333.0, 1),
                "explains_log": v5 < tq + 15 and v5 < 320,
            }
        )

    # Confidence text
    conf = (
        "Confiance: HAUTE que tqlim_base clippe le wish ≥4000 (cliff 370→278). "
        "MOYENNE que ça explique tout le mou (soft @3814 encore autorisé ~346 Nm). "
        "Preview ≠ preuve log ; tegt ORI reste un autre risque si EGT≥780."
    )

    payload = {
        "title": "tqlim_base_pu_4A · V5d vs V6f preview",
        "note": (
            "V6f = fill haut régime ATM≥850 (4000→~350, 4200→~335, 4600→~280). "
            "Pas plat 370 jusqu'au cut. Preview only."
        ),
        "confidence": conf,
        "unit": "Nm",
        "addr": f"{ADDR:06X}",
        "axisX": atm,
        "axisY": rpm,
        "axisXName": "ATM (mbar)",
        "axisYName": "RPM",
        "v5d": g5,
        "v6": g6,
        "ace": ga,
        "ori": go,
        "delta": delta,
        "stats": st,
        "slice_atm1000": {
            "atm": sl5["atm_col"],
            "rpm": rpm,
            "v5d": sl5["v5d"],
            "v6": [g6[r][sl5["col_index"]] for r in range(ROWS)],
            "ace": sla["v5d"],
            "ori": slo["v5d"],
        },
        "log_probes": probes,
        "verdict": {
            "summary": conf,
            "sure_for_ge4000": True,
            "sure_for_3814_soft": False,
        },
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)
    print("stats", st)
    print("ATM1000 slice (rpm >= 3000):")
    ci = sl5["col_index"]
    for r, rv in enumerate(rpm):
        if rv >= 3000:
            print(
                f"  {rv:5.0f}  v5d={g5[r][ci]:6.1f}  v6={g6[r][ci]:6.1f}  "
                f"d={delta[r][ci]:+6.1f}  ace={ga[r][ci]:6.1f}  ori={go[r][ci]:6.1f}"
            )
    print("\nProbes:")
    for p in probes:
        print(
            f"  {p['src']:4} rpm={p['rpm']} log={p['log_tq']:.0f} "
            f"tqlim V5d={p['tqlim_v5d']} V6f={p['tqlim_v6f']} "
            f"HR_wish V5d={p['headroom_wish_v5d']:+.0f} V6f={p['headroom_wish_v6f']:+.0f}"
        )
    print("\n" + conf)


if __name__ == "__main__":
    main()
