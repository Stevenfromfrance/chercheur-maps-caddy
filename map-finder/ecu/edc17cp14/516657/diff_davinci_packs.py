# -*- coding: utf-8 -*-
from pathlib import Path
from collections import defaultdict
import csv

ori_path = Path(
    r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy\map-finder\ecu\edc17cp14\516657\ORI_FLS.fls"
)
dtc_dir = Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off")
out_dir = Path(
    r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy\map-finder\ecu\edc17cp14\516657"
)

ori = ori_path.read_bytes()
n = len(ori)
assert n == 2_097_152


def regions(a: bytes, b: bytes, merge_gap: int = 16):
    diffs = [i for i in range(n) if a[i] != b[i]]
    if not diffs:
        return [], diffs
    regs = []
    s = e = diffs[0]
    for i in diffs[1:]:
        if i <= e + merge_gap:
            e = i
        else:
            regs.append((s, e + 1))
            s = e = i
    regs.append((s, e + 1))
    return regs, diffs


def hx(data: bytes, lim: int = 12) -> str:
    return data[:lim].hex()


packs = {}
for p in sorted(dtc_dir.glob("DaVinci*.BIN")):
    if "_DPF_" in p.name:
        key = "DPF"
    elif "_EGR_" in p.name:
        key = "EGR"
    elif "_TVA_" in p.name:
        key = "TVA"
    elif "_LAMBDA_" in p.name:
        key = "LAMBDA"
    elif "_FLAPS_" in p.name:
        key = "FLAPS"
    else:
        continue
    data = p.read_bytes()
    assert len(data) == n
    regs, diffs = regions(ori, data)
    packs[key] = {"path": p, "data": data, "regs": regs, "diffs": diffs}

lines = ["# A5 516657 — DaVinci packs vs ORI FLS", ""]
print("=== PAR PACK vs ORI ===")
lines.append("| Pack | Octets | Régions | Première | Dernière |")
lines.append("|------|-------:|--------:|----------|----------|")
for k in ("DPF", "EGR", "FLAPS", "LAMBDA", "TVA"):
    v = packs[k]
    regs, diffs = v["regs"], v["diffs"]
    sizes = [e - s for s, e in regs]
    print(
        f"{k:7s}  bytes={len(diffs):5d}  regions={len(regs):4d}  "
        f"min={min(sizes)} max={max(sizes)}  "
        f"first={regs[0][0]:06X} last={regs[-1][0]:06X}"
    )
    lines.append(
        f"| **{k}** | {len(diffs)} | {len(regs)} | `{regs[0][0]:06X}` | `{regs[-1][0]:06X}` |"
    )

print("\n=== TOP REGIONS ===")
for k in ("DPF", "EGR", "FLAPS", "LAMBDA", "TVA"):
    v = packs[k]
    print(f"\n-- {k} --")
    lines.append(f"\n## {k}\n")
    lines.append("| Start | End | Size | zeroed | ORI | MOD |")
    lines.append("|-------|-----|-----:|-------:|-----|-----|")
    ranked = sorted(v["regs"], key=lambda r: r[1] - r[0], reverse=True)
    show = ranked[:15]
    for s, e in show:
        o = ori[s:e]
        d = v["data"][s:e]
        z = sum(1 for x in d if x == 0)
        print(
            f"  {s:06X}-{e-1:06X}  {e-s:5d}B  zeroed={z:5d}  "
            f"ori={hx(o)}  mod={hx(d)}"
        )
        lines.append(
            f"| `{s:06X}` | `{e-1:06X}` | {e-s} | {z} | `{hx(o)}` | `{hx(d)}` |"
        )
    if len(ranked) > 15:
        lines.append(f"\n… +{len(ranked)-15} régions plus petites\n")

print("\n=== CHEVAUCHEMENT ===")
keys = ["DPF", "EGR", "FLAPS", "LAMBDA", "TVA"]
for i, a in enumerate(keys):
    sa = set(packs[a]["diffs"])
    for b in keys[i + 1 :]:
        inter = len(sa & set(packs[b]["diffs"]))
        if inter:
            print(f"  {a} / {b} overlap = {inter} octets")

needles = [
    ("P0118", bytes.fromhex("0118")),
    ("P0606", bytes.fromhex("0606")),
    ("P2185", bytes.fromhex("2185")),
    ("P242A", bytes.fromhex("242A")),
    ("P2002", bytes.fromhex("2002")),
    ("P2463LE", bytes.fromhex("6324")),
    ("P0400", bytes.fromhex("0400")),
    ("P0130", bytes.fromhex("0130")),
    ("P2008", bytes.fromhex("2008")),
    ("P0638", bytes.fromhex("0638")),
]
print("\n=== CODES DANS FENETRE DES ZONES ===")
for k in keys:
    found = []
    for s, e in packs[k]["regs"]:
        window = ori[max(0, s - 8) : min(n, e + 8)]
        for name, pat in needles:
            if pat in window:
                found.append(f"{name}@{s:06X}")
    print(f"  {k}: {len(found)}  {', '.join(found[:12])}")

bertin = set()
for k in ("DPF", "EGR", "FLAPS"):
    bertin |= set(packs[k]["diffs"])
print("\n=== PACK BERTIN ===")
print(f"DPF+EGR+FLAPS unique bytes={len(bertin)}")
print(f"LAMBDA extra={len(set(packs['LAMBDA']['diffs']) - bertin)}")
print(f"TVA extra={len(set(packs['TVA']['diffs']) - bertin)}")

# checksum note: files named noCHK
print("\nfiles are __noCHK — checksum not corrected")

# CSV all regions
csv_path = out_dir / "DTC_OFF_packs.csv"
rows = []
for k in keys:
    for i, (s, e) in enumerate(packs[k]["regs"], 1):
        rows.append(
            {
                "pack": k,
                "region_i": i,
                "start": f"0x{s:06X}",
                "end": f"0x{e-1:06X}",
                "size": e - s,
                "ori_hex": ori[s:e].hex(),
                "mod_hex": packs[k]["data"][s:e].hex(),
            }
        )
with csv_path.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(
        f, fieldnames=["pack", "region_i", "start", "end", "size", "ori_hex", "mod_hex"]
    )
    w.writeheader()
    w.writerows(rows)

md_path = out_dir / "DTC_OFF_packs.md"
md_path.write_text("\n".join(lines), encoding="utf-8")
print(f"\nCSV={csv_path} rows={len(rows)}")
print(f"MD={md_path}")

# Merge DPF+EGR+FLAPS onto ORI. Conflict = same offset, different new values.
order = ("DPF", "EGR", "FLAPS")
merged = bytearray(ori)
conflicts = []
applied = {}
for k in order:
    data = packs[k]["data"]
    for i in packs[k]["diffs"]:
        nv = data[i]
        if i in applied and applied[i][1] != nv:
            conflicts.append((i, applied[i], (k, nv)))
        applied[i] = (k, nv)
        merged[i] = nv
print(f"\n=== MERGE DPF+EGR+FLAPS ===")
print(f"offsets={len(applied)} conflicts={len(conflicts)}")
if conflicts[:8]:
    for i, (ka, va), (kb, vb) in conflicts[:8]:
        print(f"  {i:06X} {ka}={va:02X} vs {kb}={vb:02X} ori={ori[i]:02X}")

dest = dtc_dir / "A5_516657_DPF-EGR-FLAPS_noCHK.bin"
dest.write_bytes(merged)
print(f"wrote {dest}")
