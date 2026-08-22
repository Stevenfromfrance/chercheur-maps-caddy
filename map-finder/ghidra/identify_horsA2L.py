# -*- coding: utf-8 -*-
"""Identify Golf 9980 hors-A2L interp_2d grids vs 9979 A2L / atlas.

Analysis only. Writes golf9980_horsA2L_identified.csv

Honesty: the WinOLS A2L only names ~299 maps. Most interp_2d grids are
*not* CHARACTERISTIC starts. ~50 sit *inside* a known map (row / subview) —
those get medium comments, not a fake new IdName. High = unique family match
near the A2L start (header skip / same payload).
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS = ROOT.parents[1]
GOLF = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
VEH = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
    r"\Caddy-CAYE-2013-03L906023PA-2531"
)
A2L_JSON = (
    VEH
    / "A2L"
    / "Volkswagen_Golf_2008_(VI)_1.6_TDI_CR_105_hp_Siemens_PCR2.1_OBD_NR.json"
)
ORI_CANDIDATES = [
    VEH / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin",
    Path(
        r"C:\Users\theda\OneDrive\Bureau\caddy cartho\ORI CADDY STEVEN"
        r"\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27"
    ),
]
ATLAS = WS / "map-finder" / "atlas" / "9979.json"
HORS = ROOT / "golf9980_horsA2L_maps.csv"
OUT = ROOT / "golf9980_horsA2L_identified.csv"

FLASH = 0x80000000
FP_N = 64
USER_NAMED = {
    0x1CBE40,
    0x1CBE7C,
    0x1D1E64,
    0x1D0E48,
    0x1CEE20,
    0x1CDE04,
    0x19E480,
    0x1C4994,
    0x1C59B0,
    0x1C89FC,
}
FORCE_LOW = {0x1C4994}  # 0x8000 fill / pointer-like


def find_ori() -> Path:
    for p in ORI_CANDIDATES:
        if p.exists():
            return p
    raise SystemExit("9979 ORI not found")


def sx16(v: int) -> int:
    return v - 0x10000 if v >= 0x8000 else v


def parse_movha(code: bytes, i: int):
    if i < 0 or i + 3 >= len(code) or code[i] != 0x91 or (code[i + 1] & 0x0F):
        return None
    const16 = (code[i + 1] >> 4) | (code[i + 2] << 4) | ((code[i + 3] & 0x0F) << 12)
    return const16 << 16, code[i + 3] >> 4


def parse_lea(code: bytes, i: int):
    if i < 0 or i + 3 >= len(code) or code[i] != 0xD9:
        return None
    dest = code[i + 1] & 0x0F
    base = (code[i + 1] >> 4) & 0x0F
    offu = struct.unpack_from("<H", code, i + 2)[0]
    return dest, base, sx16(offu)


def recover_abs(code: bytes, site_off: int, reg: int, window: int = 120):
    start = max(0, site_off - window)
    i = site_off - 4
    while i >= start:
        lea = parse_lea(code, i)
        if lea and lea[0] == reg:
            _dest, base, off = lea
            j = i - 4
            while j >= start:
                mh = parse_movha(code, j)
                if mh and mh[1] == base:
                    return (mh[0] + off) & 0xFFFFFFFF
                j -= 2
        i -= 2
    return None


def file_off(va: int | None) -> int | None:
    if va is None:
        return None
    return va & 0xFFFFFF


def family_id(name: str) -> str:
    s = re.sub(r"^CH_", "", name or "")
    s = re.sub(r"@.*$", "", s)
    s = re.sub(r"_\d+$", "", s)
    return s


def ghidra_safe(name: str) -> str:
    s = "".join(ch if ch.isalnum() or ch in "._" else "_" for ch in (name or ""))
    s = s.strip("_") or "unnamed"
    if s[0].isdigit():
        s = "m_" + s
    return s[:60]


def u16s(blob: bytes, off: int, n: int) -> list[int]:
    raw = blob[off : off + n * 2]
    if len(raw) < 2:
        return []
    return list(struct.unpack_from("<%dH" % (len(raw) // 2), raw))


def looks_ptr(vals: list[int]) -> bool:
    if len(vals) < 8:
        return False
    return sum(1 for v in vals[:16] if v in (0x8000, 0xA000, 0x0000)) >= 12


def load_a2l_maps() -> list[dict]:
    maps = json.loads(A2L_JSON.read_text(encoding="utf-8"))["maps"]
    out = []
    for am in maps:
        try:
            addr = int(am["Fieldvalues.StartAddr"])
        except (KeyError, ValueError, TypeError):
            continue
        typ = am.get("Type") or "eZweidim"
        cols = int(am.get("Columns") or 1)
        rows = int(am.get("Rows") or 1)
        cs = 1 if am.get("DataOrg") == "eByte" else 2
        if typ == "eEinzel":
            ln = cs
        elif typ == "eEindim":
            ln = max(cols, rows) * cs
        else:
            ln = cols * rows * cs
        try:
            ax = int(am.get("AxisX.DataAddr") or 0) or None
        except (TypeError, ValueError):
            ax = None
        try:
            ay = int(am.get("AxisY.DataAddr") or 0) or None
        except (TypeError, ValueError):
            ay = None
        out.append(
            {
                "id": am.get("IdName") or "",
                "name": am.get("Name") or "",
                "folder": am.get("FolderName") or "",
                "addr": addr,
                "length": ln,
                "cols": cols,
                "rows": rows,
                "type": typ,
                "axis_x": ax,
                "axis_y": ay,
            }
        )
    return out


def load_atlas_maps() -> list[dict]:
    data = json.loads(ATLAS.read_text(encoding="utf-8"))
    out = []
    for m in data.get("maps") or []:
        out.append(
            {
                "id": m.get("id") or "",
                "name": m.get("name") or "",
                "folder": m.get("folder") or "",
                "addr": m["addr"],
                "length": m.get("length") or 0,
                "cols": m.get("cols") or 1,
                "rows": m.get("rows") or 1,
                "type": m.get("type") or "eZweidim",
                "axis_x": (m.get("axis_x") or {}).get("addr"),
                "axis_y": (m.get("axis_y") or {}).get("addr"),
                "fp_hex": (m.get("fingerprint") or {}).get("hex") or "",
            }
        )
    return out


def main() -> None:
    golf = GOLF.read_bytes()
    ori = find_ori().read_bytes()
    a2l_maps = load_a2l_maps()
    atlas_maps = load_atlas_maps()
    # Prefer A2L rows; atlas fills ids already in A2L anyway
    catalog = a2l_maps + [m for m in atlas_maps if all(m["addr"] != a["addr"] for a in a2l_maps)]

    hors = list(csv.DictReader(HORS.open(newline="", encoding="utf-8")))
    rows_out = []
    counts = {"high": 0, "medium": 0, "low": 0}

    for row in hors:
        grid_va = int(row["grid80"], 16) & 0xFFFFFFFF
        call_va = int(row["call_site"], 16) & 0xFFFFFFFF
        old = row["name"]
        goff = grid_va - FLASH
        vals = u16s(golf, goff, 32)
        uniq = len(set(vals))
        g64 = golf[goff : goff + FP_N]
        o64 = ori[goff : goff + FP_N] if goff + FP_N <= len(ori) else b""
        same9979 = g64 == o64
        ptr = looks_ptr(vals) or goff in FORCE_LOW
        sha = hashlib.sha256(golf[goff : goff + 32]).hexdigest()[:12]

        a4 = file_off(recover_abs(golf, call_va - FLASH, 4))
        a5 = file_off(recover_abs(golf, call_va - FLASH, 5))
        a6 = file_off(recover_abs(golf, call_va - FLASH, 6))

        inside = []
        for am in catalog:
            if am["length"] <= 0:
                continue
            if am["addr"] <= goff < am["addr"] + am["length"]:
                d = goff - am["addr"]
                inside.append((d, am))
        inside.sort(key=lambda x: (x[0], -x[1]["length"]))

        near_start = [t for t in inside if t[0] <= 0x40]
        fams = sorted(set(family_id(t[1]["id"]) for t in near_start if t[1]["id"]))

        # 64-byte payload equals A2L/atlas start+delta (diverse only)
        payload_hits = []
        if uniq >= 6 and not ptr:
            for am in catalog:
                addr, ln = am["addr"], am["length"] or 256
                for d in range(0, min(0x41, ln), 4):
                    chunk = ori[addr + d : addr + d + FP_N]
                    if len(chunk) == FP_N and chunk == g64:
                        payload_hits.append((d, am))
                        break
        payload_fams = sorted(set(family_id(t[1]["id"]) for t in payload_hits if t[1]["id"]))

        conf = "low"
        a2l_id = ""
        folder = ""
        nice = old
        notes = []

        if ptr:
            conf = "low"
            notes.append("low: 8000/A000 fill — pas une grille Nm lisible (ex. 1C4994)")
            if inside:
                am = inside[0][1]
                notes.append(
                    "tombe dans %s +0x%X (%s) — ne pas renommer" % (am["id"], inside[0][0], am["folder"])
                )
        elif (near_start or payload_hits) and uniq >= 6 and len(set(fams or payload_fams)) == 1:
            fam = (fams or payload_fams)[0]
            am = (near_start or payload_hits)[0][1]
            dlt = (near_start or payload_hits)[0][0]
            conf = "high"
            a2l_id = fam
            folder = am["folder"]
            nice = ghidra_safe(fam)
            notes.append(
                "high: empreinte diverse = famille A2L %s (%s) delta=0x%X cols=%s rows=%s"
                % (fam, am["folder"], dlt, am["cols"], am["rows"])
            )
        elif inside:
            am = inside[0][1]
            dlt = inside[0][0]
            conf = "medium"
            a2l_id = am["id"]
            folder = am["folder"]
            nice = old  # comment only
            notes.append(
                "medium: pointe DANS %s @0x%06X +0x%X (%s) — pas le debut de map; comment only"
                % (am["id"], am["addr"], dlt, am["folder"])
            )
        else:
            conf = "low"
            notes.append("low: pas dans l A2L/atlas 9979 (299 maps WinOLS) — nommer a la main si besoin")

        if same9979:
            notes.append("identique 64o vs 9979 au meme offset")
        else:
            notes.append("differe de 9979 au meme offset")
        notes.append("fp32=%s uniq_u16=%d" % (sha, uniq))
        if a4 is not None:
            notes.append("grid_rec=0x%06X%s" % (a4, "" if a4 == goff else " (mismatch)"))
        if a5 is not None:
            notes.append("ax=0x%06X" % a5)
        if a6 is not None:
            notes.append("ay=0x%06X" % a6)
        if goff in USER_NAMED:
            notes.append("user-named: garder map_horsA2L_ en primaire")

        counts[conf] += 1
        rows_out.append(
            {
                "offset": "0x%06X" % goff,
                "old_name": old,
                "new_name": nice,
                "confidence": conf,
                "a2l_id": a2l_id,
                "notes": "; ".join(notes).replace(",", ";"),
                "grid80": "0x%08X" % grid_va,
                "call_site": "0x%08X" % call_va,
                "a2l_folder": folder,
                "axis_x": ("0x%06X" % a5) if a5 else "",
                "axis_y": ("0x%06X" % a6) if a6 else "",
                "same_9979": "1" if same9979 else "0",
            }
        )

    fields = [
        "offset",
        "old_name",
        "new_name",
        "confidence",
        "a2l_id",
        "notes",
        "grid80",
        "call_site",
        "a2l_folder",
        "axis_x",
        "axis_y",
        "same_9979",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows_out)

    print("Wrote", OUT)
    print(
        "counts high=%d medium=%d low=%d total=%d"
        % (counts["high"], counts["medium"], counts["low"], len(rows_out))
    )
    print("--- high ---")
    for r in rows_out:
        if r["confidence"] == "high":
            print("%s  %s -> %s  [%s]" % (r["offset"], r["old_name"], r["new_name"], r["a2l_folder"]))
    print("--- medium (first 15) ---")
    n = 0
    for r in rows_out:
        if r["confidence"] != "medium":
            continue
        print("%s  %s  ~ %s" % (r["offset"], r["old_name"], r["a2l_id"]))
        n += 1
        if n >= 15:
            break


if __name__ == "__main__":
    main()
