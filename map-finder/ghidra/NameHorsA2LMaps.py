# -*- coding: utf-8 -*-
# Label hors-A2L grids + their interp_2d call sites (Golf 9980).
# Does not replace NamePcr21Hub — run after it. Safe to re-run (skips existing names).
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit


def put_label(prog, addr_int, name):
    mem = prog.getMemory()
    st = prog.getSymbolTable()
    listing = prog.getListing()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        return False
    for s in st.getSymbols(addr):
        if s.getName() == name:
            return False
    try:
        st.createLabel(addr, name, SourceType.USER_DEFINED)
        listing.setComment(addr, CodeUnit.EOL_COMMENT, "PCR21 horsA2L via interp_2d")
        return True
    except:
        return False


def run():
    prog = currentProgram
    path = getSourceFile().getParentFile().getAbsolutePath() + "\\golf9980_horsA2L_maps.csv"
    ngrid = 0
    ncall = 0
    skipped = 0
    f = open(path, "r")
    try:
        f.readline()
        for line in f:
            if monitor.isCancelled():
                break
            parts = line.strip().split(",")
            if len(parts) < 3:
                continue
            grid = int(parts[0], 16) & 0xFFFFFFFF
            site = int(parts[1], 16) & 0xFFFFFFFF
            name = parts[2]
            call_name = "call_" + name
            if put_label(prog, grid, name):
                ngrid += 1
            else:
                skipped += 1
            if put_label(prog, site, call_name):
                ncall += 1
    finally:
        f.close()
    print("PCR21 horsA2L: grids_new=%d calls_new=%d skipped=%d" % (ngrid, ncall, skipped))
    print("G map_horsA2L_1CBE40  or  G map_horsA2L_1C4994")


run()
