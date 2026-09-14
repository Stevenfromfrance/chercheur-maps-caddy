# -*- coding: utf-8 -*-
"""Build Caddy 9979 V5f FINAL — pack atelier complet.

Base V5e (launch0 + tqlim V6f + AccPed V6e + stack V5d) + :
  tqlim_tegt_temp = milieu ORI↔ACE (blend 50 % → max ~320 Nm)

  python tools/build_caddy_v5f.py
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
ACE = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_ACE_stage1_dpf_egr.NOCS"
BASE = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5e_launch0_tqlimV6f_accpedV6e.NOCS"
OUT_NAME = "Caddy_CAYE_03L906023TB_9979_MOD_V5f_final_tegt320.NOCS"
OUT = VEH / "MOD" / OUT_NAME
OUT_STEVEN = STEVEN / OUT_NAME

VERIFY = REPO / "VERIFY-V5F.txt"
FICHE = REPO / "FICHE-V5F-FINAL.md"
MANIFEST = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5f_manifest.json"
MANIFEST_REPO = REPO / "map-finder" / "reports" / "caddy-9979-v5f-manifest.json"

TEGT = 0x1D35A8
TEGT_LEN = 512  # 16×16
TEGT_AXIS_X = 0x1A6D1E  # EGT °C
TEGT_AXIS_Y = 0x1A6256  # RPM
TEGT_COLS = TEGT_ROWS = 16
NM_F, NM_O = 0.03125, -1024.0
EGT_F, EGT_O = 0.0625, -273.0

# 0.0 = ORI, 1.0 = ACE → 0.5 ≈ max 320 Nm (entre 290 et 350)
BLEND = 0.5

CLUTCH = 0x1D0860
CLUTCH_AXIS = 0x1A612A
CLUTCH_COLS, CLUTCH_ROWS = 8, 8


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


def decode_egt(raw: int) -> float:
    return raw * EGT_F + EGT_O


def patch_tegt_mid(buf: bytearray, ori: bytes, ace: bytes) -> dict:
    cells = TEGT_LEN // 2
    changed = 0
    max_ori = max_ace = max_after = -1e9
    samples = []

    egts = [decode_egt(u16(buf, TEGT_AXIS_X + i * 2)) for i in range(TEGT_COLS)]
    rpms = [float(u16(buf, TEGT_AXIS_Y + i * 2)) for i in range(TEGT_ROWS)]

    for i in range(cells):
        off = TEGT + i * 2
        o = decode_nm(u16(ori, off))
        a = decode_nm(u16(ace, off))
        target = o + BLEND * (a - o)
        put_u16(buf, off, encode_nm(target))
        n = decode_nm(u16(buf, off))
        if abs(n - o) > 0.05:
            changed += 1
        max_ori = max(max_ori, o)
        max_ace = max(max_ace, a)
        max_after = max(max_after, n)

    # samples @ hot EGT cols (≥780) mid/hi rpm for VERIFY
    for r, rpm in enumerate(rpms):
        if rpm not in (3750.0, 4000.0, 4250.0, 3000.0):
            # axis may not be exact — pick nearest interesting
            if abs(rpm - 3750) > 50 and abs(rpm - 4000) > 50 and abs(rpm - 3000) > 50:
                continue
        for c, egt in enumerate(egts):
            if egt < 780:
                continue
            off = TEGT + (r * TEGT_COLS + c) * 2
            samples.append(
                {
                    "rpm": rpm,
                    "egt": round(egt, 1),
                    "ori": round(decode_nm(u16(ori, off)), 1),
                    "ace": round(decode_nm(u16(ace, off)), 1),
                    "v5f": round(decode_nm(u16(buf, off)), 1),
                }
            )
            if len(samples) >= 8:
                break
        if len(samples) >= 8:
            break

    return {
        "addr": f"{TEGT:06X}",
        "blend": BLEND,
        "cells_changed": changed,
        "max_nm_ori": round(max_ori, 1),
        "max_nm_ace": round(max_ace, 1),
        "max_nm_v5f": round(max_after, 1),
        "egt_axis_min_hot": round(min(e for e in egts if e >= 700), 1) if any(e >= 700 for e in egts) else None,
        "egt_axis": [round(e, 1) for e in egts],
        "samples_hot": samples,
    }


def check_launch_zero(buf: bytearray) -> dict:
    rpms = [u16(buf, CLUTCH_AXIS + i * 2) for i in range(CLUTCH_ROWS)]
    holds = {}
    for r, rpm in enumerate(rpms):
        if rpm in (2700, 2800, 3000):
            holds[rpm] = [
                round(decode_nm(u16(buf, CLUTCH + (r * CLUTCH_COLS + c) * 2)), 2)
                for c in (0, 1)
            ]
    assert 4801 in rpms
    r4801 = rpms.index(4801)
    for c in range(CLUTCH_COLS):
        assert abs(decode_nm(u16(buf, CLUTCH + (r4801 * CLUTCH_COLS + c) * 2))) < 0.1
    return {"hold_nm_by_rpm": holds, "hardcut_4801": "OK"}


def main() -> None:
    ori = ORI.read_bytes()
    ace = ACE.read_bytes()
    base = BASE.read_bytes()
    assert len(ori) == len(ace) == len(base), "size mismatch"
    buf = bytearray(base)

    tegt = patch_tegt_mid(buf, ori, ace)
    launch = check_launch_zero(buf)

    bytes_vs = sum(1 for i in range(len(base)) if base[i] != buf[i])
    OUT.write_bytes(buf)
    try:
        OUT_STEVEN.parent.mkdir(parents=True, exist_ok=True)
        OUT_STEVEN.write_bytes(buf)
    except OSError:
        pass

    verify = [
        f"OUT={OUT}",
        f"bytes_vs_v5e={bytes_vs}",
        f"tegt_blend={BLEND} (ORI↔ACE) max {tegt['max_nm_ori']}→{tegt['max_nm_v5f']} (ACE={tegt['max_nm_ace']})",
        f"tegt_cells_changed={tegt['cells_changed']}",
        f"tegt_egt_axis={tegt['egt_axis']}",
        f"tegt_samples_hot={tegt['samples_hot']}",
        f"launch_hold={launch['hold_nm_by_rpm']}",
        f"hardcut_4801={launch['hardcut_4801']}",
        "stack=V5e + tegt mid320",
        "includes=launch0 + tqlimV6f + AccPedV6e + tegt50%ORI-ACE",
    ]
    VERIFY.write_text("\n".join(verify) + "\n", encoding="utf-8")

    manifest = {
        "version": "V5f",
        "role": "FINAL flash atelier",
        "file": OUT_NAME,
        "base": BASE.name,
        "bytes_vs_v5e": bytes_vs,
        "tegt_mid": tegt,
        "launch_check": launch,
        "includes": [
            "V5e: launch 0 @2700/2800/3000",
            "V5e: tqlim_base V6f hi-rpm fill",
            "V5e: AccPed V6e soft+hold+WOT fill",
            "V5d stack: fillbass + smoke375 + tqlim370 mid + HC4800",
            "V5f: tqlim_tegt blend 50% ORI→ACE (~320 Nm max)",
        ],
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    MANIFEST_REPO.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_REPO.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    fiche = f"""# FICHE V5f — FINAL (V5e + EGT lim milieu ~320)

**Fichier :** `{OUT_NAME}`  
**Base :** V5e (`launch0 + tqlimV6f + AccPedV6e`)  
**Rôle :** carto flash finale atelier (derniers avancés)

## Contenu

| Couche | V5e | **V5f FINAL** |
|---|---|---|
| AccPed | V6e | **inchangé** |
| tqlim_base | V6f fill haut régime | **inchangé** |
| Launch | 0 Nm @2700/2800/3000 | **inchangé** (hold pratique **~2800**) |
| **tqlim_tegt** | ORI max **290** | **milieu ORI↔ACE** blend 50 % → max **~{tegt['max_nm_v5f']:.0f}** (ACE=350) |
| smoke / HC / turbo / rail | inchangé | **inchangé** |

Octets ≠ V5e : **{bytes_vs}**

## Pourquoi tegt milieu

- Jour chaud = moins de pêche → ORI 290 trop strict possible
- ACE 350 = plafond Stage1 connu, mais V5e monte déjà le haut régime
- Compromis **~320** = entre safe ORI et ACE, sans aller au-dessus d’ACE

## Flash

1. KESS **CHK**
2. Clear DTC
3. Logs : `fiche-logs-vcds-a4-v5e.html` (mêmes runs, soft = **V5f**)

## Risques

- tegt plus haut qu’ORI → un peu moins de frein couple à EGT élevée (voulu)
- Toujours surveiller fumée / EGT ressenti / MAP sur ROUTE_SOFT

## VERIFY

Voir `VERIFY-V5F.txt`.
"""
    FICHE.write_text(fiche, encoding="utf-8")

    print("Wrote", OUT)
    print("bytes vs V5e:", bytes_vs)
    print(
        "tegt max ORI/ACE/V5f",
        tegt["max_nm_ori"],
        tegt["max_nm_ace"],
        tegt["max_nm_v5f"],
    )
    print("VERIFY", VERIFY)


if __name__ == "__main__":
    main()
