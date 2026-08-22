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
    """Coerce Java/Jython value to unicode without ascii default-encoding traps."""
    if s is None:
        return u""
    try:
        if isinstance(s, unicode):
            return s
    except Exception:
        pass
    # Prefer latin-1 on byte strings: never fails; keeps 0xe2 as U+00E2 for _ascii
    try:
        if isinstance(s, str):
            return s.decode("latin-1", "replace")
    except Exception:
        pass
    try:
        if hasattr(s, "toString"):
            t = s.toString()
            if isinstance(t, unicode):
                return t
            if isinstance(t, str):
                return t.decode("latin-1", "replace")
    except Exception:
        pass
    try:
        t = str(s)
        if isinstance(t, unicode):
            return t
        return t.decode("latin-1", "replace")
    except Exception:
        return u""


def _ascii(s):
    """ASCII-only Python str for Jython setComment (never call str.encode on UTF-8 bytes)."""
    u = _u(s)
    for a, b in (
        (u"\u2014", u"-"),  # em dash
        (u"\u2013", u"-"),  # en dash
        (u"\u2026", u"..."),
        (u"\u00a0", u" "),
        # UTF-8 punctuation that arrived via latin-1 byte roundtrip
        (u"\u00e2\u0080\u0094", u"-"),
        (u"\u00e2\u0080\u0093", u"-"),
        (u"\u00e2\u0080\u00a6", u"..."),
    ):
        u = u.replace(a, b)
    out = []
    for ch in u:
        o = ord(ch)
        if o < 128:
            out.append(chr(o))
        else:
            out.append("?")
    return "".join(out)


def put_comment(prog, addr_int, text):
    mem = prog.getMemory()
    listing = prog.getListing()
    addr = toAddr(addr_int)
    if mem.getBlock(addr) is None:
        return False
    old_a = _ascii(listing.getComment(CodeUnit.PLATE_COMMENT, addr))
    text_a = _ascii(text)
    if old_a and "PCR21 hub MEDIUM" in old_a:
        return False
    # Coerce BOTH sides before concat (Jython: unicode + non-ascii str crashes)
    if old_a and old_a.strip():
        text_a = old_a + "\n" + text_a
    listing.setComment(addr, CodeUnit.PLATE_COMMENT, text_a)
    return True


def _csv_lines(path):
    """Read CSV as binary then latin-1 so Jython never hits UTF-8 decode errors."""
    f = open(path, "rb")
    try:
        data = f.read()
    finally:
        f.close()
    return data.decode("latin-1", "replace").splitlines()


def run():
    prog = currentProgram
    path = (
        getSourceFile().getParentFile().getAbsolutePath()
        + "\\golf9980_hub_grids_MEDIUM_stage1.csv"
    )
    ncom = 0
    nskip = 0
    seen = {}
    lines = _csv_lines(path)
    if not lines:
        print("CSV empty:", path)
        return
    header = lines[0]
    cols = [c.strip() for c in header.strip().split(",")]
    idx = {}
    for i, c in enumerate(cols):
        idx[c] = i
    need = ("addr", "id_name", "hub")
    for k in need:
        if k not in idx:
            print("CSV missing column:", k)
            return
    for line in lines[1:]:
        if monitor.isCancelled():
            break
        # notes field may contain commas; we only use early columns
        parts = line.strip().split(",")
        if len(parts) <= max(idx.values()):
            nskip += 1
            continue
        addr_s = _ascii(parts[idx["addr"]]).strip()
        id_name = _ascii(parts[idx["id_name"]]) if "id_name" in idx else ""
        hub = _ascii(parts[idx["hub"]]) if "hub" in idx else ""
        delta = _ascii(parts[idx["delta"]]) if "delta" in idx else ""
        if not addr_s or not id_name:
            nskip += 1
            continue
        goff = int(addr_s, 16) & 0xFFFFFF
        if goff in seen:
            nskip += 1
            continue
        seen[goff] = True
        addr = FLASH + goff
        txt = (
            "PCR21 hub MEDIUM: "
            + id_name
            + " inside map (not start)"
            + " hub="
            + hub
            + " delta="
            + delta
        )
        if put_comment(prog, addr, txt):
            ncom += 1
        else:
            nskip += 1
    print(
        "PCR21 hub MEDIUM Stage1: medium_comments=%d skipped=%d unique_addrs=%d"
        % (ncom, nskip, len(seen))
    )
    print("Search plate comment: PCR21 hub MEDIUM")


run()
