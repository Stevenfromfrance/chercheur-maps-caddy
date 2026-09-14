# -*- coding: utf-8 -*-
"""Export AccPed V5d vs V6-preview JSON for local HTML compare (2D/3D).

V6 preview (AccPed only — not a flashable full carto):
  - Soft tip-in: blend low pedal cols toward ORI
  - Mid WOT plateau: keep V5d
  - High-rpm WOT hold: lift cells toward mid plateau fraction (before hardcut)

  python tools/export_v5d_v6_accped_preview.py
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
OUT_JSON = REPO / "compare-v5d-v6-accped-data.json"

NM_F, NM_O = 0.03125, -1024.0
COLS, ROWS = 8, 16
BANKS = [
    0x1CF9C0,
    0x1CFAC0,
    0x1CFBC0,
    0x1CFCC0,
    0x1CFDC0,
    0x1CFEC0,
    0x1CFFC0,
    0x1D0640,
]
PEDAL = [0.9765625, 4.00390625, 9.9609375, 23.046875, 50.0, 75.0, 84.9609375, 99.90234375]
RPM = [0.0, 399.0, 609.0, 900.0, 1008.0, 1491.0, 1995.0, 2499.0, 3003.0, 3990.0, 4998.0, 5355.0, 5600.0, 5700.0, 5800.0, 6000.0]


def u16(b: bytes | bytearray, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def decode_nm(raw: int) -> float:
    return raw * NM_F + NM_O


def encode_nm(val: float) -> int:
    return int(round((val - NM_O) / NM_F))


def read_bank(buf: bytes, addr: int) -> list[list[float]]:
    grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            off = addr + (r * COLS + c) * 2
            row.append(round(decode_nm(u16(buf, off)), 2))
        grid.append(row)
    return grid


def soft_k(pedal: float) -> float:
    """Blend toward ORI for tip-in (1=full ORI, 0=keep V5d)."""
    if pedal <= 10.5:
        return 0.90
    if pedal <= 15.0:
        return 0.75
    if pedal <= 24.0:
        return 0.75  # ~23% : closer to ORI (was 0.30 — still jerky)
    if pedal <= 35.0:
        return 0.20  # soft handoff into mid pedal
    return 0.0


def hold_decay(rpm: float) -> float | None:
    """
    Multiplier vs Nm @ ~3000 rpm on same pedal column.
    Almost flat to ~4000, then gentle drop — never above anchor (no bump).
    """
    if rpm < 3200:
        return None
    if rpm >= 5600:
        return None
    if rpm <= 4000:
        # 3200→4000 : 1.00 → 0.98 (quasi-plat)
        t = (rpm - 3200) / 800.0
        return 1.00 - t * 0.02
    if rpm <= 5000:
        # 4000→5000 : 0.98 → 0.88
        t = (rpm - 4000) / 1000.0
        return 0.98 - t * 0.10
    # 5000→5600 : 0.88 → 0.50
    t = (rpm - 5000) / 600.0
    return 0.88 - min(1.0, t) * 0.38


def mid_plateau(v5: list[list[float]]) -> float:
    """Mean WOT (last col) around 2000–3000 rpm."""
    vals = []
    for r, rpm in enumerate(RPM):
        if 1800 <= rpm <= 3200:
            vals.append(v5[r][COLS - 1])
    return sum(vals) / len(vals) if vals else 330.0


def value_near_rpm(grid: list[list[float]], c: int, target_rpm: float) -> float:
    best_i = min(range(len(RPM)), key=lambda i: abs(RPM[i] - target_rpm))
    return grid[best_i][c]


def wot_fill_target(rpm: float, anchor: float, v5_cell: float) -> float | None:
    """
    AccPed 100% high-rpm fill — gentler than V5d, not a flat 360 to cut.
    Anchor = WOT @ ~3003 (~333 Nm). Targets:
      3990: keep ~anchor (V5d already OK)
      4998: ~0.88 * anchor (~293) — pull toward hardcut
      5355: ~0.55 * anchor (~183) — taper into cut
      >=5600: leave V5d (hardcut zone)
    """
    if rpm < 3800 or rpm >= 5600:
        return None
    if rpm <= 4000:
        return None  # already ~plateau
    if rpm <= 5000:
        # 4000→5000 : 1.00 → 0.88 of anchor
        t = (rpm - 4000) / 1000.0
        target = anchor * (1.00 - t * 0.12)
    else:
        # 5000→5600 : 0.88 → 0.50 (but we stop applying at 5600)
        t = (rpm - 5000) / 600.0
        target = anchor * (0.88 - min(1.0, t) * 0.38)
    # Never raise above anchor; only fill if V5d is below target
    target = min(anchor, target)
    if v5_cell >= target - 0.5:
        return None
    return target


def build_v6(v5: list[list[float]], ori: list[list[float]]) -> tuple[list[list[float]], dict]:
    mid = mid_plateau(v5)
    out = [row[:] for row in v5]
    stats = {
        "mid_plateau_nm": round(mid, 1),
        "soft_cells": 0,
        "hold_cells": 0,
        "wot_fill_cells": 0,
        "unchanged": 0,
        "max_delta_pos": 0.0,
        "max_delta_neg": 0.0,
        "version": "v6e_soft23_hold_wotfill",
    }
    wot_anchor = value_near_rpm(v5, COLS - 1, 3003.0)
    for r, rpm in enumerate(RPM):
        for c, ped in enumerate(PEDAL):
            v = v5[r][c]
            o = ori[r][c]
            nv = v
            sk = soft_k(ped)
            if sk > 0:
                nv = v + (o - v) * sk
                stats["soft_cells"] += 1

            # Hold: 70–92% pedal only (not WOT 100%).
            # Anchor = cell @ ~3003 → never target > anchor (no triangle bump).
            if 70.0 <= ped < 95.0:
                decay = hold_decay(rpm)
                if decay is not None:
                    anchor = value_near_rpm(v5, c, 3003.0)
                    target = min(anchor, anchor * decay)
                    if nv < target - 0.5:
                        nv = nv + (target - nv) * 0.65
                        stats["hold_cells"] += 1

            # WOT 100% fill 4000→~5355 (gentle decay, not flat 360)
            if ped >= 95.0:
                wt = wot_fill_target(rpm, wot_anchor, v)
                if wt is not None and nv < wt - 0.5:
                    nv = nv + (wt - nv) * 0.85  # strong fill toward target
                    stats["wot_fill_cells"] += 1

            nv = round(nv, 2)
            if rpm >= 5600 and v <= 1.0 and o <= 1.0:
                nv = v
            d = nv - v
            if abs(d) < 0.05:
                stats["unchanged"] += 1
                nv = v
            else:
                stats["max_delta_pos"] = max(stats["max_delta_pos"], d)
                stats["max_delta_neg"] = min(stats["max_delta_neg"], d)
            out[r][c] = nv
    stats["max_delta_pos"] = round(stats["max_delta_pos"], 2)
    stats["max_delta_neg"] = round(stats["max_delta_neg"], 2)
    stats["wot_anchor_nm"] = round(wot_anchor, 1)
    return out, stats


def flat(grid: list[list[float]]) -> list[float]:
    return [v for row in grid for v in row]


def main() -> None:
    v5d = V5D.read_bytes()
    ori = ORI.read_bytes()
    banks = []
    for addr in BANKS:
        g5 = read_bank(v5d, addr)
        go = read_bank(ori, addr)
        g6, st = build_v6(g5, go)
        banks.append(
            {
                "addr": f"{addr:06X}",
                "v5d": g5,
                "ori": go,
                "v6": g6,
                "delta": [
                    [round(g6[r][c] - g5[r][c], 2) for c in range(COLS)]
                    for r in range(ROWS)
                ],
                "stats": st,
            }
        )

    primary = banks[0]
    payload = {
        "title": "AccPed_trq4A · V5d vs V6 preview",
        "note": "V6e preview AccPed — soft 0–23% ORI + hold 75–85% + WOT 100% fill 4000→5355 (pas plat 360). Pas un .NOCS flashable.",
        "unit": "Nm",
        "cols": COLS,
        "rows": ROWS,
        "axisX": PEDAL,
        "axisY": RPM,
        "axisXName": "Pédale %",
        "axisYName": "RPM",
        "banks": [{"addr": b["addr"], "stats": b["stats"]} for b in banks],
        "primary_addr": primary["addr"],
        "v5d": primary["v5d"],
        "v6": primary["v6"],
        "ori": primary["ori"],
        "delta": primary["delta"],
        "stats": primary["stats"],
        "flat": {
            "v5d": flat(primary["v5d"]),
            "v6": flat(primary["v6"]),
            "delta": flat(primary["delta"]),
        },
        "all_banks": {
            b["addr"]: {
                "v5d": b["v5d"],
                "v6": b["v6"],
                "delta": b["delta"],
                "stats": b["stats"],
            }
            for b in banks
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", OUT_JSON)
    print("Primary", primary["addr"], primary["stats"])
    # print WOT column compare
    print("WOT col (V5d -> V6) by rpm:")
    for r, rpm in enumerate(RPM):
        print(
            f"  {rpm:6.0f}  {primary['v5d'][r][-1]:7.1f} -> {primary['v6'][r][-1]:7.1f}  "
            f"d={primary['delta'][r][-1]:+6.1f}  soft10%={primary['v5d'][r][2]:6.1f}->{primary['v6'][r][2]:6.1f}"
        )


if __name__ == "__main__":
    main()
