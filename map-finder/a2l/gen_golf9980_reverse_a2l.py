# -*- coding: utf-8 -*-
"""Generate reverse-engineered ASAP2 skeleton for PCR2.1 Golf SW 9980.

NOT Continental OEM. Do not flash. Addresses are WinOLS file offsets
(Ghidra 80xxxxxx / A0xxxxxx & 0x1FFFFF).
"""
from __future__ import annotations

import csv
import json
import re
import struct
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
GHIDRA = WS / "map-finder" / "ghidra"
ATLAS = WS / "map-finder" / "atlas" / "9979.json"
GOLF = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
OUT = Path(__file__).resolve().parent / "PCR21_Golf9980_REVERSE.a2l"
COPY = Path(r"C:\Users\theda\ghidra_scripts") / "PCR21_Golf9980_REVERSE.a2l"

RAM_APP = 0xD0002198
RAM_NMOT = 0xD000219A
RAIL_PATH = Path(__file__).resolve().parent / "PCR21_Golf9980_RAIL_PATH.a2l"

# Ghidra-proved rail path (2026-08-23). Names = role in code, not OEM IdNames.
# SIZE unproven unless noted. Do not flash from these labels.
RE_FLASH = [
    {
        "off": 0x18D0F0,
        "name": "rail_sp_curve_18D0F0",
        "kind": "CURVE",
        "ax": 0x1930CC,
        "nx": 16,
        "comment": "RE interp_C@8007D4D4 a4=18D0F0 a5=1930CC X=D0018666 -> D0013872/3870; size 16 placeholder",
    },
    {
        "off": 0x19314A,
        "name": "rail_sp_pt1_gain",
        "kind": "VALUE",
        "comment": "RE u16 d6 of FUN_8004d15c @800BA0C8 (PT1 gain for D0013874); sits in a 82xx table",
    },
    {
        "off": 0x18C154,
        "name": "rail_sp_default",
        "kind": "VALUE",
        "comment": "RE ld.hu default into D0013870 (code uses one u16; value 0 on this dump)",
    },
    {
        "off": 0x197382,
        "name": "e6e8_curve_197382",
        "kind": "VALUE",
        "comment": "RE 1D FUN_8004bdc8 X=D000E6E8 (ratio, NOT rail bar). Size unproven.",
    },
    {
        "off": 0x1973A8,
        "name": "e6e8_interpH_1973A8",
        "kind": "VALUE",
        "comment": "RE map_interp_H after E6E8 store @80091ADC. Size unproven.",
    },
]
RE_RAM = [
    (0xD0013870, "UWORD", "rail_sp_target", "cible avant PT1 (sortie interp_C 18D0F0)"),
    (0xD0013874, "UWORD", "rail_sp_filtered", "apres FUN_8004d15c; copie vers D000B6AE"),
    (0xD000B6AE, "UWORD", "rail_sp_x_1E9DE0", "X du site rail 2d 800F5114"),
    (0xD0018666, "UWORD", "rail_sp_curve_x", "X de 18D0F0 = D000048A / D00019DC"),
    (0xD00019DC, "UWORD", "rail_sp_ratio_den", "denominateur du ratio 8666"),
    (0xD000048A, "ULONG", "rail_sp_ratio_num", "numerateur (ld.w) voisin ram_0414"),
    (0xD000E6E8, "UWORD", "e6e8_ratio", "quotient FUN_80080f4c; PAS consigne bar"),
    (0xD000A946, "UBYTE", "rail_bank_index", "ld.bu mode/index site rail B 800B5A96 - porte multi-map"),
]


def wol(addr: int | str | None) -> int | None:
    if addr is None or addr == "":
        return None
    if isinstance(addr, str):
        addr = int(addr.strip(), 16)
    a = addr & 0xFFFFFFFF
    if 0xD0000000 <= a < 0xD1000000:
        return None
    return a & 0x1FFFFF


def ident(s: str, maxlen: int = 31) -> str:
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    if not s or s[0].isdigit():
        s = "M_" + s
    return s[:maxlen]


def a2l_str(s: str, maxlen: int = 80) -> str:
    """ASCII-safe ASAP2 string literal (no quotes)."""
    s = (s or "").replace('"', "'")
    s = s.replace("\u2014", "-").replace("\u2013", "-")
    s = s.encode("ascii", "replace").decode("ascii")
    s = re.sub(r"[\r\n\t]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:maxlen]


def parse_hex_field(v: str) -> int | None:
    v = (v or "").strip()
    if not v:
        return None
    try:
        return int(v, 16)
    except ValueError:
        return None


def axis_count_header(blob: bytes, off: int | None) -> int | None:
    """PCR-ish: u16 LE count immediately before axis data (often after 0000)."""
    if off is None or off < 4 or off >= len(blob):
        return None
    for delta in (2, 4):
        n = struct.unpack_from("<H", blob, off - delta)[0]
        if 2 <= n <= 64:
            return n
    return None


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def merge_axis(dst: dict, ax, ay) -> None:
    axw, ayw = wol(ax) if ax else None, wol(ay) if ay else None
    if axw and not dst.get("ax"):
        dst["ax"] = axw
    if ayw and not dst.get("ay"):
        dst["ay"] = ayw


def write_rail_path_a2l() -> None:
    """Small readable A2L: only Ghidra-proved rail-path objects."""
    lines = [
        "ASAP2_VERSION 1 60",
        "/*",
        " * PCR2.1 Golf 9980 - RAIL PATH only (RE, not OEM).",
        " * Source: Ghidra chain 2026-08-23. Do not flash from these labels.",
        " * Units unknown. Names = role in code.",
        " */",
        '/begin PROJECT PCR21_Golf9980_RAIL_PATH "RE rail path 9980 - NOT OEM"',
        '/begin MODULE PCR21_SM2G0P_9980_RAIL "rail_sp + e6e8 + bank index"',
        '/begin AXIS_PTS AX_1930CC "RE axis interp_C a5; 16 placeholder" 0x1930CC RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0 16',
        '  FORMAT "%%5.0"',
        "/end AXIS_PTS",
        '/begin CHARACTERISTIC rail_sp_curve_18D0F0 "interp_C a4 -> D0013872/3870; X=D0018666" CURVE 0x18D0F0 RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0',
        '  FORMAT "%%5.0"',
        "  /begin AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY NO_COMPU_METHOD 16",
        "    AXIS_PTS_REF AX_1930CC",
        "  /end AXIS_DESCR",
        "/end CHARACTERISTIC",
        '/begin CHARACTERISTIC rail_sp_pt1_gain "d6 FUN_8004d15c @800BA0C8" VALUE 0x19314A RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0',
        "/end CHARACTERISTIC",
        '/begin CHARACTERISTIC rail_sp_default "ld.hu into D0013870; dump value 0" VALUE 0x18C154 RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0',
        "/end CHARACTERISTIC",
        '/begin CHARACTERISTIC e6e8_curve_197382 "FUN_8004bdc8 X=D000E6E8 not rail bar" VALUE 0x197382 RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0',
        "/end CHARACTERISTIC",
        '/begin CHARACTERISTIC e6e8_interpH_1973A8 "map_interp_H @80091ADC" VALUE 0x1973A8 RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0',
        "/end CHARACTERISTIC",
    ]
    for addr, dtype, name, cmt in RE_RAM:
        lo, hi = (0, 255) if dtype == "UBYTE" else ((0, 4294967295) if dtype == "ULONG" else (0, 65535))
        lines += [
            '/begin MEASUREMENT %s "%s" %s RL_IDENTITY 0 0 %d %d'
            % (ident(name), a2l_str(cmt), dtype, lo, hi),
            "  ECU_ADDRESS 0x%08X" % addr,
            "/end MEASUREMENT",
        ]
    lines += ["/end MODULE", "/end PROJECT", ""]
    RAIL_PATH.write_text("\n".join(lines) + "\n", encoding="ascii", errors="replace")
    print("wrote", RAIL_PATH)


def accped_like(rec: dict) -> bool:
    if rec.get("family") == "fam_0001":
        return True
    if rec.get("ram_x") == RAM_APP and rec.get("ram_y") in (RAM_NMOT, None):
        return rec.get("family") == "fam_0001"
    return False


def main() -> None:
    blob = GOLF.read_bytes() if GOLF.exists() else b""
    maps: dict[int, dict] = {}

    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    for m in atlas.get("maps", []):
        off = int(m["addr_hex"], 16)
        ax = m.get("axis_x") or {}
        ay = m.get("axis_y") or {}
        ax_off = int(ax["addr_hex"], 16) if ax.get("addr_hex") else None
        ay_off = int(ay["addr_hex"], 16) if ay.get("addr_hex") else None
        cols = m.get("cols")
        rows = m.get("rows")
        kind = m.get("type") or ""
        is_curve = kind in ("eEinDim", "CURVE") or (rows in (None, 0, 1) and cols)
        rec = {
            "off": off,
            "name": ident(m["id"] if m.get("id") else "atlas_%06X" % off),
            "comment": "atlas9979 %s / %s (IdName Caddy 9979 — verifier sur 9980)"
            % (m.get("id"), m.get("name", "")),
            "source": "atlas9979",
            "ax": ax_off,
            "ay": ay_off,
            "nx": cols,
            "ny": rows if not is_curve else None,
            "kind": "CURVE" if is_curve and not ay_off else "MAP",
            "folder": m.get("folder") or "",
            "a2l_id": m.get("id"),
            "family": "",
            "ram_x": None,
            "ram_y": None,
            "call": "",
            "full_map": True,
        }
        if rec["kind"] == "MAP" and (not cols or not rows):
            rec["kind"] = "STUB"
        maps[off] = rec

    # Families (9980 Ghidra) — unique grids, enrich atlas or add
    # All golf9980_*_families.csv present (2d + B..O); separate files do not wipe each other
    family_csvs = [
        (GHIDRA / "golf9980_interp_families.csv", "interp_2d"),
        (GHIDRA / "golf9980_interp_B_families.csv", "interp_2d_B"),
        (GHIDRA / "golf9980_interp_C_families.csv", "map_interp_C"),
        (GHIDRA / "golf9980_interp_D_families.csv", "map_interp_D"),
        (GHIDRA / "golf9980_interp_E_families.csv", "map_interp_E"),
        (GHIDRA / "golf9980_interp_F_families.csv", "map_interp_F"),
        (GHIDRA / "golf9980_interp_G_families.csv", "map_interp_G"),
        (GHIDRA / "golf9980_interp_H_families.csv", "map_interp_H"),
        (GHIDRA / "golf9980_interp_I_families.csv", "map_interp_I"),
        (GHIDRA / "golf9980_interp_J_families.csv", "map_interp_J"),
        (GHIDRA / "golf9980_interp_K_families.csv", "map_interp_K"),
        (GHIDRA / "golf9980_interp_L_families.csv", "map_interp_L"),
        (GHIDRA / "golf9980_interp_M_families.csv", "map_interp_M"),
        (GHIDRA / "golf9980_interp_N_families.csv", "map_interp_N"),
        (GHIDRA / "golf9980_interp_O_families.csv", "map_interp_O"),
    ]
    known_names = {p.name for p, _ in family_csvs}
    if GHIDRA.is_dir():
        for p in sorted(GHIDRA.glob("golf9980_*_families.csv")):
            if "stats" in p.name.lower() or p.name in known_names:
                continue
            family_csvs.append((p, p.stem.replace("golf9980_", "").replace("_families", "")))
    for fam_path, hub_tag in family_csvs:
        if not fam_path.exists():
            continue
        for row in read_csv(fam_path):
            off = wol(row.get("grid80"))
            if off is None:
                continue
            rec = maps.get(off)
            if rec is None:
                rec = {
                    "off": off,
                    "name": "",
                    "comment": "",
                    "source": "families",
                    "ax": None,
                    "ay": None,
                    "nx": None,
                    "ny": None,
                    "kind": "MAP",
                    "folder": "",
                    "a2l_id": "",
                    "family": row.get("family_id") or "",
                    "ram_x": parse_hex_field(row.get("ram_x") or ""),
                    "ram_y": parse_hex_field(row.get("ram_y") or ""),
                    "call": row.get("call_site") or "",
                    "full_map": True,
                }
                maps[off] = rec
            rec["family"] = rec.get("family") or (row.get("family_id") or "")
            rec["ram_x"] = rec.get("ram_x") or parse_hex_field(row.get("ram_x") or "")
            rec["ram_y"] = rec.get("ram_y") or parse_hex_field(row.get("ram_y") or "")
            rec["call"] = rec.get("call") or (row.get("call_site") or "")
            merge_axis(rec, row.get("axis_x"), row.get("axis_y"))
            notes = row.get("notes") or ""
            hm = re.search(r"hors=(map_horsA2L_[0-9A-Fa-f]+)", notes)
            if rec["source"] == "atlas9979":
                rec["comment"] += "; 9980 %s %s" % (hub_tag, row.get("family_id") or "")
            else:
                # Prefer first name; later hub only enriches comment/axes/RAM
                if not rec.get("name"):
                    rec["name"] = ident(
                        (hm.group(1) if hm else "")
                        or ((row.get("family_id") or "") + "_%06X" % off if row.get("family_id") else "")
                        or row.get("suggested_name")
                        or "map_%06X" % off
                    )
                tag = "RE %s %s call=%s" % (hub_tag, row.get("family_id"), row.get("call_site"))
                if rec.get("comment"):
                    if hub_tag not in rec["comment"]:
                        rec["comment"] += "; " + tag
                else:
                    rec["comment"] = tag

    ident_rows = read_csv(GHIDRA / "golf9980_horsA2L_identified.csv")
    inside_skip = 0
    for row in ident_rows:
        off = wol(row.get("offset") or row.get("grid80"))
        if off is None:
            continue
        conf = (row.get("confidence") or "").lower()
        notes = row.get("notes") or ""
        a2l_id = (row.get("a2l_id") or "").strip()
        inside = "pas le debut" in notes.lower() or "pointe DANS" in notes
        rec = maps.get(off)
        merge_into = rec
        if rec is None:
            rec = {
                "off": off,
                "name": ident(row.get("old_name") or "map_horsA2L_%06X" % off),
                "comment": notes[:180],
                "source": "horsA2L",
                "ax": None,
                "ay": None,
                "nx": None,
                "ny": None,
                "kind": "STUB",
                "folder": row.get("a2l_folder") or "",
                "a2l_id": a2l_id,
                "family": "",
                "ram_x": None,
                "ram_y": None,
                "call": row.get("call_site") or "",
                "full_map": not inside,
            }
            maps[off] = rec
            merge_into = rec
        merge_axis(merge_into, row.get("axis_x"), row.get("axis_y"))
        if conf == "high" and a2l_id:
            want = ident(a2l_id)
            clash = any(o != off and m["name"] == want for o, m in maps.items())
            if merge_into["source"] == "atlas9979" and merge_into.get("a2l_id") == a2l_id:
                merge_into["name"] = ident("%s_%06X" % (a2l_id, off)) if clash else want
            else:
                merge_into["name"] = ident("%s_%06X" % (a2l_id, off)) if clash else want
            merge_into["comment"] = "HIGH 9980 ident = %s; %s" % (a2l_id, notes[:120])
            merge_into["full_map"] = True
            # high ident often includes cols/rows in notes: cols=16 rows=20
            mc = re.search(r"cols=(\d+)\s+rows=(\d+)", notes)
            if mc and not merge_into.get("nx"):
                merge_into["nx"] = int(mc.group(1))
                merge_into["ny"] = int(mc.group(2))
                merge_into["kind"] = "MAP"
        elif inside:
            merge_into["full_map"] = False
            merge_into["kind"] = "STUB"
            merge_into["comment"] = "NOT map start (medium inside %s); %s" % (a2l_id or "?", notes[:100])
            inside_skip += 1
        else:
            if merge_into["source"] != "atlas9979" and not merge_into.get("name"):
                merge_into["name"] = ident(row.get("old_name") or "map_horsA2L_%06X" % off)
            if merge_into["source"] == "horsA2L":
                merge_into["comment"] = notes[:160]

    for path in (GHIDRA / "golf9980_horsA2L_maps.csv", GHIDRA / "golf9980_horsA2L.csv"):
        for row in read_csv(path):
            off = wol(row.get("grid80"))
            if off is None:
                continue
            if off in maps:
                continue
            maps[off] = {
                "off": off,
                "name": ident(row.get("name") or "map_horsA2L_%06X" % off),
                "comment": "horsA2L interp call=%s" % (row.get("call_site") or ""),
                "source": "horsA2L",
                "ax": None,
                "ay": None,
                "nx": None,
                "ny": None,
                "kind": "STUB",
                "folder": "",
                "a2l_id": "",
                "family": "",
                "ram_x": None,
                "ram_y": None,
                "call": row.get("call_site") or "",
                "full_map": True,
            }

    # Dimensions from bin header / AccPed-like / atlas
    for rec in maps.values():
        if rec.get("full_map") is not False and accped_like(rec) and rec.get("nx") is None:
            rec["nx"], rec["ny"] = 8, 16
            rec["kind"] = "MAP"
            rec["comment"] += "; AccPed-like 8x16 placeholder (APP_r/nmot fam_0001)"
            if rec["source"] != "atlas9979" and not rec.get("a2l_id"):
                rec["name"] = ident("fam_0001_%06X" % rec["off"])
        if rec.get("ax"):
            n = axis_count_header(blob, rec["ax"]) if blob else None
            if n and rec.get("nx") is None:
                rec["nx"] = n
        if rec.get("ay"):
            n = axis_count_header(blob, rec["ay"]) if blob else None
            if n and rec.get("ny") is None:
                rec["ny"] = n
        if rec["kind"] == "MAP" and rec.get("ax") and rec.get("ay"):
            if rec.get("nx") and rec.get("ny"):
                pass
            else:
                # known axes but unknown size: keep MAP refs without inventing grid
                rec["kind"] = "MAP"
        elif rec.get("nx") and rec.get("ny") and rec["kind"] != "CURVE":
            rec["kind"] = "MAP"
        elif rec["source"] == "atlas9979" and rec.get("nx") and not rec.get("ny"):
            rec["kind"] = "CURVE"

        if rec["source"] != "atlas9979" and rec["kind"] == "STUB":
            if rec.get("family") and not rec["name"].startswith("map_hors") and not rec["name"].startswith("fam_"):
                rec["name"] = ident("%s_%06X" % (rec["family"], rec["off"]))
            elif not rec.get("name"):
                rec["name"] = ident("map_horsA2L_%06X" % rec["off"])

    for extra in RE_FLASH:
        off = extra["off"]
        rec = maps.get(off)
        if rec is None:
            rec = {
                "off": off,
                "name": ident(extra["name"]),
                "comment": extra["comment"],
                "source": "rail_path",
                "ax": extra.get("ax"),
                "ay": extra.get("ay"),
                "nx": extra.get("nx"),
                "ny": extra.get("ny"),
                "kind": extra["kind"],
                "folder": "rail_path",
                "a2l_id": extra["name"],
                "family": "",
                "ram_x": None,
                "ram_y": None,
                "call": "",
                "full_map": True,
            }
            maps[off] = rec
        else:
            rec["comment"] = (rec.get("comment") or "") + "; " + extra["comment"]
            if extra.get("ax") and not rec.get("ax"):
                rec["ax"] = extra["ax"]
            if extra.get("nx") and not rec.get("nx"):
                rec["nx"] = extra["nx"]
            if rec["kind"] == "STUB" and extra["kind"] != "STUB":
                rec["kind"] = extra["kind"]
            if rec["source"] != "atlas9979":
                rec["name"] = ident(extra["name"])
                rec["source"] = "rail_path"

    # Unique names
    used = set()
    for rec in sorted(maps.values(), key=lambda r: r["off"]):
        base = rec["name"] or ident("map_%06X" % rec["off"])
        name = base
        n = 2
        while name.lower() in used:
            name = ident("%s_%X" % (base[:24], rec["off"]))
            if name.lower() in used:
                name = ident("%s_%d" % (base[:20], n))
                n += 1
        rec["name"] = name
        used.add(name.lower())

    write_rail_path_a2l()

    # Flash CHARACTERISTIC/AXIS_PTS + RAM MEASUREMENT (Ghidra reverse catalog).

    emit = [
        rec
        for rec in maps.values()
        if rec.get("full_map") is not False or rec["source"] == "atlas9979"
    ]

    # AXIS_PTS unique (only maps we emit)
    axes: dict[int, dict] = {}
    for rec in emit:
        for key, role in (("ax", "X"), ("ay", "Y")):
            off = rec.get(key)
            if not off:
                continue
            n = rec["nx"] if role == "X" else rec["ny"]
            hdr = axis_count_header(blob, off) if blob else None
            cnt = hdr or n
            if off not in axes:
                axes[off] = {"off": off, "n": cnt, "src": hdr, "role": role}
            elif cnt and not axes[off]["n"]:
                axes[off]["n"] = cnt
            elif hdr:
                axes[off]["n"] = hdr
                axes[off]["src"] = hdr

    lines = [
        "ASAP2_VERSION 1 60",
        "/*",
        " * PCR2.1 Golf SW 9980  HW 03L997558A  project SM2G0P",
        " * Reverse-engineered skeleton - NOT Continental OEM A2L.",
        " * First draft for WinOLS import. Incomplete. Do not flash from this file.",
        " *",
        " * WinOLS offset = Ghidra 80xxxxxx or A0xxxxxx & 0x1FFFFF",
        " *   example: Ghidra 0xA01CBE40 -> WinOLS 0x1CBE40",
        " * Uses RL_IDENTITY / NO_INPUT_QUANTITY (WinOLS-friendly stub syntax).",
        " * AXIS_PTS: u16 LE count read 2 or 4 bytes before axis if 2..64.",
        " * AccPed-like (fam_0001 APP_r/nmot): 8x16 placeholder only.",
        " * Atlas 9979 maps included with Caddy IdNames - offsets may differ on 9980.",
        " * Interior horsA2L hits (pointer inside a larger map) are omitted.",
        " * Rail-path extras + RAM MEASUREMENT: PCR21_Golf9980_RAIL_PATH.a2l",
        " * Generated by map-finder/a2l/gen_golf9980_reverse_a2l.py",
        " */",
        '/begin PROJECT PCR21_Golf9980_REVERSE "RE PCR2.1 9980 SM2G0P - NOT OEM"',
        '/begin MODULE PCR21_SM2G0P_9980 "Golf 03L997558A SW9980; reverse draft"',
        "/* NOT OEM. RL_IDENTITY = raw UWORD grid. RAM MEASUREMENT = RE role names. */",
    ]

    n_meas = 0

    n_axis = 0
    axis_name = {}
    for off in sorted(axes):
        info = axes[off]
        nm = ident("AX_%06X" % off)
        axis_name[off] = nm
        cnt = info["n"] if info["n"] else 2
        src = "header_u16" if info["src"] else ("from_map" if info["n"] else "unknown_use_2")
        lines += [
            "/* AXIS_PTS 0x%06X count=%s (%s) - values not dumped */" % (off, info["n"] or "?", src),
            '/begin AXIS_PTS %s "RE axis ptr not OEM" 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0 %d'
            % (nm, off, cnt),
            '  FORMAT "%%5.0"',
            "/end AXIS_PTS",
        ]
        n_axis += 1

    n_char = 0
    n_map = 0
    n_stub = 0
    n_skip_inside = 0
    for rec in sorted(maps.values(), key=lambda r: r["off"]):
        if rec.get("full_map") is False and rec["source"] != "atlas9979":
            n_skip_inside += 1
            continue
        name = rec["name"]
        off = rec["off"]
        cmt = a2l_str(rec["comment"])
        ax, ay = rec.get("ax"), rec.get("ay")
        nx, ny = rec.get("nx"), rec.get("ny")
        lines.append("/* src=%s fam=%s ax=0x%s ay=0x%s */" % (
            rec["source"], rec.get("family") or "-",
            ("%06X" % ax) if ax else "-",
            ("%06X" % ay) if ay else "-",
        ))
        if rec["kind"] == "MAP" and ax and ay and ax in axis_name and ay in axis_name:
            cx = nx or axes[ax]["n"] or 2
            cy = ny or axes[ay]["n"] or 2
            lines += [
                '/begin CHARACTERISTIC %s "%s" MAP 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0' % (name, cmt, off),
                '  FORMAT "%%5.0"',
                "  /begin AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY NO_COMPU_METHOD %d" % cx,
                "    AXIS_PTS_REF %s" % axis_name[ax],
                "  /end AXIS_DESCR",
                "  /begin AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY NO_COMPU_METHOD %d" % cy,
                "    AXIS_PTS_REF %s" % axis_name[ay],
                "  /end AXIS_DESCR",
                "/end CHARACTERISTIC",
            ]
            n_map += 1
        elif rec["kind"] == "CURVE" and ax and ax in axis_name:
            cx = nx or axes[ax]["n"] or 2
            lines += [
                '/begin CHARACTERISTIC %s "%s" CURVE 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0' % (name, cmt, off),
                '  FORMAT "%%5.0"',
                "  /begin AXIS_DESCR COM_AXIS NO_INPUT_QUANTITY NO_COMPU_METHOD %d" % cx,
                "    AXIS_PTS_REF %s" % axis_name[ax],
                "  /end AXIS_DESCR",
                "/end CHARACTERISTIC",
            ]
            n_map += 1
        else:
            lines += [
                "/* STUB unknown size; axis_x=0x%s axis_y=0x%s */"
                % (("%06X" % ax) if ax else "-", ("%06X" % ay) if ay else "-"),
                '/begin CHARACTERISTIC %s "%s" VALUE 0x%06X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0' % (name, cmt, off),
                "/end CHARACTERISTIC",
            ]
            n_stub += 1
        n_char += 1

    n_meas = 0
    lines.append("/* RAM MEASUREMENT - RE role names, not OEM. Units unknown. */")
    for addr, dtype, name, cmt in RE_RAM:
        lo, hi = (0, 255) if dtype == "UBYTE" else ((0, 4294967295) if dtype == "ULONG" else (0, 65535))
        lines += [
            '/begin MEASUREMENT %s "%s" %s RL_IDENTITY 0 0 %d %d'
            % (ident(name), a2l_str(cmt), dtype, lo, hi),
            "  ECU_ADDRESS 0x%08X" % addr,
            "/end MEASUREMENT",
        ]
        n_meas += 1

    lines += [
        "/end MODULE",
        "/end PROJECT",
        "",
        "/* COUNTS CHARACTERISTIC=%d (MAP/CURVE=%d STUB=%d) MEASUREMENT=%d AXIS_PTS=%d skipped_interior=%d */"
        % (n_char, n_map, n_stub, n_meas, n_axis, n_skip_inside),
    ]
    text = "\n".join(lines) + "\n"
    out_path = Path(__file__).resolve().parent / "PCR21_Golf9980_REVERSE.a2l"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_path.write_text(text, encoding="ascii", errors="replace")
    except PermissionError:
        out_path = out_path.with_name(out_path.stem + "_FIXED.a2l")
        out_path.write_text(text, encoding="ascii", errors="replace")
        print("WARN: locked primary A2L - wrote", out_path)
    if COPY.parent.exists():
        try:
            COPY.write_text(text, encoding="ascii", errors="replace")
        except PermissionError:
            print("WARN: locked copy", COPY)
    print("wrote", out_path, "bytes", out_path.stat().st_size)
    print("CHARACTERISTIC", n_char, "MAP/CURVE", n_map, "STUB", n_stub)
    print("MEASUREMENT", n_meas, "AXIS_PTS", n_axis)
    print("maps dict", len(maps), "emitted", n_char, "skipped_interior", n_skip_inside)
    if COPY.parent.exists():
        print("copy", COPY)
        try:
            (COPY.parent / RAIL_PATH.name).write_text(RAIL_PATH.read_text(encoding="ascii"), encoding="ascii")
        except PermissionError:
            print("WARN: locked rail-path copy")


if __name__ == "__main__":
    main()
