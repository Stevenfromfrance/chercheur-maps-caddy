# -*- coding: utf-8 -*-
"""Export JSON data for V5f vs V5g compare page (GitHub Pages).

  python tools/export_v5f_v5g_compare.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

VEH = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
    r"\Caddy-CAYE-2013-03L906023PA-2531"
)
REPO = Path(r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy")
OUT = REPO / "compare-v5f-v5g-data.json"
ATLAS = REPO / "map-finder" / "atlas" / "9979.json"

ORI = (VEH / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin").read_bytes()
ACE = (VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_ACE_stage1_dpf_egr.NOCS").read_bytes()
V5F = (VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5f_final_tegt320.NOCS").read_bytes()
V5G = (VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5g_360_longband.NOCS").read_bytes()

NM_F, NM_O = 0.03125, -1024.0
EGT_F, EGT_O = 0.0625, -273.0

ACCPED = 0x1CF9C0
AP_COLS, AP_ROWS = 8, 16
PEDAL = [0.9765625, 4.00390625, 9.9609375, 23.046875, 50.0, 75.0, 84.9609375, 99.90234375]
RPM_AP = [
    0.0, 399.0, 609.0, 900.0, 1008.0, 1491.0, 1995.0, 2499.0,
    3003.0, 3990.0, 4998.0, 5355.0, 5600.0, 5700.0, 5800.0, 6000.0,
]

TQLIM = 0x1D3190
TQLIM_COLS, TQLIM_ROWS = 8, 26
ATM_AXIS = 0x1A42BA
ATM_F = 0.0829187

SMOKE = 0x1D1D18
SM_COLS, SM_ROWS = 19, 18

TEGT = 0x1D35A8
TEGT_COLS = TEGT_ROWS = 16
TEGT_AXIS_X = 0x1A6D1E
TEGT_AXIS_Y = 0x1A6256


def u16(b: bytes, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def dn(raw: int, offset: float = NM_O) -> float:
    return raw * NM_F + offset


def read_grid(buf: bytes, addr: int, cols: int, rows: int, offset: float = NM_O) -> list[list[float]]:
    g = []
    for r in range(rows):
        row = []
        for c in range(cols):
            row.append(round(dn(u16(buf, addr + (r * cols + c) * 2), offset), 2))
        g.append(row)
    return g


def main() -> None:
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    m = next(x for x in atlas["maps"] if x["id"] == "tqlim_base_pu_4A")
    rpm_tq = [
        round(u16(V5G, m["axis_y"]["addr"] + i * 2) * m["axis_y"]["factor"], 1)
        for i in range(TQLIM_ROWS)
    ]
    atm = [round(u16(V5G, ATM_AXIS + i * 2) * ATM_F, 1) for i in range(TQLIM_COLS)]
    ci = min(range(len(atm)), key=lambda i: abs(atm[i] - 1000.0))

    g_ap_f = read_grid(V5F, ACCPED, AP_COLS, AP_ROWS)
    g_ap_g = read_grid(V5G, ACCPED, AP_COLS, AP_ROWS)
    g_ap_a = read_grid(ACE, ACCPED, AP_COLS, AP_ROWS)
    g_ap_o = read_grid(ORI, ACCPED, AP_COLS, AP_ROWS)

    g_tq_f = read_grid(V5F, TQLIM, TQLIM_COLS, TQLIM_ROWS)
    g_tq_g = read_grid(V5G, TQLIM, TQLIM_COLS, TQLIM_ROWS)
    g_tq_a = read_grid(ACE, TQLIM, TQLIM_COLS, TQLIM_ROWS)
    g_tq_o = read_grid(ORI, TQLIM, TQLIM_COLS, TQLIM_ROWS)

    # smoke axis from atlas if present
    sm = next(x for x in atlas["maps"] if x["id"] == "smoke_mapA")
    boost = [
        round(u16(V5G, sm["axis_x"]["addr"] + i * 2) * sm["axis_x"]["factor"], 1)
        for i in range(SM_COLS)
    ]
    rpm_sm = [
        round(u16(V5G, sm["axis_y"]["addr"] + i * 2) * sm["axis_y"]["factor"], 1)
        for i in range(SM_ROWS)
    ]
    g_sm_f = read_grid(V5F, SMOKE, SM_COLS, SM_ROWS, offset=0.0)
    g_sm_g = read_grid(V5G, SMOKE, SM_COLS, SM_ROWS, offset=0.0)
    c_map = min(range(len(boost)), key=lambda i: abs(boost[i] - 2500))

    egts = [round(u16(V5G, TEGT_AXIS_X + i * 2) * EGT_F + EGT_O, 1) for i in range(TEGT_COLS)]
    rpm_tg = [float(u16(V5G, TEGT_AXIS_Y + i * 2)) for i in range(TEGT_ROWS)]
    g_tg_f = read_grid(V5F, TEGT, TEGT_COLS, TEGT_ROWS)
    g_tg_g = read_grid(V5G, TEGT, TEGT_COLS, TEGT_ROWS)
    g_tg_a = read_grid(ACE, TEGT, TEGT_COLS, TEGT_ROWS)
    g_tg_o = read_grid(ORI, TEGT, TEGT_COLS, TEGT_ROWS)
    # slice @ ~3000 rpm
    ri_tg = min(range(len(rpm_tg)), key=lambda i: abs(rpm_tg[i] - 3000))

    # WOT AccPed
    wot_rpm = [r for r in RPM_AP if 900 <= r <= 5600]
    wot_idx = [RPM_AP.index(r) for r in wot_rpm]
    wot = {
        "rpm": wot_rpm,
        "v5f": [g_ap_f[r][7] for r in wot_idx],
        "v5g": [g_ap_g[r][7] for r in wot_idx],
        "ace": [g_ap_a[r][7] for r in wot_idx],
        "ori": [g_ap_o[r][7] for r in wot_idx],
    }

    # pedal curves at key rpm
    pedal_rpms = [1491.0, 1995.0, 2499.0, 3003.0, 3990.0]
    pedal_curves = []
    for rpm in pedal_rpms:
        ri = RPM_AP.index(rpm)
        pedal_curves.append(
            {
                "rpm": rpm,
                "pedal": PEDAL,
                "v5f": g_ap_f[ri],
                "v5g": g_ap_g[ri],
                "ace": g_ap_a[ri],
                "ori": g_ap_o[ri],
            }
        )

    # tqlim ATM~1000
    tqlim_slice = {
        "rpm": rpm_tq,
        "atm": atm[ci],
        "v5f": [g_tq_f[r][ci] for r in range(TQLIM_ROWS)],
        "v5g": [g_tq_g[r][ci] for r in range(TQLIM_ROWS)],
        "ace": [g_tq_a[r][ci] for r in range(TQLIM_ROWS)],
        "ori": [g_tq_o[r][ci] for r in range(TQLIM_ROWS)],
    }

    smoke_slice = {
        "rpm": rpm_sm,
        "map": boost[c_map],
        "v5f": [g_sm_f[r][c_map] for r in range(SM_ROWS)],
        "v5g": [g_sm_g[r][c_map] for r in range(SM_ROWS)],
    }

    tegt_slice = {
        "egt": egts,
        "rpm": rpm_tg[ri_tg],
        "v5f": g_tg_f[ri_tg],
        "v5g": g_tg_g[ri_tg],
        "ace": g_tg_a[ri_tg],
        "ori": g_tg_o[ri_tg],
    }

    # reactive delta table
    reactive = []
    for rpm in (1491.0, 1995.0, 2499.0):
        ri = RPM_AP.index(rpm)
        for c, ped in enumerate(PEDAL):
            if ped < 45 or ped >= 95:
                continue
            reactive.append(
                {
                    "rpm": rpm,
                    "pedal": round(ped, 1),
                    "v5f": g_ap_f[ri][c],
                    "v5g": g_ap_g[ri][c],
                    "delta": round(g_ap_g[ri][c] - g_ap_f[ri][c], 1),
                }
            )

    data = {
        "title": "Caddy 9979 · V5f FINAL vs V5g 360 long band",
        "files": {
            "v5f": "Caddy_CAYE_03L906023TB_9979_MOD_V5f_final_tegt320.NOCS",
            "v5g": "Caddy_CAYE_03L906023TB_9979_MOD_V5g_360_longband.NOCS",
        },
    "chain": "wish 360 < tqlim 370 <= smoke 375 · rail inchangé · tegt jusqu'à 360 si EGT < ~800",
    "summary": {
      "wot_plateau_v5f": max(wot["v5f"][1:6]),
      "wot_plateau_v5g": max(wot["v5g"][1:6]),
            "rolloff_start": 3800,
            "tegt_max_v5f": max(max(row) for row in g_tg_f),
            "tegt_max_v5g": max(max(row) for row in g_tg_g),
            "smoke_unchanged": smoke_slice["v5f"] == smoke_slice["v5g"],
        },
        "wot": wot,
        "pedal_curves": pedal_curves,
        "tqlim_atm1000": tqlim_slice,
        "smoke_map2500": smoke_slice,
        "tegt_rpm3000": tegt_slice,
        "reactive_partials": reactive,
        "notes": [
            "Tip-in soft (pédale basse) conservé — deltas partiels ciblés 1500–2000.",
            "WOT V5g = 360 Nm plat jusqu’à ~3800 puis roll-off progressif (anti-falaise).",
            "tqlim aligné : 370 plat → descente dès 3800.",
            "smoke inchangé (375) = marge au-dessus de 360.",
            "tegt V5g autorise 360 à EGT modérée ; frein si plus chaud.",
        ],
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT)
    print("summary", data["summary"])


if __name__ == "__main__":
    main()
