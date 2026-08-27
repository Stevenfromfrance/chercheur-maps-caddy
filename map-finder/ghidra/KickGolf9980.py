# -*- coding: utf-8 -*-
# Golf 9980: kick TriCore from reset 0x80031184 (bounded; full Auto Analyze in GUI).
# @category PCR21
# @runtime Jython

from ghidra.app.cmd.disassemble import DisassembleCommand
from ghidra.app.cmd.function import CreateFunctionCmd
from ghidra.program.model.address import AddressSet
from ghidra.program.model.symbol import SourceType

RESET = 0x80031184
TRAP = 0x80023EEE
CAL_START = 0x80180000


def run():
    prog = currentProgram
    listing = prog.getListing()

    try:
        listing.clearCodeUnits(toAddr(CAL_START), toAddr(0x801FFFFF), False)
    except:
        pass

    windows = (
        (RESET, 0x80030000, 0x80050000),
        (TRAP, 0x80023000, 0x80028000),
        (0x80020000, 0x80020000, 0x80021000),
    )
    for entry, lo, hi in windows:
        if monitor.isCancelled():
            break
        code_set = AddressSet(toAddr(lo), toAddr(hi - 1))
        ea = toAddr(entry)
        ok = DisassembleCommand(ea, code_set, True).applyTo(prog, monitor)
        CreateFunctionCmd(ea).applyTo(prog)
        if entry == RESET:
            prog.getSymbolTable().createLabel(ea, "reset", SourceType.USER_DEFINED)
        elif entry == TRAP:
            prog.getSymbolTable().createLabel(ea, "trap_or_init", SourceType.USER_DEFINED)
        print("disassemble 0x%08X in %08X-%08X -> %s" % (entry, lo, hi, ok))

    fn = prog.getFunctionManager().getFunctionCount()
    print("PCR21 Golf9980 functions after kick: %d" % fn)


run()
