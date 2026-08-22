# -*- coding: utf-8 -*-
"""Build Ghidra label files from map-finder atlas JSON.

Outputs:
  - atlas_9979_labels.csv   (address,name,namespace)
  - atlas_9979_labels.py    (Ghidra Jython post-script)

Addresses are file-offset + FLASH_BASE (default 0xA0000000, TC1766 PFLASH cached).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLASH_BASE = 0xA0000000


def sanitize(name: str) -> str:
    out = []
    for ch in name:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    s = "".join(out).strip("_")
    return s or "map"


def collect_symbols(atlas: dict, base: int) -> list[tuple[int, str, str]]:
    symbols = []
    seen = set()
    for m in atlas.get("maps") or []:
        mid = sanitize(str(m.get("id") or "map"))
        addr = int(m["addr"]) + base
        ns = sanitize(str(m.get("folder") or "maps"))
        key = (addr, mid)
        if key not in seen:
            symbols.append((addr, mid, ns))
            seen.add(key)
        for ax_key, suffix in (("axis_x", "X"), ("axis_y", "Y")):
            ax = m.get(ax_key) or {}
            ax_addr = ax.get("addr")
            if not ax_addr:
                continue
            ax_name = f"{mid}_axis{suffix}"
            a = int(ax_addr) + base
            key = (a, ax_name)
            if key not in seen:
                symbols.append((a, ax_name, ns))
                seen.add(key)
    symbols.sort()
    return symbols


def write_csv(path: Path, symbols: list[tuple[int, str, str]]) -> None:
    lines = ["address,name,namespace"]
    for addr, name, ns in symbols:
        lines.append(f"0x{addr:08X},{name},{ns}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_ghidra_script(path: Path, symbols: list[tuple[int, str, str]], base: int) -> None:
    # Jython 2.7 — no f-strings with type hints
    rows = ",\n".join(
        '    (0x%08X, "%s", "%s")' % (addr, name, ns) for addr, name, ns in symbols
    )
    body = """# -*- coding: utf-8 -*-
# Import PCR2.1 atlas labels (generated, do not edit)
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit

FLASH_BASE = 0x%08X
SYMBOLS = [
%s
]

def ensure_ns(symtab, name):
    existing = symtab.getNamespace(name, None)
    if existing is not None:
        return existing
    return symtab.createNameSpace(None, name, SourceType.USER_DEFINED)

def run():
    prog = currentProgram
    mem = prog.getMemory()
    symtab = prog.getSymbolTable()
    listing = prog.getListing()
    created = 0
    skipped = 0
    for addr_int, name, ns_name in SYMBOLS:
        addr = toAddr(addr_int)
        if addr is None or mem.getBlock(addr) is None:
            skipped += 1
            continue
        ns = ensure_ns(symtab, ns_name)
        # Avoid duplicate user labels at same address+name
        already = False
        for s in symtab.getSymbols(addr):
            if s.getName() == name:
                already = True
                break
        if already:
            skipped += 1
            continue
        symtab.createLabel(addr, name, ns, SourceType.USER_DEFINED)
        listing.setComment(addr, CodeUnit.EOL_COMMENT, "PCR21 atlas: " + name)
        created += 1
    print("PCR21 labels: created=%%d skipped=%%d base=0x%%08X" %% (created, skipped, FLASH_BASE))

run()
""" % (base, rows)
    path.write_text(body, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", type=Path, default=ROOT / "atlas" / "9979.json")
    ap.add_argument("--base", type=lambda x: int(x, 0), default=FLASH_BASE)
    ap.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent)
    args = ap.parse_args()
    atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    symbols = collect_symbols(atlas, args.base)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / ("atlas_%s_labels.csv" % atlas.get("soft", "unk"))
    py_path = args.out_dir / ("ImportAtlas_%s.py" % atlas.get("soft", "unk"))
    write_csv(csv_path, symbols)
    write_ghidra_script(py_path, symbols, args.base)
    print("Wrote %s (%d symbols)" % (csv_path, len(symbols)))
    print("Wrote %s" % py_path)


if __name__ == "__main__":
    main()
