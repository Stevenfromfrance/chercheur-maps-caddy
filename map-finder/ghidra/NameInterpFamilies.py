# -*- coding: utf-8 -*-
# Secondary labels + comments for interp hub families (Golf 9980 method 4).
# Does NOT delete map_horsA2L_* (G search still works).
#
# Processes EVERY matching CSV next to this script (order = do not wipe prior labels):
#   golf9980_interp_families.csv        (interp_2d -> fam_)
#   golf9980_interp_B_families.csv      (interp_2d_B -> B_fam_)
#   golf9980_interp_C_families.csv .. O (map_interp_C..O -> C_fam_ .. O_fam_)
# Optional override: set env PCR21_INTERP_FAMILIES_CSV to a single path.
#
# Comment lancer (debutant) — UNE seule fois pour TOUS les hubs:
# 1. File -> Save
# 2. Window -> Script Manager  (icone Play)
# 3. Refresh, filtre: NameInterpFamilies
# 4. NameInterpFamilies.py -> Run
# 5. Console: une ligne par CSV (B/C/D/E...O + 2d)
# 6. File -> Save
# 7. G -> F_fam_... / G_fam_... / call_B_fam_...  ou  G -> map_horsA2L_...
# 8. G -> map_interp_F / interp_2d_B / etc. -> References
#
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit
import os
import re

FLASH = 0x80000000
PFLASH0 = 0xA0000000

# Preferred order (additive; skip_exists if label already present)
DEFAULT_CSVS = [
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


def to80(addr_int):
    """WinOLS / CSV VA -> uncached PFLASH (Ghidra Golf9980 base 0x80000000)."""
    a = addr_int & 0xFFFFFFFF
    if a >= PFLASH0:
        return (a - PFLASH0) + FLASH
    if a >= FLASH:
        return a
    # Bare offset (0x19E6C4 / 0x073FCE) -> 0x8019E6C4 / 0x80073FCE
    return FLASH + a


def to_a0(addr_int):
    """Mirror in cached PFLASH 0xA0xxxxxx (if that block exists)."""
    a80 = to80(addr_int)
    return (a80 - FLASH) + PFLASH0


def flash_candidates(addr_int):
    """Prefer 0x80 (Golf9980 load); also try 0xA0 if mapped."""
    a80 = to80(addr_int)
    a0 = to_a0(addr_int)
    out = [a80]
    if a0 != a80:
        out.append(a0)
    return out


def put_label(prog, addr_int, name, stats=None):
    """Create USER_DEFINED label. Returns True if newly created.
    stats dict keys: ok, skip_exists, err_noblock, err_create (optional).
    """
    mem = prog.getMemory()
    st = prog.getSymbolTable()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        if stats is not None:
            stats["err_noblock"] = stats.get("err_noblock", 0) + 1
        return False
    for s in st.getSymbols(addr):
        if s.getName() == name:
            if stats is not None:
                stats["skip_exists"] = stats.get("skip_exists", 0) + 1
            return False
    try:
        st.createLabel(addr, name, SourceType.USER_DEFINED)
        if stats is not None:
            stats["ok"] = stats.get("ok", 0) + 1
        return True
    except Exception as e:
        if stats is not None:
            stats["err_create"] = stats.get("err_create", 0) + 1
            if stats.get("err_create", 0) <= 5:
                print("  ! createLabel fail @ 0x%08X name=%s: %s" % (addr_int, name, e))
        return False


def put_label_flash(prog, addr_int, name, stats=None):
    """Place label on first valid flash mirror (80 then A0). Returns True if newly created."""
    mem = prog.getMemory()
    st = prog.getSymbolTable()
    saw_block = False
    for a in flash_candidates(addr_int):
        addr = toAddr(a)
        if mem.getBlock(addr) is None:
            continue
        saw_block = True
        for s in st.getSymbols(addr):
            if s.getName() == name:
                if stats is not None:
                    stats["skip_exists"] = stats.get("skip_exists", 0) + 1
                return False
        try:
            st.createLabel(addr, name, SourceType.USER_DEFINED)
            if stats is not None:
                stats["ok"] = stats.get("ok", 0) + 1
            return True
        except Exception as e:
            if stats is not None:
                stats["err_create"] = stats.get("err_create", 0) + 1
                if stats.get("err_create", 0) <= 5:
                    print("  ! createLabel fail @ 0x%08X name=%s: %s" % (a, name, e))
    if not saw_block and stats is not None:
        stats["err_noblock"] = stats.get("err_noblock", 0) + 1
    return False


def put_eol(prog, addr_int, text, marker):
    mem = prog.getMemory()
    listing = prog.getListing()
    for a in flash_candidates(addr_int):
        addr = toAddr(a)
        if mem.getBlock(addr) is None:
            continue
        old = listing.getComment(CodeUnit.EOL_COMMENT, addr)
        if old and marker in old:
            return False
        listing.setComment(addr, CodeUnit.EOL_COMMENT, text)
        return True
    return False


def csv_kind(path):
    """Letter hub tag: 2d | B | C | ... | O"""
    name = os.path.basename(path).lower()
    m = re.search(r"interp_([b-o])_families", name)
    if m:
        return m.group(1).upper()
    if name == "golf9980_interp_families.csv":
        return "2d"
    return "?"


def csv_marker(path):
    kind = csv_kind(path)
    if kind == "2d":
        return "PCR21 fam:"
    if kind == "?":
        return "PCR21 fam:"
    return "PCR21 fam%s:" % kind


def list_csv_paths(folder):
    env = os.environ.get("PCR21_INTERP_FAMILIES_CSV")
    if env:
        return [env]
    paths = []
    for name in DEFAULT_CSVS:
        p = folder + "\\" + name
        if os.path.isfile(p):
            paths.append(p)
    # Also pick any golf9980_*_families.csv not already listed
    try:
        for fn in sorted(os.listdir(folder)):
            low = fn.lower()
            if not low.endswith("_families.csv"):
                continue
            if not low.startswith("golf9980_"):
                continue
            if "stats" in low:
                continue
            full = folder + "\\" + fn
            if full not in paths and os.path.isfile(full):
                paths.append(full)
    except:
        pass
    return paths


def process_csv(prog, path):
    marker = csv_marker(path)
    kind = csv_kind(path)
    nlab = 0
    ncom = 0
    nskip = 0
    nerr = 0
    lab_stats = {}
    f = open(path, "r")
    try:
        header = f.readline()
        cols = [c.strip() for c in header.strip().split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        need = ["call_site", "family_id", "suggested_name"]
        for col in need:
            if col not in idx:
                print("  ! %s missing column %s - abort this CSV" % (
                    os.path.basename(path), col))
                return 0, 0, 0, 1
        for line in f:
            if monitor.isCancelled():
                break
            parts = line.strip().split(",")
            if len(parts) < 8:
                nskip += 1
                continue
            grid_s = parts[idx["grid80"]].strip() if "grid80" in idx else ""
            site_s = parts[idx["call_site"]].strip()
            fam = parts[idx["family_id"]].strip()
            sug = parts[idx["suggested_name"]].strip()
            flab = parts[idx["fam_label"]].strip() if "fam_label" in idx else sug
            # Accept fam_ / B_fam_ .. O_fam_ / anything non-empty (no prefix filter)
            if not flab:
                flab = fam or sug
            if not site_s:
                nskip += 1
                continue
            site = int(site_s, 16) & 0xFFFFFFFF
            txt = marker + " " + fam + " " + sug + " RE_not_OEM"

            if put_eol(prog, site, txt[:200], marker):
                ncom += 1
            else:
                nskip += 1

            # Always label call site as call_<fam_label>
            if flab and put_label(prog, site, "call_" + flab[:50], lab_stats):
                nlab += 1

            if grid_s:
                g_raw = int(grid_s, 16)
                if put_label_flash(prog, g_raw, flab[:60], lab_stats):
                    nlab += 1
                # Alias family_id when different (G -> D_fam_0089 works too)
                if fam and fam != flab and put_label_flash(prog, g_raw, fam[:60], lab_stats):
                    nlab += 1
                put_eol(prog, g_raw, txt[:200], marker)
            else:
                # No grid: still expose exact fam_label at CALL site (not only call_*)
                # Fixes G "No results" for D_fam_unkX_unkY_073FCE etc.
                if flab and put_label(prog, site, flab[:60], lab_stats):
                    nlab += 1
                if fam and fam != flab and put_label(prog, site, fam[:60], lab_stats):
                    nlab += 1

        nerr = lab_stats.get("err_noblock", 0) + lab_stats.get("err_create", 0)
    finally:
        f.close()

    base = os.path.basename(path)
    print("%s csv: %s -> labels=%d comments=%d skipped=%d errors=%d (noblock=%d create=%d exists=%d)" % (
        kind, base, nlab, ncom, nskip, nerr,
        lab_stats.get("err_noblock", 0),
        lab_stats.get("err_create", 0),
        lab_stats.get("skip_exists", 0)))
    return nlab, ncom, nskip, nerr


def run():
    prog = currentProgram
    folder = getSourceFile().getParentFile().getAbsolutePath()
    print("NameInterpFamilies folder: " + folder)
    paths = list_csv_paths(folder)
    if not paths:
        print("No family CSV found in " + folder)
        print("Expected: golf9980_interp*_families.csv (2d + B..O)")
        return

    print("CSVs to process (%d):" % len(paths))
    for p in paths:
        print("  - %s" % os.path.basename(p))

    total_lab = total_com = total_skip = total_err = 0
    for path in paths:
        nlab, ncom, nskip, nerr = process_csv(prog, path)
        total_lab += nlab
        total_com += ncom
        total_skip += nskip
        total_err += nerr
    print("PCR21 interp families TOTAL: labels=%d comments=%d skipped=%d errors=%d" % (
        total_lab, total_com, total_skip, total_err))
    print("map_horsA2L_* kept. G fam_... / B_fam_... / C_fam_... .. O_fam_... or G call_*_fam_...")
    print("One run labels ALL hubs present next to this script. Then File -> Save.")


run()
