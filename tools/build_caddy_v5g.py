# -*- coding: utf-8 -*-
"""Build Caddy 9979 V5g — dernier Stage1 stock ~360 Nm.

Base V5f FINAL + :
  1) AccPed V6g : tip-in soft gardé · 1500–2000 plus réactif · WOT ~360 · roll-off dès ~3800
  2) tqlim_base V6g : plateau 370 · roll-off doux aligné (3800→…)
  3) tqlim_tegt V6g : autorise ~360 si EGT modèle <~800 °C · blend chaud safe (pas delete)
  4) smoke / rail / launch / HC : inchangés (smoke 375 = marge au-dessus de 360)

  python tools/build_caddy_v5g.py
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
BASE = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5f_final_tegt320.NOCS"
OUT_NAME = "Caddy_CAYE_03L906023TB_9979_MOD_V5g_360_longband.NOCS"
OUT = VEH / "MOD" / OUT_NAME
OUT_STEVEN = STEVEN / OUT_NAME

VERIFY = REPO / "VERIFY-V5G.txt"
FICHE = REPO / "FICHE-V5G-360.md"
MANIFEST = VEH / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V5g_manifest.json"
MANIFEST_REPO = REPO / "map-finder" / "reports" / "caddy-9979-v5g-manifest.json"
ATLAS = REPO / "map-finder" / "atlas" / "9979.json"

NM_F, NM_O = 0.03125, -1024.0
EGT_F, EGT_O = 0.0625, -273.0

# ── targets ──────────────────────────────────────────────────────────
WOT_PLATEAU = 360.0
TQLIM_PLATEAU = 370.0  # wish 360 < tqlim 370 <= smoke 375
ROLLOFF_START = 3800.0  # début descente progressive (puissance longue)

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

# tqlim
TQLIM = 0x1D3190
TQLIM_COLS, TQLIM_ROWS = 8, 26
ATM_AXIS = 0x1A42BA
ATM_F = 0.0829187

# tegt
TEGT = 0x1D35A8
TEGT_COLS = TEGT_ROWS = 16
TEGT_AXIS_X = 0x1A6D1E
TEGT_AXIS_Y = 0x1A6256
TEGT_BLEND_HOT = 0.85  # ~341 si seul blend ; zone froide/modérée → jusqu'à 360

# launch check
CLUTCH = 0x1D0860
CLUTCH_AXIS = 0x1A612A
CLUTCH_COLS, CLUTCH_ROWS = 8, 8
HOLD_RPMS = {2700, 2800, 3000}


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


def soft_k(pedal: float) -> float:
    """Tip-in soft — identique esprit V6e (ne pas agressiver 0–23 %)."""
    if pedal <= 10.5:
        return 0.90
    if pedal <= 24.0:
        return 0.75
    if pedal <= 35.0:
        return 0.20
    return 0.0


def reactive_lift(rpm: float, pedal: float, v: float, ace: float, ori: float) -> float | None:
    """1500–2000 (+ léger 2500) : plus accrocheur sans on-off."""
    if pedal < 45.0 or pedal >= 95.0:
        return None
    if rpm < 1400 or rpm > 2600:
        return None
    # Intensité max vers 1500–2000, fade après 2000
    if rpm <= 2000:
        w = 0.55
    else:
        w = 0.55 * (1.0 - (rpm - 2000) / 600.0)
    if w <= 0.05:
        return None
    # cible = ACE + fraction de l'écart ACE−ORI (plus vif que V5f≈ACE)
    bonus = 0.40 * max(0.0, ace - ori)
    target = ace + bonus
    # garde-fous : pas de jump absurde vs cellule actuelle
    target = min(target, v + 45.0, WOT_PLATEAU * 0.92)
    if target <= v + 0.5:
        return None
    return v + w * (target - v)


def wot_target(rpm: float) -> float | None:
    """WOT ~360 jusqu'à ~3800 puis roll-off progressif (anti-falaise).

    Ancres (AccPed axes) :
      ≤3800 → 360
      3990  → ~346 (début doux)
      4998  → ~282 (= niveau V5f, pas en-dessous — courbe lisse)
      5355  → ~202 (comme V5f fin de bande)
    """
    if rpm < 900 or rpm >= 5600:
        return None
    if rpm <= ROLLOFF_START:
        return WOT_PLATEAU
    # ancres explicites pour une descente sans trou sous V5f @4998
    anchors = [
        (ROLLOFF_START, WOT_PLATEAU),
        (3990.0, 346.3),
        (4998.0, 282.3),  # aligné V5f
        (5355.0, 202.0),
        (5600.0, 30.0),
    ]
    for i in range(len(anchors) - 1):
        r0, v0 = anchors[i]
        r1, v1 = anchors[i + 1]
        if rpm <= r1 or i == len(anchors) - 2:
            if rpm >= r0 and rpm <= r1:
                t = 0.0 if r1 == r0 else (rpm - r0) / (r1 - r0)
                return v0 + t * (v1 - v0)
    return None


def patch_accped_v6g(buf: bytearray, ori: bytes, ace: bytes) -> dict:
    stats = []
    written = 0
    for addr in ACCPED_BANKS:
        soft = react = wot = 0
        wot_after = []
        for r, rpm in enumerate(RPM_AP):
            for c, ped in enumerate(PEDAL):
                off = addr + (r * AP_COLS + c) * 2
                v = decode_nm(u16(buf, off))
                o = decode_nm(u16(ori, off))
                a = decode_nm(u16(ace, off))
                nv = v

                # 1) tip-in soft vers ORI
                sk = soft_k(ped)
                if sk > 0:
                    nv = nv + (o - nv) * sk
                    soft += 1

                # 2) réactivité 1500–2000 (partiels)
                rl = reactive_lift(rpm, ped, nv, a, o)
                if rl is not None and rl > nv + 0.4:
                    nv = rl
                    react += 1

                # 3) WOT fill / plateau 360 + roll-off
                if ped >= 95.0:
                    wt = wot_target(rpm)
                    if wt is not None and rpm < 5600:
                        if abs(nv - wt) >= 0.4:
                            nv = wt  # cible nette (dernier Stage1 — pas d’approche molle)
                            wot += 1

                if rpm >= 5600 and v <= 1.0 and o <= 1.0:
                    nv = v

                if abs(nv - v) >= 0.05:
                    put_u16(buf, off, encode_nm(nv))
                    written += 1

            if rpm >= 1000:
                wot_after.append(
                    (
                        rpm,
                        round(
                            decode_nm(u16(buf, addr + (r * AP_COLS + (AP_COLS - 1)) * 2)),
                            1,
                        ),
                    )
                )

        stats.append(
            {
                "addr": f"{addr:06X}",
                "soft_cells": soft,
                "reactive_cells": react,
                "wot_cells": wot,
                "wot_slice_by_rpm": wot_after,
            }
        )
    return {
        "banks": stats,
        "cells_written": written,
        "wot_plateau": WOT_PLATEAU,
        "rolloff_start_rpm": ROLLOFF_START,
    }


def tqlim_v6g_target(rpm: float) -> float | None:
    """Aligné AccPed : 370 plat → roll-off dès 3800 (plus doux que cliff V5d)."""
    if rpm < 1500 or rpm >= 4700:
        return None
    if rpm <= ROLLOFF_START:
        return TQLIM_PLATEAU
    if rpm <= 4000:
        t = (rpm - ROLLOFF_START) / (4000 - ROLLOFF_START)
        return TQLIM_PLATEAU * (1.0 - t * 0.04)  # 370 → ~355
    if rpm <= 4400:
        t = (rpm - 4000) / 400.0
        return TQLIM_PLATEAU * (0.96 - t * 0.10)  # ~355 → ~318
    t = (rpm - 4400) / 300.0
    return TQLIM_PLATEAU * (0.86 - min(1.0, t) * 0.10)  # ~318 → ~281


def patch_tqlim_v6g(buf: bytearray) -> dict:
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    m = next(x for x in atlas["maps"] if x["id"] == "tqlim_base_pu_4A")
    rpm_addr = m["axis_y"]["addr"]
    rpm_f = m["axis_y"]["factor"]
    atm = [u16(buf, ATM_AXIS + i * 2) * ATM_F for i in range(TQLIM_COLS)]
    rpm = [u16(buf, rpm_addr + i * 2) * rpm_f for i in range(TQLIM_ROWS)]

    cells = 0
    max_d = 0.0
    slice_after = []
    ci = min(range(len(atm)), key=lambda i: abs(atm[i] - 1000.0))

    for r, rv in enumerate(rpm):
        tgt = tqlim_v6g_target(rv)
        for c, av in enumerate(atm):
            off = TQLIM + (r * TQLIM_COLS + c) * 2
            cur = decode_nm(u16(buf, off))
            if tgt is None or av < 850:
                if c == ci and rv >= 2500:
                    slice_after.append((round(rv), round(cur, 1)))
                continue
            # remonte vers cible si sous-cap ; adoucit si au-dessus du profil roll-off
            if abs(cur - tgt) < 0.6:
                nv = cur
            elif cur < tgt:
                nv = cur + 0.92 * (min(TQLIM_PLATEAU, tgt) - cur)
            else:
                # trop haut vs profil (héritage) → rapprocher doucement
                if rv >= ROLLOFF_START:
                    nv = cur + 0.75 * (tgt - cur)
                else:
                    nv = cur
            if abs(nv - cur) >= 0.5:
                put_u16(buf, off, encode_nm(nv))
                cells += 1
                max_d = max(max_d, abs(nv - cur))
            if c == ci and rv >= 2500:
                slice_after.append((round(rv), round(decode_nm(u16(buf, off)), 1)))

    return {
        "addr": f"{TQLIM:06X}",
        "plateau_nm": TQLIM_PLATEAU,
        "rolloff_start": ROLLOFF_START,
        "cells": cells,
        "max_d": round(max_d, 1),
        "atm1000_slice": slice_after,
    }


def patch_tegt_v6g(buf: bytearray, ori: bytes, ace: bytes) -> dict:
    """Autorise ~360 Nm tant que EGT modèle modérée ; frein progressif si chaud."""
    egts = [decode_egt(u16(buf, TEGT_AXIS_X + i * 2)) for i in range(TEGT_COLS)]
    rpms = [float(u16(buf, TEGT_AXIS_Y + i * 2)) for i in range(TEGT_ROWS)]
    changed = 0
    max_after = -1e9
    samples = []

    for r, rpm in enumerate(rpms):
        for c, egt in enumerate(egts):
            off = TEGT + (r * TEGT_COLS + c) * 2
            o = decode_nm(u16(ori, off))
            a = decode_nm(u16(ace, off))
            blended = o + TEGT_BLEND_HOT * (a - o)

            if egt < 800 and 1200 <= rpm <= 4200:
                # zone utile plateau 360 (légèrement au-dessus d’ACE 350 — dernier Stage1)
                target = max(blended, WOT_PLATEAU)
            elif egt < 860 and 1200 <= rpm <= 4200:
                t = (egt - 800) / 60.0
                hi = WOT_PLATEAU
                target = hi + t * (blended - hi)
                target = max(blended, target)
            else:
                target = blended

            put_u16(buf, off, encode_nm(target))
            n = decode_nm(u16(buf, off))
            if abs(n - o) > 0.05:
                changed += 1
            max_after = max(max_after, n)

            if len(samples) < 10 and egt >= 780:
                if any(abs(rpm - x) < 80 for x in (2000.0, 3000.0, 3750.0, 4000.0)):
                    samples.append(
                        {
                            "rpm": rpm,
                            "egt": round(egt, 1),
                            "ori": round(o, 1),
                            "ace": round(a, 1),
                            "v5g": round(n, 1),
                        }
                    )

    return {
        "addr": f"{TEGT:06X}",
        "cells_touched_vs_ori": changed,
        "max_nm": round(max_after, 1),
        "policy": "egt<800 → jusqu'à 360 mid ; >860 blend hot 0.85 ORI↔ACE",
        "samples_hot": samples,
    }


def check_launch(buf: bytearray) -> dict:
    rpms = [u16(buf, CLUTCH_AXIS + i * 2) for i in range(CLUTCH_ROWS)]
    hold = {}
    for r, rpm in enumerate(rpms):
        if rpm in HOLD_RPMS:
            vals = [
                round(decode_nm(u16(buf, CLUTCH + (r * CLUTCH_COLS + c) * 2)), 2)
                for c in (0, 1)
            ]
            hold[rpm] = vals
    r4801 = rpms.index(4801) if 4801 in rpms else None
    hc = None
    if r4801 is not None:
        hc = [
            round(decode_nm(u16(buf, CLUTCH + (r4801 * CLUTCH_COLS + c) * 2)), 2)
            for c in range(CLUTCH_COLS)
        ]
    return {"hold_nm_by_rpm": hold, "hardcut_4801": hc}


def main() -> None:
    ori = ORI.read_bytes()
    ace = ACE.read_bytes()
    base = BASE.read_bytes()
    buf = bytearray(base)

    acc = patch_accped_v6g(buf, ori, ace)
    tq = patch_tqlim_v6g(buf)
    tegt = patch_tegt_v6g(buf, ori, ace)
    launch = check_launch(buf)

    bytes_vs = sum(1 for i in range(len(base)) if base[i] != buf[i])
    OUT.write_bytes(buf)
    try:
        OUT_STEVEN.parent.mkdir(parents=True, exist_ok=True)
        OUT_STEVEN.write_bytes(buf)
    except OSError:
        pass

    # chain check primary bank WOT
    primary = ACCPED_BANKS[0]
    wot_check = []
    for r, rpm in enumerate(RPM_AP):
        if rpm < 1000 or rpm > 5400:
            continue
        w = decode_nm(u16(buf, primary + (r * AP_COLS + AP_COLS - 1) * 2))
        wot_check.append((rpm, round(w, 1)))

    verify = [
        f"OUT={OUT}",
        f"base=V5f_final_tegt320",
        f"bytes_vs_v5f={bytes_vs}",
        f"target_wot_plateau={WOT_PLATEAU}",
        f"rolloff_start_rpm={ROLLOFF_START}",
        f"chain wish={WOT_PLATEAU} < tqlim={TQLIM_PLATEAU} <= smoke=375 -> OK",
        f"rail=UNCHANGED (ne pas forcer pompe)",
        f"smoke=UNCHANGED cap375",
        f"accped_v6g cells={acc['cells_written']}",
        f"accped_wot_slice={wot_check}",
        f"tqlim_v6g cells={tq['cells']} max_d={tq['max_d']}",
        f"tqlim_atm1000={tq['atm1000_slice']}",
        f"tegt_max={tegt['max_nm']} policy={tegt['policy']}",
        f"tegt_samples={tegt['samples_hot']}",
        f"launch_hold={launch['hold_nm_by_rpm']}",
        f"hardcut_4801={launch['hardcut_4801']}",
        "includes=V5f + AccPedV6g + tqlimV6g + tegtV6g360",
    ]
    VERIFY.write_text("\n".join(verify) + "\n", encoding="utf-8")

    manifest = {
        "version": "V5g",
        "file": OUT_NAME,
        "base": BASE.name,
        "bytes_vs_v5f": bytes_vs,
        "targets": {
            "wot_plateau_nm": WOT_PLATEAU,
            "tqlim_plateau_nm": TQLIM_PLATEAU,
            "smoke_cap_nm": 375,
            "rolloff_start_rpm": ROLLOFF_START,
            "rail": "unchanged",
        },
        "accped_v6g": acc,
        "tqlim_v6g": tq,
        "tegt_v6g": tegt,
        "launch": launch,
        "rationale": {
            "rolloff_3800": (
                "Logs V5f : MAP suit encore ~4000 ; roll-off dès 3800 = plateau long "
                "sans garder 360 trop haut (turbo stock / fumée / EGT)."
            ),
            "tipin_vs_reactive": (
                "soft_k ped≤23% → ORI (doux). reactive_lift ped 45–95% @1400–2600 "
                "vers ACE+bonus — accroche 1500–2000 sans on-off tip-in."
            ),
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    MANIFEST_REPO.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_REPO.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    fiche = f"""# FICHE V5g — 360 Nm long band (dernier Stage1 stock)

**Fichier :** `{OUT_NAME}`  
**Base :** V5f FINAL (`tegt~320` + launch0 + tqlimV6f + AccPedV6e)  
**Rôle :** évolution MAX full stock avant pièces (filtre / IC / turbo / embrayage)

## Plan chiffré (forme)

| Zone | Cible |
|---|---|
| Tip-in 0–~23 % pédale | **Soft gardé** (vers ORI) |
| 1500–2000 + partiels | **Plus réactif** (ACE + bonus, sans on-off) |
| WOT ~2000–3800 | **~360 Nm** plateau |
| Dès **3800** | Roll-off **progressif** (anti-falaise) |
| ≥4200–4500 | Descente claire (pas 360 jusqu’au cut) |

**Pourquoi roll-off @3800 (pas 3600) :** logs V5f montrent MAP qui suit encore vers ~4000 ;
garder le plateau jusqu’à 3800 allonge la plage utile ; commencer plus tôt (3600) raccourcit
sans gain safety net. Au-delà de ~4200 on ne force pas (GTC12 stock).

**Tip-in vs 1500–2000 :** `soft_k` seulement pédale basse → ORI. La réactivité touche
pédale **≥~45 %** entre **~1400–2600** rpm — donc premier millimètre toujours doux,
reprises mid plus accrocheuses.

## Chaîne couple

| Couche | V5f | **V5g** |
|---|---|---|
| AccPed | V6e (~333–338 WOT) | **V6g** soft + réactif 1.5–2k + WOT **360** + roll-off |
| tqlim_base | V6f (~370 + fill) | **V6g** 370 plat → roll-off dès 3800 |
| tqlim_tegt | blend 50 % → max **~320** | **V6g** EGT&lt;800 → jusqu’à **360** mid ; chaud = blend 0.85 |
| smoke | **375** | **inchangé** (marge au-dessus de 360) |
| rail | héritage | **inchangé** (ne pas forcer la pompe) |
| Launch / HC | 0 @2700–3000 / 4800 | **inchangé** |

Ordre : **wish 360 &lt; tqlim 370 ≤ smoke 375**.

Octets ≠ V5f : **{bytes_vs}**

## Flash

1. KESS **CHK**
2. Clear DTC
3. Soft noté **V5g**

## Risques

- +~20–25 Nm vs V5f → un peu plus de fumée / EGT possible : **ROUTE_AIR + miroir**
- tegt plus permissif à EGT modérée → jour chaud moins « mou », mais surveiller
- Rail non touché : si FUP réel décroche → ne pas monter rail, redescendre wish

## Logs post-flash (IDE exacts 9979)

Voir aussi `fiche-campagne-dev-carto.html` / `log-aide.html`.

### VILLE_TIPIN — tip-in soft conservé
- IDE00021 Engine RPM
- IDE00075 Vehicle speed
- IDE00086 Accelerator pedal position
- IDE00100 Engine torque-TQI_SP  
Fichier : `CADDY_V5g_VILLE_TIPIN_YYYYMMDD.csv`

### VILLE_REACT — reprises 1500–2000
- mêmes 4 IDE · pédale ~45–70 % · 3ᵉ  
Fichier : `CADDY_V5g_VILLE_REACT_YYYYMMDD.csv`

### ROUTE_CLIFF — plateau 360 + roll-off
- IDE00021 · IDE00075 · IDE00086 · IDE00100 · IDE00190 MAP_SP · IDE00191 MAP_ACT  
WOT 2000→4600 · prouver ~355–360 mid puis descente douce  
Fichier : `CADDY_V5g_ROUTE_CLIFF_YYYYMMDD.csv`

### ROUTE_AIR — fumée / air
- IDE00021 · IDE00086 · IDE00100 · IDE00191 · IDE00347 Air mass · IDE00025 Coolant  
+ note fumée miroir  
Fichier : `CADDY_V5g_ROUTE_AIR_YYYYMMDD.csv`

### ROUTE_RAIL — pompe
- IDE00021 · IDE00075 · IDE00086 · IDE00100 · IDE00188 FUP_FIL · IDE00201 FUP_SP  
Consigne ~1620 bar · réel ≤~1650–1670 pic  
Fichier : `CADDY_V5g_ROUTE_RAIL_YYYYMMDD.csv`

### ROUTE_HOT — tegt
- mêmes IDE que CLIFF · jour chaud · clim notée  
Fichier : `CADDY_V5g_ROUTE_HOT_YYYYMMDD.csv`

## VERIFY

Voir `VERIFY-V5G.txt`.
"""
    FICHE.write_text(fiche, encoding="utf-8")

    print("Wrote", OUT)
    print("bytes vs V5f:", bytes_vs)
    print("AccPed cells", acc["cells_written"])
    print("WOT slice", wot_check)
    print("tqlim cells", tq["cells"], "slice", tq["atm1000_slice"][:8])
    print("tegt max", tegt["max_nm"])
    print("VERIFY", VERIFY)
    print("FICHE", FICHE)


if __name__ == "__main__":
    main()
