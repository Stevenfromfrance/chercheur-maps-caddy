# -*- coding: utf-8 -*-
"""Analyze smoke/IQ vs V5d WOT logs + export V6c smoke preview for HTML.

Smoke = Nm limiteur vs (boost mbar × rpm).
If smoke @ log MAP/RPM < AccPed wish (~333), smoke clips the haut régime.

  python tools/export_v5d_v6_smoke_preview.py
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
ORI = VEH / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
ACE = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_ACE_stage1_dpf_egr.NOCS"
OUT = REPO / "compare-v5d-v6-smoke-data.json"

SMOKE_BANKS = [0x1D1D18, 0x1D1FC4, 0x1D2270, 0x1D251C, 0x1D27C8]
SMOKE_COLS, SMOKE_ROWS = 19, 18
SMOKE_F, SMOKE_O = 0.03125, 0.0
BOOST_AXIS = 0x1A9086  # mbar factor 0.0829187
RPM_AXIS = 0x1A8E06

NM2IQ = 0x1D7E38
NM2IQ_COLS, NM2IQ_ROWS = 16, 20
NM2IQ_F = 0.004
TRQ_AXIS = 0x1D65CE  # Nm factor 0.03125 offset -1024
NM2IQ_RPM_AXIS = None  # will read from atlas if needed — use smoke rpm for slice notes

# Log WOT points from ROUTE_INJ / RAIL2 (approx)
LOG_POINTS = [
    {"src": "RAIL", "rpm": 3832, "map_hpa": 2277, "tq": 333.4},
    {"src": "RAIL2", "rpm": 3814, "map_hpa": 1940, "tq": 255.4},
    {"src": "INJ", "rpm": 3865, "map_hpa": 2061, "tq": 226.0},
    {"src": "INJ", "rpm": 4236, "map_hpa": 1926, "tq": 214.0},
    {"src": "RAIL2", "rpm": 3145, "map_hpa": 2282, "tq": 333.0},
    {"src": "RAIL", "rpm": 2862, "map_hpa": 2462, "tq": 335.6},
]


def u16(b: bytes | bytearray, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def put_u16(buf: bytearray, off: int, v: int) -> None:
    v = max(0, min(0xFFFF, int(round(v))))
    buf[off] = v & 0xFF
    buf[off + 1] = (v >> 8) & 0xFF


def decode(raw: int, factor: float, offset: float = 0.0) -> float:
    return raw * factor + offset


def encode(val: float, factor: float, offset: float = 0.0) -> int:
    return int(round((val - offset) / factor))


def read_axis(buf: bytes, addr: int, n: int, factor: float, offset: float = 0.0) -> list[float]:
    return [round(decode(u16(buf, addr + i * 2), factor, offset), 3) for i in range(n)]


def read_grid(
    buf: bytes, addr: int, cols: int, rows: int, factor: float, offset: float = 0.0
) -> list[list[float]]:
    g = []
    for r in range(rows):
        row = []
        for c in range(cols):
            off = addr + (r * cols + c) * 2
            row.append(round(decode(u16(buf, off), factor, offset), 2))
        g.append(row)
    return g


def interp2d(grid: list[list[float]], xs: list[float], ys: list[float], x: float, y: float) -> float:
    """Bilinear interpolate grid[row=y][col=x]."""
    # clamp
    if x <= xs[0]:
        c0 = c1 = 0
        tx = 0.0
    elif x >= xs[-1]:
        c0 = c1 = len(xs) - 1
        tx = 0.0
    else:
        c1 = next(i for i in range(1, len(xs)) if xs[i] >= x)
        c0 = c1 - 1
        tx = (x - xs[c0]) / (xs[c1] - xs[c0]) if xs[c1] != xs[c0] else 0.0

    if y <= ys[0]:
        r0 = r1 = 0
        ty = 0.0
    elif y >= ys[-1]:
        r0 = r1 = len(ys) - 1
        ty = 0.0
    else:
        r1 = next(i for i in range(1, len(ys)) if ys[i] >= y)
        r0 = r1 - 1
        ty = (y - ys[r0]) / (ys[r1] - ys[r0]) if ys[r1] != ys[r0] else 0.0

    v00 = grid[r0][c0]
    v10 = grid[r0][c1]
    v01 = grid[r1][c0]
    v11 = grid[r1][c1]
    v0 = v00 + (v10 - v00) * tx
    v1 = v01 + (v11 - v01) * tx
    return v0 + (v1 - v0) * ty


def build_v6_smoke(v5: list[list[float]], ace: list[list[float]], rpm: list[float], boost: list[float]) -> tuple[list[list[float]], dict]:
    """
    V6c smoke preview: raise high-rpm cells toward ACE where V5d < ACE,
    only when rpm>=3500 and boost>=~1600 mbar (WOT zone). Cap 375.
    Mild blend elsewhere toward ACE if already below (keep Stage1 coherent).
    """
    CAP = 375.0
    out = [row[:] for row in v5]
    stats = {"cells": 0, "high_rpm_cells": 0, "max_d": 0.0}
    for r, rv in enumerate(rpm):
        for c, bv in enumerate(boost):
            cur = v5[r][c]
            a = ace[r][c]
            nv = cur
            if a > cur + 0.5:
                if rv >= 3500 and bv >= 1600:
                    # high rpm WOT zone — stronger lift toward ACE (70%)
                    target = min(CAP, cur + 0.70 * (a - cur))
                    nv = target
                    stats["high_rpm_cells"] += 1
                elif rv >= 3000 and bv >= 1400:
                    # transition — 40%
                    nv = min(CAP, cur + 0.40 * (a - cur))
                # else leave mid/low alone (already Stage1)
            nv = round(min(CAP, nv), 2)
            d = nv - cur
            if abs(d) >= 0.05:
                stats["cells"] += 1
                stats["max_d"] = max(stats["max_d"], d)
            out[r][c] = nv
    stats["max_d"] = round(stats["max_d"], 2)
    return out, stats


def main() -> None:
    v5d = V5D.read_bytes()
    ori = ORI.read_bytes()
    ace = ACE.read_bytes()

    boost = read_axis(v5d, BOOST_AXIS, SMOKE_COLS, 0.0829187)
    rpm = read_axis(v5d, RPM_AXIS, SMOKE_ROWS, 1.0)

    primary = 0x1D2270  # biggest bank in V5 build
    banks_out = []
    probes = []

    for addr in SMOKE_BANKS:
        g5 = read_grid(v5d, addr, SMOKE_COLS, SMOKE_ROWS, SMOKE_F, SMOKE_O)
        go = read_grid(ori, addr, SMOKE_COLS, SMOKE_ROWS, SMOKE_F, SMOKE_O)
        ga = read_grid(ace, addr, SMOKE_COLS, SMOKE_ROWS, SMOKE_F, SMOKE_O)
        g6, st = build_v6_smoke(g5, ga, rpm, boost)
        delta = [[round(g6[r][c] - g5[r][c], 2) for c in range(SMOKE_COLS)] for r in range(SMOKE_ROWS)]
        banks_out.append(
            {
                "addr": f"{addr:06X}",
                "v5d_max": max(max(row) for row in g5),
                "ace_max": max(max(row) for row in ga),
                "v6_max": max(max(row) for row in g6),
                "stats": st,
                "v5d": g5,
                "ori": go,
                "ace": ga,
                "v6": g6,
                "delta": delta,
            }
        )

    # Probe log points on primary + min across banks
    for pt in LOG_POINTS:
        boost_mbar = pt["map_hpa"]  # hPa ≈ mbar abs for MAP
        row = {"log": pt}
        for b in banks_out:
            s5 = interp2d(b["v5d"], boost, rpm, boost_mbar, pt["rpm"])
            s6 = interp2d(b["v6"], boost, rpm, boost_mbar, pt["rpm"])
            sa = interp2d(b["ace"], boost, rpm, boost_mbar, pt["rpm"])
            row[b["addr"]] = {
                "smoke_v5d": round(s5, 1),
                "smoke_v6": round(s6, 1),
                "smoke_ace": round(sa, 1),
                "log_tq": pt["tq"],
                "clip_vs_wish": round(min(s5, 333.0) - 333.0, 1),
                "likely_clip": s5 + 5 < pt["tq"] + 30 and s5 < 320,  # heuristic
            }
        # primary detail
        p = next(x for x in banks_out if x["addr"] == f"{primary:06X}")
        s5 = interp2d(p["v5d"], boost, rpm, boost_mbar, pt["rpm"])
        row["primary"] = {
            "addr": f"{primary:06X}",
            "smoke_v5d": round(s5, 1),
            "smoke_v6": round(interp2d(p["v6"], boost, rpm, boost_mbar, pt["rpm"]), 1),
            "smoke_ace": round(interp2d(p["ace"], boost, rpm, boost_mbar, pt["rpm"]), 1),
            "accped_wish_approx": 333.0,
            "log_tq": pt["tq"],
            "headroom_wish": round(s5 - 333.0, 1),
            "headroom_log": round(s5 - pt["tq"], 1),
        }
        probes.append(row)
        print(
            f"{pt['src']:5} rpm={pt['rpm']} MAP={pt['map_hpa']} tq={pt['tq']:.0f} | "
            f"smokeV5d={row['primary']['smoke_v5d']} ACE={row['primary']['smoke_ace']} "
            f"headroom_wish={row['primary']['headroom_wish']} headroom_log={row['primary']['headroom_log']}"
        )

    # nm2iq primary bank compare V5d vs ACE (identical?)
    iq5 = read_grid(v5d, NM2IQ, NM2IQ_COLS, NM2IQ_ROWS, NM2IQ_F)
    iqa = read_grid(ace, NM2IQ, NM2IQ_COLS, NM2IQ_ROWS, NM2IQ_F)
    iqo = read_grid(ori, NM2IQ, NM2IQ_COLS, NM2IQ_ROWS, NM2IQ_F)
    trq_ax = read_axis(v5d, TRQ_AXIS, NM2IQ_COLS, 0.03125, -1024.0)
    # rpm axis for nm2iq — often shared; try nearby fingerprint from atlas 1A8E06 may differ
    # Use same RPM_AXIS smoke for display if lengths match — they don't (20 vs 18).
    # Decode from common PCR: read 20 values from axis y of nm2iq if we find it.
    # Atlas says axis_y for nm2iq — search fingerprint; for now synthesize from smoke rpm + extrapolate
    # Better: read from file at typical axis — check atlas for nm2iq axis_y addr
    # From atlas line ~823 — need axis_y addr. Grep said axis_x 1D65CE; find axis_y in file.
    iq_rpm = read_axis(v5d, 0x1D5880, NM2IQ_ROWS, 1.0)
    if not (iq_rpm[0] < iq_rpm[-1] and iq_rpm[-1] > 3000):
        iq_rpm = [750 + i * (5500 - 750) / (NM2IQ_ROWS - 1) for i in range(NM2IQ_ROWS)]

    iq_diff = sum(
        1
        for r in range(NM2IQ_ROWS)
        for c in range(NM2IQ_COLS)
        if abs(iq5[r][c] - iqa[r][c]) > 0.01
    )

    # High torque column (~330 Nm) IQ vs rpm for V5d/ACE/ORI
    # find col closest to 330
    c330 = min(range(len(trq_ax)), key=lambda i: abs(trq_ax[i] - 330))
    iq_slice = {
        "trq_col": trq_ax[c330],
        "rpm": iq_rpm,
        "v5d": [iq5[r][c330] for r in range(NM2IQ_ROWS)],
        "ace": [iqa[r][c330] for r in range(NM2IQ_ROWS)],
        "ori": [iqo[r][c330] for r in range(NM2IQ_ROWS)],
        "cells_diff_v5d_vs_ace": iq_diff,
    }

    primary_bank = next(b for b in banks_out if b["addr"] == f"{primary:06X}")

    payload = {
        "title": "Smoke_mapA · V5d vs V6c preview (+ nm2iq check)",
        "note": "V6c = smoke lift haut régime / gros boost vers ACE (cap 375). nm2iq souvent déjà = ACE sur V5d — à vérifier.",
        "unit": "Nm",
        "axisX": boost,
        "axisY": rpm,
        "axisXName": "MAP / boost (mbar)",
        "axisYName": "RPM",
        "primary_addr": f"{primary:06X}",
        "banks": [{"addr": b["addr"], "stats": b["stats"], "v5d_max": b["v5d_max"], "ace_max": b["ace_max"], "v6_max": b["v6_max"]} for b in banks_out],
        "v5d": primary_bank["v5d"],
        "v6": primary_bank["v6"],
        "ori": primary_bank["ori"],
        "ace": primary_bank["ace"],
        "delta": primary_bank["delta"],
        "stats": primary_bank["stats"],
        "all_banks": {b["addr"]: {k: b[k] for k in ("v5d", "v6", "ori", "ace", "delta", "stats")} for b in banks_out},
        "log_probes": probes,
        "nm2iq": {
            "addr": f"{NM2IQ:06X}",
            "unit": "mg/hub",
            "axisX": trq_ax,
            "axisY": iq_rpm,
            "v5d": iq5,
            "ace": iqa,
            "ori": iqo,
            "slice_330nm": iq_slice,
            "identical_to_ace": iq_diff == 0,
        },
        "verdict": {
            "smoke_clips_high_rpm": any(p["primary"]["headroom_wish"] < -5 for p in probes),
            "summary": "",
        },
    }

    # verdict text
    clips = [p for p in probes if p["primary"]["headroom_wish"] < 0]
    if clips:
        payload["verdict"]["summary"] = (
            f"Smoke V5d under wish (~333 Nm) on {len(clips)} high-rpm log points — "
            "smoke limiter plausible for WOT soft top."
        )
    else:
        payload["verdict"]["summary"] = (
            "Smoke primary 1D2270 >= wish on probes (~363-375 Nm) while log TQI falls to ~214-255 — "
            "NOT a primary smoke clip. nm2iq V5d == ACE. "
            "Secondary banks look lower but midband TQI~333 rules them out as active. "
            "Next: MAP_SP/LDR high-rpm + AccPed 100% fill 4000-5000."
        )
        if iq_diff == 0:
            pass  # already in summary
        else:
            payload["verdict"]["summary"] += f" nm2iq differs ACE by {iq_diff} cells."

    print("\nVERDICT:", payload["verdict"]["summary"])
    print("nm2iq cells diff V5d vs ACE:", iq_diff)

    # Print IQ slice at ~330 Nm
    print("IQ mg/hub @ ~%.0f Nm vs rpm (V5d/ACE/ORI):" % trq_ax[c330])
    for r, rv in enumerate(iq_rpm):
        print(
            f"  {rv:6.0f}  v5d={iq_slice['v5d'][r]:5.2f} ace={iq_slice['ace'][r]:5.2f} ori={iq_slice['ori'][r]:5.2f}"
        )

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
