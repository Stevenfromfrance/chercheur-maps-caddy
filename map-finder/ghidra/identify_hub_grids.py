# -*- coding: utf-8 -*-
"""Identify Golf 9980 interpolator-hub grids vs atlas 9979 + A2L / hors-A2L.

Reads all hub family CSVs (interp_2d + B..O), fingerprints each grid80 from
the Golf 9980 fullflash, matches against:
  - A2L WinOLS maps (preferred)
  - atlas/9979.json fingerprints + extents
  - optional golf9980_horsA2L_identified.csv HIGH hits at same offset

Confidence (same spirit as identify_horsA2L.py):
  HIGH   — diverse payload + unique family (near A2L/atlas start, unique
           payload fingerprint, or unique atlas fp match)
  MEDIUM — grid sits inside a known map but not at start (comment only)
  LOW    — pointer fill / no unique match — do not invent OEM names

Outputs:
  golf9980_hub_grids_identified.csv
  golf9980_hub_grids_HIGH.txt

Does not flash. Does not invent IdNames without a fingerprint match.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
from collections import defaultdict
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
HORS_ID = ROOT / "golf9980_horsA2L_identified.csv"
OUT_CSV = ROOT / "golf9980_hub_grids_identified.csv"
OUT_TXT = ROOT / "golf9980_hub_grids_HIGH.txt"
GHIDRA_SCRIPTS = Path(r"C:\Users\theda\ghidra_scripts")

FLASH80 = 0x80000000
PFLASH0 = 0xA0000000
CAL0, CAL1 = 0x180000, 0x200000
FP_N = 64
FORCE_LOW: set[int] = set()

# Hub stem -> short letter (2d = main interp_2d, no letter prefix in fam_)
HUB_FILES = [
    ("2d", ROOT / "golf9980_interp_families.csv"),
    ("B", ROOT / "golf9980_interp_B_families.csv"),
    ("C", ROOT / "golf9980_interp_C_families.csv"),
    ("D", ROOT / "golf9980_interp_D_families.csv"),
    ("E", ROOT / "golf9980_interp_E_families.csv"),
    ("F", ROOT / "golf9980_interp_F_families.csv"),
    ("G", ROOT / "golf9980_interp_G_families.csv"),
    ("H", ROOT / "golf9980_interp_H_families.csv"),
    ("I", ROOT / "golf9980_interp_I_families.csv"),
    ("J", ROOT / "golf9980_interp_J_families.csv"),
    ("K", ROOT / "golf9980_interp_K_families.csv"),
    ("L", ROOT / "golf9980_interp_L_families.csv"),
    ("M", ROOT / "golf9980_interp_M_families.csv"),
    ("N", ROOT / "golf9980_interp_N_families.csv"),
    ("O", ROOT / "golf9980_interp_O_families.csv"),
]


def find_ori() -> Path | None:
    for p in ORI_CANDIDATES:
        if p.exists():
            return p
    return None


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


def file_off(va: int) -> int:
    return va & 0xFFFFFF


def in_cal(off: int) -> bool:
    return CAL0 <= off < CAL1


def load_a2l_maps() -> list[dict]:
    if not A2L_JSON.exists():
        return []
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
                "fp_hex": "",
                "src": "a2l",
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
                "src": "atlas",
            }
        )
    return out


def load_hors_high() -> dict[int, dict]:
    """offset -> {id_name, notes} for prior hors-A2L HIGH hits."""
    out: dict[int, dict] = {}
    if not HORS_ID.exists():
        return out
    for row in csv.DictReader(HORS_ID.open(newline="", encoding="utf-8")):
        if (row.get("confidence") or "").lower() != "high":
            continue
        try:
            off = int(row["offset"], 16) & 0xFFFFFF
        except (KeyError, ValueError):
            continue
        out[off] = {
            "id_name": row.get("a2l_id") or row.get("new_name") or "",
            "new_name": row.get("new_name") or "",
            "notes": row.get("notes") or "",
        }
    return out


def collect_hub_rows() -> list[dict]:
    """Unique (hub, file_offset) from all family CSVs."""
    seen: set[tuple[str, int]] = set()
    rows: list[dict] = []
    for hub, path in HUB_FILES:
        if not path.exists():
            print("WARN missing", path.name)
            continue
        for r in csv.DictReader(path.open(newline="", encoding="utf-8")):
            g = (r.get("grid80") or "").strip()
            if not g:
                continue
            try:
                va = int(g, 16) & 0xFFFFFFFF
            except ValueError:
                continue
            off = file_off(va)
            if not in_cal(off):
                continue
            key = (hub, off)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "hub": hub,
                    "fam_label": (r.get("fam_label") or "").strip(),
                    "family_id": (r.get("family_id") or "").strip(),
                    "suggested_name": (r.get("suggested_name") or "").strip(),
                    "grid80": "0x%08X" % va,
                    "call_site": (r.get("call_site") or "").strip(),
                    "axis_x": (r.get("axis_x") or "").strip(),
                    "axis_y": (r.get("axis_y") or "").strip(),
                    "offset": off,
                    "notes_src": (r.get("notes") or "").strip(),
                }
            )
    return rows


def build_fp_index(catalog: list[dict], ori: bytes | None) -> dict[bytes, list[dict]]:
    """Map payload bytes -> catalog entries (atlas fp and/or ORI start)."""
    idx: dict[bytes, list[dict]] = defaultdict(list)
    for am in catalog:
        fp_hex = am.get("fp_hex") or ""
        if fp_hex:
            try:
                payload = bytes.fromhex(fp_hex)
            except ValueError:
                payload = b""
            # Index full fp and first FP_N for shorter grid probes
            if len(payload) >= 8:
                idx[payload].append(am)
                if len(payload) > FP_N:
                    idx[payload[:FP_N]].append(am)
        if ori is not None:
            addr, ln = am["addr"], am.get("length") or 0
            if ln >= FP_N and addr + FP_N <= len(ori):
                chunk = ori[addr : addr + FP_N]
                if chunk and am not in idx[chunk]:
                    idx[chunk].append(am)
    return idx


def unique_fams(hits: list[dict]) -> list[str]:
    return sorted({family_id(h["id"]) for h in hits if h.get("id")})


def identify_one(
    goff: int,
    golf: bytes,
    ori: bytes | None,
    catalog: list[dict],
    fp_index: dict[bytes, list[dict]],
    hors_high: dict[int, dict],
) -> dict:
    vals = u16s(golf, goff, 32)
    uniq = len(set(vals))
    g64 = golf[goff : goff + FP_N]
    same9979 = False
    if ori is not None and goff + FP_N <= len(ori):
        same9979 = g64 == ori[goff : goff + FP_N]
    ptr = looks_ptr(vals) or goff in FORCE_LOW
    sha = hashlib.sha256(golf[goff : goff + 32]).hexdigest()[:12]

    inside: list[tuple[int, dict]] = []
    for am in catalog:
        if am["length"] <= 0:
            continue
        if am["addr"] <= goff < am["addr"] + am["length"]:
            inside.append((goff - am["addr"], am))
    inside.sort(key=lambda x: (x[0], -x[1]["length"]))
    near_start = [t for t in inside if t[0] <= 0x40]
    fams_near = unique_fams([t[1] for t in near_start])

    # Payload equals catalog start+delta on ORI (diverse only)
    payload_hits: list[tuple[int, dict]] = []
    if uniq >= 6 and not ptr and ori is not None:
        for am in catalog:
            addr, ln = am["addr"], am["length"] or 256
            for d in range(0, min(0x41, ln), 4):
                if addr + d + FP_N > len(ori):
                    break
                chunk = ori[addr + d : addr + d + FP_N]
                if len(chunk) == FP_N and chunk == g64:
                    payload_hits.append((d, am))
                    break
    fams_payload = unique_fams([t[1] for t in payload_hits])

    # Unique atlas/ORI fingerprint index hit at this offset
    fp_hits: list[dict] = []
    if uniq >= 6 and not ptr and len(g64) == FP_N:
        # Prefer longer exact matches: try full fps that equal golf[:len]
        cand: list[dict] = []
        for needle, ams in fp_index.items():
            if len(needle) < 8:
                continue
            if goff + len(needle) > len(golf):
                continue
            if golf[goff : goff + len(needle)] == needle:
                cand.extend(ams)
        # Also exact 64-byte index
        cand.extend(fp_index.get(g64, []))
        # Dedup by (id, addr)
        seen_k: set[tuple[str, int]] = set()
        for am in cand:
            k = (am.get("id") or "", am["addr"])
            if k in seen_k:
                continue
            seen_k.add(k)
            fp_hits.append(am)
    fams_fp = unique_fams(fp_hits)

    conf = "low"
    id_name = ""
    folder = ""
    notes: list[str] = []

    hors = hors_high.get(goff)

    if ptr:
        conf = "low"
        notes.append("low: 8000/A000 fill — pas une grille lisible")
        if inside:
            am = inside[0][1]
            notes.append(
                "tombe dans %s +0x%X (%s) — ne pas renommer"
                % (am["id"], inside[0][0], am["folder"])
            )
    elif (near_start or payload_hits) and uniq >= 6 and len(set(fams_near or fams_payload)) == 1:
        fam = (fams_near or fams_payload)[0]
        am = (near_start or payload_hits)[0][1]
        dlt = (near_start or payload_hits)[0][0]
        conf = "high"
        id_name = fam
        folder = am["folder"]
        notes.append(
            "high: empreinte diverse = famille %s (%s) delta=0x%X cols=%s rows=%s src=%s"
            % (fam, am["folder"], dlt, am["cols"], am["rows"], am.get("src", ""))
        )
    elif fams_fp and len(fams_fp) == 1 and uniq >= 6:
        fam = fams_fp[0]
        am = next(h for h in fp_hits if family_id(h["id"]) == fam)
        conf = "high"
        id_name = fam
        folder = am["folder"]
        notes.append(
            "high: empreinte atlas/ORI unique = %s (%s) addr=0x%06X src=%s"
            % (fam, am["folder"], am["addr"], am.get("src", ""))
        )
    elif hors and hors.get("id_name"):
        # Prior hors-A2L HIGH at same cal offset — corroborate
        conf = "high"
        id_name = family_id(hors["id_name"])
        notes.append(
            "high: confirme horsA2L HIGH au meme offset (%s)" % hors["id_name"]
        )
    elif inside:
        am = inside[0][1]
        dlt = inside[0][0]
        conf = "medium"
        id_name = am["id"]
        folder = am["folder"]
        notes.append(
            "medium: pointe DANS %s @0x%06X +0x%X (%s) - pas le debut; comment only"
            % (am["id"], am["addr"], dlt, am["folder"])
        )
    elif fams_fp and len(fams_fp) > 1:
        conf = "low"
        notes.append(
            "low: empreinte ambigue familles=%s — pas de rename auto" % ",".join(fams_fp)
        )
    else:
        conf = "low"
        notes.append("low: pas dans A2L/atlas 9979 — nommer a la main si besoin")

    if same9979:
        notes.append("identique 64o vs 9979 au meme offset")
    elif ori is not None:
        notes.append("differe de 9979 au meme offset")
    notes.append("fp32=%s uniq_u16=%d" % (sha, uniq))

    return {
        "confidence": conf,
        "id_name": id_name,
        "folder": folder,
        "notes": "; ".join(notes).replace(",", ";"),
        "same_9979": "1" if same9979 else "0",
        "fp32": sha,
    }


def main() -> None:
    if not GOLF.exists():
        raise SystemExit("Golf fullflash not found: %s" % GOLF)
    golf = GOLF.read_bytes()
    ori_path = find_ori()
    ori = ori_path.read_bytes() if ori_path else None
    if ori_path:
        print("ORI 9979:", ori_path)
    else:
        print("WARN: 9979 ORI not found — atlas fp + extent match only")

    a2l_maps = load_a2l_maps()
    atlas_maps = load_atlas_maps()
    catalog = a2l_maps + [
        m for m in atlas_maps if all(m["addr"] != a["addr"] for a in a2l_maps)
    ]
    print("catalog: a2l=%d atlas_extra=%d total=%d" % (len(a2l_maps), len(catalog) - len(a2l_maps), len(catalog)))

    fp_index = build_fp_index(catalog, ori)
    hors_high = load_hors_high()
    print("horsA2L HIGH offsets:", len(hors_high))

    hub_rows = collect_hub_rows()
    print("unique hub grids:", len(hub_rows))

    rows_out = []
    counts = {"high": 0, "medium": 0, "low": 0}

    for hr in hub_rows:
        goff = hr["offset"]
        hit = identify_one(goff, golf, ori, catalog, fp_index, hors_high)
        conf = hit["confidence"]
        counts[conf] += 1
        id_name = hit["id_name"]
        nice = ghidra_safe(id_name) if conf == "high" and id_name else ""
        rows_out.append(
            {
                "hub": hr["hub"],
                "fam_label": hr["fam_label"],
                "addr": "0x%06X" % goff,
                "grid80": hr["grid80"],
                "id_name": id_name if conf != "low" else (id_name or ""),
                "new_name": nice,
                "confidence": conf,
                "notes": hit["notes"],
                "call_site": hr["call_site"],
                "axis_x": hr["axis_x"],
                "axis_y": hr["axis_y"],
                "folder": hit["folder"],
                "same_9979": hit["same_9979"],
                "family_id_re": hr["family_id"],
            }
        )

    fields = [
        "hub",
        "fam_label",
        "addr",
        "grid80",
        "id_name",
        "new_name",
        "confidence",
        "notes",
        "call_site",
        "axis_x",
        "axis_y",
        "folder",
        "same_9979",
        "family_id_re",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows_out)

    high_rows = [r for r in rows_out if r["confidence"] == "high"]
    # Dedup HIGH by addr for user summary (same map via several hubs)
    by_addr: dict[str, list[dict]] = defaultdict(list)
    for r in high_rows:
        by_addr[r["addr"]].append(r)

    lines = [
        "Golf 9980 hub grids — HIGH only (empreinte unique vs atlas 9979 / A2L)",
        "Generated by identify_hub_grids.py — ne pas inventer de noms hors cette liste",
        "counts high=%d medium=%d low=%d total=%d  (unique HIGH addrs=%d)"
        % (
            counts["high"],
            counts["medium"],
            counts["low"],
            len(rows_out),
            len(by_addr),
        ),
        "",
        "addr      id_name                        hubs",
        "-" * 72,
    ]
    for addr in sorted(by_addr.keys(), key=lambda a: int(a, 16)):
        group = by_addr[addr]
        name = group[0]["id_name"]
        hubs = ",".join(sorted({g["hub"] for g in group}))
        lines.append("%s  %-30s  %s" % (addr, name, hubs))
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote", OUT_CSV)
    print("Wrote", OUT_TXT)
    print(
        "counts high=%d medium=%d low=%d total=%d unique_high_addr=%d"
        % (
            counts["high"],
            counts["medium"],
            counts["low"],
            len(rows_out),
            len(by_addr),
        )
    )
    print("--- high (by addr) ---")
    for addr in sorted(by_addr.keys(), key=lambda a: int(a, 16)):
        g = by_addr[addr]
        print(
            "%s  %s  hubs=%s  [%s]"
            % (
                addr,
                g[0]["id_name"],
                ",".join(sorted({x["hub"] for x in g})),
                g[0].get("folder") or "",
            )
        )

    # Optional copy to ghidra_scripts (CSV always; script copied by companion write)
    if GHIDRA_SCRIPTS.is_dir():
        dest = GHIDRA_SCRIPTS / OUT_CSV.name
        dest.write_bytes(OUT_CSV.read_bytes())
        print("Copied CSV ->", dest)


if __name__ == "__main__":
    main()
