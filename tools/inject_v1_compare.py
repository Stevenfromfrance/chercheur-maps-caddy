# -*- coding: utf-8 -*-
"""Inject V1 arrays into MAP_GRIDS + v1 bytes into hex-atlas.json."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
INDEX = SITE / "index.html"
ATLAS = SITE / "data" / "hex-atlas.json"

ROOT = Path(r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules\Caddy-CAYE-2013-03L906023PA-2531")
JSON_PATH = ROOT / "A2L" / "Volkswagen_Golf_2008_(VI)_1.6_TDI_CR_105_hp_Siemens_PCR2.1_OBD_NR.json"
ORI_PATH = ROOT / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
ACE_PATH = ROOT / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_ACE_stage1_dpf_egr.NOCS"
V1_PATH = ROOT / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V1_350wot_smooth.NOCS"


def parse_factor(s: str) -> float:
    return float(s.replace(",", ".")) if s else 1.0


def read_raw(blob: bytes, addr: int, n: int, org: str, signed: bool) -> list[int]:
    out = []
    cs = 1 if org == "eByte" else 2
    for i in range(n):
        off = addr + i * cs
        if org == "eByte":
            v = blob[off]
            if signed and v >= 0x80:
                v -= 0x100
        else:
            v = blob[off] | (blob[off + 1] << 8)
            if signed and v >= 0x8000:
                v -= 0x10000
        out.append(v)
    return out


def phys(raw: list[int], factor: float, offset: float) -> list[float]:
    return [r * factor + offset for r in raw]


def round_vals(vals: list[float], prec: int) -> list[float]:
    return [round(v, prec) for v in vals]


def main() -> None:
    ori = ORI_PATH.read_bytes()
    ace = ACE_PATH.read_bytes()
    v1 = V1_PATH.read_bytes()
    maps = json.loads(JSON_PATH.read_text(encoding="utf-8"))["maps"]
    by_addr = {int(m["Fieldvalues.StartAddr"]): m for m in maps}

    html = INDEX.read_text(encoding="utf-8")
    m = re.search(r"const MAP_GRIDS = (\[.*?\]);\s*\nlet v2dMode", html, re.S)
    if not m:
        raise SystemExit("MAP_GRIDS not found")
    grids = json.loads(m.group(1))

    for g in grids:
        addr = int(g["addr"], 16)
        am = by_addr.get(addr)
        prec = int(g.get("precision", 1))
        if not am:
            # fallback: copy ACE (unchanged vs V1 for unknown)
            g["v1"] = list(g["ace"])
            g["v1Max"] = g["aceMax"]
            g["changedCellsV1Ace"] = 0
            g["changedCellsV1Ori"] = g.get("changedCells", 0)
            continue
        cols = int(am["Columns"])
        rows = int(am["Rows"])
        t = am["Type"]
        n = 1 if t == "eEinzel" else (max(cols, rows) if t == "eEindim" else cols * rows)
        org = am["DataOrg"]
        factor = parse_factor(am.get("Fieldvalues.Factor", "1"))
        offset = parse_factor(am.get("Fieldvalues.Offset", "0") or "0")
        signed = am.get("Fieldvalues.bSigned", "0") == "1"
        v1_p = round_vals(phys(read_raw(v1, addr, n, org, signed), factor, offset), prec)
        # keep length aligned with existing ori
        if len(v1_p) != len(g["ori"]):
            v1_p = v1_p[: len(g["ori"])]
            while len(v1_p) < len(g["ori"]):
                v1_p.append(g["ace"][len(v1_p)])
        g["v1"] = v1_p
        g["v1Max"] = max(v1_p) if v1_p else 0.0
        g["changedCellsV1Ace"] = sum(1 for a, b in zip(g["ace"], v1_p) if abs(a - b) > 1e-9)
        g["changedCellsV1Ori"] = sum(1 for a, b in zip(g["ori"], v1_p) if abs(a - b) > 1e-9)

    new_json = json.dumps(grids, ensure_ascii=False, separators=(",", ":"))
    html = html[: m.start(1)] + new_json + html[m.end(1) :]
    INDEX.write_text(html, encoding="utf-8")
    print(f"Updated MAP_GRIDS ({len(grids)} maps) with v1")

    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    for w in atlas["windows"]:
        start = w["start"]
        ori_b = base64.b64decode(w["ori"])
        n = len(ori_b)
        w["v1"] = base64.b64encode(v1[start : start + n]).decode("ascii")
    # also ensure V1-only change regions covered: AccPed/tqlim/rail/smoke already in ACE windows
    atlas["hasV1"] = True
    atlas["v1Note"] = "V1 = ACE base + AccPed/tqlim/rail/smoke (350 WOT + hardcut 4800)"
    ATLAS.write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Updated hex-atlas.json ({len(atlas['windows'])} windows) with v1")

    # quick sanity
    acc = next(g for g in grids if g["id"] == "AccPed_trq4A")
    print("AccPed max ORI/ACE/V1", acc["oriMax"], acc["aceMax"], acc["v1Max"])
    print("AccPed V1!=ACE cells", acc["changedCellsV1Ace"])


if __name__ == "__main__":
    main()
