# -*- coding: utf-8 -*-
"""Export turbo_base3B V5d vs ACE/ORI + V6d preview + log MAP_SP probes.

V6d = lift high-rpm / high-torque cells gently toward ACE (never above ACE).
Not a flashable NOCS — preview only.

  python tools/export_v5d_v6_turbo_preview.py
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
OUT = REPO / "compare-v5d-v6-turbo-data.json"

# Primary + a few sister banks (atlas priority)
BANKS = [
    0x1C04AC,  # primary
    0x1C072C,
    0x1C09AC,
    0x1C1B2C,
    0x1C202C,
]
COLS, ROWS = 16, 20
FACTOR = 0.0829187
TRQ_AXIS = 0x1A7B26  # factor 0.03125, offset 0
RPM_AXIS = 0x1A5B6C  # factor 1.0

# Log probes: (src, rpm, map_sp_hpa, map_act_hpa, tq)
PROBES = [
    ("RAIL", 2862, 2494, 2462, 335.6),
    ("RAIL", 3395, 2355, 2328, 333.9),
    ("RAIL", 3832, 2203, 2277, 333.4),  # holds torque
    ("RAIL2", 3145, 2267, 2282, 333.0),
    ("RAIL2", 3814, 2005, 1940, 255.4),  # soft
    ("INJ", 3364, 2212, 2268, 332.1),
    ("INJ", 3865, 2107, 2061, 226.0),  # soft
    ("INJ", 4006, 1754, 1818, 230.6),  # soft + MAP_SP drop
    ("INJ", 4236, 1926, 1926, 214.0),  # soft (map approx)
]


def u16(b: bytes | bytearray, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def read_axis(buf: bytes, addr: int, n: int, factor: float, offset: float = 0.0) -> list[float]:
    return [round(u16(buf, addr + i * 2) * factor + offset, 3) for i in range(n)]


def read_grid(buf: bytes, addr: int) -> list[list[float]]:
    out = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            raw = u16(buf, addr + (r * COLS + c) * 2)
            row.append(round(raw * FACTOR, 1))
        out.append(row)
    return out


def interp2d(grid: list[list[float]], xs: list[float], ys: list[float], x: float, y: float) -> float:
    """Bilinear; xs = torque cols, ys = rpm rows."""
    # clamp
    if x <= xs[0]:
        c0 = c1 = 0
        tx = 0.0
    elif x >= xs[-1]:
        c0 = c1 = COLS - 1
        tx = 0.0
    else:
        c1 = next(i for i in range(1, COLS) if xs[i] >= x)
        c0 = c1 - 1
        tx = (x - xs[c0]) / (xs[c1] - xs[c0]) if xs[c1] != xs[c0] else 0.0

    if y <= ys[0]:
        r0 = r1 = 0
        ty = 0.0
    elif y >= ys[-1]:
        r0 = r1 = ROWS - 1
        ty = 0.0
    else:
        r1 = next(i for i in range(1, ROWS) if ys[i] >= y)
        r0 = r1 - 1
        ty = (y - ys[r0]) / (ys[r1] - ys[r0]) if ys[r1] != ys[r0] else 0.0

    def cell(r, c):
        return grid[r][c]

    v00 = cell(r0, c0)
    v01 = cell(r0, c1)
    v10 = cell(r1, c0)
    v11 = cell(r1, c1)
    v0 = v00 + (v01 - v00) * tx
    v1 = v10 + (v11 - v10) * tx
    return v0 + (v1 - v0) * ty


def build_v6d(v5: list[list[float]], ace: list[list[float]], trq: list[float], rpm: list[float]) -> tuple[list[list[float]], dict]:
    """
    Lift toward ACE only where:
      - rpm >= ~3200
      - torque axis >= ~250 Nm
      - V5d < ACE
    Blend 55% of gap — keep stock-safe margin vs full ACE.
    """
    out = [row[:] for row in v5]
    stats = {"cells": 0, "max_d": 0.0, "sum_d": 0.0, "version": "v6d_turbo_hi_rpm_toward_ace"}
    for r, rv in enumerate(rpm):
        for c, tv in enumerate(trq):
            if rv < 3200 or tv < 250:
                continue
            a = ace[r][c]
            v = v5[r][c]
            if a <= v + 1.0:
                continue
            nv = round(v + (a - v) * 0.55, 1)
            # never exceed ACE
            nv = min(nv, a)
            d = nv - v
            if d > 0.5:
                out[r][c] = nv
                stats["cells"] += 1
                stats["max_d"] = max(stats["max_d"], d)
                stats["sum_d"] += d
    stats["max_d"] = round(stats["max_d"], 1)
    stats["sum_d"] = round(stats["sum_d"], 1)
    return out, stats


def main() -> None:
    v5d = V5D.read_bytes()
    ace = ACE.read_bytes()
    ori = ORI.read_bytes()

    trq = read_axis(v5d, TRQ_AXIS, COLS, 0.03125, 0.0)
    rpm = read_axis(v5d, RPM_AXIS, ROWS, 1.0, 0.0)
    # rpm axis fingerprint matches nm2iq — expect 800..5500
    if not (rpm[0] < rpm[-1]):
        raise SystemExit(f"bad rpm axis: {rpm[:3]}...{rpm[-3:]}")

    banks_out = []
    for addr in BANKS:
        g5 = read_grid(v5d, addr)
        ga = read_grid(ace, addr)
        go = read_grid(ori, addr)
        g6, st = build_v6d(g5, ga, trq, rpm)
        diff_ace = sum(
            1 for r in range(ROWS) for c in range(COLS) if abs(g5[r][c] - ga[r][c]) > 1.0
        )
        banks_out.append(
            {
                "addr": f"{addr:06X}",
                "v5d": g5,
                "v6": g6,
                "ace": ga,
                "ori": go,
                "delta": [
                    [round(g6[r][c] - g5[r][c], 1) for c in range(COLS)]
                    for r in range(ROWS)
                ],
                "stats": st,
                "identical_to_ace": diff_ace == 0,
                "cells_diff_v5d_ace": diff_ace,
                "v5d_max": max(max(row) for row in g5),
                "ace_max": max(max(row) for row in ga),
                "v6_max": max(max(row) for row in g6),
                "ori_max": max(max(row) for row in go),
            }
        )

    primary = next(b for b in banks_out if b["addr"] == "1C04AC")

    probes = []
    print("Probes MAP_SP vs turbo_base3B@1C04AC (interp @ rpm,tq):")
    for src, prpm, msp, mact, ptq in PROBES:
        req5 = interp2d(primary["v5d"], trq, rpm, ptq, prpm)
        reqa = interp2d(primary["ace"], trq, rpm, ptq, prpm)
        req6 = interp2d(primary["v6"], trq, rpm, ptq, prpm)
        req_o = interp2d(primary["ori"], trq, rpm, ptq, prpm)
        # Also wish-tq probe at 333 even if log tq soft — shows what map would ask if torque held
        req5_wish = interp2d(primary["v5d"], trq, rpm, 333.0, prpm)
        row = {
            "src": src,
            "rpm": prpm,
            "tq": ptq,
            "map_sp": msp,
            "map_act": mact,
            "turbo_v5d_at_log_tq": round(req5, 1),
            "turbo_v5d_at_wish333": round(req5_wish, 1),
            "turbo_v6": round(req6, 1),
            "turbo_ace": round(reqa, 1),
            "turbo_ori": round(req_o, 1),
            "gap_sp_vs_v5d_wish": round(msp - req5_wish, 1),
            "gap_sp_vs_v5d_logtq": round(msp - req5, 1),
        }
        probes.append(row)
        print(
            f"  {src:5} rpm={prpm} tq={ptq:.0f} MAP_SP={msp} | "
            f"turbo@wish333={row['turbo_v5d_at_wish333']} @logtq={row['turbo_v5d_at_log_tq']} "
            f"ACE={row['turbo_ace']} gap_sp_wish={row['gap_sp_vs_v5d_wish']:+.0f}"
        )

    # Verdict heuristic
    soft = [p for p in probes if p["tq"] < 300]
    hold = [p for p in probes if p["tq"] >= 320]
    # If map request at wish333 already near/above logged MAP_SP on soft points → request not the droop cause
    # If map request at wish333 >> MAP_SP on soft → something else lowers SP (limiter / atm / PID)
    # If map request at wish333 falls with rpm and tracks MAP_SP → turbo map shapes the droop
    soft_track = all(
        abs(p["gap_sp_vs_v5d_wish"]) < 120 or p["turbo_v5d_at_wish333"] < 2100 for p in soft
    )
    # Compare hold vs soft request at same ~3800
    hold_3800 = [p for p in hold if 3700 <= p["rpm"] <= 3900]
    soft_3800 = [p for p in soft if 3700 <= p["rpm"] <= 4000]

    summary_parts = []
    if primary["identical_to_ace"]:
        summary_parts.append("turbo_base3B V5d == ACE (pas de marge carto ACE).")
    else:
        summary_parts.append(
            f"turbo V5d differs ACE on {primary['cells_diff_v5d_ace']} cells "
            f"(max V5d {primary['v5d_max']} / ACE {primary['ace_max']})."
        )

    if hold_3800 and soft_3800:
        h = hold_3800[0]
        s = soft_3800[0]
        summary_parts.append(
            f"@~3800: hold MAP_SP={h['map_sp']} turbo@333={h['turbo_v5d_at_wish333']} "
            f"| soft MAP_SP={s['map_sp']} turbo@333={s['turbo_v5d_at_wish333']} "
            f"(même rpm/wish → même demande carte)."
        )
        if abs(h["turbo_v5d_at_wish333"] - s["turbo_v5d_at_wish333"]) < 30:
            summary_parts.append(
                "Demande turbo@333 identique hold vs soft → le trou MAP_SP "
                "vient d'ailleurs (ATM lim / N75 / air / charge), pas d'une case turbo basse."
            )
        else:
            summary_parts.append("Demande turbo@333 change entre hold et soft — revoir axes/interp.")

    # High rpm wish request trend
    hi = sorted([p for p in probes if p["rpm"] >= 3800], key=lambda p: p["rpm"])
    if hi:
        summary_parts.append(
            "turbo@wish333 vs rpm: "
            + ", ".join(f"{p['rpm']}=>{p['turbo_v5d_at_wish333']}" for p in hi)
        )

    payload = {
        "title": "turbo_base3B · V5d vs V6d preview (+ MAP_SP probes)",
        "note": (
            "V6d = lift rpm≥3200 & trq≥250 vers ACE (55% gap). "
            "Si V5d==ACE, V6d = V5d (rien à gagner). Preview only."
        ),
        "unit": "mbar",
        "axisX": trq,
        "axisY": rpm,
        "axisXName": "Couple interne (Nm)",
        "axisYName": "RPM",
        "primary_addr": "1C04AC",
        "banks": [
            {
                "addr": b["addr"],
                "stats": b["stats"],
                "identical_to_ace": b["identical_to_ace"],
                "cells_diff_v5d_ace": b["cells_diff_v5d_ace"],
                "v5d_max": b["v5d_max"],
                "ace_max": b["ace_max"],
                "v6_max": b["v6_max"],
            }
            for b in banks_out
        ],
        "v5d": primary["v5d"],
        "v6": primary["v6"],
        "ace": primary["ace"],
        "ori": primary["ori"],
        "delta": primary["delta"],
        "stats": primary["stats"],
        "identical_to_ace": primary["identical_to_ace"],
        "all_banks": {
            b["addr"]: {
                k: b[k]
                for k in (
                    "v5d",
                    "v6",
                    "ace",
                    "ori",
                    "delta",
                    "stats",
                    "identical_to_ace",
                    "v5d_max",
                    "ace_max",
                )
            }
            for b in banks_out
        },
        "log_probes": probes,
        "verdict": {
            "soft_tracks_map": soft_track,
            "summary": " ".join(summary_parts),
        },
    }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nVERDICT:", payload["verdict"]["summary"])
    print("Wrote", OUT)
    print(
        "Primary identical_to_ace=",
        primary["identical_to_ace"],
        "V6d cells",
        primary["stats"]["cells"],
        "max_d",
        primary["stats"]["max_d"],
    )


if __name__ == "__main__":
    main()
