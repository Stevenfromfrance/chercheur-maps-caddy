# -*- coding: utf-8 -*-
# Stage1 VALIDATED pack - HIGH rename/label + MEDIUM comments.
# Reads golf9980_stage1_validated.csv next to this script.
# HIGH: safe rename (skip AccPed if already labeled) OR plate "PCR21 Stage1 HIGH".
# MEDIUM: comments only "PCR21 Stage1 MEDIUM" - never rename.
#
# Comment lancer (one-shot):
# 1. File -> Save
# 2. Window -> Script Manager
# 3. Refresh, filtre: NameHubStage1Validated
# 4. NameHubStage1Validated.py -> Run
#    (CSV golf9980_stage1_validated.csv doit etre a cote du script)
# 5. Console: high_labels=... high_comments=... medium_comments=... skipped=...
# 6. File -> Save
# 7. Search plate: "PCR21 Stage1 HIGH" / "PCR21 Stage1 MEDIUM"
#
# @category PCR21
# @runtime Jython

from ghidra.program.model.symbol import SourceType
from ghidra.program.model.listing import CodeUnit

FLASH = 0x80000000

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


def _u(s):
    """Coerce Java/Jython str/unicode/None to unicode (Py2)."""
    if s is None:
        return u""
    if isinstance(s, unicode):
        return s
    try:
        return s.decode("utf-8")
    except Exception:
        try:
            return s.decode("latin-1", "replace")
        except Exception:
            return unicode(s)


def _ascii(s):
    """ASCII-only plate text for Jython (em-dash etc. -> safe)."""
    u = _u(s)
    for a, b in (
        (u"\u2014", u"-"),
        (u"\u2013", u"-"),
        (u"\u2026", u"..."),
        (u"\u00a0", u" "),
    ):
        u = u.replace(a, b)
    return u.encode("ascii", "replace").decode("ascii")


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


def put_comment(prog, addr_int, text, marker):
    mem = prog.getMemory()
    listing = prog.getListing()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        return False
    old = listing.getComment(CodeUnit.PLATE_COMMENT, addr)
    old_u = _u(old)
    text_u = _ascii(text)
    if old_u and marker in old_u:
        return False
    if old_u and old_u.strip():
        text_u = _ascii(old_u) + "\n" + text_u
    listing.setComment(addr, CodeUnit.PLATE_COMMENT, text_u)
    return True


def parse_hex_field(s):
    s = (s or "").strip()
    if not s:
        return None
    if s.lower().startswith("0x"):
        s = s[2:]
    try:
        return int(s, 16)
    except Exception:
        return None


def run():
    prog = currentProgram
    path = (
        getSourceFile().getParentFile().getAbsolutePath()
        + "\\golf9980_stage1_validated.csv"
    )
    nlab = 0
    nhigh_com = 0
    nmed_com = 0
    nskip = 0
    nprot = 0
    seen = {}
    f = open(path, "r")
    try:
        header = f.readline()
        cols = [c.strip() for c in header.strip().split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        need = ("confidence", "id_name", "winols", "ghidra")
        for k in need:
            if k not in idx:
                print("CSV missing column:", k)
                return
        for line in f:
            if monitor.isCancelled():
                break
            # notes may contain commas; use early columns only
            parts = line.strip().split(",")
            if len(parts) <= max(idx[k] for k in need):
                nskip += 1
                continue
            conf = parts[idx["confidence"]].strip().lower()
            id_name = parts[idx["id_name"]].strip() if "id_name" in idx else ""
            category = parts[idx["category"]].strip() if "category" in idx else ""
            hub = parts[idx["hub"]].strip() if "hub" in idx else ""
            delta = parts[idx["delta"]].strip() if "delta" in idx else ""
            winols_s = parts[idx["winols"]].strip() if "winols" in idx else ""
            ghidra_s = parts[idx["ghidra"]].strip() if "ghidra" in idx else ""
            if not id_name or conf not in ("high", "medium"):
                nskip += 1
                continue
            goff = parse_hex_field(winols_s)
            if goff is None:
                gfull = parse_hex_field(ghidra_s)
                if gfull is None:
                    nskip += 1
                    continue
                goff = gfull & 0xFFFFFF
            else:
                goff = goff & 0xFFFFFF
            if goff in seen:
                nskip += 1
                continue
            seen[goff] = True
            addr = FLASH + goff
            st = prog.getSymbolTable()
            a = toAddr(addr)

            if conf == "high":
                # AccPed: never auto-rename if already labeled / atlas-owned
                if is_accped_or_protected(id_name) or has_protected_label(st, a):
                    nprot += 1
                    txt = (
                        "PCR21 Stage1 HIGH: "
                        + _ascii(id_name)
                        + " cat="
                        + _ascii(category)
                        + " hub="
                        + _ascii(hub)
                        + " delta="
                        + _ascii(delta)
                        + " (AccPed protected - comment only)"
                    )
                    if put_comment(prog, addr, txt, "PCR21 Stage1 HIGH"):
                        nhigh_com += 1
                    else:
                        nskip += 1
                    continue
                labeled = put_label(prog, addr, id_name)
                if labeled:
                    nlab += 1
                txt = (
                    "PCR21 Stage1 HIGH: "
                    + _ascii(id_name)
                    + " cat="
                    + _ascii(category)
                    + " hub="
                    + _ascii(hub)
                    + " delta="
                    + _ascii(delta)
                )
                if put_comment(prog, addr, txt, "PCR21 Stage1 HIGH"):
                    nhigh_com += 1
                elif not labeled:
                    nskip += 1
            else:
                # MEDIUM: comments only
                txt = (
                    "PCR21 Stage1 MEDIUM: "
                    + _ascii(id_name)
                    + " cat="
                    + _ascii(category)
                    + " hub="
                    + _ascii(hub)
                    + " delta="
                    + _ascii(delta)
                    + " (inside map - not start)"
                )
                if put_comment(prog, addr, txt, "PCR21 Stage1 MEDIUM"):
                    nmed_com += 1
                else:
                    nskip += 1
    finally:
        f.close()
    print(
        "PCR21 Stage1 validated: high_labels=%d high_comments=%d medium_comments=%d "
        "protected_skip=%d other_skip=%d unique_addrs=%d"
        % (nlab, nhigh_com, nmed_com, nprot, nskip, len(seen))
    )
    print("Search plate: PCR21 Stage1 HIGH  /  PCR21 Stage1 MEDIUM")


run()
