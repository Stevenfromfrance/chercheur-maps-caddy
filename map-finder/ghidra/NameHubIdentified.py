# -*- coding: utf-8 -*-
# Apply HIGH IdNames from hub-grid identification (atlas 9979 / A2L).
# HIGH only. Does NOT overwrite user names or AccPed atlas labels.
# Secondary label + plate comment; RE fam_* labels stay searchable.
#
# Comment lancer:
# 1. File -> Save
# 2. Window -> Script Manager
# 3. Refresh, filtre: NameHubIdentified
# 4. NameHubIdentified.py -> Run
# 5. Console: high_labels=... skipped=...
# 6. File -> Save
# 7. G -> turbo_base3B   (exemple)
#
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit

FLASH = 0x80000000

# Prefixes we may add alongside (RE / horsA2L) — not treated as "user names"
RE_PREFIXES = (
    "fam_",
    "B_fam_",
    "C_fam_",
    "D_fam_",
    "E_fam_",
    "F_fam_",
    "G_fam_",
    "H_fam_",
    "I_fam_",
    "J_fam_",
    "K_fam_",
    "L_fam_",
    "M_fam_",
    "N_fam_",
    "O_fam_",
    "map_horsA2L_",
    "B_lookup_",
    "C_lookup_",
    "D_lookup_",
    "E_lookup_",
    "F_lookup_",
    "G_lookup_",
    "H_lookup_",
    "I_lookup_",
    "J_lookup_",
    "K_lookup_",
    "L_lookup_",
    "M_lookup_",
    "N_lookup_",
    "O_lookup_",
    "lookup_",
)


def is_re_name(name):
    if not name:
        return True
    for p in RE_PREFIXES:
        if name.startswith(p):
            return True
    return False


def is_accped_or_protected(name):
    if not name:
        return False
    n = name.lower()
    if n.startswith("accped"):
        return True
    if "accped" in n:
        return True
    return False


def has_protected_label(st, addr):
    for s in st.getSymbols(addr):
        if is_accped_or_protected(s.getName()):
            return True
    return False


def has_user_non_re(st, addr):
    for s in st.getSymbols(addr):
        name = s.getName()
        if is_accped_or_protected(name):
            continue
        if is_re_name(name):
            continue
        # DAT_ / LAB_ / FUN_ defaults — ignore
        if name.startswith("DAT_") or name.startswith("LAB_") or name.startswith("FUN_"):
            continue
        if name.startswith("unnamed"):
            continue
        return True
    return False


def put_label(prog, addr_int, name):
    mem = prog.getMemory()
    st = prog.getSymbolTable()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        return False
    if has_protected_label(st, addr):
        return False
    if has_user_non_re(st, addr):
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
    if old and "PCR21 hub id:" in old:
        return False
    listing.setComment(addr, CodeUnit.PLATE_COMMENT, text)
    return True


def parse_csv_line(line, idx):
    # Simple CSV split (notes may contain semicolons; commas avoided by writer)
    parts = line.strip().split(",")
    if len(parts) < 7:
        return None
    return parts


def run():
    prog = currentProgram
    path = getSourceFile().getParentFile().getAbsolutePath() + "\\golf9980_hub_grids_identified.csv"
    nlab = 0
    ncom = 0
    nskip = 0
    nprot = 0
    seen_addr = {}
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
            if len(parts) < 7:
                continue
            conf = parts[idx["confidence"]]
            if conf != "high":
                nskip += 1
                continue
            addr_s = parts[idx["addr"]]
            new_name = parts[idx["new_name"]] if "new_name" in idx else ""
            id_name = parts[idx["id_name"]] if "id_name" in idx else ""
            hub = parts[idx["hub"]] if "hub" in idx else ""
            if not new_name:
                new_name = id_name
            if not new_name:
                nskip += 1
                continue
            # AccPed IdNames: never auto-rename (atlas ImportAtlas owns them)
            if is_accped_or_protected(new_name) or is_accped_or_protected(id_name):
                nprot += 1
                continue
            goff = int(addr_s, 16) & 0xFFFFFF
            if goff in seen_addr:
                # Already labeled this cal addr from another hub row
                nskip += 1
                continue
            seen_addr[goff] = True
            addr = FLASH + goff
            st = prog.getSymbolTable()
            a = toAddr(addr)
            if has_protected_label(st, a):
                nprot += 1
                continue
            if put_label(prog, addr, new_name):
                nlab += 1
            txt = "PCR21 hub id: " + new_name + " (" + id_name + ") HIGH hub=" + hub
            if put_comment(prog, addr, txt):
                ncom += 1
            else:
                nskip += 1
    finally:
        f.close()
    print(
        "PCR21 hub identified: high_labels=%d comments=%d protected_skip=%d other_skip=%d"
        % (nlab, ncom, nprot, nskip)
    )
    print("G turbo_base3B  or  search plate comment PCR21 hub id:")


run()
