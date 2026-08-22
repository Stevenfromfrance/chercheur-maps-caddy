# -*- coding: utf-8 -*-
"""Export atlas PCR2.1 soft 9979 (gold standard) for multi-soft map finding.

Sources:
  - MAP_GRIDS in site index.html (dims, folders, packs-relevant grids)
  - A2L/WinOLS JSON (factors, axis addrs, DataOrg)
  - ORI bin 9979 (raw fingerprints + context)

Output:
  map-finder/atlas/9979.json
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "atlas" / "9979.json"
PACKS = Path(__file__).resolve().parent / "packs.json"

VEH = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules\Caddy-CAYE-2013-03L906023PA-2531"
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

CTX = 16  # bytes before/after map for signature context


def parse_factor(s: str | None) -> float | None:
    if s is None or s == "":
        return None
    return float(str(s).replace(",", "."))


def cell_bytes(data_org: str) -> int:
    return 1 if data_org == "eByte" else 2


def map_byte_len(typ: str, cols: int, rows: int, data_org: str) -> int:
    cs = cell_bytes(data_org)
    if typ == "eEinzel":
        n = 1
    elif typ == "eEindim":
        n = max(cols, rows)
    else:
        n = cols * rows
    return n * cs


def assign_roles(g: dict) -> list[str]:
    roles: list[str] = []
    mid = g.get("id", "")
    folder = g.get("folder", "")
    group = g.get("group", "")
    mid_l = mid.lower()
    folder_l = folder.lower()

    if group == "priority":
        roles.append("stage1_core")
    if group == "a2l" and folder in {
        "Turbo boost pressure",
        "Smoke limitation",
        "Rail pressure",
    }:
        roles.append("stage1_support")
    if folder == "Vehicle speed limiters" or mid_l.startswith("vmax"):
        roles.append("speed_limiter")
    if mid_l.startswith("tqlim_cluth_prot"):
        roles.append("clutch_prot")
    if folder == "Air control" or "airctl" in mid_l or (
        "egr" in mid_l and group != "dtc"
    ):
        roles.append("egr_control")
    if group == "dtc":
        fam = {
            "DPF": "dtc_dpf",
            "EGR": "dtc_egr",
            "EGT": "dtc_egt",
            "EGR/DPF": "dtc_egr_dpf",
            "EGR com": "dtc_egr_com",
            "DPF/O2": "dtc_dpf_o2",
        }.get(folder)
        if fam:
            roles.append(fam)
        else:
            roles.append("dtc_other")
    if group == "provisoire":
        roles.append("provisoire")
    if not roles:
        roles.append("other")
    return roles


def load_map_grids() -> list[dict]:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    m = re.search(r"const MAP_GRIDS = (\[.*?\]);", html, re.S)
    if not m:
        raise SystemExit("MAP_GRIDS not found in index.html")
    return json.loads(m.group(1))


def load_a2l_by_addr() -> dict[int, dict]:
    if not A2L_JSON.exists():
        print(f"WARN: A2L JSON missing: {A2L_JSON}")
        return {}
    maps = json.loads(A2L_JSON.read_text(encoding="utf-8"))["maps"]
    out: dict[int, dict] = {}
    for am in maps:
        try:
            addr = int(am["Fieldvalues.StartAddr"])
        except (KeyError, ValueError, TypeError):
            continue
        out[addr] = am
    return out


def find_ori() -> Path:
    for p in ORI_CANDIDATES:
        if p.exists():
            return p
    raise SystemExit("ORI 9979 not found — update ORI_CANDIDATES in export_atlas_9979.py")


def slice_hex(blob: bytes, start: int, length: int) -> str | None:
    if start < 0 or length <= 0 or start + length > len(blob):
        return None
    return blob[start : start + length].hex()


def build_fingerprint(blob: bytes, addr: int, length: int) -> dict | None:
    if addr < 0 or length <= 0 or addr + length > len(blob):
        return None
    raw = blob[addr : addr + length]
    before = blob[max(0, addr - CTX) : addr]
    after = blob[addr + length : min(len(blob), addr + length + CTX)]
    return {
        "length": length,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "hex": raw.hex(),
        "context_before_hex": before.hex(),
        "context_after_hex": after.hex(),
        "context_pad_before": CTX - len(before),
        "context_pad_after": CTX - len(after),
    }


def axis_meta(am: dict | None, which: str) -> dict | None:
    if not am:
        return None
    prefix = f"Axis{which}."
    addr_s = am.get(prefix + "DataAddr")
    try:
        addr = int(addr_s) if addr_s not in (None, "", "0", 0) else None
    except (TypeError, ValueError):
        addr = None
    if not addr:
        return {
            "name": am.get(prefix + "Name"),
            "id_name": am.get(prefix + "IdName"),
            "unit": am.get(prefix + "Unit"),
            "factor": parse_factor(am.get(prefix + "Factor")),
            "offset": parse_factor(am.get(prefix + "Offset") or "0"),
            "data_org": am.get(prefix + "DataOrg"),
            "addr": None,
        }
    return {
        "name": am.get(prefix + "Name"),
        "id_name": am.get(prefix + "IdName"),
        "unit": am.get(prefix + "Unit"),
        "factor": parse_factor(am.get(prefix + "Factor")),
        "offset": parse_factor(am.get(prefix + "Offset") or "0"),
        "data_org": am.get(prefix + "DataOrg") or "eLoHi",
        "addr": addr,
        "addr_hex": f"{addr:06X}",
    }


def main() -> None:
    grids = load_map_grids()
    a2l = load_a2l_by_addr()
    ori_path = find_ori()
    ori = ori_path.read_bytes()
    packs_doc = json.loads(PACKS.read_text(encoding="utf-8"))

    maps_out: list[dict] = []
    role_index: dict[str, list[str]] = {}
    fp_ok = 0
    a2l_hit = 0

    for g in grids:
        addr = int(g["addr"], 16)
        end = int(g["end"], 16)
        am = a2l.get(addr)
        if am:
            a2l_hit += 1

        typ = (am or {}).get("Type") or g.get("type") or "eZweidim"
        cols = int((am or {}).get("Columns") or g.get("cols") or 1)
        rows = int((am or {}).get("Rows") or g.get("rows") or 1)
        data_org = (am or {}).get("DataOrg") or "eLoHi"
        length = end - addr + 1
        # Prefer computed length from A2L dims when consistent
        computed = map_byte_len(typ, cols, rows, data_org)
        if am and abs(computed - length) <= 2:
            length = computed

        roles = assign_roles(g)
        entry: dict = {
            "id": g["id"],
            "name": g.get("name"),
            "folder": g.get("folder"),
            "group": g.get("group"),
            "roles": roles,
            "addr": addr,
            "addr_hex": f"{addr:06X}",
            "end": end,
            "end_hex": f"{end:06X}",
            "length": length,
            "cols": cols,
            "rows": rows,
            "type": typ,
            "data_org": data_org,
            "unit": (am or {}).get("Fieldvalues.Unit") or g.get("unit"),
            "factor": parse_factor((am or {}).get("Fieldvalues.Factor"))
            if am
            else None,
            "offset": parse_factor((am or {}).get("Fieldvalues.Offset") or "0")
            if am
            else None,
            "signed": (
                (am or {}).get("Fieldvalues.bSigned", (am or {}).get("bSigned", "0"))
                == "1"
            )
            if am
            else None,
            "axis_x_name": g.get("axisXName"),
            "axis_y_name": g.get("axisYName"),
            "axis_x_unit": g.get("axisXUnit"),
            "axis_y_unit": g.get("axisYUnit"),
            "axis_x": axis_meta(am, "X"),
            "axis_y": axis_meta(am, "Y"),
            "source": "a2l" if am else g.get("group"),
            "stats": {
                "ori_max": g.get("oriMax"),
                "ace_max": g.get("aceMax"),
                "v1_max": g.get("v1Max"),
                "v2_max": g.get("v2Max"),
            },
        }

        fp = build_fingerprint(ori, addr, length)
        if fp:
            entry["fingerprint"] = fp
            fp_ok += 1
            # Axis fingerprints (useful for launch/hardcut axis remap detection)
            for key, ax in (("axis_x", entry["axis_x"]), ("axis_y", entry["axis_y"])):
                if not ax or not ax.get("addr"):
                    continue
                n_pts = cols if key == "axis_x" else rows
                ax_len = n_pts * cell_bytes(ax.get("data_org") or "eLoHi")
                ax_fp = build_fingerprint(ori, int(ax["addr"]), ax_len)
                if ax_fp:
                    ax["fingerprint"] = ax_fp

        maps_out.append(entry)
        for r in roles:
            role_index.setdefault(r, []).append(g["id"])

    atlas = {
        "schema": 1,
        "ecu": "Siemens PCR2.1",
        "soft": "9979",
        "family": "SM2G0P",
        "hw": "03L906023TB",
        "project": "SM2G0P2000000",
        "vehicle": "VW Caddy CAYE 1.6 TDI",
        "flash_size": len(ori),
        "ori_file": str(ori_path),
        "a2l_file": str(A2L_JSON) if A2L_JSON.exists() else None,
        "generated_from": ["index.html MAP_GRIDS", "A2L JSON", "ORI bin"],
        "counts": {
            "maps": len(maps_out),
            "with_fingerprint": fp_ok,
            "with_a2l": a2l_hit,
            "by_group": {},
            "by_role": {k: len(v) for k, v in sorted(role_index.items())},
        },
        "packs": packs_doc["packs"],
        "role_index": role_index,
        "maps": maps_out,
    }
    from collections import Counter

    atlas["counts"]["by_group"] = dict(Counter(m["group"] for m in maps_out))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(atlas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {OUT.relative_to(SITE)} — {len(maps_out)} maps, "
        f"{fp_ok} fingerprints, {a2l_hit} A2L hits"
    )
    print("Roles:", atlas["counts"]["by_role"])


if __name__ == "__main__":
    main()
