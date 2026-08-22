# -*- coding: utf-8 -*-
"""Scan a PCR2.1 flash dump against atlas 9979 fingerprints.

Usage:
  python map-finder/scan_bin.py path/to/ORI.bin
  python map-finder/scan_bin.py path/to/ORI.bin --role clutch_prot
  python map-finder/scan_bin.py path/to/ORI.bin --pack stage1 --json out.json

Strategies (in order of confidence):
  1. exact     — payload bytes identical to 9979 ORI (same soft / copy)
  2. context   — payload moved but surrounding context matches (offset shift)
  3. miss      — not found (different soft / values) → Phase 2 signatures needed
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from detect import resolve_atlas

ROOT = Path(__file__).resolve().parent


def load_atlas(path: Path | None = None) -> dict:
    """Load a specific atlas file (no auto-detect)."""
    atlas_path = Path(path) if path else ROOT / "atlas" / "9979.json"
    if not atlas_path.exists():
        raise SystemExit(f"Missing {atlas_path}")
    return json.loads(atlas_path.read_text(encoding="utf-8"))


def find_all(hay: bytes, needle: bytes, limit: int = 20) -> list[int]:
    if not needle:
        return []
    out: list[int] = []
    start = 0
    while len(out) < limit:
        i = hay.find(needle, start)
        if i < 0:
            break
        out.append(i)
        start = i + 1
    return out


def scan_map(blob: bytes, m: dict) -> dict:
    fp = m.get("fingerprint")
    res = {
        "id": m["id"],
        "name": m.get("name"),
        "roles": m.get("roles", []),
        "folder": m.get("folder"),
        "ref_addr_hex": m.get("addr_hex"),
        "length": m.get("length"),
        "status": "no_fingerprint",
        "matches": [],
    }
    if not fp or not fp.get("hex"):
        return res

    payload = bytes.fromhex(fp["hex"])
    ref_addr = int(m["addr"])
    exact_at_ref = (
        ref_addr + len(payload) <= len(blob)
        and blob[ref_addr : ref_addr + len(payload)] == payload
    )
    hits = find_all(blob, payload)

    if exact_at_ref:
        res["status"] = "exact_same_addr"
        res["matches"] = [{"addr": ref_addr, "addr_hex": f"{ref_addr:06X}", "method": "exact"}]
        return res

    if hits:
        res["status"] = "exact_relocated" if hits != [ref_addr] else "exact_same_addr"
        res["matches"] = [
            {"addr": h, "addr_hex": f"{h:06X}", "method": "exact"} for h in hits
        ]
        return res

    # Context search: before + after sandwich (payload may differ)
    before = bytes.fromhex(fp.get("context_before_hex") or "")
    after = bytes.fromhex(fp.get("context_after_hex") or "")
    if len(before) >= 8 and len(after) >= 8:
        # Search before, then verify after at expected gap
        gap = fp["length"]
        for bpos in find_all(blob, before, limit=50):
            payload_start = bpos + len(before)
            after_start = payload_start + gap
            if after_start + len(after) > len(blob):
                continue
            if blob[after_start : after_start + len(after)] == after:
                res["status"] = "context_only"
                res["matches"].append(
                    {
                        "addr": payload_start,
                        "addr_hex": f"{payload_start:06X}",
                        "method": "context",
                        "note": "borders match, payload differs — likely same map slot, different soft values",
                    }
                )
        if res["matches"]:
            return res

    res["status"] = "miss"
    return res


def filter_maps(atlas: dict, role: str | None, pack: str | None) -> list[dict]:
    maps = atlas["maps"]
    if role:
        return [m for m in maps if role in m.get("roles", [])]
    if pack:
        pack_def = atlas.get("packs", {}).get(pack)
        if not pack_def:
            raise SystemExit(f"Unknown pack: {pack}. Known: {list(atlas.get('packs', {}))}")
        roles = pack_def.get("map_roles", [])
        if roles == ["*"]:
            return maps
        return [m for m in maps if any(r in roles for r in m.get("roles", []))]
    return maps


def summarize(results: list[dict]) -> dict:
    from collections import Counter

    c = Counter(r["status"] for r in results)
    return {
        "total": len(results),
        "exact_same_addr": c.get("exact_same_addr", 0),
        "exact_relocated": c.get("exact_relocated", 0),
        "context_only": c.get("context_only", 0),
        "miss": c.get("miss", 0),
        "no_fingerprint": c.get("no_fingerprint", 0),
        "hit_rate_exact": round(
            (c.get("exact_same_addr", 0) + c.get("exact_relocated", 0))
            / max(1, len(results)),
            3,
        ),
        "hit_rate_any": round(
            (
                c.get("exact_same_addr", 0)
                + c.get("exact_relocated", 0)
                + c.get("context_only", 0)
            )
            / max(1, len(results)),
            3,
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Scan PCR2.1 bin vs atlas 9979")
    ap.add_argument("bin", type=Path, help="Flash dump (.bin / .NOCS / raw)")
    ap.add_argument("--atlas", type=Path, help="Force atlas JSON (sinon détection auto)")
    ap.add_argument("--role", help="Filter by role (clutch_prot, dtc_dpf, …)")
    ap.add_argument("--pack", help="Filter by pack (stage1, dpf_off, …)")
    ap.add_argument("--json", type=Path, help="Write full JSON report")
    ap.add_argument("--show-miss", action="store_true", help="List missed maps")
    args = ap.parse_args()

    if not args.bin.exists():
        raise SystemExit(f"File not found: {args.bin}")

    blob = args.bin.read_bytes()
    picked = resolve_atlas(blob, args.atlas)
    atlas = picked["atlas"]
    maps = filter_maps(atlas, args.role, args.pack)
    results = [scan_map(blob, m) for m in maps]
    summary = summarize(results)

    print(f"Target : {args.bin} ({len(blob)} bytes)")
    print(f"ID     : {picked['identity']}")
    print(f"Family : {picked.get('family')} -- {picked['reason']}")
    print(f"Atlas  : soft {atlas.get('soft')} ({picked['path'].name}) — {summary['total']} maps scanned")
    if args.role:
        print(f"Filter : role={args.role}")
    if args.pack:
        print(f"Filter : pack={args.pack}")
    print(
        f"Hits   : exact@{summary['exact_same_addr']}  "
        f"relocated={summary['exact_relocated']}  "
        f"context={summary['context_only']}  "
        f"miss={summary['miss']}"
    )
    print(
        f"Rates  : exact={summary['hit_rate_exact']:.1%}  "
        f"any={summary['hit_rate_any']:.1%}"
    )

    # Show interesting non-trivial hits
    relocated = [r for r in results if r["status"] == "exact_relocated"]
    context = [r for r in results if r["status"] == "context_only"]
    if relocated:
        print("\nRelocated (exact payload, other address):")
        for r in relocated[:20]:
            addrs = ", ".join(m["addr_hex"] for m in r["matches"][:3])
            print(f"  {r['id']:28} ref {r['ref_addr_hex']} -> {addrs}")
    if context:
        print("\nContext-only (slot found, values differ):")
        for r in context[:20]:
            addrs = ", ".join(m["addr_hex"] for m in r["matches"][:3])
            print(f"  {r['id']:28} ref {r['ref_addr_hex']} -> {addrs}")
    if args.show_miss:
        print("\nMisses:")
        for r in results:
            if r["status"] == "miss":
                print(f"  {r['id']:28} {r.get('folder')} @{r['ref_addr_hex']}")

    report = {
        "target": str(args.bin),
        "size": len(blob),
        "atlas_soft": atlas.get("soft"),
        "atlas_file": str(picked["path"]),
        "family": picked.get("family"),
        "identity": picked["identity"],
        "atlas_reason": picked["reason"],
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
