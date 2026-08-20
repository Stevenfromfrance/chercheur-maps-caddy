# -*- coding: utf-8 -*-
"""Verify Top checklist addresses on Golf 9980 vs atlas 9979."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
ATLAS = ROOT / "atlas" / "9979.json"

CHECKS = [
    ("AccPed", "AccPed_trq4A", 0x1CFFC0, "HIGH"),
    ("AccPed", "AccPed_trq4A", 0x1CFCE4, "HIGH"),
    ("AccPed", "AccPed_trq4A", 0x1CFAE4, "HIGH"),
    ("tqlim", "tqlim_base_pu_4A", 0x1D32CC, "MEDIUM"),
    ("tqlim", "tqlim_base_pu_4A", 0x1D330C, "MEDIUM"),
    ("tqlim", "tqlim_base_pu_4A", 0x1D332C, "MEDIUM"),
    ("smoke", "smoke_mapA", 0x1D0F34, "MEDIUM"),
    ("smoke", "smoke_mapA", 0x1D0F80, "MEDIUM"),
    ("smoke", "smoke_mapA", 0x1D282C, "MEDIUM"),
    ("turbo", "turbo_base3B", 0x1C09B0, "HIGH"),
    ("turbo", "turbo_base3B", 0x1C1B50, "HIGH"),
    ("turbo", "turbo_base3B", 0x1C206C, "HIGH"),
]


def main() -> None:
    blob = BIN.read_bytes()
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    maps = {m["id"]: m for m in atlas["maps"]}
    extents = [(m["addr"], m["addr"] + m["length"], m["id"], m.get("name", "")) for m in atlas["maps"]]

    def containing(off: int):
        return [(mid, name, off - a) for a, e, mid, name in extents if a <= off < e]

    print("=== VERIF auto Golf 9980 vs atlas 9979 ===\n")
    print(f"{'role':7} {'Ghidra':10} {'claimed_id':20} {'delta':>8} {'inside':6} {'same64':6}  verdict")
    print("-" * 100)

    for role, mid, off, conf in CHECKS:
        m = maps.get(mid)
        start = m["addr"] if m else None
        length = m["length"] if m else 0
        inside = start is not None and start <= off < start + length
        delta = (off - start) if start is not None else None
        golf64 = blob[off : off + 64]
        same_rel = False
        if inside and m and m.get("fingerprint"):
            rel = off - start
            fp_hex = m["fingerprint"]["hex"]
            if rel * 2 + 128 <= len(fp_hex):
                expected = bytes.fromhex(fp_hex[rel * 2 : rel * 2 + 128])
                same_rel = golf64 == expected
        hits = containing(off)
        hit_ids = ",".join(h[0] for h in hits[:4]) or "-"

        if inside and same_rel:
            verdict = "OK — meme octets que 9979 a cet offset"
        elif inside and not same_rel:
            verdict = "OK zone — dans la map, valeurs soft differentes (normal 9980)"
        elif hits:
            verdict = f"OK autre map atlas: {hit_ids}"
        else:
            verdict = "ATTENTION — hors etendue atlas claim"

        # refine smoke: often different smoke id
        if role == "smoke" and not inside and hits:
            verdict = f"OK — dans {hit_ids} (pas smoke_mapA start 1D1D18)"

        if role == "turbo" and not inside and hits:
            verdict = f"OK — turbo/autre: {hit_ids}"

        ghidra = off + 0x80000000
        dlt = f"+0x{delta:X}" if delta is not None else "?"
        print(
            f"{role:7} {ghidra:08X} {mid:20} {dlt:>8} {str(inside):6} {str(same_rel):6}  {verdict}"
        )

    print("\n=== Contenant reel (qui contient l'adresse) ===")
    for role, mid, off, conf in CHECKS:
        hits = containing(off)
        ghidra = off + 0x80000000
        if not hits:
            print(f"  {ghidra:08X}  AUCUN map atlas 9979")
            continue
        parts = [f"{h[0]} (+0x{h[2]:X})" for h in hits]
        print(f"  {ghidra:08X}  {', '.join(parts)}")

    # AccPed / tqlim / turbo starts on Golf vs 9979 fingerprint
    print("\n=== Debut de map atlas sur Golf (exact 64o vs ORI 9979) ===")
    for mid in ("AccPed_trq4A", "tqlim_base_pu_4A", "smoke_mapA", "turbo_base3B"):
        m = maps[mid]
        s = m["addr"]
        exp = bytes.fromhex(m["fingerprint"]["hex"][:128])
        got = blob[s : s + 64]
        print(
            f"  {mid:20} @{m['addr_hex']} G={s+0x80000000:08X} exact64={got==exp} sha={hashlib.sha256(got).hexdigest()[:10]}"
        )


if __name__ == "__main__":
    main()
