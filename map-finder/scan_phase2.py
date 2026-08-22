# -*- coding: utf-8 -*-
"""Phase 2 scan — offset clusters + axis fingerprints + predicted-slot validation.

Usage:
  python map-finder/scan_phase2.py path/to/ORI.bin
  python map-finder/scan_phase2.py path/to/ORI.bin --pack stage1 --json out.json
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

from detect import extract_soft_id, resolve_atlas
from scan_bin import filter_maps, find_all, scan_map, summarize

ROOT = Path(__file__).resolve().parent


def read_u16_le(blob: bytes, addr: int, n: int) -> list[int]:
    out = []
    for i in range(n):
        off = addr + i * 2
        if off + 1 >= len(blob):
            break
        out.append(blob[off] | (blob[off + 1] << 8))
    return out


def phys(raw: list[int], factor: float | None, offset: float | None, signed: bool | None) -> list[float]:
    f = 1.0 if factor is None else factor
    o = 0.0 if offset is None else offset
    vals = []
    for r in raw:
        if signed and r >= 0x8000:
            r -= 0x10000
        vals.append(r * f + o)
    return vals


def _family(r: dict) -> str:
    """Separate DTC masks from calibration maps — they shift differently."""
    if r.get("group") == "dtc" or str(r.get("id", "")).startswith("DTC_"):
        return "dtc"
    folder = (r.get("folder") or "").lower()
    if "speed" in folder or str(r.get("id", "")).lower().startswith("vmax"):
        return "speed"
    return "cal"


def cluster_offsets(phase1: list[dict], bin_size: int = 0x10000) -> dict[str, int]:
    """Dominant delta per (family, address band) from relocated / context hits."""
    buckets: dict[str, list[int]] = defaultdict(list)
    for r in phase1:
        if r["status"] not in ("exact_relocated", "context_only"):
            continue
        ref = int(r["ref_addr_hex"], 16)
        if not r["matches"]:
            continue
        best = min(r["matches"], key=lambda m: abs(m["addr"] - ref))
        delta = best["addr"] - ref
        # Ignore absurd jumps (>64KB) — false positive payload collisions
        if abs(delta) > 0x10000:
            continue
        key = f"{_family(r)}:{region_key(ref, bin_size)}"
        buckets[key].append(delta)
    # Also family-global modes (fallback when band empty)
    fam_buckets: dict[str, list[int]] = defaultdict(list)
    for key, deltas in buckets.items():
        fam = key.split(":", 1)[0]
        fam_buckets[fam].extend(deltas)

    out: dict[str, int] = {}
    for key, deltas in buckets.items():
        mode, _n = Counter(deltas).most_common(1)[0]
        out[key] = mode
    for fam, deltas in fam_buckets.items():
        mode, _n = Counter(deltas).most_common(1)[0]
        out[f"{fam}:*"] = mode
    return out


def region_key(addr: int, bin_size: int = 0x10000) -> str:
    return f"{(addr // bin_size) * bin_size:06X}"


def lookup_delta(offsets: dict[str, int], m: dict) -> list[int]:
    """Ordered candidate deltas for a map (band → family → other families)."""
    ref = int(m["addr"])
    fam = _family(m)
    band = region_key(ref)
    ordered: list[int] = []
    for key in (f"{fam}:{band}", f"{fam}:*"):
        if key in offsets and offsets[key] not in ordered:
            ordered.append(offsets[key])
    # Also try other family modes (rarely useful, last resort)
    for key, d in offsets.items():
        if d not in ordered:
            ordered.append(d)
    return ordered


def validate_predicted(blob: bytes, m: dict, pred: int) -> dict | None:
    length = int(m.get("length") or 0)
    if pred < 0 or length <= 0 or pred + length > len(blob):
        return None
    data_org = m.get("data_org") or "eLoHi"
    cols = int(m.get("cols") or 1)
    rows = int(m.get("rows") or 1)
    n = 1 if m.get("type") == "eEinzel" else (
        max(cols, rows) if m.get("type") == "eEindim" else cols * rows
    )
    unit = (m.get("unit") or "").lower()
    factor = m.get("factor")
    offset = m.get("offset")
    signed = m.get("signed")

    if data_org == "eByte":
        raw = list(blob[pred : pred + n])
    else:
        raw = read_u16_le(blob, pred, n)
        if len(raw) < max(1, n // 2):
            return None

    vals = phys(raw, factor, offset, signed)
    if not vals:
        return None
    vmin, vmax = min(vals), max(vals)
    # Plausibility by unit family
    ok = True
    reason = []
    if unit in ("nm",):
        ok = -50 <= vmin and vmax <= 1200 and vmax >= 20
        reason.append(f"Nm[{vmin:.1f},{vmax:.1f}]")
    elif unit in ("mbar",):
        ok = 0 <= vmin and vmax <= 5000 and vmax >= 500
        reason.append(f"mbar[{vmin:.1f},{vmax:.1f}]")
    elif unit in ("km/h",):
        ok = 0 <= vmax <= 400
        reason.append(f"km/h[{vmin:.1f},{vmax:.1f}]")
    elif unit in ("%",):
        ok = -5 <= vmin and vmax <= 200
        reason.append(f"%[{vmin:.1f},{vmax:.1f}]")
    elif unit in ("bar",):
        ok = 0 <= vmax <= 2500
        reason.append(f"bar[{vmin:.1f},{vmax:.1f}]")
    else:
        # Generic: not all zeros / not all 0xFFFF
        if data_org != "eByte":
            ok = not (all(r == 0 for r in raw) or all(r == 0xFFFF for r in raw))
        reason.append(f"raw/phys[{vmin:.2f},{vmax:.2f}]")

    # DTC / mask maps: accept any non-empty
    if m.get("group") == "dtc":
        ok = True
        reason = ["dtc_mask"]

    if not ok:
        return None
    return {
        "addr": pred,
        "addr_hex": f"{pred:06X}",
        "method": "offset_predict",
        "phys_min": round(vmin, 3),
        "phys_max": round(vmax, 3),
        "note": " ".join(reason),
    }


def scan_axes(blob: bytes, m: dict) -> dict:
    out = {}
    for key in ("axis_x", "axis_y"):
        ax = m.get(key) or {}
        fp = ax.get("fingerprint") or {}
        hx = fp.get("hex")
        if not hx:
            continue
        hits = find_all(blob, bytes.fromhex(hx), limit=8)
        ref = ax.get("addr")
        out[key] = {
            "ref_addr_hex": ax.get("addr_hex"),
            "hits": [{"addr": h, "addr_hex": f"{h:06X}", "delta": (h - ref) if ref else None} for h in hits],
        }
    return out


def enrich_phase2(blob: bytes, maps: list[dict], phase1: list[dict]) -> list[dict]:
    offsets = cluster_offsets(phase1)
    by_id = {r["id"]: r for r in phase1}
    results = []
    for m in maps:
        r = dict(by_id[m["id"]])
        r["axes"] = scan_axes(blob, m)
        if r["status"] in ("exact_same_addr", "exact_relocated", "context_only"):
            results.append(r)
            continue
        # miss / no_fingerprint → try family/band offsets
        ref = int(m["addr"])
        deltas = lookup_delta(offsets, m)
        preferred = deltas[0] if deltas else None
        candidates = []
        for d in deltas:
            pred = ref + d
            if pred not in candidates:
                candidates.append(pred)

        matches = []
        for pred in candidates:
            hit = validate_predicted(blob, m, pred)
            if hit:
                hit["delta"] = pred - ref
                matches.append(hit)
        if matches:
            def rank(h: dict) -> tuple:
                d = h.get("delta")
                pref = 0 if preferred is not None and d == preferred else 1
                unit = (m.get("unit") or "").lower()
                mx = h.get("phys_max")
                quality = 0
                if unit == "nm" and isinstance(mx, (int, float)):
                    # Drivers wish / torque limiters: stock peaks usually 200–420 Nm
                    if 200 <= mx <= 420:
                        quality = 0
                    elif 150 <= mx <= 500:
                        quality = 1
                    else:
                        quality = 3
                elif unit == "mbar" and isinstance(mx, (int, float)):
                    quality = 0 if 1500 <= mx <= 3500 else 2
                return (quality, pref, abs(d or 0))

            matches.sort(key=rank)
            r["status"] = "offset_predict"
            r["matches"] = matches[:5]
        results.append(r)
    return results, offsets


def summarize_p2(results: list[dict]) -> dict:
    s = summarize(results)
    s["offset_predict"] = sum(1 for r in results if r["status"] == "offset_predict")
    s["miss"] = sum(1 for r in results if r["status"] == "miss")
    s["hit_rate_any"] = round(
        (
            s["exact_same_addr"]
            + s["exact_relocated"]
            + s["context_only"]
            + s["offset_predict"]
        )
        / max(1, s["total"]),
        3,
    )
    return s


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase2 PCR2.1 map finder")
    ap.add_argument("bin", type=Path)
    ap.add_argument("--atlas", type=Path, help="Force atlas JSON (sinon détection auto)")
    ap.add_argument("--role")
    ap.add_argument("--pack")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--show-miss", action="store_true")
    args = ap.parse_args()

    if not args.bin.exists():
        raise SystemExit(f"File not found: {args.bin}")

    blob = args.bin.read_bytes()
    picked = resolve_atlas(blob, args.atlas)
    atlas = picked["atlas"]
    maps = filter_maps(atlas, args.role, args.pack)
    phase1 = [scan_map(blob, m) for m in maps]
    results, offsets = enrich_phase2(blob, maps, phase1)
    summary = summarize_p2(results)

    print(f"Target : {args.bin} ({len(blob)} bytes)")
    print(f"ID     : {picked['identity']}")
    print(f"Family : {picked.get('family')} -- {picked['reason']}")
    print(f"Atlas  : soft {atlas.get('soft')} ({picked['path'].name}) — {summary['total']} maps")
    if args.pack:
        print(f"Filter : pack={args.pack}")
    if args.role:
        print(f"Filter : role={args.role}")
    print(f"Offsets: { {k: f'{v:+d}' for k, v in sorted(offsets.items())} }")
    print(
        f"Hits   : exact@{summary['exact_same_addr']}  "
        f"reloc={summary['exact_relocated']}  "
        f"ctx={summary['context_only']}  "
        f"predict={summary['offset_predict']}  "
        f"miss={summary['miss']}"
    )
    print(f"Rates  : exact={summary['hit_rate_exact']:.1%}  any={summary['hit_rate_any']:.1%}")

    predicted = [r for r in results if r["status"] == "offset_predict"]
    if predicted:
        print("\nOffset-predicted (Phase 2):")
        for r in predicted[:25]:
            m0 = r["matches"][0]
            print(
                f"  {r['id']:28} ref {r['ref_addr_hex']} -> {m0['addr_hex']} "
                f"(d={m0.get('delta'):+d}) {m0.get('note','')}"
            )

    if args.show_miss:
        print("\nStill miss:")
        for r in results:
            if r["status"] == "miss":
                print(f"  {r['id']:28} {r.get('folder')} @{r['ref_addr_hex']}")

    # Key pack maps quick view
    key_ids = [
        "AccPed_trq4A",
        "tqlim_base_pu_4A",
        "tqlim_cluth_prot",
        "vmax3",
        "smoke_mapA",
        "turbo_base3B",
        "airctl_hysteresisC",
    ]
    print("\nKey maps:")
    by = {r["id"]: r for r in results}
    for kid in key_ids:
        r = by.get(kid)
        if not r:
            continue
        addr = r["matches"][0]["addr_hex"] if r.get("matches") else "-"
        print(f"  {kid:28} {r['status']:16} {addr}")

    report = {
        "target": str(args.bin),
        "size": len(blob),
        "identity": picked["identity"],
        "family": picked.get("family"),
        "atlas_soft": atlas.get("soft"),
        "atlas_file": str(picked["path"]),
        "atlas_reason": picked["reason"],
        "offset_clusters": offsets,
        "filter": {"role": args.role, "pack": args.pack},
        "summary": summary,
        "results": results,
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
