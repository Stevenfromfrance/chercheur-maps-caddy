# -*- coding: utf-8 -*-
"""Dump parent context of the 3 validated Stage1 CALLs (offline, no Ghidra)."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import FLASH80, emulate_site, to_a0  # noqa: E402

BIN = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")

SITES = [
    ("clutch / launch-hardcut", 0x800FC314),
    ("clutch sibling (same RAM)", 0x800FC2F6),
    ("AccPed", 0x800CC4AA),
    ("tqlim", 0x8008736E),
]


def u16s(blob: bytes, off: int, n: int = 16) -> list[int]:
    out = []
    for i in range(n):
        p = off + i * 2
        if p + 1 >= len(blob):
            break
        out.append(blob[p] | (blob[p + 1] << 8))
    return out


def main() -> None:
    blob = BIN.read_bytes()
    code = blob
    print("=== parent emu (80/256 bytes before CALL) ===\n")
    for name, va in SITES:
        emu = emulate_site(code, va)
        print(f"## {name}  CALL @ {va:#010x}")
        print(f"  d4 RAM={emu.Dsrc[4]!s:12} how={emu.d4_how}")
        print(f"  d5 RAM={emu.Dsrc[5]!s:12} how={emu.d5_how}")
        a_known = [(i, emu.A[i]) for i in range(16) if emu.A[i] is not None]
        if a_known:
            print("  A-regs: " + ", ".join(f"A{i}={v:#010x}" for i, v in a_known[:8]))
        print("  PFLASH last: " + ", ".join(f"{a:#010x}" for a, _ in emu.pflash[-6:]) or "-")
        print("  RAM last:    " + ", ".join(f"{a:#010x}" for a, _ in emu.ramabs[-6:]) or "-")
        print()

    axes = {
        "clutch ax 1A8BCC": 0x1A8BCC,
        "clutch ay 1A73D0": 0x1A73D0,
        "sib ay 1B1744": 0x1B1744,
        "AccPed ax 1AA8E4": 0x1AA8E4,
        "AccPed ay 1B3900": 0x1B3900,
        "tqlim ax 1B4894": 0x1B4894,
        "tqlim ay 1B2868": 0x1B2868,
    }
    print("=== axis samples (u16 LE, 12 pts) ===\n")
    for lab, off in axes.items():
        vals = u16s(blob, off, 12)
        print(f"{lab:22} {vals}")


if __name__ == "__main__":
    main()
