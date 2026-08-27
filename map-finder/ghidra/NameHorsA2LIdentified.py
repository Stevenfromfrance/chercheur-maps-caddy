# -*- coding: utf-8 -*-
# Extra labels/comments for hors-A2L grids identified vs A2L 9979.
# Does NOT delete map_horsA2L_* (G search still works).
# High: secondary label (IdName). Medium: comment only. Low: skip.
#
# Comment lancer (debutant):
# 1. File -> Save
# 2. Window -> Script Manager  (ou icone Play)
# 3. Refresh, filtre: NameHorsA2LIdentified
# 4. NameHorsA2LIdentified.py -> Run
# 5. Console: high_labels=... medium_comments=...
# 6. File -> Save
# 7. G -> turbo_base3B   ou   G -> map_horsA2L_1C1B50
#
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit

FLASH = 0x80000000


def put_label(prog, addr_int, name):
    mem = prog.getMemory()
    st = prog.getSymbolTable()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        return False
    for s in st.getSymbols(addr):
        if s.getName() == name:
            return False
    try:
        st.createLabel(addr, name, SourceType.USER_DEFINED)
        return True
    except:
        return False


def put_comment(prog, addr_int, text):
    mem = prog.getMemory()
    listing = prog.getListing()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        return False
    old = listing.getComment(CodeUnit.PLATE_COMMENT, addr)
    if old and "PCR21 id:" in old:
        return False
    listing.setComment(addr, CodeUnit.PLATE_COMMENT, text)
    return True


def run():
    prog = currentProgram
    path = getSourceFile().getParentFile().getAbsolutePath() + "\\golf9980_horsA2L_identified.csv"
    nlab = 0
    ncom = 0
    nskip = 0
    f = open(path, "r")
    try:
        header = f.readline()
        cols = [c.strip() for c in header.strip().split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        for line in f:
            if monitor.isCancelled():
                break
            parts = line.strip().split(",")
            if len(parts) < 6:
                continue
            off_s = parts[idx["offset"]]
            old_name = parts[idx["old_name"]]
            new_name = parts[idx["new_name"]]
            conf = parts[idx["confidence"]]
            a2l_id = parts[idx["a2l_id"]]
            notes = parts[idx["notes"]] if "notes" in idx else ""
            goff = int(off_s, 16) & 0xFFFFFF
            addr = FLASH + goff
            if conf == "high" and new_name and new_name != old_name:
                if put_label(prog, addr, new_name):
                    nlab += 1
                txt = "PCR21 id: " + new_name + " (" + a2l_id + ") HIGH — map_horsA2L_ conserve"
                if put_comment(prog, addr, txt):
                    ncom += 1
            elif conf == "medium" and a2l_id:
                txt = "PCR21 id: dans " + a2l_id + " (medium; pas un rename) | " + notes[:180]
                if put_comment(prog, addr, txt):
                    ncom += 1
                else:
                    nskip += 1
            else:
                nskip += 1
    finally:
        f.close()
    print("PCR21 horsA2L identified: high_labels=%d comments=%d skipped=%d" % (nlab, ncom, nskip))
    print("G turbo_base3B  or  G map_horsA2L_1C1B50")


run()
