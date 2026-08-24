# -*- coding: utf-8 -*-
"""SOFT/RACE lab patch on the purchased Caddy 9979 fullflash WORK copy.

Does NOT touch:
  map-finder/bins/caddy-9979-TB-fullflash-ORI-DONOTTOUCH.bin
Does NOT flash a car.

    python map-finder/ghidra/patch_caddy_multimap.py
    python map-finder/ghidra/patch_caddy_multimap.py --no-hook   # AccPed copy only

Encodings from Ghidra tricore.sinc (same as PCR TC1796).
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_interp_families import FLASH80, HUBS, emulate_site, find_calls, sx  # noqa: E402

BINS = Path(__file__).resolve().parent.parent / "bins"
ORI = BINS / "caddy-9979-TB-fullflash-ORI-DONOTTOUCH.bin"
WORK = BINS / "caddy-9979-TB-fullflash-WORK.bin"
REPORT = Path(__file__).resolve().parent.parent / "reports" / "map-switch-soft-race.md"

HOOK = 0x800CC4AA
HOOK_LAUNCH = (0x800FC314, 0x800FC25A)  # map_interp_C slices of tqlim_cluth_prot
CAVE = 0x8017FE04
INTERP = HUBS["interp_2d"]["addr"]  # 0x8004C7A0
HUB_C = HUBS["map_interp_C"]["addr"]  # 0x8004CCA0
SOFT_GRID = 0x1CFFC0  # live wish at HOOK (not WinOLS 1CF9C0)
RACE_GRID = 0x1CB064
WINOLS_GRID = 0x1CF9C0
RACE_SPARE_WINOLS = 0x1CB164
SOFT_CLUTCH = 0x1D0860
RACE_CLUTCH = 0x1CB264
CLUTCH_LEN = 128
CLUTCH_DELTA = RACE_CLUTCH - SOFT_CLUTCH  # -0x55FC, fits signed lea off16
MAP_SEL = 0xD0002890  # +0 sel, +1 prev_hi, +2 pumps, +3 kind (0 AccPed / 1 launch)
APP_RAM = 0xD0002198
SPEED_RAM = 0xD0002810
APP_HI = 900  # ~87.9 %  (factor 0.09765625)
APP_LO = 150  # ~14.6 %
SPEED_MAX = 8  # raw; "≈ stopped" (km/h factor not in our A2L)
PUMPS_NEED = 3
TILE = 256
NM_F, NM_OFF = 0.03125, -1024.0
RPM_AXIS = 0x1A612A
RACE_HOLD_RPM = 2800  # telltale: this dump SOFT already holds ~2650; +50 at 2700 is too tight


def u32(h0: int, h1: int) -> bytes:
    return struct.pack("<HH", h0 & 0xFFFF, h1 & 0xFFFF)


def encode_call(pc: int, target: int) -> bytes:
    disp24 = (target - pc) // 2
    return bytes([0x6D, (disp24 >> 16) & 0xFF, disp24 & 0xFF, (disp24 >> 8) & 0xFF])


def encode_j24(pc: int, target: int) -> bytes:
    disp24 = (target - pc) // 2
    return bytes([0x1D, (disp24 >> 16) & 0xFF, disp24 & 0xFF, (disp24 >> 8) & 0xFF])


def encode_abs(op: int, rd: int, addr: int, mode: int) -> bytes:
    op1215 = (addr >> 28) & 0xF
    op1621 = addr & 0x3F
    op2225 = (addr >> 10) & 0xF
    op2831 = (addr >> 6) & 0xF
    h0 = op | (rd << 8) | (op1215 << 12)
    h1 = op1621 | (op2225 << 6) | (mode << 10) | (op2831 << 12)
    return u32(h0, h1)


def ld_hu_abs(rd: int, addr: int) -> bytes:
    return encode_abs(0x05, rd, addr, 3)


def ld_bu_abs(rd: int, addr: int) -> bytes:
    return encode_abs(0x05, rd, addr, 1)


def st_b_abs(addr: int, rd: int) -> bytes:
    return encode_abs(0x25, rd, addr, 0)


def lea_abs(ra: int, addr: int) -> bytes:
    return encode_abs(0xC5, ra, addr, 0)


def mov_imm16(rd: int, imm: int) -> bytes:
    imm &= 0xFFFF
    op1215 = imm & 0xF
    sop1627 = (imm >> 4) & 0xFFF
    h0 = 0x3B | (op1215 << 12)
    h1 = sop1627 | (rd << 12)
    return u32(h0, h1)


def addi(rd_dest: int, rd_src: int, imm: int) -> bytes:
    imm &= 0xFFFF
    op1215 = imm & 0xF
    sop1627 = (imm >> 4) & 0xFFF
    h0 = 0x1B | (rd_src << 8) | (op1215 << 12)
    h1 = sop1627 | (rd_dest << 12)
    return u32(h0, h1)


def xor_imm9(rd_dest: int, rd_src: int, imm: int) -> bytes:
    op1215 = imm & 0xF
    op1620 = (imm >> 4) & 0x1F
    h0 = 0x8F | (rd_src << 8) | (op1215 << 12)
    h1 = op1620 | (0x0C << 5) | (rd_dest << 12)
    return u32(h0, h1)


def br_rr(op: int, da: int, db: int, pc: int, target: int, bit31: int) -> bytes:
    disp15 = (target - pc) // 2
    if disp15 < -16384 or disp15 > 16383:
        raise ValueError("disp15 out of range %d" % disp15)
    h0 = op | (da << 8) | (db << 12)
    h1 = (disp15 & 0x7FFF) | (bit31 << 15)
    return u32(h0, h1)


def br_const4(op: int, da: int, const4: int, pc: int, target: int, bit31: int) -> bytes:
    disp15 = (target - pc) // 2
    if disp15 < -16384 or disp15 > 16383:
        raise ValueError("disp15 out of range %d" % disp15)
    h0 = op | (da << 8) | ((const4 & 0xF) << 12)
    h1 = (disp15 & 0x7FFF) | (bit31 << 15)
    return u32(h0, h1)


def movh_a(ra: int, hi16: int) -> bytes:
    op1215 = hi16 & 0xF
    op1627 = (hi16 >> 4) & 0xFFF
    h0 = 0x91 | (op1215 << 12)
    h1 = op1627 | (ra << 12)
    return u32(h0, h1)


def lea_bol(ra: int, rb: int, off: int) -> bytes:
    h0 = 0xD9 | (ra << 8) | (rb << 12)
    return u32(h0, off & 0xFFFF)


RET = bytes([0x00, 0x90])


class Asm:
    def __init__(self, origin: int):
        self.origin = origin
        self.buf = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str, str]] = []

    def here(self) -> int:
        return self.origin + len(self.buf)

    def label(self, name: str) -> None:
        self.labels[name] = self.here()

    def emit(self, data: bytes) -> None:
        self.buf.extend(data)

    def j24(self, name: str) -> None:
        self.fixups.append((len(self.buf), name, "j24"))
        self.emit(b"\x00\x00\x00\x00")

    def jge_u(self, da: int, db: int, name: str) -> None:
        self.fixups.append((len(self.buf), name, "jgeu"))
        self.emit(bytes([da, db, 0, 0]))  # placeholder overwritten

    def patch_br(self, off: int, kind: str, da: int, db_or_c: int, target: int) -> None:
        pc = self.origin + off
        if kind == "j24":
            self.buf[off : off + 4] = encode_j24(pc, target)
        elif kind == "jgeu":
            self.buf[off : off + 4] = br_rr(0x7F, da, db_or_c, pc, target, 1)
        elif kind == "jltu":
            self.buf[off : off + 4] = br_rr(0x3F, da, db_or_c, pc, target, 1)
        elif kind == "jne0":
            self.buf[off : off + 4] = br_const4(0xDF, da, 0, pc, target, 1)
        elif kind == "jeq0":
            self.buf[off : off + 4] = br_const4(0xDF, da, 0, pc, target, 0)
        elif kind == "jgeu4":
            self.buf[off : off + 4] = br_const4(0xFF, da, db_or_c, pc, target, 1)
        else:
            raise ValueError(kind)

    def br(self, kind: str, da: int, db_or_c: int, name: str) -> None:
        self.fixups.append((len(self.buf), name, kind))
        self.emit(bytes([da & 0xFF, db_or_c & 0xFF, 0, 0]))

    def resolve(self) -> bytes:
        for off, name, kind in self.fixups:
            if name not in self.labels:
                raise KeyError(name)
            da = self.buf[off]
            db = self.buf[off + 1]
            self.patch_br(off, kind, da, db, self.labels[name])
        return bytes(self.buf)


def build_trampoline() -> tuple[bytes, dict[str, int]]:
    a = Asm(CAVE)
    # Two entries so AccPed (interp_2d) and launch (map_interp_C) share the combo.
    a.label("accped_entry")
    a.emit(mov_imm16(0, 0))
    a.emit(st_b_abs(MAP_SEL + 3, 0))
    a.j24("combo")

    a.label("launch_entry")
    a.emit(mov_imm16(0, 1))
    a.emit(st_b_abs(MAP_SEL + 3, 0))
    a.j24("combo")

    a.label("combo")
    # d0 speed, d1 APP, d2 thresh — do not touch d4/d5/a4/a5/a6
    a.emit(ld_hu_abs(0, SPEED_RAM))
    a.emit(ld_hu_abs(1, APP_RAM))
    a.emit(mov_imm16(2, SPEED_MAX))
    a.br("jgeu", 0, 2, "reset")

    a.emit(mov_imm16(2, APP_HI))
    a.br("jltu", 1, 2, "not_high")

    a.emit(ld_bu_abs(0, MAP_SEL + 1))
    a.br("jne0", 0, 0, "select")
    a.emit(mov_imm16(0, 1))
    a.emit(st_b_abs(MAP_SEL + 1, 0))
    a.emit(ld_bu_abs(0, MAP_SEL + 2))
    a.emit(addi(0, 0, 1))
    a.emit(st_b_abs(MAP_SEL + 2, 0))
    a.br("jgeu4", 0, PUMPS_NEED, "toggle")
    a.j24("select")

    a.label("not_high")
    a.emit(mov_imm16(2, APP_LO))
    a.br("jgeu", 1, 2, "select")
    a.emit(mov_imm16(0, 0))
    a.emit(st_b_abs(MAP_SEL + 1, 0))
    a.j24("select")

    a.label("toggle")
    a.emit(ld_bu_abs(0, MAP_SEL))
    a.emit(xor_imm9(0, 0, 1))
    a.emit(st_b_abs(MAP_SEL, 0))
    a.emit(mov_imm16(0, 0))
    a.emit(st_b_abs(MAP_SEL + 2, 0))
    a.emit(st_b_abs(MAP_SEL + 1, 0))
    a.j24("select")

    a.label("reset")
    a.emit(mov_imm16(0, 0))
    a.emit(st_b_abs(MAP_SEL + 2, 0))
    a.emit(st_b_abs(MAP_SEL + 1, 0))

    a.label("select")
    a.emit(ld_bu_abs(0, MAP_SEL))
    a.br("jeq0", 0, 0, "dispatch")  # SOFT: keep caller a4
    a.emit(ld_bu_abs(1, MAP_SEL + 3))
    a.br("jne0", 1, 0, "race_launch")
    a.emit(movh_a(4, 0xA01D))
    a.emit(lea_bol(4, 4, 0xB064))  # A01CB064 AccPed RACE
    a.j24("dispatch")

    a.label("race_launch")
    a.emit(lea_bol(4, 4, CLUTCH_DELTA & 0xFFFF))  # same slice, RACE copy

    a.label("dispatch")
    a.emit(ld_bu_abs(0, MAP_SEL + 3))
    a.br("jne0", 0, 0, "call_C")
    pc = a.here()
    a.emit(encode_call(pc, INTERP))
    a.emit(RET)

    a.label("call_C")
    pc = a.here()
    a.emit(encode_call(pc, HUB_C))
    a.emit(RET)
    code = a.resolve()
    return code, dict(a.labels)


def selfcheck() -> None:
    got = encode_call(HOOK, INTERP)
    if got != bytes.fromhex("6dfc7b01"):
        raise SystemExit("call encode fail %s" % got.hex())
    got = encode_call(HOOK, CAVE)
    if got != bytes.fromhex("6d05ad9c"):
        raise SystemExit("hook call encode fail %s" % got.hex())
    got = lea_abs(14, APP_RAM)
    if got != bytes.fromhex("c5de1862"):
        raise SystemExit("lea APP fail %s" % got.hex())
    got = movh_a(4, 0xA01D)
    if got != bytes.fromhex("91d0014a"):
        raise SystemExit("movh.a fail %s" % got.hex())
    got = lea_bol(4, 4, -64 & 0xFFFF)
    if got != bytes.fromhex("d944c0ff"):
        raise SystemExit("lea bol fail %s" % got.hex())
    race = 0xA01D0000 + (0xB064 - 0x10000)
    if race != 0xA01CB064:
        raise SystemExit("RACE lea math fail %08X" % race)
    if CLUTCH_DELTA != -0x55FC:
        raise SystemExit("clutch delta %X" % (CLUTCH_DELTA & 0xFFFFFFFF))
    if not (-32768 <= CLUTCH_DELTA <= 32767):
        raise SystemExit("clutch delta not signed-16")
    oem_c = encode_call(0x800FC314, HUB_C)
    if oem_c != bytes.fromhex("6dfac684"):
        raise SystemExit("launch C call encode fail %s" % oem_c.hex())


def nm_of(raw: int) -> float:
    return raw * NM_F + NM_OFF


def shift_launch_hold(grid: bytearray, axis: tuple[int, ...]) -> int:
    """Un-zero standstill cells below RACE_HOLD_RPM so hold moves up the RPM axis."""
    vals = list(struct.unpack_from("<64H", bytes(grid)))
    last_nz = 0
    first_zero = None
    for r in range(8):
        if abs(nm_of(vals[r * 8 + 0])) >= 5.0:
            last_nz = r
            continue
        if first_zero is None:
            first_zero = r
        if axis[r] < RACE_HOLD_RPM:
            for c in (0, 1):
                vals[r * 8 + c] = vals[last_nz * 8 + c]
    struct.pack_into("<64H", grid, 0, *vals)
    return -1 if first_zero is None else first_zero


def copy_tiles(buf: bytearray) -> int:
    live = bytes(buf[SOFT_GRID : SOFT_GRID + TILE])
    winols = bytes(buf[WINOLS_GRID : WINOLS_GRID + TILE])
    clutch = bytes(buf[SOFT_CLUTCH : SOFT_CLUTCH + CLUTCH_LEN])
    if live.count(0xFF) == TILE:
        raise SystemExit("live AccPed 1CFFC0 is empty")
    buf[RACE_GRID : RACE_GRID + TILE] = live
    buf[RACE_SPARE_WINOLS : RACE_SPARE_WINOLS + TILE] = winols
    race_clutch = bytearray(clutch)
    axis = struct.unpack_from("<8H", buf, RPM_AXIS)
    shifted = shift_launch_hold(race_clutch, axis)
    buf[RACE_CLUTCH : RACE_CLUTCH + CLUTCH_LEN] = race_clutch
    return shifted


def apply_hook(buf: bytearray, cave: bytes, labels: dict[str, int]) -> None:
    off_cave = CAVE - FLASH80
    buf[off_cave : off_cave + len(cave)] = cave
    buf[HOOK - FLASH80 : HOOK - FLASH80 + 4] = encode_call(HOOK, CAVE)
    launch = labels["launch_entry"]
    for site in HOOK_LAUNCH:
        orig = bytes(buf[site - FLASH80 : site - FLASH80 + 4])
        want_oem = encode_call(site, HUB_C)
        want_hook = encode_call(site, launch)
        if orig not in (want_oem, want_hook):
            raise SystemExit("unexpected launch hook %08X %s" % (site, orig.hex()))
        buf[site - FLASH80 : site - FLASH80 + 4] = want_hook


def write_report_tail(cave_len: int, hooked: bool, shifted: int, launch_va: int) -> None:
    extra = [
        "",
        "## Lab 2026-08-23 — dump acheté (WORK)",
        "",
        "ECU **reste dans le Caddy**. Ce fichier n’est **pas** à flasher dans la voiture.",
        "",
        "| Fichier | Rôle |",
        "|---------|------|",
        "| `map-finder/bins/caddy-9979-TB-fullflash-ORI-DONOTTOUCH.bin` | original dump, on n’y touche plus |",
        "| `map-finder/bins/caddy-9979-TB-fullflash-WORK.bin` | copie de labo patchée |",
        "",
        "**Alignement AccPed :** le call `800CC4AA` lit **`1CFFC0`** (max **234.9 Nm** sur cet ORI), pas WinOLS `1CF9C0` (293.7 Nm). Axes Y différents (`1A8EA6` vs `1A8752`) — on **ne copie pas** `1CF9C0` par-dessus `1CFFC0`. RACE = clone de la grille **live** `1CFFC0` → `1CB064` (identique pour l’instant). Spare WinOLS à `1CB164`.",
        "",
        "Hook %s. Cave **%d** o @ `8017FE04` (AccPed) + launch entry `0x%08X`. Combo 3 coups. `map_sel` @ `D0002890`."
        % ("**écrit**" if hooked else "**pas écrit** (`--no-hook`)", cave_len, launch_va),
        "",
        "**Test visuel (launch, pas AccPed) :** AccPed RACE = copie identique → tu ne sentiras rien à la pédale. Dump `1A612A` : 800 / 1000 / 1500 / 2000 / **2650** / 2700 / **2800** / 3200. SOFT hold col0 = 0 Nm dès **2650**. RACE `1CB264` : 0 Nm seulement à partir de **2800** (2650 et 2700 trop proches pour un test au compte-tours). SOFT `1D0860` inchangé."
        "",
        "Checksum PCR : pas recalculé ici. Un flash (plus tard, autre ECU ou lecture **ton** Caddy) = KESS **CHK**.",
        "",
    ]
    text = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
    marker = "## Lab 2026-08-23 — dump acheté (WORK)"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n"
    REPORT.write_text(text + "\n".join(extra), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-hook", action="store_true")
    args = ap.parse_args()
    selfcheck()
    if not ORI.exists():
        raise SystemExit("missing ORI bin")
    ori = ORI.read_bytes()
    if len(ori) != 0x200000:
        raise SystemExit("bad size")
    # Always rebuild from ORI so trampoline/layout changes don't stack.
    work = bytearray(ori)

    shifted = copy_tiles(work)
    cave, labels = build_trampoline()
    if len(cave) > 500:
        raise SystemExit("cave too big %d" % len(cave))
    if labels["accped_entry"] != CAVE:
        raise SystemExit("accped entry not at cave start")
    if not args.no_hook:
        apply_hook(work, cave, labels)
    else:
        work[(CAVE - FLASH80) : (CAVE - FLASH80) + len(cave)] = cave

    WORK.write_bytes(work)
    write_report_tail(len(cave), not args.no_hook, shifted, labels["launch_entry"])

    hooked = bytes(work[HOOK - FLASH80 : HOOK - FLASH80 + 4])
    print("ORI untouched", ORI.read_bytes() == ori)
    print("shifted clutch row", shifted)
    print("SOFT clutch==ORI", bytes(work[SOFT_CLUTCH : SOFT_CLUTCH + CLUTCH_LEN]) == ori[SOFT_CLUTCH : SOFT_CLUTCH + CLUTCH_LEN])
    print("RACE AccPed==live", bytes(work[RACE_GRID : RACE_GRID + TILE]) == bytes(work[SOFT_GRID : SOFT_GRID + TILE]))
    print("RACE clutch!=SOFT", bytes(work[RACE_CLUTCH : RACE_CLUTCH + CLUTCH_LEN]) != bytes(work[SOFT_CLUTCH : SOFT_CLUTCH + CLUTCH_LEN]))
    print("hook AccPed", hooked.hex(" "))
    print("launch_entry", hex(labels["launch_entry"]))
    for site in HOOK_LAUNCH:
        b = work[site - FLASH80 : site - FLASH80 + 4]
        tgt = (site + (((b[2] | (b[3] << 8)) | (sx(b[1], 8) << 16)) * 2)) & 0xFFFFFFFF
        print("hook launch", hex(site), b.hex(" "), "->", hex(tgt))
    print("cave len", len(cave))
    print("calls to cave start", len(find_calls(bytes(work), CAVE)))
    print("calls to launch_entry", len(find_calls(bytes(work), labels["launch_entry"])))
    print("wrote", WORK)


if __name__ == "__main__":
    main()
