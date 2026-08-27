# -*- coding: utf-8 -*-
# Bounded disassemble at known interp / Stage1 call sites (Golf 9980).
# Completes KickGolf9980 windows so Ghidra XREFs exist outside 0x80030000-0x80050000.
# Starts LOOKBACK bytes BEFORE each CALL (not at the CALL) so parent lea/ld.hu
# are decoded — otherwise Ghidra leaves ?? and you have to press D by hand.
# @category PCR21
# @runtime Jython

from ghidra.app.cmd.disassemble import DisassembleCommand
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.program.model.address import AddressSet

FLASH = 0x80000000
PFLASH0 = 0xA0000000
CODE_LO = 0x80020000
CODE_HI = 0x8017FFFF
WINDOW = 0x80
LOOKBACK = 0x100


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


def collect_sites(folder):
    sites = {}
    names = (
        "golf9980_stage1_validated.csv",
    )
    for name in names:
        path = folder + "\\" + name
        try:
            f = open(path, "rb")
        except Exception:
            continue
        try:
            header = f.readline()
            if not header:
                continue
            cols = [c.strip().lower() for c in header.decode("latin-1", "replace").split(",")]
            idx = {}
            for i, c in enumerate(cols):
                idx[c] = i
            want = []
            for key in ("call_site", "site", "from"):
                if key in idx:
                    want.append(idx[key])
            if not want:
                continue
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


def run():
    prog = currentProgram
    folder = getSourceFile().getParentFile().getAbsolutePath()
    sites = collect_sites(folder)
    print("KickFromCallSites: unique sites=%d" % len(sites))
    ok_n = 0
    fail_n = 0
    for raw in sites:
        if monitor.isCancelled():
            break
        a = to80(raw)
        if a < CODE_LO or a > CODE_HI:
            continue
        # Start BEFORE the CALL so lea/ld.hu are not left as ?? (D manuel).
        lo = max(CODE_LO, a - LOOKBACK) & ~1
        hi = min(CODE_HI, a + WINDOW)
        code_set = AddressSet(toAddr(lo), toAddr(hi))
        ok = DisassembleCommand(toAddr(lo), code_set, True).applyTo(prog, monitor)
        if not ok:
            ok = DisassembleCommand(toAddr(a), code_set, True).applyTo(prog, monitor)
        try:
            CreateFunctionCmd(toAddr(a)).applyTo(prog)
        except Exception:
            pass
        if ok:
            ok_n += 1
        else:
            fail_n += 1
    fn = prog.getFunctionManager().getFunctionCount()
    print("KickFromCallSites: disasm_ok=%d fail=%d functions=%d" % (ok_n, fail_n, fn))


run()
