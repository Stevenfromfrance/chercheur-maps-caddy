# -*- coding: utf-8 -*-
# Golf 9980 full flash uses uncached PFLASH 0x80000000 (vectors at 0x80031184).
# Atlas CSV is 0xA0xxxxxx — convert to 0x80xxxxxx.
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit

FLASH_CACHED = 0xA0000000
FLASH_UNCACHED = 0x80000000


def ensure_ns(symtab, name):
    existing = symtab.getNamespace(name, None)
    if existing is not None:
        return existing
    return symtab.createNameSpace(None, name, SourceType.USER_DEFINED)


def load_rows():
    parent = getSourceFile().getParentFile().getAbsolutePath()
    path = parent + "\\atlas_9979_labels.csv"
    rows = []
    f = open(path, "r")
    try:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 3:
                continue
            addr = int(parts[0], 16)
            name = parts[1]
            ns = parts[2]
            if addr >= FLASH_CACHED:
                addr = (addr - FLASH_CACHED) + FLASH_UNCACHED
            rows.append((addr, name, ns))
    finally:
        f.close()
    return rows


def run():
    prog = currentProgram
    mem = prog.getMemory()
    listing = prog.getListing()
    symtab = prog.getSymbolTable()
    created = 0
    skipped = 0
    for addr_int, name, ns_name in load_rows():
        addr = toAddr(addr_int)
        if addr is None or mem.getBlock(addr) is None:
            skipped += 1
            continue
        ns = ensure_ns(symtab, ns_name)
        already = False
        for s in symtab.getSymbols(addr):
            if s.getName() == name:
                already = True
                break
        if already:
            skipped += 1
            continue
        try:
            symtab.createLabel(addr, name, ns, SourceType.USER_DEFINED)
            listing.setComment(addr, CodeUnit.EOL_COMMENT, "PCR21 atlas: " + name)
            created += 1
        except:
            skipped += 1
    print("PCR21 Golf9980 labels: created=%d skipped=%d base=0x%08X" % (created, skipped, FLASH_UNCACHED))


run()
