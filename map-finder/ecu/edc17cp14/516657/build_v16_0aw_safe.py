# -*- coding: utf-8 -*-
"""Build A5 Bertin V1.6 0AW SAFE — strip PCR2.1 contaminations from V1.5.

Without logs. Goal: file we can trust on Multitronic 0AW + EDC17 methodology.

FROM V1.5 KEEP (aligned Lesson 21 / EDC17):
- DaVinci DPF/EGR/FLAPS
- Injection Time soft (~+1.7%, cap +3%)
- IQ #1 +2% ; IQ #2/#3/#4 ORI
- Smoke Higher Lambda ~+5%
- Turbo Pressure ~+4% + Limiter Turbo ~+4% (paired)
- SOI Main ~+5%
- Rail / rail lim ~+3%

RESTORE TO ORI (PCR2.1-style mistakes on EDC17/0AW):
1. Torque Request Standard + Gear 1..5
   → AccPed-like mid fill (+100..200% on partiels) = PCR aggression
   → Lesson 21 gearbox protection: do NOT raise gear wish on 0AW
   → Helps Multitronic shift under WOT (wish gear back to stock)
2. RPM Limiters raised +8%
   → 5450→5900 / 5600→6050 real rpm (factor 0.5) = raise redline PCR-style
3. Turbo cells where ORI == 1000 hPa (0-boost / atm floor)
   → V1.5 blind +4% made 1000→1040 — Lesson 21: leave 1000 rpm / 0-boost alone

python build_v16_0aw_safe.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORI = ROOT / "ORI_FLS.fls"
V15 = ROOT / "A5_516657_V1.5_0AW_injtime_cruiseIQ_vmaxoff_nosmoke_fill400_DPF_EGR_HC_SOI_noCHK.fls"
OUT_NAME = "A5_516657_V1.6_0AW_SAFE_noPCR_wish_noRPMup_injtime_turbo_DPF_EGR_noCHK.fls"
OUT = ROOT / OUT_NAME
MANIFEST = ROOT / "A5_516657_V1.6_0AW_SAFE_manifest.json"
LIVRAISON = ROOT / "LIVRAISON-V1.6-0AW-SAFE.txt"

IDS = [b"516657", b"8K1907401K", b"0008", b"B3UX", b"CGKA", b"1037516657"]

# Torque / wish maps — full block restore (from winols KP sizes)
WISH_RESTORE = [
    ("Torque_Request_Standard", 0x183FFE, 128),
    ("Torque_Request_Gear_1", 0x19AE94, 256),
    ("Torque_Request_Gear_2", 0x19AFC8, 256),
    ("Torque_Request_Gear_3", 0x19B0FC, 256),
    ("Torque_Request_Gear_4", 0x19B230, 256),
    ("Torque_Request_Gear_5", 0x19B4BA, 256),
]

# RPM limiters raised in V1.5 (u16 LE) — restore ORI
RPM_LIM_RESTORE = [
    ("RPM_Limiter_Neutral_1", 0x1917C0),
    ("RPM_Limiter_Neutral_2", 0x191810),
    ("RPM_Limiter_Neutral_3", 0x191814),
    ("RPM_Limiter_2", 0x1AFD70),
    ("RPM_Limiter_3", 0x1AFD72),
]

# Turbo banks + limiteur — restore only atm floor cells (ORI raw == 1000 hPa)
TURBO_FLOOR_REGIONS = [
    ("Turbo_1", 0x1D5D7C, 320),
    ("Turbo_2", 0x1D5EF4, 320),
    ("Turbo_3", 0x1D606C, 320),
    ("Turbo_4", 0x1D61E4, 320),
    ("Turbo_5", 0x1D635C, 320),
    ("Turbo_6", 0x1D64D4, 320),
    ("Turbo_7", 0x1D67C4, 320),
    ("Turbo_Limiter_APS", 0x1D6DF8, 210),
]
TURBO_ATM_FLOOR = 1000  # hPa — 0-boost / atmospheric


def u16(b: bytes | bytearray, i: int) -> int:
    return b[i] | (b[i + 1] << 8)


def main() -> None:
    ori = ORI.read_bytes()
    v15 = V15.read_bytes()
    n = len(ori)
    assert n == 2_097_152 == len(v15)

    out = bytearray(v15)
    report_restore = {
        "wish_bytes": 0,
        "rpm_bytes": 0,
        "turbo_floor_cells": 0,
        "wish_maps": [],
        "rpm_maps": [],
        "turbo_floor": [],
    }

    for name, addr, size in WISH_RESTORE:
        before = sum(1 for i in range(size) if out[addr + i] != ori[addr + i])
        out[addr : addr + size] = ori[addr : addr + size]
        after = sum(1 for i in range(size) if out[addr + i] != ori[addr + i])
        assert after == 0
        report_restore["wish_bytes"] += before
        report_restore["wish_maps"].append(
            {"name": name, "addr_hex": f"{addr:06X}", "size": size, "bytes_restored": before}
        )

    for name, addr in RPM_LIM_RESTORE:
        o = u16(ori, addr)
        v = u16(out, addr)
        if o != v:
            out[addr] = ori[addr]
            out[addr + 1] = ori[addr + 1]
            report_restore["rpm_bytes"] += 2
            report_restore["rpm_maps"].append(
                {
                    "name": name,
                    "addr_hex": f"{addr:06X}",
                    "v15_raw": v,
                    "ori_raw": o,
                    "v15_rpm_x0_5": v * 0.5,
                    "ori_rpm_x0_5": o * 0.5,
                }
            )

    # Turbo: keep +4% only where ORI > atm floor; restore 1000 hPa cells
    for name, addr, size in TURBO_FLOOR_REGIONS:
        cells = 0
        for i in range(0, size, 2):
            o = u16(ori, addr + i)
            if o == TURBO_ATM_FLOOR and u16(out, addr + i) != TURBO_ATM_FLOOR:
                out[addr + i] = ori[addr + i]
                out[addr + i + 1] = ori[addr + i + 1]
                cells += 1
        if cells:
            report_restore["turbo_floor_cells"] += cells
            report_restore["turbo_floor"].append(
                {"name": name, "addr_hex": f"{addr:06X}", "cells_restored_to_1000hPa": cells}
            )

    # Verify restores
    for _, addr, size in WISH_RESTORE:
        assert out[addr : addr + size] == ori[addr : addr + size]
    for _, addr in RPM_LIM_RESTORE:
        assert u16(out, addr) == u16(ori, addr)

    # IDs intact
    id_ok = all(bytes(out).find(x) >= 0 for x in IDS)
    id_unmoved = all(bytes(out).find(x) == ori.find(x) for x in IDS)

    # Kept from V1.5: InjTime still differs
    inj_changed = sum(
        1
        for i in range(0x1D1496, 0x1D1496 + 800, 2)
        if i + 1 < n and u16(out, i) != u16(ori, i)
    )

    bytes_vs_ori = sum(1 for i in range(n) if out[i] != ori[i])
    bytes_vs_v15 = sum(1 for i in range(n) if out[i] != v15[i])

    errors = []
    if not id_ok:
        errors.append("ids_missing")
    if not id_unmoved:
        errors.append("ids_moved")
    if inj_changed < 50:
        errors.append(f"injtime_lost {inj_changed}")
    if report_restore["wish_bytes"] < 100:
        errors.append("wish_restore_too_small")
    if report_restore["rpm_bytes"] < 6:
        errors.append("rpm_restore_incomplete")
    if report_restore["turbo_floor_cells"] < 20:
        errors.append("turbo_floor_restore_too_small")

    # No remaining atm-floor raises
    floor_left = 0
    for _, addr, size in TURBO_FLOOR_REGIONS:
        for i in range(0, size, 2):
            if u16(ori, addr + i) == TURBO_ATM_FLOOR and u16(out, addr + i) != TURBO_ATM_FLOOR:
                floor_left += 1
    if floor_left:
        errors.append(f"turbo_floor_left {floor_left}")

    report = {
        "file": OUT_NAME,
        "ok": not errors,
        "errors": errors,
        "based_on": "V1.5_0AW",
        "goal": "strip_PCR21_wish_fill_rpm_raise_and_turbo_atm_floor",
        "bytes_changed_vs_ori": bytes_vs_ori,
        "bytes_changed_vs_v15": bytes_vs_v15,
        "restored_to_ori": report_restore,
        "kept_from_v15": {
            "davinci_dpf_egr_flaps": True,
            "injection_time_soft": True,
            "injtime_u16_cells_still_diff": inj_changed,
            "iq_cruise_logic": True,
            "smoke_lambda_soft": True,
            "turbo_plus_4pct_except_atm_floor_1000hPa": True,
            "soi_soft": True,
            "rail_soft": True,
        },
        "pcr21_errors_removed": [
            "Torque Request Standard + Gear1-5 mid-fill (AccPed-style PCR) — fixes 0AW WOT shift fight",
            "RPM limiters +8% (raise redline 5450→5900 / 5600→6050 real rpm)",
            "Turbo atm floor 1000→1040 hPa (0-boost / ~1000 rpm zone) — Lesson 21 leave alone",
        ],
        "symptoms_targeted": {
            "hard_to_shift_at_wot": "Gear TQ maps restored ORI (V1.5 fill fought Multitronic)",
            "issue_around_1000_rpm_or_1000hPa_floor": "Turbo cells ORI=1000 hPa restored (no blind +4%)",
        },
        "ids_ok": id_ok,
        "ids_unmoved": id_unmoved,
        "note": (
            "noCHK. V1.6 SAFE = V1.5 minus PCR2.1 contaminations. "
            "Wish/Gear TQ + RPM lim = ORI; turbo keeps +4% except 1000 hPa floor. "
            "0AW: no launch, no gear wish raise, no redline raise, no fake boost at atm."
        ),
    }

    MANIFEST.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "restored_to_ori"}, indent=2))
    print(json.dumps(report["restored_to_ori"], indent=2))

    if errors:
        raise SystemExit("VERIFY FAIL: " + ", ".join(errors))

    OUT.write_bytes(out)

    liv = f"""A5 Bertin — V1.6 0AW SAFE (sans logs)

Fichier :
  {OUT_NAME}

Pourquoi V1.6 (correction PCR2.1 → EDC17)
  V1.5 appliquait encore des reflexes Caddy/PCR2.1 :
  1) Fill agressif Torque Request Standard + Gear 1-5 (partiels +100..200 %)
  2) RPM limiters +8 % (redline reel ~5450→5900 / 5600→6050)

Corrige (restore ORI)
  - Torque Request Standard @ 183FFE
  - Torque Request Gear 1..5 @ 19AE94..19B4BA
    → vise difficulte a passer un rapport a fond de pedale (0AW)
  - RPM Limiter Neutral + RPM Limiter #2/#3
  - Turbo cellules ORI=1000 hPa (plancher 0-boost) laissees a 1000
    → vise zone ~1000 rpm / 0-boost (Lesson 21) ; le +4 % reste ailleurs

Conserve de V1.5 (methodo EDC17 / Lesson 21)
  - DaVinci DPF/EGR/FLAPS
  - Injection Time soft (~+1.7 %, cap +3 %)
  - IQ #1 +2 % ; IQ #2/#3/#4 ORI
  - Smoke lambda ~+5 %
  - Turbo ~+4 % + limiteur (sauf plancher 1000 hPa)
  - SOI ~+5 %
  - Rail ~+3 %

Philosophie
  Stage1 soft 0AW = fuel/air soft + deletes.
  PAS de wish gear style AccPed PCR.
  PAS de hausse redline.
  PAS de fausse consigne boost a 1000 hPa.

OBLIGATOIRE avant flash
  1. CHK WinOLS/KESS
  2. G83 / EGT / FAP+EGR physiques
  3. Lecture KESS OBD (516657 + 2 Mo) puis ecriture V1.6 CHK

Octets ≠ ORI : {bytes_vs_ori}
Octets ≠ V1.5 : {bytes_vs_v15} (restores)
"""
    LIVRAISON.write_text(liv, encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"wrote {MANIFEST}")
    print(f"wrote {LIVRAISON}")


if __name__ == "__main__":
    main()
