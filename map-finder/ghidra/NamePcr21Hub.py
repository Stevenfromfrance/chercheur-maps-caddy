# -*- coding: utf-8 -*-
# Name interpolator hubs, AccPed call sites, CALL xrefs so References works.
# @category PCR21
# @runtime Jython

from ghidra.app.cmd.disassemble import DisassembleCommand
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.program.model.symbol import RefType, SourceType
from ghidra.program.model.address import AddressSet
from ghidra.program.model.listing import CodeUnit

HUBS = {
    0x8004C7A0: "interp_2d",
    0x8004C960: "interp_2d_B",
    0x8004CCA0: "map_interp_C",
    0x8004CF80: "map_interp_D",
    0x8004CD40: "map_interp_E",
    0x8004DB5C: "map_interp_F",
    0x8004CF60: "map_interp_G",
    0x8004E260: "map_interp_H",
    0x8004BAC0: "map_interp_I",
    0x8004CF20: "map_interp_J",
    0x8004C600: "map_interp_K",
    0x8004E4E8: "map_interp_L",
    0x8004F46C: "map_interp_M",
    0x8004CDE0: "map_interp_N",
    0x8004D760: "map_interp_O",
}

SITES = [
    (0x800CC492, "AccPed_load_1CFFC0"),
    (0x800CC4AA, "call_interp_AccPed_1CFFC0"),
    (0x800CC4B2, "AccPed_load_trq4A"),
    (0x800CC4BE, "AccPed_lea_A01CF9C0"),
    (0x800CC4D4, "call_interp_AccPed_trq4A"),
]


def put_label(prog, addr_int, name):
    st = prog.getSymbolTable()
    listing = prog.getListing()
    addr = toAddr(addr_int)
    if prog.getMemory().getBlock(addr) is None:
        return False
    for s in st.getSymbols(addr):
        if s.getName() == name:
            return True
    try:
        st.createLabel(addr, name, SourceType.USER_DEFINED)
        listing.setComment(addr, CodeUnit.EOL_COMMENT, "PCR21: " + name)
        return True
    except:
        return False


def run():
    prog = currentProgram
    mem = prog.getMemory()
    listing = prog.getListing()
    rm = prog.getReferenceManager()

    nlab = 0
    for addr, name in HUBS.items():
        if put_label(prog, addr, name):
            nlab += 1
        ea = toAddr(addr)
        DisassembleCommand(ea, AddressSet(ea, ea.add(0x80)), True).applyTo(prog, monitor)
        CreateFunctionCmd(ea).applyTo(prog)

    for addr, name in SITES:
        if put_label(prog, addr, name):
            nlab += 1

    # Atlas aliases at cached PFLASH 0xA0xxxxxx (code uses A0, dump loaded at 80)
    csv_atlas = getSourceFile().getParentFile().getAbsolutePath() + "\\atlas_9979_labels.csv"
    na0 = 0
    f = open(csv_atlas, "r")
    try:
        f.readline()
        seen = {}
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            a80 = int(parts[0], 16)
            if a80 >= 0xA0000000:
                a80 = (a80 - 0xA0000000) + 0x80000000
            a0 = (a80 - 0x80000000) + 0xA0000000
            name = parts[1] + "_A0"
            if a0 in seen:
                continue
            seen[a0] = 1
            if mem.getBlock(toAddr(a0)) is None:
                continue
            if put_label(prog, a0, name):
                na0 += 1
    finally:
        f.close()

    calls_path = getSourceFile().getParentFile().getAbsolutePath() + "\\golf9980_interp_calls.csv"
    nref = 0
    ndis = 0
    f = open(calls_path, "r")
    try:
        f.readline()
        for line in f:
            if monitor.isCancelled():
                break
            parts = line.strip().split(",")
            if len(parts) < 3:
                continue
            site = int(parts[0], 16) & 0xFFFFFFFF
            target = int(parts[1], 16) & 0xFFFFFFFF
            sa = toAddr(site)
            ta = toAddr(target)
            if mem.getBlock(sa) is None:
                continue
            aset = AddressSet(sa, sa.add(3))
            if DisassembleCommand(sa, aset, True).applyTo(prog, monitor):
                ndis += 1
            rm.addMemoryReference(sa, ta, RefType.UNCONDITIONAL_CALL, SourceType.USER_DEFINED, 0)
            nref += 1
    finally:
        f.close()

    print("PCR21 hub labels=%d  A0 aliases=%d  call xrefs=%d  disasm=%d" % (nlab, na0, nref, ndis))
    print("Then: G interp_2d -> References. AccPed: G call_interp_AccPed_trq4A")


run()
