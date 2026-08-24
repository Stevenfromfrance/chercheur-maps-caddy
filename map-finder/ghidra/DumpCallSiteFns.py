# -*- coding: utf-8 -*-
# For each Stage1 call_site, print containing function after KickFromCallSites.
# @category PCR21
# @runtime Jython

CORE_PREFIX = (
    "clutch_prot",
    "AccPed",
    "tqlim",
    "smoke",
    "turbo",
    "rail",
    "duration",
    "speed_limiter",
    "egr_control",
)


def _u(s):
    if s is None:
        return "-"
    try:
        return str(s)
    except Exception:
        return "-"


def parse_hex(s):
    t = _u(s).strip().lower().replace("0x", "")
    if not t:
        return None
    try:
        return int(t, 16)
    except Exception:
        return None


def run():
    prog = currentProgram
    folder = getSourceFile().getParentFile().getAbsolutePath()
    path = folder + "\\golf9980_stage1_validated.csv"
    out_path = folder + "\\golf9980_callsite_functions.txt"
    fm = prog.getFunctionManager()
    listing = prog.getListing()
    f = open(path, "rb")
    lines = ["Golf 9980 Stage1 call-site -> function", "functions=%d" % fm.getFunctionCount(), ""]
    try:
        header = f.readline().decode("latin-1", "replace")
        cols = [c.strip() for c in header.split(",")]
        idx = {}
        for i, c in enumerate(cols):
            idx[c] = i
        icat = idx.get("category", 0)
        iid = idx.get("id_name", 1)
        ihub = idx.get("hub", 6)
        icall = idx.get("call_site", 19)
        seen = {}
        while True:
            raw = f.readline()
            if not raw:
                break
            parts = raw.decode("latin-1", "replace").strip().split(",")
            if max(icat, iid, ihub, icall) >= len(parts):
                continue
            cat = parts[icat].strip()
            if not cat.startswith(CORE_PREFIX) and cat not in (
                "AccPed",
                "clutch_prot",
                "tqlim",
                "smoke",
                "turbo",
                "rail",
                "duration",
                "speed_limiter",
                "egr_control",
            ):
                continue
            site = parse_hex(parts[icall])
            if site is None:
                continue
            key = site
            if key in seen:
                continue
            seen[key] = True
            a = toAddr(site)
            fn = fm.getFunctionContaining(a)
            instr = listing.getInstructionAt(a)
            lines.append(
                "%-16s %-28s hub=%-12s site=0x%08X fn=%s instr=%s"
                % (
                    cat[:16],
                    parts[iid][:28],
                    parts[ihub][:12],
                    site,
                    _u(fn.getName()) if fn is not None else "-",
                    _u(instr) if instr is not None else "no-instr",
                )
            )
    finally:
        f.close()
    text = "\n".join(lines) + "\n"
    out = open(out_path, "w")
    try:
        out.write(text)
    finally:
        out.close()
    print("DumpCallSiteFns wrote %s rows=%d" % (out_path, len(seen)))


run()
