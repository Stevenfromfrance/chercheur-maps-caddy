# -*- coding: utf-8 -*-
"""Method 4 automated: RAM/axis inputs before every CALL to an interp hub (Golf 9980).

Static trace of ~80 bytes before each CALL 0x6D to a chosen hub
(default interp_2d @ 0x8004C7A0; lettered hubs via --hub).
Follows MOVH.A/LEA, LEA ABS (D0/A0), ld.hu into d4/d5, and A10 stack slots
that those loads use. Indirect loads without a prior store in lookback are
counted as misses (honest coverage).

Does not flash. Names are reverse-engineered, not OEM IdNames.

Label prefixes (Ghidra fam_*):
  interp_2d     -> fam_...          (legacy, no letter)
  interp_2d_B   -> B_fam_...        (sibling 2d hub @ 0x8004C960)
  map_interp_C  -> C_fam_...
  map_interp_D  -> D_fam_...
  map_interp_E..O -> E_fam_... .. O_fam_...

Examples:
  python scan_interp_families.py
  python scan_interp_families.py --hub map_interp_C
  python scan_interp_families.py --hub interp_2d_B
  python scan_interp_families.py --hub map_interp_F
  # all remaining lettered hubs:
  for %h in (interp_2d_B map_interp_E map_interp_F map_interp_G map_interp_H map_interp_I map_interp_J map_interp_K map_interp_L map_interp_M map_interp_N map_interp_O) do python scan_interp_families.py --hub %h
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS = ROOT.parents[1]
GOLF = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
A2L_JSON = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
    r"\Caddy-CAYE-2013-03L906023PA-2531\A2L"
    r"\Volkswagen_Golf_2008_(VI)_1.6_TDI_CR_105_hp_Siemens_PCR2.1_OBD_NR.json"
)
HORS = ROOT / "golf9980_horsA2L_maps.csv"
ATLAS = ROOT / "atlas_9979_labels.csv"
CALLS_CSV = ROOT / "golf9980_interp_calls.csv"
GHIDRA_SCRIPTS = Path(r"C:\Users\theda\ghidra_scripts")

FLASH80 = 0x80000000
PFLASH0 = 0xA0000000
CAL0, CAL1 = 0x180000, 0x200000
RAM0, RAM1 = 0xD0000000, 0xD0020000
WINDOW = 80
LOOKBACK = 256  # only to resolve [a10+k] stores used inside WINDOW

# Hub registry: name -> addr / output stem / Ghidra label_prefix
# interp_2d keeps legacy filenames (no wipe / backward compat).
# Letter prefixes: B_fam_ (interp_2d_B), C_fam_..O_fam_ (map_interp_*).
HUBS = {
    "interp_2d": {
        "addr": 0x8004C7A0,
        "stem": "golf9980_interp_families",
        "a2l": "golf9980_interp_families_HIGH.a2l",
        "label_prefix": "",
    },
    # Sibling 2d interpolator (not map_interp_*); prefix B_ -> B_fam_
    "interp_2d_B": {
        "addr": 0x8004C960,
        "stem": "golf9980_interp_B_families",
        "a2l": "golf9980_interp_B_HIGH.a2l",
        "label_prefix": "B_",
    },
    "map_interp_C": {
        "addr": 0x8004CCA0,
        "stem": "golf9980_interp_C_families",
        "a2l": "golf9980_interp_C_HIGH.a2l",
        "label_prefix": "C_",
    },
    "map_interp_D": {
        "addr": 0x8004CF80,
        "stem": "golf9980_interp_D_families",
        "a2l": "golf9980_interp_D_HIGH.a2l",
        "label_prefix": "D_",
    },
    "map_interp_E": {
        "addr": 0x8004CD40,
        "stem": "golf9980_interp_E_families",
        "a2l": "golf9980_interp_E_HIGH.a2l",
        "label_prefix": "E_",
    },
    "map_interp_F": {
        "addr": 0x8004DB5C,
        "stem": "golf9980_interp_F_families",
        "a2l": "golf9980_interp_F_HIGH.a2l",
        "label_prefix": "F_",
    },
    "map_interp_G": {
        "addr": 0x8004CF60,
        "stem": "golf9980_interp_G_families",
        "a2l": "golf9980_interp_G_HIGH.a2l",
        "label_prefix": "G_",
    },
    "map_interp_H": {
        "addr": 0x8004E260,
        "stem": "golf9980_interp_H_families",
        "a2l": "golf9980_interp_H_HIGH.a2l",
        "label_prefix": "H_",
    },
    "map_interp_I": {
        "addr": 0x8004BAC0,
        "stem": "golf9980_interp_I_families",
        "a2l": "golf9980_interp_I_HIGH.a2l",
        "label_prefix": "I_",
    },
    "map_interp_J": {
        "addr": 0x8004CF20,
        "stem": "golf9980_interp_J_families",
        "a2l": "golf9980_interp_J_HIGH.a2l",
        "label_prefix": "J_",
    },
    "map_interp_K": {
        "addr": 0x8004C600,
        "stem": "golf9980_interp_K_families",
        "a2l": "golf9980_interp_K_HIGH.a2l",
        "label_prefix": "K_",
    },
    "map_interp_L": {
        "addr": 0x8004E4E8,
        "stem": "golf9980_interp_L_families",
        "a2l": "golf9980_interp_L_HIGH.a2l",
        "label_prefix": "L_",
    },
    "map_interp_M": {
        "addr": 0x8004F46C,
        "stem": "golf9980_interp_M_families",
        "a2l": "golf9980_interp_M_HIGH.a2l",
        "label_prefix": "M_",
    },
    "map_interp_N": {
        "addr": 0x8004CDE0,
        "stem": "golf9980_interp_N_families",
        "a2l": "golf9980_interp_N_HIGH.a2l",
        "label_prefix": "N_",
    },
    "map_interp_O": {
        "addr": 0x8004D760,
        "stem": "golf9980_interp_O_families",
        "a2l": "golf9980_interp_O_HIGH.a2l",
        "label_prefix": "O_",
    },
}
# Hubs already mined (do not re-run unless intentionally refreshing):
MINED_HUBS = ("interp_2d", "map_interp_C", "map_interp_D")
# Remaining hubs to mine in one batch:
REMAINING_HUBS = (
    "interp_2d_B",
    "map_interp_E",
    "map_interp_F",
    "map_interp_G",
    "map_interp_H",
    "map_interp_I",
    "map_interp_J",
    "map_interp_K",
    "map_interp_L",
    "map_interp_M",
    "map_interp_N",
    "map_interp_O",
)
ADDR_TO_HUB = {v["addr"]: k for k, v in HUBS.items()}

# PCR-ish axis names seen in the partial WinOLS JSON (not claimed as OEM MEASUREMENT)
KNOWN_AXIS = {
    "nmot": "nmot",
    "app_r": "APP_r",
    "app": "APP_r",
    "pu_w": "MAP",
    "map": "MAP",
    "int_trq": "int_trq",
    "maf": "MAF",
}


def sx(v: int, bits: int) -> int:
    s = 1 << (bits - 1)
    v &= (1 << bits) - 1
    return v - (1 << bits) if v & s else v


def is32(op: int) -> bool:
    return (op & 1) == 1


def off18(h0: int, h1: int) -> int:
    op1215 = (h0 >> 12) & 0xF
    op1621 = h1 & 0x3F
    op2225 = (h1 >> 6) & 0xF
    op2831 = (h1 >> 12) & 0xF
    return (op1215 << 28) | (op2225 << 10) | (op2831 << 6) | op1621


def off16_bol(h1: int) -> int:
    return sx(h1 & 0xFFFF, 16)


def off10_bo(h1: int) -> int:
    op1621 = h1 & 0x3F
    op2831 = (h1 >> 12) & 0xF
    return sx(op1621 | (op2831 << 6), 10)


def in_pflash(addr: int | None) -> bool:
    if addr is None:
        return False
    off = addr & 0xFFFFFF
    top = addr & 0xFF000000
    return top in (0xA0000000, 0x80000000) and CAL0 <= off < CAL1


def in_ram(addr: int | None) -> bool:
    return addr is not None and RAM0 <= (addr & 0xFFFFFFFF) < RAM1


def to_a0(addr: int) -> int:
    off = addr & 0xFFFFFF
    return PFLASH0 + off


def classify_flash(addr: int) -> str:
    off = addr & 0xFFFFFF
    if 0x1A0000 <= off < 0x1C0000:
        return "axis"
    if 0x1C0000 <= off < CAL1:
        return "grid"
    if CAL0 <= off < 0x1A0000:
        return "grid"
    return "other"


def parse_movha(h0: int, h1: int):
    # bytes: op=0x91, b1, b2, b3 with h0=b0|b1<<8, h1=b2|b3<<8
    b1 = (h0 >> 8) & 0xFF
    b2 = h1 & 0xFF
    b3 = (h1 >> 8) & 0xFF
    if (b1 & 0x0F) != 0:
        return None
    const16 = (b1 >> 4) | (b2 << 4) | ((b3 & 0x0F) << 12)
    ra = b3 >> 4
    return ra, (const16 << 16) & 0xFFFFFFFF


def find_calls(code: bytes, target: int) -> list[int]:
    sites = []
    i = 0
    end = min(len(code), CAL0) - 3
    while i <= end:
        op = code[i]
        if is32(op):
            if op == 0x6D:
                va = FLASH80 + i
                b1, b2, b3 = code[i + 1], code[i + 2], code[i + 3]
                disp = ((b2 | (b3 << 8)) | (sx(b1, 8) << 16)) * 2
                if ((va + disp) & 0xFFFFFFFF) == target:
                    sites.append(va)
            i += 4
        else:
            i += 2
    return sites


def sync_start(code: bytes, site_off: int, win: int) -> int:
    """Even start so linear 16/32 decode lands on the CALL."""
    want = site_off
    lo = max(0, site_off - win)
    for start in range(lo, site_off, 2):
        i = start
        ok = True
        while i < want:
            if i >= len(code):
                ok = False
                break
            i += 4 if is32(code[i]) else 2
            if i > want:
                ok = False
                break
        if ok and i == want:
            return start
    return lo & ~1


class Emu:
    def __init__(self):
        self.A = [None] * 16
        self.Dsrc = [None] * 16  # RAM addr last loaded into Dn
        self.stack = {}  # a10+off -> value
        self.pflash = []  # (addr, when_off)
        self.ramabs = []
        self.d4_how = ""
        self.d5_how = ""

    def setA(self, r: int, val: int | None, pc: int):
        if r < 0 or r > 15:
            return
        self.A[r] = None if val is None else val & 0xFFFFFFFF
        if self.A[r] is None:
            return
        if in_pflash(self.A[r]):
            a0 = to_a0(self.A[r])
            if (a0 & 0xFFFF) != 0:
                self.pflash.append((a0, pc))
        if in_ram(self.A[r]):
            self.ramabs.append((self.A[r], pc))

    def load_hu(self, dest: int, ea: int | None, how: str):
        ram = ea if in_ram(ea) else None
        # If [a15] is still unknown, first input often sits in a14 (lea then reload a15 from stack).
        if ram is None and dest == 4 and in_ram(self.A[14]):
            ram = self.A[14]
            how = how + "+a14"
        if ram is None and dest == 5 and in_ram(self.A[15]):
            ram = self.A[15]
            how = how + "+a15"
        if dest == 4:
            self.Dsrc[4] = ram
            self.d4_how = how if ram else (how + "/indirect")
        if dest == 5:
            self.Dsrc[5] = ram
            self.d5_how = how if ram else (how + "/indirect")

    def step(self, code: bytes, i: int) -> int:
        op = code[i]
        if is32(op):
            h0 = struct.unpack_from("<H", code, i)[0]
            h1 = struct.unpack_from("<H", code, i + 2)[0]
            ra = (h0 >> 8) & 0xF
            rb = (h0 >> 12) & 0xF
            if op == 0x91:
                mh = parse_movha(h0, h1)
                if mh:
                    self.setA(mh[0], mh[1], i)
            elif op == 0xD9:
                off = off16_bol(h1)
                base = self.A[rb]
                self.setA(ra, None if base is None else (base + off) & 0xFFFFFFFF, i)
            elif op == 0xC5 and ((h1 >> 10) & 3) == 0:
                self.setA(ra, off18(h0, h1), i)
            elif op == 0x11:  # addih.a
                const16 = h1
                base = self.A[ra]
                dest = (h1 >> 12) & 0xF
                # addih.a Rc, Ra, const16 — encoding: dest in instr2 high nibble
                # Ghidra: addih.a Ra2831, Ra0811, const1227Z op=0x11
                dest = (h1 >> 12) & 0xF
                # const is bits of h1 low + parts... skip if unsure
            elif op == 0xB9:  # ld.hu BOL
                ea = None if self.A[rb] is None else (self.A[rb] + off16_bol(h1)) & 0xFFFFFFFF
                self.load_hu(ra, ea, "ld.hu_bol")
            elif op == 0x05 and ((h1 >> 10) & 3) == 3:  # ld.hu ABS
                self.load_hu(ra, off18(h0, h1), "ld.hu_abs")
            elif op == 0x09:
                op2225 = (h1 >> 6) & 0xF
                op2627 = (h1 >> 10) & 3
                if op2225 == 3 and op2627 == 2:  # ld.hu [Ab]off10
                    off = off10_bo(h1)
                    ea = None if self.A[rb] is None else (self.A[rb] + off) & 0xFFFFFFFF
                    self.load_hu(ra, ea, "ld.hu_bo")
            elif op == 0x99:  # ld.a BOL
                ea = None if self.A[rb] is None else (self.A[rb] + off16_bol(h1)) & 0xFFFFFFFF
                val = self.stack.get(ea) if ea is not None else None
                if rb == 10 and ea is not None:
                    # treat as a10-relative if A10 unknown: key by offset
                    off = off16_bol(h1)
                    val = self.stack.get(("sp", off), val)
                self.setA(ra, val, i)
            elif op == 0xB5:  # st.a BOL
                ea_off = off16_bol(h1)
                if rb == 10:
                    self.stack[("sp", ea_off)] = self.A[ra]
            return 4
        # 16-bit
        b1 = code[i + 1] if i + 1 < len(code) else 0
        rc = b1 & 0x0F
        rb = (b1 >> 4) & 0x0F
        if op == 0x40:  # mov.aa dest=rc? Ghidra Ra0811=bits8-11=rc, Ra1215=rb
            # byte1 = AF → bits8-11=F dest, bits12-15=A src
            dest = rc
            src = rb
            self.setA(dest, self.A[src], i)
        elif op == 0xD8:  # ld.a a15, [a10+4*const8]
            off = b1 * 4
            val = self.stack.get(("sp", off))
            self.setA(15, val, i)
        elif op == 0xD4:  # ld.a Ac, [Ab]
            if rb == 10:
                val = self.stack.get(("sp", 0))
            else:
                val = self.A[rb]  # wrong: should load memory; if Ab is known RAM ptr, unknown
                val = None
            self.setA(rc, val, i)
        elif op == 0xF8:  # st.a [a10+4*const8], a15
            self.stack[("sp", b1 * 4)] = self.A[15]
        elif op == 0xEC:  # st.a SRO [Ab+off], a15 — off in low nibble of b1
            off = (b1 & 0x0F)
            base_r = (b1 >> 4) & 0xF
            if base_r == 10:
                self.stack[("sp", off)] = self.A[15]
        elif op == 0xB0:  # add.a Ac, const4
            c4 = sx(rb, 4)
            base = self.A[rc]
            self.setA(rc, None if base is None else (base + c4) & 0xFFFFFFFF, i)
        elif op == 0x30:  # add.a dest, src
            a = self.A[rc]
            b = self.A[rb]
            self.setA(rc, None if a is None or b is None else (a + b) & 0xFFFFFFFF, i)
        return 2


def emulate_site(code: bytes, site_va: int) -> Emu:
    site_off = site_va - FLASH80
    start80 = sync_start(code, site_off, WINDOW)
    start_lb = sync_start(code, site_off, LOOKBACK)
    emu = Emu()
    i = start_lb
    while i < site_off:
        i += emu.step(code, i)
    # Restrict listed pflash/ram to those constructed in last 80 bytes
    emu.pflash = [(a, pc) for a, pc in emu.pflash if pc >= start80]
    emu.ramabs = [(a, pc) for a, pc in emu.ramabs if pc >= start80]
    return emu


def pick_grid_axes(emu: Emu) -> tuple[str, str, str]:
    grids, axes = [], []
    seen = set()
    for addr, _pc in emu.pflash:
        if addr in seen:
            continue
        seen.add(addr)
        kind = classify_flash(addr)
        if kind == "grid":
            grids.append(addr)
        elif kind == "axis":
            axes.append(addr)
    grid = ""
    a4 = emu.A[4]
    if a4 and in_pflash(a4) and classify_flash(a4) == "grid" and (to_a0(a4) & 0xFFFF) != 0:
        grid = "0x%08X" % to_a0(a4)
    elif grids:
        grid = "0x%08X" % grids[-1]
    ax = ay = ""
    a5, a6 = emu.A[5], emu.A[6]
    if a5 and in_pflash(a5) and classify_flash(a5) == "axis" and (to_a0(a5) & 0xFFFF) != 0:
        ax = "0x%08X" % to_a0(a5)
    if a6 and in_pflash(a6) and classify_flash(a6) == "axis" and (to_a0(a6) & 0xFFFF) != 0:
        ay = "0x%08X" % to_a0(a6)
    leftover = [a for a in axes if "0x%08X" % a not in (ax, ay)]
    if not ax and leftover:
        ax = "0x%08X" % leftover.pop(0)
    if not ay and leftover:
        ay = "0x%08X" % leftover.pop(0)
    # a12/a13 often hold axes on PCR
    for r in (12, 13, 14, 15, 2, 3):
        v = emu.A[r]
        if v and in_pflash(v) and classify_flash(v) == "axis":
            s = "0x%08X" % to_a0(v)
            if not ax:
                ax = s
            elif not ay and s != ax:
                ay = s
    return grid, ax, ay


def ram_hex(v: int | None) -> str:
    return "" if not v else "0x%08X" % (v & 0xFFFFFFFF)


def parse_a2l_addr(s) -> int | None:
    """WinOLS JSON StartAddr / DataAddr are decimal file offsets."""
    if s is None or s == "":
        return None
    t = str(s).strip()
    try:
        if t.lower().startswith("0x"):
            return int(t, 16) & 0xFFFFFF
        return int(t, 10) & 0xFFFFFF
    except ValueError:
        return None


def load_axis_names() -> dict[int, str]:
    names: dict[int, list[str]] = defaultdict(list)
    if A2L_JSON.exists():
        maps = json.loads(A2L_JSON.read_text(encoding="utf-8")).get("maps") or []
        for am in maps:
            for key in ("AxisX", "AxisY"):
                addr = parse_a2l_addr(am.get(key + ".DataAddr"))
                idn = (am.get(key + ".IdName") or "").strip()
                if addr and idn:
                    names[addr].append(idn)
    if ATLAS.exists():
        with ATLAS.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                addr = int(row["address"], 16) & 0xFFFFFF
                n = row["name"]
                if "_axis" in n.lower() or n.lower() in KNOWN_AXIS:
                    names[addr].append(n)
    out = {}
    for addr, lst in names.items():
        # prefer short IdName
        short = [x for x in lst if x in KNOWN_AXIS or x.lower() in KNOWN_AXIS]
        out[addr] = short[0] if short else lst[0]
    return out


def load_hors() -> dict[int, tuple[int, str]]:
    """call_site -> (grid80, name)"""
    d = {}
    if not HORS.exists():
        return d
    with HORS.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d[int(row["call_site"], 16)] = (int(row["grid80"], 16), row["name"])
    return d


def ident_strings(blob: bytes) -> list[str]:
    hits = []
    for m in re.finditer(rb"[\x20-\x7e]{6,80}", blob[: min(len(blob), 0x40000)]):
        s = m.group().decode("ascii", "ignore")
        if any(k in s.lower() for k in ("pcr", "siemens", "sm2", "caye", "03l9", "golf")):
            hits.append(s)
    # also near end of cal
    tail = blob[0x1F0000:0x200000]
    for m in re.finditer(rb"[\x20-\x7e]{6,80}", tail):
        s = m.group().decode("ascii", "ignore")
        if any(k in s.lower() for k in ("pcr", "siemens", "sm2", "9980", "9979")):
            hits.append(s)
    return hits[:40]


def ghidra_safe(name: str) -> str:
    s = "".join(ch if ch.isalnum() or ch in "._" else "_" for ch in name)
    s = re.sub(r"_+", "_", s).strip("_") or "unnamed"
    if s[0].isdigit():
        s = "m_" + s
    return s[:60]


def axis_label(addr_s: str, axis_names: dict[int, str]) -> str:
    if not addr_s:
        return ""
    off = int(addr_s, 16) & 0xFFFFFF
    raw = axis_names.get(off, "")
    key = raw.lower().replace(".", "_")
    for k, v in KNOWN_AXIS.items():
        if k in key:
            return v
    if raw and len(raw) <= 24 and re.match(r"^[A-Za-z][A-Za-z0-9_]*$", raw):
        return raw
    return ""


def ram_nick(addr: int, vote: str) -> str:
    if vote:
        return vote
    return "RAM_%08X" % (addr & 0xFFFFFFFF)


def monotonic_u16_len(blob: bytes, off: int, cap: int = 32) -> int:
    if off < 0 or off + 4 > len(blob):
        return 0
    n = 0
    prev = None
    for i in range(cap):
        if off + 2 * i + 2 > len(blob):
            break
        v = struct.unpack_from("<H", blob, off + 2 * i)[0]
        if prev is not None and v < prev:
            break
        if prev is not None and v == prev and n >= 4:
            break
        prev = v
        n += 1
    return n if n >= 4 else 0


def resolve_hub(spec: str) -> tuple[str, dict]:
    """Accept hub name (map_interp_C) or address (0x8004CCA0 / 8004CCA0)."""
    s = (spec or "interp_2d").strip()
    if s in HUBS:
        return s, HUBS[s]
    try:
        addr = int(s, 16) if s.lower().startswith("0x") else int(s, 16)
    except ValueError as e:
        raise SystemExit(
            "Unknown --hub %r. Use %s or a hub address."
            % (spec, ", ".join(sorted(HUBS)))
        ) from e
    addr &= 0xFFFFFFFF
    if addr in ADDR_TO_HUB:
        name = ADDR_TO_HUB[addr]
        return name, HUBS[name]
    # Unknown address: invent stem from hex so we never wipe interp_2d outputs
    stem = "golf9980_hub_%08X_families" % addr
    cfg = {
        "addr": addr,
        "stem": stem,
        "a2l": "golf9980_hub_%08X_HIGH.a2l" % addr,
        "label_prefix": "H%06X_" % (addr & 0xFFFFFF),
    }
    return "hub_%08X" % addr, cfg


def load_sites_from_calls_csv(hub_addr: int, hub_name: str) -> list[int] | None:
    """Prefer call sites listed in golf9980_interp_calls.csv when present."""
    if not CALLS_CSV.exists():
        return None
    sites = []
    with CALLS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tgt = int(row["target"], 16) & 0xFFFFFFFF
            if tgt != (hub_addr & 0xFFFFFFFF):
                continue
            sites.append(int(row["call_site"], 16) & 0xFFFFFFFF)
    if not sites:
        return None
    # de-dupe preserve order
    seen = set()
    out = []
    for s in sites:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Mine interp hub call families (Golf 9980)")
    ap.add_argument(
        "--hub",
        default="interp_2d",
        help="Hub name (interp_2d, interp_2d_B, map_interp_C..O) or address. Default: interp_2d",
    )
    ap.add_argument(
        "--all-remaining",
        action="store_true",
        help="Scan every hub in REMAINING_HUBS (B,E..O). Does not re-run 2d/C/D.",
    )
    ap.add_argument(
        "--bin",
        type=Path,
        default=GOLF,
        help="Full-flash bin path",
    )
    args = ap.parse_args(argv)
    if args.all_remaining:
        for name in REMAINING_HUBS:
            print("=" * 60)
            print("SCAN hub", name)
            print("=" * 60)
            main(["--hub", name, "--bin", str(args.bin)])
        return
    hub_name, hub = resolve_hub(args.hub)
    hub_addr = hub["addr"]
    prefix = hub.get("label_prefix") or ""
    out_csv = ROOT / (hub["stem"] + ".csv")
    out_stats = ROOT / (hub["stem"] + "_stats.txt")
    out_a2l = ROOT / hub["a2l"]

    golf = args.bin.read_bytes()
    code = golf
    csv_sites = load_sites_from_calls_csv(hub_addr, hub_name)
    scanned_sites = find_calls(code, hub_addr)
    if csv_sites is not None:
        sites = csv_sites
        site_source = "calls_csv(%d) + flash_scan(%d)" % (len(csv_sites), len(scanned_sites))
        # Merge any flash-found sites missing from CSV (honest union)
        extra = [s for s in scanned_sites if s not in set(csv_sites)]
        if extra:
            sites = list(csv_sites) + extra
            site_source += " +%d extra_from_scan" % len(extra)
    else:
        sites = scanned_sites
        site_source = "flash_scan_only"
    axis_names = load_axis_names()
    hors = load_hors()
    ident = ident_strings(golf)

    rows = []
    both = 0
    one = 0
    d4n = d5n = 0
    grids_n = 0
    ram_x_votes: dict[int, Counter] = defaultdict(Counter)
    ram_y_votes: dict[int, Counter] = defaultdict(Counter)

    for site in sites:
        emu = emulate_site(code, site)
        grid, ax, ay = pick_grid_axes(emu)
        if site in hors and not grid:
            grid = "0x%08X" % hors[site][0]
        if site in hors:
            g80 = hors[site][0]
            if not grid:
                grid = "0x%08X" % g80
        if grid:
            grids_n += 1
        ram_x = emu.Dsrc[4]
        ram_y = emu.Dsrc[5]
        if ram_x:
            d4n += 1
        if ram_y:
            d5n += 1
        if ram_x and ram_y:
            both += 1
        elif ram_x or ram_y:
            one += 1
        notes_pre = ""
        if ram_x is None and in_ram(emu.A[14]):
            ram_x = emu.A[14]
            notes_pre = "ram_x=a14_at_call"
        if ram_y is None and in_ram(emu.A[15]):
            ram_y = emu.A[15]
            notes_pre = (notes_pre + ";" if notes_pre else "") + "ram_y=a15_at_call"
        rams = []
        seenr = set()
        for a, _ in emu.ramabs:
            if a not in seenr:
                seenr.add(a)
                rams.append(a)
        notes = [notes_pre] if notes_pre else []
        notes.append("hub=" + hub_name)
        if not ram_x and not ram_y and len(rams) == 2:
            ram_x, ram_y = rams[0], rams[1]
            notes.append("ram_pair_from_lea_fallback_not_d4d5")
        elif not ram_x and len(rams) == 1 and ram_y and rams[0] != ram_y:
            ram_x = rams[0]
            notes.append("ram_x_from_lea")
        elif not ram_y and len(rams) == 1 and ram_x and rams[0] != ram_x:
            ram_y = rams[0]
            notes.append("ram_y_from_lea")
        if emu.d4_how:
            notes.append("d4=" + emu.d4_how)
        if emu.d5_how:
            notes.append("d5=" + emu.d5_how)
        if not ram_x or not ram_y:
            notes.append("static_miss_indirect_d4d5")

        lx = axis_label(ax, axis_names)
        ly = axis_label(ay, axis_names)
        if ram_x and lx:
            ram_x_votes[ram_x][lx] += 1
        if ram_y and ly:
            ram_y_votes[ram_y][ly] += 1

        rows.append(
            {
                "grid80": grid,
                "call_site": "0x%08X" % site,
                "ram_x": ram_hex(ram_x),
                "ram_y": ram_hex(ram_y),
                "axis_x": ax,
                "axis_y": ay,
                "axis_x_hint": lx,
                "axis_y_hint": ly,
                "hors": hors[site][1] if site in hors else "",
                "notes": ";".join(notes),
                "_rx": ram_x,
                "_ry": ram_y,
            }
        )

    ram_lab: dict[int, str] = {}
    all_ram = set(ram_x_votes) | set(ram_y_votes)
    for addr in all_ram:
        cx, cy = ram_x_votes[addr], ram_y_votes[addr]
        merged = cx + cy
        if merged:
            name, n = merged.most_common(1)[0]
            if n >= 2 or name in ("nmot", "APP_r", "MAP"):
                ram_lab[addr] = name
            else:
                ram_lab[addr] = ""
        else:
            ram_lab[addr] = ""

    fam_key_to_id = {}
    fam_sizes = Counter()

    def fam_key(r):
        if r["axis_x"] and r["axis_y"]:
            return ("ax", r["axis_x"], r["axis_y"])
        if r["ram_x"] and r["ram_y"]:
            a, b = sorted((r["ram_x"], r["ram_y"]))
            return ("ram", a, b)
        if r["ram_x"] or r["ram_y"]:
            return ("ram1", r["ram_x"], r["ram_y"])
        if r["axis_x"] or r["axis_y"]:
            return ("ax1", r["axis_x"], r["axis_y"])
        return ("unk", r["call_site"], "")

    for r in rows:
        fam_sizes[fam_key(r)] += 1
    for i, k in enumerate(sorted(fam_sizes, key=lambda x: (-fam_sizes[x], str(x))), 1):
        fam_key_to_id[k] = i

    out_rows = []
    for r in rows:
        k = fam_key(r)
        fid = "fam_%04d" % fam_key_to_id[k]
        if prefix:
            fid = prefix.rstrip("_") + "_" + fid
        rx, ry = r["_rx"], r["_ry"]
        goff = ""
        if r["grid80"]:
            goff = "%X" % (int(r["grid80"], 16) & 0xFFFFFF)
        if rx and ry:
            sug = "lookup_%08X_x_%08X" % (rx & 0xFFFFFFFF, ry & 0xFFFFFFFF)
            if goff:
                sug = "lookup_%08X_x_%08X_%s" % (rx & 0xFFFFFFFF, ry & 0xFFFFFFFF, goff)
        elif r["axis_x"] or r["axis_y"]:
            sug = "lookup_ax_%s_%s_%s" % (
                ghidra_safe(r.get("axis_x_hint") or "X"),
                ghidra_safe(r.get("axis_y_hint") or "Y"),
                goff or r["call_site"][-6:],
            )
        else:
            sug = "lookup_unresolved_%s" % r["call_site"][-6:]
        if prefix:
            sug = prefix + sug
        sug = ghidra_safe(sug)
        slx = ("%08X" % (rx & 0xFFFFFFFF)) if rx else "unkX"
        sly = ("%08X" % (ry & 0xFFFFFFFF)) if ry else "unkY"
        fam_lbl = ghidra_safe(
            "%sfam_%s_%s_%s" % (prefix, slx, sly, goff or r["call_site"][-6:])
        )
        note = r["notes"]
        if r["hors"]:
            note = (note + ";" if note else "") + "hors=" + r["hors"]
        if r.get("axis_x_hint") or r.get("axis_y_hint"):
            note = (note + ";" if note else "") + "axis_hints=%s/%s" % (
                r.get("axis_x_hint") or "",
                r.get("axis_y_hint") or "",
            )
        note += ";RE_not_OEM"
        out_rows.append(
            {
                "grid80": r["grid80"],
                "call_site": r["call_site"],
                "ram_x": r["ram_x"],
                "ram_y": r["ram_y"],
                "axis_x": r["axis_x"],
                "axis_y": r["axis_y"],
                "family_id": fid,
                "suggested_name": sug,
                "fam_label": fam_lbl,
                "cluster_n": fam_sizes[k],
                "notes": note.replace(",", ";"),
            }
        )

    fields = [
        "grid80",
        "call_site",
        "ram_x",
        "ram_y",
        "axis_x",
        "axis_y",
        "family_id",
        "suggested_name",
        "fam_label",
        "cluster_n",
        "notes",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    n = len(sites)
    both_after = sum(1 for r in out_rows if r["ram_x"] and r["ram_y"])
    uniq_x = sorted({r["ram_x"] for r in out_rows if r["ram_x"]})
    uniq_y = sorted({r["ram_y"] for r in out_rows if r["ram_y"]})
    biggest = fam_sizes.most_common(15)
    n_fam = len(fam_sizes)

    def show_fam(k, sz):
        want = "fam_%04d" % fam_key_to_id[k]
        s = next(
            r
            for r in out_rows
            if r["family_id"] == want or r["family_id"].endswith("_" + want)
        )
        return "%s n=%d  ram %s / %s  ax %s / %s  e.g. %s %s" % (
            s["family_id"],
            sz,
            s["ram_x"] or "-",
            s["ram_y"] or "-",
            s["axis_x"] or "-",
            s["axis_y"] or "-",
            s["call_site"],
            s["suggested_name"],
        )

    lines = [
        "Golf 9980 %s family scan (method 4, static)" % hub_name,
        "%s @ 0x%08X  CALL sites=%d  (%s)" % (hub_name, hub_addr, n, site_source),
        "window=%d bytes before call; lookback=%d only to fill [a10+k] slots" % (WINDOW, LOOKBACK),
        "",
        "Families: %d" % n_fam,
        "Grids labeled (potential): %d/%d (%.1f%%)"
        % (grids_n, n, 100.0 * grids_n / n if n else 0),
        "COVERAGE (d4 AND d5 RAM resolved, no lea-fallback): %d/%d = %.1f%%"
        % (both, n, 100.0 * both / n if n else 0),
        "d4 RAM found: %d/%d (%.1f%%)  d5: %d/%d (%.1f%%)  exactly one: %d"
        % (d4n, n, 100.0 * d4n / n if n else 0, d5n, n, 100.0 * d5n / n if n else 0, one),
        "After lea-fallback, rows with both ram_x and ram_y: %d/%d (%.1f%%)"
        % (both_after, n, 100.0 * both_after / n if n else 0),
        "Honesty: ld.a a15,[a10+k] / ld.hu d4,[a15] misses when the pointer was stored outside lookback.",
        "",
        "Unique RAM as X: %d" % len(uniq_x),
        "Unique RAM as Y: %d" % len(uniq_y),
        "RAM labels (voted from A2L axis IdNames co-occurring; NOT OEM MEASUREMENT):",
    ]
    for addr in sorted(set(ram_lab) | {int(x, 16) for x in uniq_x} | {int(y, 16) for y in uniq_y}):
        lab = ram_lab.get(addr, "")
        nx = sum(1 for r in out_rows if r["ram_x"] == "0x%08X" % addr)
        ny = sum(1 for r in out_rows if r["ram_y"] == "0x%08X" % addr)
        lines.append("  0x%08X  asX=%d asY=%d  %s" % (addr, nx, ny, lab or "RAM_D000xxxx"))
    lines += ["", "Biggest families:"]
    for k, sz in biggest:
        lines.append("  " + show_fam(k, sz))
    lines += ["", "Ident-ish strings (firmware, not map names):"]
    lines += ["  " + s for s in ident[:20]]
    lines += [
        "",
        "Wrote " + str(out_csv),
        "Wrote " + str(out_stats),
        "Wrote " + str(out_a2l),
        "Ghidra: NameInterpFamilies.py processes ALL golf9980_interp*_families.csv next to the script.",
        "Secondary labels fam_* / B_fam_* .. O_fam_* do not delete map_horsA2L_*.",
        "Public A2L: families + AXIS_PTS from flash, not OEM CHARACTERISTIC names.",
    ]
    out_stats.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # HIGH-cluster A2L: both axes+grid for 2d; lettered hubs accept grid+one axis and n>=2
    # (lettered families are more fragmented than interp_2d — n>=4 is almost empty)
    if prefix:
        high = [
            r
            for r in out_rows
            if int(r["cluster_n"]) >= 2
            and r["grid80"]
            and (r["axis_x"] or r["axis_y"])
        ]
    else:
        high = [
            r
            for r in out_rows
            if int(r["cluster_n"]) >= 4 and r["grid80"] and r["axis_x"] and r["axis_y"]
        ]
    seen_char = set()
    seen_ax = set()
    a2l = [
        "ASAP2_VERSION 1 60",
        "/begin PROJECT PCR21_9980_RE \"Reverse-engineered stub - NOT OEM A2L\"",
        "/begin MODULE PCR21_SM2G0P_9980 \"Golf 03L997558A 9980; names from %s families\""
        % hub_name,
        "/* Generated by scan_interp_families.py --hub %s. Do not treat IdNames as Siemens. */"
        % hub_name,
        "/* HIGH clusters only (n>=4). */",
    ]
    for r in high:
        ax_s = r["axis_x"] or r["axis_y"]
        ay_s = r["axis_y"] if r["axis_x"] else ""
        if not r["axis_x"] and r["axis_y"]:
            ax_s, ay_s = r["axis_y"], ""
        key = (r["grid80"], r["axis_x"], r["axis_y"])
        if key in seen_char:
            continue
        seen_char.add(key)
        g = int(r["grid80"], 16) & 0xFFFFFF
        name = r["suggested_name"][:40]
        if r["axis_x"] and r["axis_y"]:
            ax = int(r["axis_x"], 16) & 0xFFFFFF
            ay = int(r["axis_y"], 16) & 0xFFFFFF
            nx = monotonic_u16_len(golf, ax)
            ny = monotonic_u16_len(golf, ay)
            xname = "AX_%X" % ax
            yname = "AY_%X" % ay
            if ax not in seen_ax:
                seen_ax.add(ax)
                a2l.append(
                    "/begin AXIS_PTS %s \"RE axis (code ptr, not OEM AXIS_PTS)\" 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0 %d"
                    % (xname, ax, max(nx, 4))
                )
                a2l.append("  FORMAT \"%%5.0\"")
                a2l.append("/end AXIS_PTS")
            if ay not in seen_ax:
                seen_ax.add(ay)
                a2l.append(
                    "/begin AXIS_PTS %s \"RE axis (code ptr, not OEM AXIS_PTS)\" 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0 %d"
                    % (yname, ay, max(ny, 4))
                )
                a2l.append("  FORMAT \"%%5.0\"")
                a2l.append("/end AXIS_PTS")
            a2l.append(
                "/begin CHARACTERISTIC %s \"RE lookup family %s n=%s\" MAP 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0"
                % (name, r["family_id"], r["cluster_n"], g)
            )
            a2l.append("  FORMAT \"%%5.0\"")
            a2l.append(
                "  /begin AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY NO_COMPU_METHOD %d"
                % max(nx, 4)
            )
            a2l.append("    AXIS_PTS_REF %s" % xname)
            a2l.append("  /end AXIS_DESCR")
            a2l.append(
                "  /begin AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY NO_COMPU_METHOD %d"
                % max(ny, 4)
            )
            a2l.append("    AXIS_PTS_REF %s" % yname)
            a2l.append("  /end AXIS_DESCR")
            a2l.append("/end CHARACTERISTIC")
        else:
            # Curve-like (one axis) — common for map_interp_C callers
            ax = int(ax_s, 16) & 0xFFFFFF
            nx = monotonic_u16_len(golf, ax)
            xname = "AX_%X" % ax
            if ax not in seen_ax:
                seen_ax.add(ax)
                a2l.append(
                    "/begin AXIS_PTS %s \"RE axis (code ptr, not OEM AXIS_PTS)\" 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0 %d"
                    % (xname, ax, max(nx, 4))
                )
                a2l.append("  FORMAT \"%%5.0\"")
                a2l.append("/end AXIS_PTS")
            a2l.append(
                "/begin CHARACTERISTIC %s \"RE curve family %s n=%s\" CURVE 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0"
                % (name, r["family_id"], r["cluster_n"], g)
            )
            a2l.append("  FORMAT \"%%5.0\"")
            a2l.append(
                "  /begin AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY NO_COMPU_METHOD %d"
                % max(nx, 4)
            )
            a2l.append("    AXIS_PTS_REF %s" % xname)
            a2l.append("  /end AXIS_DESCR")
            a2l.append("/end CHARACTERISTIC")
    a2l += ["/end MODULE", "/end PROJECT"]
    out_a2l.write_text("\n".join(a2l) + "\n", encoding="utf-8")

    if GHIDRA_SCRIPTS.exists():
        (GHIDRA_SCRIPTS / out_csv.name).write_bytes(out_csv.read_bytes())
        (GHIDRA_SCRIPTS / out_stats.name).write_bytes(out_stats.read_bytes())
        (GHIDRA_SCRIPTS / out_a2l.name).write_bytes(out_a2l.read_bytes())
        for py_name in ("NameInterpFamilies.py", "NameInterpRams.py"):
            py_src = ROOT / py_name
            if py_src.exists():
                (GHIDRA_SCRIPTS / py_name).write_bytes(py_src.read_bytes())

    print("\n".join(lines[:60]))
    print("...")
    print("hub", hub_name, "sites", n, "families", n_fam, "grids", grids_n)
    print("csv", out_csv)
    print("high a2l chars", len(seen_char), out_a2l)


if __name__ == "__main__":
    main()
