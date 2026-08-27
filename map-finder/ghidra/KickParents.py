# -*- coding: utf-8 -*-
# Auto "press D" on parent bytes BEFORE Stage1 CALLs + known RAM writers.
# KickFromCallSites only starts at the CALL, so lea/ld.hu/st.h stay as ??.
# This script syncs 16/32-bit decode onto the CALL then disassembles backward.
#
# GUI: File -> Save, Script Manager, filtre KickParents, Run, File -> Save.
# Headless: included in apply_stage1_validated_headless.bat (close GUI first).
#
# @category PCR21
# @runtime Jython

from ghidra.app.cmd.disassemble import DisassembleCommand
from ghidra.program.model.address import AddressSet

FLASH = 0x80000000
PFLASH0 = 0xA0000000
CODE_LO = 0x80020000
CODE_HI = 0x8017FFFF
LOOKBACK = 0x100
AFTER = 0x40

# Extra starts found offline (clutch ram_273C writer, AccPed lea, siblings).
HARD_SEEDS = (
    0x800FB7B4,
    0x800FB7DE,
    0x800FC2EE,
    0x800FC25A,
    0x800FC314,
    0x800CC48E,
    0x800CC4AA,
    0x8008736E,
    0x800F4A38,
    0x800F4AFA,
    0x800F4BA8,
    0x80074EBE,
    0x800FC2C8,
    0x800FB4CC,
)


def _u(s):
    if s is None:
        return ""
    try:
        return str(s)
    except Exception:
        return ""


def to80(raw):
    a = raw & 0xFFFFFFFF
    if a >= PFLASH0:
        return (a - PFLASH0) + FLASH
    if a >= FLASH:
        return a
    return FLASH + a


def parse_hex(s):
    t = _u(s).strip().lower().replace("0x", "")
    if not t:
        return None
    try:
        return int(t, 16)
    except Exception:
        return None


def is32_byte(b):
    return (b & 1) == 1


def collect_call_sites(folder):
    sites = {}
    path = folder + "\\golf9980_stage1_validated.csv"
    try:
        f = open(path, "rb")
    except Exception:
        return []
    try:
        header = f.readline()
        if not header:
            return []
        cols = [c.strip().lower() for c in header.decode("latin-1", "replace").split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        want = []
        for key in ("call_site", "site", "from"):
            if key in idx:
                want.append(idx[key])
        if not want:
            return []
        while True:
            line = f.readline()
            if not line:
                break
            parts = line.decode("latin-1", "replace").strip().split(",")
            for wi in want:
                if wi < len(parts):
                    v = parse_hex(parts[wi])
                    if v is not None:
                        sites[to80(v)] = True
    finally:
        f.close()
    return list(sites.keys())


def collect_seed_file(folder):
    out = []
    path = folder + "\\golf9980_parent_seeds.txt"
    try:
        f = open(path, "r")
    except Exception:
        return out
    try:
        for line in f:
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            token = t.split()[0]
            v = parse_hex(token)
            if v is not None:
                out.append(to80(v))
    finally:
        f.close()
    return out


def sync_start(mem, site, win):
    """Even start so linear 16/32 decode lands on site (the CALL)."""
    want = site
    lo = max(CODE_LO, site - win) & ~1
    start = lo
    while start < want:
        i = start
        ok = True
        while i < want:
            addr = toAddr(i)
            if not mem.contains(addr):
                ok = False
                break
            b = mem.getByte(addr) & 0xFF
            i += 4 if is32_byte(b) else 2
            if i > want:
                ok = False
                break
        if ok and i == want:
            return start
        start += 2
    return lo


def kick_range(prog, mem, start, hi, monitor):
    if start < CODE_LO or start > CODE_HI:
        return False
    if hi <= start:
        hi = start + 4
    hi = min(CODE_HI, hi)
    code_set = AddressSet(toAddr(start), toAddr(hi))
    return DisassembleCommand(toAddr(start), code_set, True).applyTo(prog, monitor)


def run():
    prog = currentProgram
    mem = prog.getMemory()
    folder = getSourceFile().getParentFile().getAbsolutePath()
    calls = collect_call_sites(folder)
    extras = list(HARD_SEEDS) + collect_seed_file(folder)
    print("KickParents: call_sites=%d extra_seeds=%d lookback=0x%X" % (
        len(calls), len(extras), LOOKBACK))

    ok_n = 0
    fail_n = 0
    seen = {}

    for raw in calls:
        if monitor.isCancelled():
            break
        a = to80(raw)
        if a < CODE_LO or a > CODE_HI:
            continue
        start = sync_start(mem, a, LOOKBACK)
        key = (start, a + AFTER)
        if key in seen:
            continue
        seen[key] = True
        if kick_range(prog, mem, start, a + AFTER, monitor):
            ok_n += 1
        else:
            fail_n += 1

    for raw in extras:
        if monitor.isCancelled():
            break
        a = to80(raw)
        if a < CODE_LO or a > CODE_HI:
            continue
        start = a & ~1
        key = (start, a + AFTER)
        if key in seen:
            continue
        seen[key] = True
        if kick_range(prog, mem, start, a + AFTER, monitor):
            ok_n += 1
        else:
            fail_n += 1

    print("KickParents: disasm_ok=%d fail=%d windows=%d" % (ok_n, fail_n, len(seen)))
    print("KickParents: File -> Save  then G -> 800FB7DE or 800FC2EE")


run()
