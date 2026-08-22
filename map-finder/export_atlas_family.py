# -*- coding: utf-8 -*-
"""Clone atlas 9979 onto another PCR2.1 ORI using a Phase 2 scan report.

Usage:
  python export_atlas_family.py --ori path/to/ORI.bin --report reports/xxx-phase2.json --soft 6929
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from export_atlas_9979 import build_fingerprint, cell_bytes
from scan_bin import find_all
from detect import extract_soft_id, family_from_project

ROOT = Path(__file__).resolve().parent
SRC_ATLAS = ROOT / "atlas" / "9979.json"


def pick_match(result: dict, ref: int, family_delta: int | None) -> dict | None:
    matches = result.get("matches") or []
    if not matches:
        return None
    if result.get("status") == "exact_same_addr":
        return matches[0]
    target = ref + family_delta if family_delta is not None else ref

    def score(m: dict) -> tuple:
        addr = int(m["addr"])
        method = m.get("method") or ""
        exact = 0 if method in ("exact",) else 1
        return (exact, abs(addr - target), abs(addr - ref))

    return min(matches, key=score)


def family_delta_for(m: dict, clusters: dict) -> int | None:
    mid = str(m.get("id") or "")
    folder = (m.get("folder") or "").lower()
    group = m.get("group") or ""
    if group == "dtc" or mid.startswith("DTC_"):
        fam = "dtc"
    elif "speed" in folder or mid.lower().startswith("vmax"):
        fam = "speed"
    else:
        fam = "cal"
    addr = int(m["addr"])
    band = f"{(addr // 0x10000) * 0x10000:06X}"
    for key in (f"{fam}:{band}", f"{fam}:*"):
        if key in clusters:
            return int(clusters[key])
    return None


def relocate_axis(ax: dict | None, blob: bytes, map_delta: int) -> dict | None:
    if not ax:
        return ax
    ax = copy.deepcopy(ax)
    old = ax.get("addr")
    fp = (ax.get("fingerprint") or {}).get("hex")
    new_addr = None
    method = None
    if fp:
        hits = find_all(blob, bytes.fromhex(fp), limit=8)
        if len(hits) == 1:
            new_addr = hits[0]
            method = "exact_axis"
        elif hits and old is not None:
            pred = old + map_delta
            new_addr = min(hits, key=lambda h: abs(h - pred))
            method = "axis_nearest"
    if new_addr is None and old is not None:
        new_addr = old + map_delta
        method = "axis_delta"
    if new_addr is None:
        return ax
    ax["addr"] = new_addr
    ax["addr_hex"] = f"{new_addr:06X}"
    ax["reloc_method"] = method
    n = (ax.get("fingerprint") or {}).get("length")
    if not n:
        n = 16
        org = ax.get("data_org") or "eLoHi"
        # keep previous fingerprint length if present
    new_fp = build_fingerprint(blob, new_addr, n)
    if new_fp:
        ax["fingerprint"] = new_fp
    return ax


def main() -> None:
    ap = argparse.ArgumentParser(description="Export family atlas from Phase2 report")
    ap.add_argument("--ori", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    ap.add_argument("--soft", required=True, help="Soft id for output filename, e.g. 6929")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if not args.ori.exists():
        raise SystemExit(f"ORI missing: {args.ori}")
    if not args.report.exists():
        raise SystemExit(f"Report missing: {args.report}")

    src = json.loads(SRC_ATLAS.read_text(encoding="utf-8"))
    report = json.loads(args.report.read_text(encoding="utf-8"))
    blob = args.ori.read_bytes()
    ident = extract_soft_id(blob)
    clusters = report.get("offset_clusters") or {}
    by_scan = {r["id"]: r for r in report["results"]}

    maps_out = []
    conf = {"exact": 0, "relocated": 0, "context": 0, "predict": 0, "unconfirmed": 0}
    fp_ok = 0

    for m in src["maps"]:
        nm = copy.deepcopy(m)
        ref = int(m["addr"])
        length = int(m.get("length") or 0)
        scan = by_scan.get(m["id"]) or {}
        delta = family_delta_for(m, clusters)
        picked = pick_match(scan, ref, delta) if scan else None
        status = scan.get("status") or "miss"

        if picked:
            new_addr = int(picked["addr"])
            map_delta = new_addr - ref
            if status == "exact_same_addr":
                confidence = "exact"
            elif status == "exact_relocated":
                confidence = "relocated"
            elif status == "context_only":
                confidence = "context"
            else:
                confidence = "predict"
        elif delta is not None:
            new_addr = ref + delta
            map_delta = delta
            confidence = "unconfirmed"
        else:
            new_addr = ref
            map_delta = 0
            confidence = "unconfirmed"

        conf[confidence] = conf.get(confidence, 0) + 1
        nm["addr"] = new_addr
        nm["addr_hex"] = f"{new_addr:06X}"
        nm["end"] = new_addr + length - 1
        nm["end_hex"] = f"{nm['end']:06X}"
        nm["ref_9979_addr"] = ref
        nm["ref_9979_addr_hex"] = m.get("addr_hex")
        nm["delta_from_9979"] = map_delta
        nm["locate"] = status
        nm["confidence"] = confidence

        fp = build_fingerprint(blob, new_addr, length)
        if fp:
            nm["fingerprint"] = fp
            fp_ok += 1
        nm["axis_x"] = relocate_axis(m.get("axis_x"), blob, map_delta)
        nm["axis_y"] = relocate_axis(m.get("axis_y"), blob, map_delta)
        maps_out.append(nm)

    out_path = args.out or (ROOT / "atlas" / f"{args.soft}.json")
    atlas = {
        "schema": 1,
        "ecu": "Siemens PCR2.1",
        "soft": str(args.soft),
        "family": family_from_project(ident.get("project")) or "SM2G0M",
        "hw": ident.get("hw"),
        "project": ident.get("project"),
        "vehicle": ident.get("engine") or "PCR2.1 family atlas",
        "flash_size": len(blob),
        "ori_file": str(args.ori),
        "cloned_from": "9979",
        "generated_from": [
            "atlas/9979.json",
            str(args.report),
            str(args.ori),
        ],
        "identity": ident,
        "offset_clusters": clusters,
        "counts": {
            "maps": len(maps_out),
            "with_fingerprint": fp_ok,
            "confidence": conf,
            "by_group": src["counts"].get("by_group"),
            "by_role": src["counts"].get("by_role"),
        },
        "packs": src.get("packs"),
        "role_index": src.get("role_index"),
        "maps": maps_out,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(atlas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Maps {len(maps_out)} fingerprints {fp_ok} confidence {conf}")
    print(f"ID {ident}")


if __name__ == "__main__":
    main()
