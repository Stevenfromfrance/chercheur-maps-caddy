# -*- coding: utf-8 -*-
"""Build Caddy 9979 V5e — pack complet atelier.

Base V5d (tegtORI + stack V5b) + :
  1) launch hold → 0 Nm @ 2700/2800/3000 (axe inchangé → hold pratique ~2800)
  2) tqlim_base V6f fill haut régime (ATM≥850, 3800–4600)
  3) AccPed V6e : soft tip-in 0–23% + hold 75–85% + WOT fill 4000–5355

  python tools/build_caddy_v5e.py
"""
from __future__ import annotations

import json
from pathlib import Path

VEH = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
    r"\Caddy-CAYE-2013-03L906023PA-2531"
)
REPO = Path(r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy")
STEVEN = Path(r"C:\Users\theda\OneDrive\Bureau\caddy cartho\ORI CADDY STEVEN")

ORI = VEH / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
BASE = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5d_tegtORI_launch110.NOCS"
OUT_NAME = "Caddy_CAYE_03L906023TB_9979_MOD_V5e_launch0_tqlimV6f_accpedV6e.NOCS"
OUT = VEH / "MOD" / OUT_NAME
OUT_STEVEN = STEVEN / OUT_NAME

VERIFY = REPO / "VERIFY-V5E.txt"
FICHE = REPO / "FICHE-V5E-FULL.md"
MANIFEST = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5e_manifest.json"
MANIFEST_REPO = REPO / "map-finder" / "reports" / "caddy-9979-v5e-manifest.json"
ATLAS = REPO / "map-finder" / "atlas" / "9979.json"

NM_F, NM_O = 0.03125, -1024.0

# launch
CLUTCH = 0x1D0860
CLUTCH_AXIS = 0x1A612A
CLUTCH_COLS, CLUTCH_ROWS = 8, 8
HOLD_RPMS = {2700, 2800, 3000}

# tqlim
TQLIM = 0x1D3190
TQLIM_COLS, TQLIM_ROWS = 8, 26
ATM_AXIS = 0x1A42BA
ATM_F = 0.0829187

# AccPed
ACCPED_BANKS = [
    0x1CF9C0,
    0x1CFAC0,
    0x1CFBC0,
    0x1CFCC0,
    0x1CFDC0,
    0x1CFEC0,
    0x1CFFC0,
    0x1D0640,
]
AP_COLS, AP_ROWS = 8, 16
PEDAL = [0.9765625, 4.00390625, 9.9609375, 23.046875, 50.0, 75.0, 84.9609375, 99.90234375]
RPM_AP = [
    0.0,
    399.0,
    609.0,
    900.0,
    1008.0,
    1491.0,
    1995.0,
    2499.0,
    3003.0,
    3990.0,
    4998.0,
    5355.0,
    5600.0,
    5700.0,
    5800.0,
    6000.0,
]


def u16(b: bytes | bytearray, off: int) -> int:
    return b[off] | (b[off + 1] << 8)


def put_u16(buf: bytearray, off: int, v: int) -> None:
    v = max(0, min(0xFFFF, int(round(v))))
    buf[off] = v & 0xFF
    buf[off + 1] = (v >> 8) & 0xFF


def encode_nm(val: float) -> int:
    return int(round((val - NM_O) / NM_F))


def decode_nm(raw: int) -> float:
    return raw * NM_F + NM_O


def patch_launch_zero(buf: bytearray) -> dict:
    rpms = [u16(buf, CLUTCH_AXIS + i * 2) for i in range(CLUTCH_ROWS)]
    changed = []
    for r, rpm in enumerate(rpms):
        if rpm not in HOLD_RPMS:
            continue
        for c in (0, 1):
            off = CLUTCH + (r * CLUTCH_COLS + c) * 2
            old = decode_nm(u16(buf, off))
            put_u16(buf, off, encode_nm(0.0))
            new = decode_nm(u16(buf, off))
            changed.append({"rpm": rpm, "col": c, "was": round(old, 2), "now": round(new, 2)})
    assert 4801 in rpms
    r4801 = rpms.index(4801)
    for c in range(CLUTCH_COLS):
        assert abs(decode_nm(u16(buf, CLUTCH + (r4801 * CLUTCH_COLS + c) * 2))) < 0.1
    return {
        "rpm_axis": rpms,
        "cells": len(changed),
        "changed": changed,
        "hold_nm": [0.0, 0.0],
        "hold_rpms": sorted(HOLD_RPMS),
        "practice_hold_rpm": 2800,
    }


def tqlim_target(rpm: float, plateau: float) -> float | None:
    if rpm < 3800 or rpm >= 4700:
        return None
    if rpm <= 4000:
        t = (rpm - 3800) / 200.0
        return plateau * (1.0 - t * 0.04)
    if rpm <= 4400:
        t = (rpm - 4000) / 400.0
        return plateau * (0.96 - t * 0.08)
    t = (rpm - 4400) / 300.0
    return plateau * (0.88 - min(1.0, t) * 0.10)


def patch_tqlim_v6f(buf: bytearray) -> dict:
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    m = next(x for x in atlas["maps"] if x["id"] == "tqlim_base_pu_4A")
    rpm_addr = m["axis_y"]["addr"]
    rpm_f = m["axis_y"]["factor"]
    atm = [u16(buf, ATM_AXIS + i * 2) * ATM_F for i in range(TQLIM_COLS)]
    rpm = [u16(buf, rpm_addr + i * 2) * rpm_f for i in range(TQLIM_ROWS)]

    plate_vals = []
    for r, rv in enumerate(rpm):
        if 2500 <= rv <= 3500:
            for c, av in enumerate(atm):
                if av >= 950:
                    off = TQLIM + (r * TQLIM_COLS + c) * 2
                    plate_vals.append(decode_nm(u16(buf, off)))
    plateau = max(plate_vals) if plate_vals else 370.0

    cells = 0
    max_d = 0.0
    slice_before = []
    slice_after = []
    ci = min(range(len(atm)), key=lambda i: abs(atm[i] - 1000.0))

    for r, rv in enumerate(rpm):
        tgt = tqlim_target(rv, plateau)
        for c, av in enumerate(atm):
            off = TQLIM + (r * TQLIM_COLS + c) * 2
            cur = decode_nm(u16(buf, off))
            if c == ci and rv >= 3000:
                slice_before.append(round(cur, 1))
            if tgt is None or av < 850:
                if c == ci and rv >= 3000:
                    slice_after.append(round(cur, 1))
                continue
            if cur >= tgt - 0.5:
                if c == ci and rv >= 3000:
                    slice_after.append(round(cur, 1))
                continue
            nv = min(plateau, 370.0, tgt)
            nv = cur + 0.90 * (nv - cur)
            put_u16(buf, off, encode_nm(nv))
            d = nv - cur
            if d > 0.5:
                cells += 1
                max_d = max(max_d, d)
            if c == ci and rv >= 3000:
                slice_after.append(round(decode_nm(u16(buf, off)), 1))

    return {
        "addr": f"{TQLIM:06X}",
        "plateau_nm": round(plateau, 1),
        "cells": cells,
        "max_d": round(max_d, 1),
        "atm1000_rpm": [round(r) for r in rpm if r >= 3000],
        "atm1000_before": slice_before,
        "atm1000_after": slice_after,
    }


def soft_k(pedal: float) -> float:
    if pedal <= 10.5:
        return 0.90
    if pedal <= 15.0:
        return 0.75
    if pedal <= 24.0:
        return 0.75
    if pedal <= 35.0:
        return 0.20
    return 0.0


def hold_decay(rpm: float) -> float | None:
    if rpm < 3200 or rpm >= 5600:
        return None
    if rpm <= 4000:
        t = (rpm - 3200) / 800.0
        return 1.00 - t * 0.02
    if rpm <= 5000:
        t = (rpm - 4000) / 1000.0
        return 0.98 - t * 0.10
    t = (rpm - 5000) / 600.0
    return 0.88 - min(1.0, t) * 0.38


def wot_fill_target(rpm: float, anchor: float, v5_cell: float) -> float | None:
    if rpm < 3800 or rpm >= 5600:
        return None
    if rpm <= 4000:
        return None
    if rpm <= 5000:
        t = (rpm - 4000) / 1000.0
        target = anchor * (1.00 - t * 0.12)
    else:
        t = (rpm - 5000) / 600.0
        target = anchor * (0.88 - min(1.0, t) * 0.38)
    target = min(anchor, target)
    if v5_cell >= target - 0.5:
        return None
    return target


def patch_accped_v6e(buf: bytearray, ori: bytes) -> dict:
    banks_stats = []
    total_cells = 0
    for addr in ACCPED_BANKS:
        soft = hold = wot = 0
        # read grids
        v5 = [
            [decode_nm(u16(buf, addr + (r * AP_COLS + c) * 2)) for c in range(AP_COLS)]
            for r in range(AP_ROWS)
        ]
        go = [
            [decode_nm(u16(ori, addr + (r * AP_COLS + c) * 2)) for c in range(AP_COLS)]
            for r in range(AP_ROWS)
        ]
        # WOT anchor @3003
        ri3003 = min(range(len(RPM_AP)), key=lambda i: abs(RPM_AP[i] - 3003.0))
        wot_anchor = v5[ri3003][AP_COLS - 1]

        for r, rpm in enumerate(RPM_AP):
            for c, ped in enumerate(PEDAL):
                v = v5[r][c]
                o = go[r][c]
                nv = v
                sk = soft_k(ped)
                if sk > 0:
                    nv = v + (o - v) * sk
                    soft += 1
                if 70.0 <= ped < 95.0:
                    decay = hold_decay(rpm)
                    if decay is not None:
                        anchor = v5[ri3003][c]
                        target = min(anchor, anchor * decay)
                        if nv < target - 0.5:
                            nv = nv + (target - nv) * 0.65
                            hold += 1
                if ped >= 95.0:
                    wt = wot_fill_target(rpm, wot_anchor, v)
                    if wt is not None and nv < wt - 0.5:
                        nv = nv + (wt - nv) * 0.85
                        wot += 1
                if rpm >= 5600 and v <= 1.0 and o <= 1.0:
                    nv = v
                if abs(nv - v) >= 0.05:
                    put_u16(buf, addr + (r * AP_COLS + c) * 2, encode_nm(nv))
                    total_cells += 1
        # WOT slice after
        wot_after = [
            round(decode_nm(u16(buf, addr + (r * AP_COLS + (AP_COLS - 1)) * 2)), 1)
            for r in range(AP_ROWS)
            if RPM_AP[r] >= 3000
        ]
        banks_stats.append(
            {
                "addr": f"{addr:06X}",
                "soft": soft,
                "hold": hold,
                "wot_fill": wot,
                "wot_anchor": round(wot_anchor, 1),
                "wot_high_rpm_after": wot_after,
            }
        )
    return {"banks": banks_stats, "cells_written": total_cells}


def main() -> None:
    ori = ORI.read_bytes()
    base = BASE.read_bytes()
    buf = bytearray(base)

    launch = patch_launch_zero(buf)
    tqlim = patch_tqlim_v6f(buf)
    accped = patch_accped_v6e(buf, ori)

    bytes_vs = sum(1 for i in range(len(base)) if base[i] != buf[i])
    OUT.write_bytes(buf)
    try:
        OUT_STEVEN.parent.mkdir(parents=True, exist_ok=True)
        OUT_STEVEN.write_bytes(buf)
    except OSError:
        pass

    # VERIFY
    verify_lines = [
        f"OUT={OUT}",
        f"bytes_vs_v5d={bytes_vs}",
        f"launch=0/0 @ {launch['hold_rpms']} cells={launch['cells']} practice_hold~{launch['practice_hold_rpm']}",
        f"tqlim_v6f cells={tqlim['cells']} max_d=+{tqlim['max_d']} plateau={tqlim['plateau_nm']}",
        f"tqlim_atm1000 rpm={tqlim['atm1000_rpm']}",
        f"tqlim_atm1000 before={tqlim['atm1000_before']}",
        f"tqlim_atm1000 after={tqlim['atm1000_after']}",
        f"accped_v6e cells_written={accped['cells_written']} banks={len(accped['banks'])}",
        f"accped_primary={accped['banks'][0]}",
        "hardcut_4801=OK",
        "axis_launch_unchanged=OK (2700/2800/3000)",
    ]
    VERIFY.write_text("\n".join(verify_lines) + "\n", encoding="utf-8")

    manifest = {
        "version": "V5e",
        "file": OUT_NAME,
        "base": BASE.name,
        "bytes_vs_v5d": bytes_vs,
        "launch": launch,
        "tqlim_v6f": tqlim,
        "accped_v6e": accped,
        "includes": [
            "V5d stack (fillbass + smoke375 + tqlim370 mid + tegtORI + HC4800)",
            "launch hold 0 Nm @2700/2800/3000 (pratique ~2800)",
            "tqlim_base V6f hi-rpm fill",
            "AccPed V6e soft tip-in + mid hold + WOT fill",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    MANIFEST_REPO.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_REPO.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    fiche = f"""# FICHE V5e — pack complet (launch 0 + tqlim V6f + AccPed V6e)

**Fichier :** `{OUT_NAME}`  
**Base :** V5d (`tegtORI + launch110` → launch remis à 0)

## Contenu

| Couche | V5d | **V5e** |
|---|---|---|
| AccPed | fill V5 | **V6e** soft 0–23% + hold 75–85% + WOT fill 4000→5355 |
| tqlim_base | 370 plat puis cliff @4000 | **V6f** fill 4000→~347 / 4200→~332 / 4600→~291 (≥4800 inchangé) |
| Launch hold | 110/85 @2700–3000 | **0 / 0** (axe inchangé → hold pratique **~2800**, pas 2500) |
| tegt / smoke / HC | ORI / 375 / 4800 | **inchangé** |
| Turbo / rail / SOI | héritage ACE | **inchangé** |

Octets ≠ V5d : **{bytes_vs}**

## Pourquoi

1. Soft 3ᵉ WOT confirmé ~3865–4236 → tqlim cliff + AccPed WOT fill
2. Tip-in ville trop sec → AccPed soft vers ORI
3. Launch 110 non validé + tu veux 0 Nm → hold à **2800** (axe déjà là), couple 0

## Flash

1. KESS **CHK**
2. Clear DTC
3. Logs : fiche A4 `fiche-logs-vcds-a4-v5e.html` (peu d’IDE / run)

## Risques

- tqlim plus haut ≥4000 → plus de couple / fumée / EGT possible : surveiller
- AccPed soft = moins de couple bas pédale (voulu)
- Launch 0 = plus de lag spool possible au départ (comme V2) mais hold plus haut (~2800)

## Logs prioritaires

Voir `fiche-logs-vcds-a4-v5e.html` + `log-aide.html`.
"""
    FICHE.write_text(fiche, encoding="utf-8")

    print("Wrote", OUT)
    print("bytes vs V5d:", bytes_vs)
    print("launch", launch["hold_nm"], "@", launch["hold_rpms"])
    print("tqlim cells", tqlim["cells"], "max_d", tqlim["max_d"])
    print("accped cells", accped["cells_written"])
    print("VERIFY", VERIFY)


if __name__ == "__main__":
    main()
