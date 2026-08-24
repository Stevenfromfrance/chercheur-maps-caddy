# -*- coding: utf-8 -*-
"""Find absolute LE pointers in Golf 9980 code that hit atlas map starts."""
from __future__ import print_function
from pathlib import Path
import csv
import struct

ROOT = Path(__file__).resolve().parent
BIN = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
CSV = ROOT / "atlas_9979_labels.csv"
OUT = ROOT / "golf9980_map_ptrs.txt"
CAL0 = 0x180000


def main():
    blob = BIN.read_bytes()
    labels = {}
    with CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            addr = int(row["address"], 16)
            labels.setdefault(addr, []).append(row["name"])

    # unique map starts only (skip duplicate axis aliases later in report)
    hits = {addr: [] for addr in labels}
    code = blob[:CAL0]
    for i in range(0, len(code) - 3, 4):
        val = struct.unpack_from("<I", code, i)[0]
        if val in hits:
            hits[val].append(0xA0000000 + i)

    lines = []
    found = 0
    for addr in sorted(hits):
        ptrs = hits[addr]
        if not ptrs:
            continue
        found += 1
        names = ",".join(labels[addr][:3])
        src = " ".join("0x%08X" % p for p in ptrs[:8])
        extra = "" if len(ptrs) <= 8 else " (+%d)" % (len(ptrs) - 8)
        lines.append("0x%08X  %-40s  n=%d  from %s%s" % (addr, names, len(ptrs), src, extra))

    header = [
        "Golf 9980 full flash — absolute pointers to 9979 atlas maps",
        "code 0x000000-0x180000, maps as 0xA0xxxxxx",
        "maps with >=1 pointer: %d / %d unique addrs" % (found, len(labels)),
        "",
    ]
    OUT.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    print("\n".join(header[:3]))
    for line in lines[:40]:
        print(line)
    if len(lines) > 40:
        print("... %d more in %s" % (len(lines) - 40, OUT))


if __name__ == "__main__":
    main()
