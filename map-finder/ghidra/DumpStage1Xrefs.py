# -*- coding: utf-8 -*-
# Dump Ghidra references to Stage1 HIGH maps (Golf 9980).
# Writes golf9980_ghidra_xrefs.txt next to this script.
# @category PCR21
# @runtime Jython

CORE = (
    ("tqlim_cluth_prot", 0x801D0860),
    ("AccPed_trq4A_1CFFC0", 0x801CFFC0),
    ("AccPed_trq4A_1D0640", 0x801D0640),
    ("tqlim_base_pu_4A", 0x801D3190),
    ("smoke_mapA", 0x801D1D18),
    ("turbo_base3B", 0x801C04AC),
    ("rail_base_int_trq2B", 0x801E9368),
    ("duration_inj6A", 0x801CDC84),
    ("vmax3", 0x8018047C),
    ("airctl_hysteresisC", 0x801D0100),
)


def _u(s):
    if s is None:
        return "-"
    try:
        return str(s)
    except Exception:
        return "-"


def run():
    prog = currentProgram
    folder = getSourceFile().getParentFile().getAbsolutePath()
    out_path = folder + "\\golf9980_ghidra_xrefs.txt"
    fm = prog.getFunctionManager()
    rm = prog.getReferenceManager()
    lines = []
    lines.append("Golf 9980 Stage1 Ghidra XREFs")
    lines.append("program=" + _u(prog.getName()))
    lines.append("functions=%d" % fm.getFunctionCount())
    lines.append("")

    total = 0
    for name, addr in CORE:
        a = toAddr(addr)
        refs = rm.getReferencesTo(a)
        n = 0
        block = ["=== %s @ 0x%08X ===" % (name, addr)]
        try:
            it = refs.iterator() if hasattr(refs, "iterator") else refs
        except Exception:
            it = refs
        for ref in it:
            n += 1
            total += 1
            fa = ref.getFromAddress()
            fn = fm.getFunctionContaining(fa)
            fn_name = _u(fn.getName()) if fn is not None else "-"
            rtype = _u(ref.getReferenceType())
            block.append("  from 0x%08X  fn=%s  type=%s" % (fa.getOffset(), fn_name, rtype))
            if n >= 40:
                block.append("  ... truncated")
                break
        block.append("  xref_count=%d" % n)
        block.append("")
        lines.extend(block)
        print("%s xrefs=%d" % (name, n))

    text = "\n".join(lines) + "\n"
    f = open(out_path, "w")
    try:
        f.write(text)
    finally:
        f.close()
    print("DumpStage1Xrefs wrote %s total_listed=%d" % (out_path, total))


run()
