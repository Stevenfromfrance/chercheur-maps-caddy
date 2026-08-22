# -*- coding: utf-8 -*-
"""Analyze ori vs DaVinci DPF/EGR/FLAPS vs A4 Stage2 for Bertin V1."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

ORI = Path(r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy\map-finder\ecu\edc17cp14\516657\ORI_FLS.fls")
S2 = Path(r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy\map-finder\ecu\edc17cp14\516657\ref-a4-516657-stage2\A4_516657_STAGE2.fls")
DAV = Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off\A5_516657_DPF-EGR-FLAPS_noCHK.bin")

ori = ORI.read_bytes()
s2 = S2.read_bytes()
dav = DAV.read_bytes()
n = len(ori)
assert n == len(s2) == len(dav) == 2_097_152


def runs(a: bytes, b: bytes, merge=8):
    diffs = [i for i in range(n) if a[i] != b[i]]
    if not diffs:
        return [], diffs
    regs = []
    s = e = diffs[0]
    for i in diffs[1:]:
        if i <= e + merge:
            e = i
        else:
            regs.append((s, e + 1))
            s = e = i
    regs.append((s, e + 1))
    return regs, diffs


dav_set = {i for i in range(n) if ori[i] != dav[i]}
s2_set = {i for i in range(n) if ori[i] != s2[i]}
both = dav_set & s2_set
dav_only = dav_set - s2_set
s2_only = s2_set - dav_set
agree = {i for i in both if dav[i] == s2[i]}
disagree = {i for i in both if dav[i] != s2[i]}

print(f"DaVinci DPF+EGR+FLAPS vs ori: {len(dav_set)} bytes")
print(f"A4 Stage2 vs ori:            {len(s2_set)} bytes")
print(f"overlap:                     {len(both)}  same_value={len(agree)}  conflict={len(disagree)}")
print(f"DaVinci only:                {len(dav_only)}")
print(f"Stage2 only (power/other):   {len(s2_only)}")

print("\n=== Stage2-only by 64KB bank ===")
c = Counter(i // 0x10000 for i in s2_only)
for bank, k in sorted(c.items()):
    print(f"  {bank:02X}0000  {k:5d}")

print("\n=== DaVinci by 64KB bank ===")
c = Counter(i // 0x10000 for i in dav_set)
for bank, k in sorted(c.items()):
    print(f"  {bank:02X}0000  {k:5d}")

print("\n=== Conflicts DaVinci vs Stage2 (first 20) ===")
for i in sorted(disagree)[:20]:
    print(f"  {i:06X} ori={ori[i]:02X} dav={dav[i]:02X} s2={s2[i]:02X}")

# Stage2-only 16-bit LE stats in 0x180000-0x1F0000
print("\n=== Stage2-only u16 LE in 0x18xxxx-0x1Exxxx ===")
inc = dec = same_hi = 0
ratios = []
samples = []
i = 0x180000
end = 0x1F0000
while i + 1 < end:
    if i in s2_only or (i + 1) in s2_only:
        o = ori[i] | (ori[i + 1] << 8)
        t = s2[i] | (s2[i + 1] << 8)
        if o != t:
            if t > o:
                inc += 1
                if o:
                    ratios.append(t / o)
                if len(samples) < 15:
                    samples.append((i, o, t, t / o if o else 0))
            else:
                dec += 1
        i += 2
    else:
        i += 1
print(f"u16 increased={inc} decreased={dec}")
if ratios:
    ratios.sort()
    print(
        f"increase ratio p10={ratios[len(ratios)//10]:.3f} "
        f"p50={ratios[len(ratios)//2]:.3f} p90={ratios[9*len(ratios)//10]:.3f} "
        f"max={ratios[-1]:.3f}"
    )
print("samples +:")
for a, o, t, r in samples:
    print(f"  {a:06X} {o:5d} -> {t:5d}  x{r:.3f}")

# Stage2-only runs
regs, _ = runs(ori, s2, merge=4)
print("\n=== Stage2 runs overlapping s2_only, size>=16, in cal ===")
shown = 0
for s, e in regs:
    if e - s < 16:
        continue
    if s < 0x180000:
        continue
    only = sum(1 for i in range(s, e) if i in s2_only)
    if only < 8:
        continue
    print(f"  {s:06X}-{e-1:06X}  {e-s:4d}B  s2_only={only}")
    shown += 1
    if shown >= 30:
        break

# IDs
needles = [b"516657", b"8K1907401K", b"0008", b"B3UX", b"CGKA", b"1037516657"]
print("\n=== IDs still in Stage2 / DaVinci ===")
for label, blob in ("s2", s2), ("dav", dav), ("ori", ori):
    print(label, {nd.decode(): (blob.find(nd) >= 0) for nd in needles})
