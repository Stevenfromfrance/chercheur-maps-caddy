# -*- coding: utf-8 -*-
# Apply atlas START HIGH labels + Stage1 validated pack in one headless/Script Manager run.
# Reads (next to this script):
#   golf9980_atlas_starts_identified.csv  (preferred for map starts)
#   golf9980_stage1_validated.csv         (hub + atlas merged pack)
#
# HIGH: rename (skip AccPed if already labeled) OR plate "PCR21 Stage1 HIGH"
# MEDIUM: comments only "PCR21 Stage1 MEDIUM" - never rename
#
# Comment lancer GUI:
# 1. File -> Save
# 2. Window -> Script Manager -> Refresh -> filtre NameHubStage1Validated
# 3. Run NameHubStage1Validated.py  (this file also works as NameAtlasStarts alias)
# 4. File -> Save
#
# Headless (close Ghidra GUI first if project locked):
#   map-finder\ghidra\apply_stage1_validated_headless.bat
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
    """Coerce Java/Jython value to unicode without ascii default-encoding traps."""
    if s is None:
        return u""
    try:
        if isinstance(s, unicode):
            return s
    except Exception:
        pass
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
        (u"\u2014", u"-"),
        (u"\u2013", u"-"),
        (u"\u2026", u"..."),
        (u"\u00a0", u" "),
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


def is_re_name(name):
    if not name:
        return True
    name = _ascii(name)
    for p in RE_PREFIXES:
        if name.startswith(p):
            return True
    return False


def is_accped_or_protected(name):
    if not name:
        return False
    n = _ascii(name).lower()
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
        name_a = _ascii(name)
        if name_a.startswith("DAT_") or name_a.startswith("LAB_") or name_a.startswith("FUN_"):
            continue
        if name_a.startswith("unnamed"):
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
    name = _ascii(name)
    for s in st.getSymbols(addr):
        if _ascii(s.getName()) == name:
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
    old_a = _ascii(listing.getComment(CodeUnit.PLATE_COMMENT, addr))
    text_a = _ascii(text)
    marker_a = _ascii(marker)
    if old_a and marker_a in old_a:
        return False
    # Coerce BOTH sides before concat (Jython: unicode + non-ascii str crashes)
    if old_a and old_a.strip():
        text_a = old_a + "\n" + text_a
    listing.setComment(addr, CodeUnit.PLATE_COMMENT, text_a)
    return True


def parse_hex_field(s):
    s = _ascii(s).strip()
    if not s:
        return None
    if s.lower().startswith("0x"):
        s = s[2:]
    try:
        return int(s, 16)
    except Exception:
        return None


def _csv_lines(path):
    """Read CSV as binary then latin-1 so Jython never hits UTF-8 decode errors."""
    f = open(path, "rb")
    try:
        data = f.read()
    finally:
        f.close()
    return data.decode("latin-1", "replace").splitlines()


def apply_csv(prog, path, tag):
    nlab = 0
    nhigh_com = 0
    nmed_com = 0
    nskip = 0
    nprot = 0
    seen = {}
    try:
        lines = _csv_lines(path)
    except Exception as e:
        print("SKIP missing CSV:", path, e)
        return 0, 0, 0, 0, 0, 0
    if not lines:
        print("CSV empty:", path)
        return 0, 0, 0, 0, 0, 0
    header = lines[0]
    cols = [c.strip() for c in header.strip().split(",")]
    idx = {}
    for i, c in enumerate(cols):
        idx[c] = i
    need = ("confidence", "id_name")
    for k in need:
        if k not in idx:
            print("CSV missing column:", k, "in", path)
            return 0, 0, 0, 0, 0, 0
    tag_a = _ascii(tag)
    for line in lines[1:]:
        if monitor.isCancelled():
            break
        parts = line.strip().split(",")
        if len(parts) <= max(idx[k] for k in need):
            nskip += 1
            continue
        conf = _ascii(parts[idx["confidence"]]).strip().lower()
        id_name = _ascii(parts[idx["id_name"]]).strip() if "id_name" in idx else ""
        category = _ascii(parts[idx["category"]]).strip() if "category" in idx else ""
        hub = _ascii(parts[idx["hub"]]).strip() if "hub" in idx else ""
        delta = _ascii(parts[idx["delta"]]).strip() if "delta" in idx else "0x0"
        winols_s = _ascii(parts[idx["winols"]]).strip() if "winols" in idx else ""
        ghidra_s = _ascii(parts[idx["ghidra"]]).strip() if "ghidra" in idx else ""
        addr_s = _ascii(parts[idx["addr"]]).strip() if "addr" in idx else ""
        if not id_name or conf not in ("high", "medium"):
            nskip += 1
            continue
        goff = parse_hex_field(winols_s)
        if goff is None:
            goff = parse_hex_field(addr_s)
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
            if is_accped_or_protected(id_name) or has_protected_label(st, a):
                nprot += 1
                txt = (
                    tag_a
                    + " HIGH: "
                    + id_name
                    + " cat="
                    + category
                    + " hub="
                    + hub
                    + " delta="
                    + delta
                    + " (AccPed protected - comment only)"
                )
                if put_comment(prog, addr, txt, tag_a + " HIGH"):
                    nhigh_com += 1
                else:
                    nskip += 1
                continue
            # Prefer family base name for labels (strip @addr)
            lab = id_name
            at = lab.find("@")
            if at > 0:
                lab = lab[:at]
            labeled = put_label(prog, addr, lab)
            if labeled:
                nlab += 1
            txt = (
                tag_a
                + " HIGH: "
                + id_name
                + " cat="
                + category
                + " hub="
                + hub
                + " delta="
                + delta
            )
            if put_comment(prog, addr, txt, tag_a + " HIGH"):
                nhigh_com += 1
            elif not labeled:
                nskip += 1
        else:
            txt = (
                tag_a
                + " MEDIUM: "
                + id_name
                + " cat="
                + category
                + " hub="
                + hub
                + " delta="
                + delta
                + " (inside map - not start)"
            )
            if put_comment(prog, addr, txt, tag_a + " MEDIUM"):
                nmed_com += 1
            else:
                nskip += 1
    return nlab, nhigh_com, nmed_com, nprot, nskip, len(seen)


def run():
    prog = currentProgram
    base = getSourceFile().getParentFile().getAbsolutePath() + "\\"
    # Prefer merged Stage1 pack (hub + atlas starts). Fallback atlas-only.
    pack = base + "golf9980_stage1_validated.csv"
    atlas = base + "golf9980_atlas_starts_identified.csv"
    path = pack
    try:
        open(pack, "rb").close()
    except Exception:
        path = atlas
    print("PCR21 applying:", path)
    nlab, nhigh_com, nmed_com, nprot, nskip, nuniq = apply_csv(
        prog, path, "PCR21 Stage1"
    )
    print(
        "PCR21 Stage1 validated: high_labels=%d high_comments=%d medium_comments=%d "
        "protected_skip=%d other_skip=%d unique_addrs=%d"
        % (nlab, nhigh_com, nmed_com, nprot, nskip, nuniq)
    )
    print("Search plate: PCR21 Stage1 HIGH  /  PCR21 Stage1 MEDIUM")
    print("Goto examples: tqlim_cluth_prot  rail_base_int_trq2B  duration_inj6A  vmax3")


run()
