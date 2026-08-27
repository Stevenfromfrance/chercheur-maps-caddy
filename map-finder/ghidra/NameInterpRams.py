# -*- coding: utf-8 -*-
# Label unique interp hub X/Y RAM cells (Golf 9980).
# Placeholders ram_XXXX (last 4 hex digits) — NOT OEM MEASUREMENT names.
# Does NOT overwrite APP_r, nmot, or existing ram_* labels.
#
# Sources (same folder as this script):
#   1. golf9980_interp_rams.csv (if present)
#   2. unique ram_x / ram_y from ALL golf9980_*_families.csv (2d + B..O)
#
# Comment lancer (debutant):
# 1. File -> Save
# 2. Window -> Script Manager  (icone Play)
# 3. Refresh, filtre: NameInterpRams
# 4. NameInterpRams.py -> Run
# 5. Console: labeled=... skipped_existing=...
# 6. File -> Save
# 7. G -> ram_1652   (exemple)
#
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
import os

# Preferred order; any extra golf9980_*_families.csv is also loaded
FAMILY_CSVS = [
    "golf9980_interp_families.csv",
    "golf9980_interp_B_families.csv",
    "golf9980_interp_C_families.csv",
    "golf9980_interp_D_families.csv",
    "golf9980_interp_E_families.csv",
    "golf9980_interp_F_families.csv",
    "golf9980_interp_G_families.csv",
    "golf9980_interp_H_families.csv",
    "golf9980_interp_I_families.csv",
    "golf9980_interp_J_families.csv",
    "golf9980_interp_K_families.csv",
    "golf9980_interp_L_families.csv",
    "golf9980_interp_M_families.csv",
    "golf9980_interp_N_families.csv",
    "golf9980_interp_O_families.csv",
]


def parse_hex(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        a = int(s, 16) & 0xFFFFFFFF
    except:
        return None
    if a == 0:
        return None
    return a


def keep_existing(st, addr):
    for s in st.getSymbols(addr):
        n = s.getName()
        if n == "APP_r" or n == "nmot" or n.startswith("ram_"):
            return True
    return False


def ram_placeholder(addr):
    return "ram_%04X" % (addr & 0xFFFF)


def collect_from_rams_csv(path, out):
    f = open(path, "r")
    try:
        header = f.readline()
        cols = [c.strip() for c in header.strip().split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue
            addr_s = parts[idx["addr"]] if "addr" in idx else parts[0]
            name = parts[idx["label"]] if "label" in idx else parts[1]
            note = parts[idx["note"]] if "note" in idx and len(parts) > idx["note"] else ""
            if note.startswith("KEEP_"):
                continue
            a = parse_hex(addr_s)
            if a is None or not name:
                continue
            if a not in out:
                out[a] = name.strip()
    finally:
        f.close()


def collect_from_families_csv(path, out):
    f = open(path, "r")
    try:
        header = f.readline()
        cols = [c.strip() for c in header.strip().split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        if "ram_x" not in idx:
            return
        for line in f:
            parts = line.strip().split(",")
            if len(parts) <= max(idx["ram_x"], idx.get("ram_y", 0)):
                continue
            for key in ("ram_x", "ram_y"):
                if key not in idx:
                    continue
                a = parse_hex(parts[idx[key]])
                if a is None:
                    continue
                if a not in out:
                    out[a] = ram_placeholder(a)
    finally:
        f.close()


def run():
    prog = currentProgram
    mem = prog.getMemory()
    st = prog.getSymbolTable()
    folder = getSourceFile().getParentFile().getAbsolutePath()
    wanted = {}
    rams_path = folder + "\\golf9980_interp_rams.csv"
    if os.path.isfile(rams_path):
        collect_from_rams_csv(rams_path, wanted)
        print("loaded " + os.path.basename(rams_path))
    for name in FAMILY_CSVS:
        p = folder + "\\" + name
        if os.path.isfile(p):
            before = len(wanted)
            collect_from_families_csv(p, wanted)
            print("loaded %s (+%d RAM)" % (name, len(wanted) - before))
    # Any extra golf9980_*_families.csv not in the preferred list
    try:
        for fn in sorted(os.listdir(folder)):
            low = fn.lower()
            if not low.startswith("golf9980_") or not low.endswith("_families.csv"):
                continue
            if "stats" in low:
                continue
            if fn in FAMILY_CSVS:
                continue
            p = folder + "\\" + fn
            before = len(wanted)
            collect_from_families_csv(p, wanted)
            print("loaded %s (+%d RAM)" % (fn, len(wanted) - before))
    except:
        pass
    labeled = 0
    skipped_existing = 0
    skipped_no_block = 0
    for a in sorted(wanted.keys()):
        if monitor.isCancelled():
            break
        name = wanted[a]
        addr = toAddr(a)
        if mem.getBlock(addr) is None:
            skipped_no_block += 1
            continue
        if keep_existing(st, addr):
            skipped_existing += 1
            continue
        already = False
        for s in st.getSymbols(addr):
            if s.getName() == name:
                already = True
                break
        if already:
            skipped_existing += 1
            continue
        try:
            st.createLabel(addr, name, SourceType.USER_DEFINED)
            labeled += 1
        except:
            skipped_existing += 1
    print("PCR21 interp RAMs: labeled=%d skipped_existing=%d skipped_no_block=%d unique=%d" % (
        labeled, skipped_existing, skipped_no_block, len(wanted)))
    print("ram_XXXX = placeholders, not OEM MEASUREMENT. APP_r / nmot kept.")
    print("G ram_1652")


run()
