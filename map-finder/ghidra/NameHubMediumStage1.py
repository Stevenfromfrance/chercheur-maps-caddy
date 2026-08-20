# -*- coding: utf-8 -*-
# MEDIUM Stage1 hub hits - COMMENTS ONLY (no rename).
# Pointer often INSIDE a known map - IdName = probable family/zone, not exact origin.
# Does NOT rename. Does NOT touch AccPed labels.
#
# Comment lancer:
# 1. File -> Save
# 2. Window -> Script Manager
# 3. Refresh, filtre: NameHubMediumStage1
# 4. NameHubMediumStage1.py -> Run
#    (CSV golf9980_hub_grids_MEDIUM_stage1.csv doit etre a cote du script)
# 5. Console: medium_comments=... skipped=...
# 6. File -> Save
# 7. Search plate: "PCR21 hub MEDIUM"
#
# @category PCR21
# @runtime Jython

from ghidra.program.model.listing import CodeUnit

FLASH = 0x80000000


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
        (u"\u2014", u"-"),  # em dash
        (u"\u2013", u"-"),  # en dash
        (u"\u2026", u"..."),
        (u"\u00a0", u" "),
    ):
        u = u.replace(a, b)
    return u.encode("ascii", "replace").decode("ascii")


def put_comment(prog, addr_int, text):
    mem = prog.getMemory()
    listing = prog.getListing()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        return False
    old = listing.getComment(CodeUnit.PLATE_COMMENT, addr)
    old_u = _u(old)
    text_u = _ascii(text)
    if old_u and "PCR21 hub MEDIUM" in old_u:
        return False
    # Keep existing HIGH / user plate if present - append on new line
    if old_u and old_u.strip():
        text_u = _ascii(old_u) + "\n" + text_u
    listing.setComment(addr, CodeUnit.PLATE_COMMENT, text_u)
    return True


def run():
    prog = currentProgram
    path = (
        getSourceFile().getParentFile().getAbsolutePath()
        + "\\golf9980_hub_grids_MEDIUM_stage1.csv"
    )
    ncom = 0
    nskip = 0
    seen = {}
    f = open(path, "r")
    try:
        header = f.readline()
        cols = [c.strip() for c in header.strip().split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        need = ("addr", "id_name", "hub")
        for k in need:
            if k not in idx:
                print("CSV missing column:", k)
                return
        for line in f:
            if monitor.isCancelled():
                break
            # notes field may contain commas; we only use early columns
            parts = line.strip().split(",")
            if len(parts) <= max(idx.values()):
                nskip += 1
                continue
            addr_s = parts[idx["addr"]]
            id_name = parts[idx["id_name"]] if "id_name" in idx else ""
            hub = parts[idx["hub"]] if "hub" in idx else ""
            delta = parts[idx["delta"]] if "delta" in idx else ""
            if not addr_s or not id_name:
                nskip += 1
                continue
            goff = int(addr_s, 16) & 0xFFFFFF
            if goff in seen:
                nskip += 1
                continue
            seen[goff] = True
            addr = FLASH + goff
            # ASCII-only: avoid UTF-8 em-dash crash under Jython 2.7
            txt = (
                "PCR21 hub MEDIUM: "
                + _ascii(id_name)
                + " inside map (not start)"
                + " hub="
                + _ascii(hub)
                + " delta="
                + _ascii(delta)
            )
            if put_comment(prog, addr, txt):
                ncom += 1
            else:
                nskip += 1
    finally:
        f.close()
    print(
        "PCR21 hub MEDIUM Stage1: medium_comments=%d skipped=%d unique_addrs=%d"
        % (ncom, nskip, len(seen))
    )
    print("Search plate comment: PCR21 hub MEDIUM")


run()
