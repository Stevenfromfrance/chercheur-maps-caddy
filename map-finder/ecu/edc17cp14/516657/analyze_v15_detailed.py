# -*- coding: utf-8 -*-
"""Analyse détaillée A5 V1.5 : extraction banques smoke, rail, accped, injection.

Génère un rapport détaillé sur le modèle de FICHE-CHANGEMENTS-ORI-V1.md (Caddy).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
ORI = ROOT / "ORI_FLS.fls"
V15 = ROOT / "A5_516657_V1.5_0AW_injtime_cruiseIQ_vmaxoff_nosmoke_fill400_DPF_EGR_HC_SOI_noCHK.fls"
OUT_JSON = ROOT / "v15_detailed_analysis.json"
OUT_MD = ROOT / "FICHE-EDC17-CHANGEMENTS-ORI-V15.md"

# Zones à investiguer (basées sur patterns EDC17 connus)
# Adapté depuis patterns Bosch EDC17 + manifest V1.5
ZONES = {
    "injection_time": {
        "start": 0x1D1496,
        "size": 714,  # 90 cells u16 × 2 + axes ?
        "desc": "Injection Time (us) — durée injection"
    },
    "cal_zone": {
        "start": 0x180000,
        "end": 0x1F0000,
        "desc": "Zone calibration principale"
    },
    "flags": {
        "start": 0x185000,
        "end": 0x186200,
        "desc": "Flags système (non modifiable)"
    },
    "dtc_zone": {
        "start": 0x19E000,
        "end": 0x1A4000,
        "desc": "Masques DTC (DaVinci)"
    }
}

# Patterns de recherche (basés sur manifests + WinOLS similar)
# AccPed : grilles 8×16 typiquement, valeurs 0–400 Nm
# Smoke : grilles variables, valeurs 0–500 mg/stroke
# Rail : grilles variables, valeurs 1400–1700 bar typiquement
# IQ : grilles, valeurs 0–100 mg/stroke

SEARCH_PATTERNS = {
    "accped_candidates": {
        "zone": (0x1CF000, 0x1D1000),
        "size_min": 256,  # 8×16 u16 = 256 bytes
        "size_max": 512,
        "value_min": 0,
        "value_max": 400,
        "desc": "AccPed banques (Nm)"
    },
    "smoke_candidates": {
        "zone": (0x1D1000, 0x1D3000),
        "size_min": 128,
        "size_max": 1024,
        "value_min": 0,
        "value_max": 500,
        "desc": "Smoke limiter (mg/stroke)"
    },
    "rail_candidates": {
        "zone": (0x1E9000, 0x1EC000),
        "size_min": 128,
        "size_max": 512,
        "value_min": 1400,
        "value_max": 1700,
        "desc": "Rail pressure (bar)"
    },
    "iq_candidates": {
        "zone": (0x1D4000, 0x1D8000),
        "size_min": 128,
        "size_max": 1024,
        "value_min": 0,
        "value_max": 100,
        "desc": "IQ quantity (mg/stroke)"
    }
}


def u16(b: bytes | bytearray, off: int) -> int:
    """Read u16 little-endian."""
    return b[off] | (b[off + 1] << 8)


def to_float_nm(raw: int) -> float:
    """Convert u16 to Nm (typical EDC17: factor 0.03125, offset -1024)."""
    return raw * 0.03125 - 1024.0


def to_float_bar(raw: int) -> float:
    """Convert u16 to bar (typical rail: factor 0.025)."""
    return raw * 0.025


def to_float_mg(raw: int) -> float:
    """Convert u16 to mg/stroke (typical IQ/smoke: factor varies)."""
    # Approximation : 0.01 pour IQ, 0.1 pour smoke — à affiner selon A2L
    return raw * 0.01


def find_changed_regions(ori: bytes, mod: bytes, min_size: int = 16, merge_gap: int = 6) -> list[tuple[int, int, int]]:
    """Find contiguous regions of changes.
    
    Returns list of (start, end, changed_bytes).
    """
    diffs = [i for i in range(len(ori)) if ori[i] != mod[i]]
    if not diffs:
        return []
    
    regions = []
    start = end = diffs[0]
    
    for i in diffs[1:]:
        if i <= end + merge_gap:
            end = i
        else:
            if end - start + 1 >= min_size:
                regions.append((start, end + 1, sum(1 for j in range(start, end + 1) if ori[j] != mod[j])))
            start = end = i
    
    if end - start + 1 >= min_size:
        regions.append((start, end + 1, sum(1 for j in range(start, end + 1) if ori[j] != mod[j])))
    
    return regions


def scan_u16_banks(ori: bytes, mod: bytes, zone_start: int, zone_end: int, 
                   val_min: float, val_max: float, min_cells: int = 8) -> list[dict[str, Any]]:
    """Scan for u16 banks (AccPed, smoke, rail...) in a zone.
    
    Returns list of candidate banks with stats.
    """
    banks = []
    i = zone_start
    
    while i + 1 < zone_end:
        # Skip if no change
        if ori[i] == mod[i] and ori[i + 1] == mod[i + 1]:
            i += 2
            continue
        
        # Potential bank start — scan forward
        bank_start = i
        cells = []
        changed = 0
        
        while i + 1 < zone_end and len(cells) < 512:  # Max 512 cells scan
            o_raw = u16(ori, i)
            m_raw = u16(mod, i)
            
            # Try Nm conversion
            o_nm = to_float_nm(o_raw)
            m_nm = to_float_nm(m_raw)
            
            # Check if plausible range
            if val_min <= o_nm <= val_max or val_min <= m_nm <= val_max:
                cells.append({
                    "offset": i,
                    "ori_raw": o_raw,
                    "mod_raw": m_raw,
                    "ori_val": o_nm,
                    "mod_val": m_nm,
                    "changed": o_raw != m_raw
                })
                if o_raw != m_raw:
                    changed += 1
                i += 2
            else:
                # Out of plausible range, end bank
                break
        
        # Valid bank if enough cells
        if len(cells) >= min_cells and changed > 0:
            banks.append({
                "addr_hex": f"{bank_start:06X}",
                "addr": bank_start,
                "size": len(cells) * 2,
                "cells": len(cells),
                "changed_cells": changed,
                "ori_min": min(c["ori_val"] for c in cells),
                "ori_max": max(c["ori_val"] for c in cells),
                "mod_min": min(c["mod_val"] for c in cells),
                "mod_max": max(c["mod_val"] for c in cells),
                "sample": cells[:5]  # First 5 cells
            })
        
        # Move to next potential bank
        if i == bank_start:
            i += 2
    
    return banks


def analyze_injection_time(ori: bytes, mod: bytes) -> dict[str, Any]:
    """Analyze injection time zone (0x1D1496)."""
    start = ZONES["injection_time"]["start"]
    size = ZONES["injection_time"]["size"]
    
    cells = []
    for i in range(start, start + size, 2):
        if i + 1 >= len(ori):
            break
        o_raw = u16(ori, i)
        m_raw = u16(mod, i)
        if o_raw != m_raw:
            cells.append({
                "offset": i,
                "ori": o_raw,
                "mod": m_raw,
                "delta_pct": round(100 * (m_raw / o_raw - 1), 2) if o_raw > 0 else 0
            })
    
    return {
        "addr_hex": f"{start:06X}",
        "size": size,
        "cells_total": size // 2,
        "cells_changed": len(cells),
        "pct_changed": round(100 * len(cells) / (size // 2), 1),
        "delta_min": min((c["delta_pct"] for c in cells), default=0),
        "delta_max": max((c["delta_pct"] for c in cells), default=0),
        "delta_med": round(sum(c["delta_pct"] for c in cells) / len(cells), 2) if cells else 0,
        "sample": cells[:10]
    }


def main() -> None:
    if not ORI.exists():
        raise SystemExit(f"ORI not found: {ORI}")
    if not V15.exists():
        raise SystemExit(f"V1.5 not found: {V15}")
    
    ori = ORI.read_bytes()
    v15 = V15.read_bytes()
    
    if len(ori) != len(v15):
        raise SystemExit(f"Size mismatch: ORI {len(ori)} vs V1.5 {len(v15)}")
    
    print("=" * 80)
    print("ANALYSE DÉTAILLÉE A5 V1.5 vs ORI")
    print("=" * 80)
    
    # Global stats
    total_changed = sum(1 for i in range(len(ori)) if ori[i] != v15[i])
    print(f"\n📊 Octets modifiés : {total_changed:,} / {len(ori):,} ({100*total_changed/len(ori):.2f}%)")
    
    # Changed regions
    print("\n🔍 Régions modifiées (≥16 octets contigus) :")
    regions = find_changed_regions(ori, v15, min_size=16, merge_gap=6)
    print(f"   {len(regions)} régions trouvées")
    
    # Top 20 regions
    regions_sorted = sorted(regions, key=lambda r: r[2], reverse=True)[:20]
    for i, (start, end, changed) in enumerate(regions_sorted, 1):
        print(f"   {i:2d}. {start:06X}–{end:06X} : {changed:5d} octets ({end-start:5d} total)")
    
    # Injection Time
    print("\n💉 Injection Time @ 0x1D1496 :")
    inj_analysis = analyze_injection_time(ori, v15)
    print(f"   Cellules modifiées : {inj_analysis['cells_changed']} / {inj_analysis['cells_total']} ({inj_analysis['pct_changed']}%)")
    print(f"   Delta : {inj_analysis['delta_min']:+.2f}% .. {inj_analysis['delta_max']:+.2f}% (méd {inj_analysis['delta_med']:+.2f}%)")
    
    # AccPed candidates
    print("\n🚗 AccPed candidates (Nm) :")
    accped = scan_u16_banks(ori, v15, 
                            SEARCH_PATTERNS["accped_candidates"]["zone"][0],
                            SEARCH_PATTERNS["accped_candidates"]["zone"][1],
                            0, 400, min_cells=64)  # 8×16 = 128 cells min
    print(f"   {len(accped)} banques trouvées")
    for bank in accped[:8]:
        print(f"   @ {bank['addr_hex']} : {bank['cells']} cells, {bank['changed_cells']} modifiées")
        print(f"      ORI {bank['ori_min']:.1f}–{bank['ori_max']:.1f} Nm → MOD {bank['mod_min']:.1f}–{bank['mod_max']:.1f} Nm")
    
    # Smoke candidates
    print("\n💨 Smoke candidates (mg/stroke) :")
    smoke = scan_u16_banks(ori, v15,
                          SEARCH_PATTERNS["smoke_candidates"]["zone"][0],
                          SEARCH_PATTERNS["smoke_candidates"]["zone"][1],
                          0, 500, min_cells=64)
    print(f"   {len(smoke)} banques trouvées")
    for bank in smoke[:5]:
        print(f"   @ {bank['addr_hex']} : {bank['cells']} cells, {bank['changed_cells']} modifiées")
    
    # Rail candidates
    print("\n⛽ Rail candidates (bar) :")
    rail_banks = []
    rail_zone = SEARCH_PATTERNS["rail_candidates"]["zone"]
    i = rail_zone[0]
    while i + 1 < rail_zone[1]:
        if ori[i] == v15[i] and ori[i + 1] == v15[i + 1]:
            i += 2
            continue
        
        bank_start = i
        cells_raw = []
        changed = 0
        
        while i + 1 < rail_zone[1] and len(cells_raw) < 512:
            o = u16(ori, i)
            m = u16(v15, i)
            o_bar = to_float_bar(o)
            m_bar = to_float_bar(m)
            
            if 1400 <= o_bar <= 1700 or 1400 <= m_bar <= 1700:
                cells_raw.append((i, o, m, o_bar, m_bar))
                if o != m:
                    changed += 1
                i += 2
            else:
                break
        
        if len(cells_raw) >= 64 and changed > 0:
            rail_banks.append({
                "addr_hex": f"{bank_start:06X}",
                "addr": bank_start,
                "cells": len(cells_raw),
                "changed": changed,
                "ori_max": max(c[3] for c in cells_raw),
                "mod_max": max(c[4] for c in cells_raw)
            })
        
        if i == bank_start:
            i += 2
    
    print(f"   {len(rail_banks)} banques trouvées")
    for bank in rail_banks[:10]:
        print(f"   @ {bank['addr_hex']} : {bank['cells']} cells, {bank['changed']} modifiées")
        print(f"      max ORI {bank['ori_max']:.1f} bar → MOD {bank['mod_max']:.1f} bar")
    
    # Build report
    report = {
        "file_ori": str(ORI.name),
        "file_mod": str(V15.name),
        "size": len(ori),
        "bytes_changed": total_changed,
        "pct_changed": round(100 * total_changed / len(ori), 4),
        "regions": [
            {"start_hex": f"{s:06X}", "end_hex": f"{e:06X}", "start": s, "end": e, "changed": c}
            for s, e, c in regions_sorted
        ],
        "injection_time": inj_analysis,
        "accped_banks": accped,
        "smoke_banks": smoke,
        "rail_banks": rail_banks,
        "zones_scanned": ZONES,
        "patterns": SEARCH_PATTERNS
    }
    
    # Write JSON
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n✅ Rapport JSON : {OUT_JSON}")
    
    # Generate Markdown
    md_lines = [
        "# FICHE CHANGEMENTS — Audi A5 EDC17CP14 SW 516657",
        "",
        "**Comparaison exacte : ORI (stock) → V1.5** (fichier à flasher)",
        "",
        "| Fichier | Rôle |",
        "|---|---|",
        f"| `{ORI.name}` | Stock usine |",
        f"| `{V15.name}` | **V1.5 0AW** (InjTime soft + cruise IQ) |",
        "",
        f"Taille dump : **{len(ori):,}** octets (identique ORI / V1.5).",
        "",
        "## 1. Résumé global octets",
        "",
        "| Métrique | Valeur |",
        "|---|---:|",
        f"| Octets différents ORI → V1.5 | **{total_changed:,}** |",
        f"| Pourcentage modifié | **{100*total_changed/len(ori):.2f}%** |",
        f"| Régions contigues (≥16 octets) | **{len(regions)}** |",
        "",
        "## 2. Top 10 régions modifiées",
        "",
        "| # | Adresse | Octets modifiés | Taille totale |",
        "|---|---|---:|---:|",
    ]
    
    for i, (start, end, changed) in enumerate(regions_sorted[:10], 1):
        md_lines.append(f"| {i} | `{start:06X}–{end:06X}` | {changed} | {end-start} |")
    
    md_lines.extend([
        "",
        "## 3. Injection Time (us) @ 0x1D1496",
        "",
        "| Métrique | Valeur |",
        "|---|---|",
        f"| Cellules totales | {inj_analysis['cells_total']} |",
        f"| Cellules modifiées | **{inj_analysis['cells_changed']}** ({inj_analysis['pct_changed']}%) |",
        f"| Delta min / max / médian | {inj_analysis['delta_min']:+.2f}% / {inj_analysis['delta_max']:+.2f}% / **{inj_analysis['delta_med']:+.2f}%** |",
        "",
        "## 4. AccPed — banques candidates (Nm)",
        "",
        f"**{len(accped)} banques détectées** (grilles ≥64 cells avec modifications)",
        "",
        "| Adresse | Cells | Modifiées | max ORI | max V1.5 |",
        "|---|---:|---:|---:|---:|",
    ])
    
    for bank in accped[:8]:
        md_lines.append(
            f"| `{bank['addr_hex']}` | {bank['cells']} | {bank['changed_cells']} | "
            f"{bank['ori_max']:.1f} | {bank['mod_max']:.1f} |"
        )
    
    md_lines.extend([
        "",
        "## 5. Smoke — banques candidates",
        "",
        f"**{len(smoke)} banques détectées**",
        "",
        "| Adresse | Cells | Modifiées | max ORI | max V1.5 |",
        "|---|---:|---:|---:|---:|",
    ])
    
    for bank in smoke[:5]:
        md_lines.append(
            f"| `{bank['addr_hex']}` | {bank['cells']} | {bank['changed_cells']} | "
            f"{bank['ori_max']:.1f} | {bank['mod_max']:.1f} |"
        )
    
    md_lines.extend([
        "",
        "## 6. Rail — banques candidates (bar)",
        "",
        f"**{len(rail_banks)} banques détectées**",
        "",
        "| Adresse | Cells | Modifiées | max ORI | max V1.5 |",
        "|---|---:|---:|---:|---:|",
    ])
    
    for bank in rail_banks[:10]:
        md_lines.append(
            f"| `{bank['addr_hex']}` | {bank['cells']} | {bank['changed']} | "
            f"{bank['ori_max']:.1f} | {bank['mod_max']:.1f} |"
        )
    
    md_lines.extend([
        "",
        "---",
        "",
        "**Notes :**",
        "- Analyse automatique basée sur patterns EDC17 connus",
        "- Facteurs de conversion approximatifs (Nm: ×0.03125 -1024, bar: ×0.025)",
        "- A2L 0008 exact non disponible → vérifier offsets avec A2L similar 0005",
        "- Valider avec WinOLS import + logs VCDS",
        "",
        f"**Généré le** {Path(__file__).stat().st_mtime} depuis `{Path(__file__).name}`",
    ])
    
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"✅ Fiche Markdown : {OUT_MD}")
    
    print("\n" + "=" * 80)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 80)


if __name__ == "__main__":
    main()
