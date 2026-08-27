# -*- coding: utf-8 -*-
"""A5 Bertin V1.1 — named Stage1 from friend WinOLS .kp + DaVinci DPF/EGR/FLAPS.

Conservative because 0AW + ~256 000 km:
- DPF off + related DTCs, EGR off + flaps + related DTCs (DaVinci)
- Stage1 only on named maps (torque / IQ / boost / rail / smoke)
- Cap per family 4–8 %, never fill empty cells, never copy A4 Stage2 10000-fill
- Skip SOI, duration, VGT/WG, idle, RPM limiter (hardcut = V2)
- No TVA, no lambda, no launch
"""
from __future__ import annotations

import json
import math
import struct
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORI = ROOT / "ORI_FLS.fls"
S2 = ROOT / "ref-a4-516657-stage2" / "A4_516657_STAGE2.fls"
KP = Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\friendmap pack\WinOLS (Audi A5 (Mappackj) - 516657).kp")
DAV = Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off\A5_516657_DPF-EGR-FLAPS_noCHK.bin")
TVA = Path(
    r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off"
    r"\DaVinci (A5_CGKA_8K1907401K_0008_BACKUP_MICRO.FLS(_TVA_))__noCHK.BIN"
)
LAMBDA = Path(
    r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\dtc off"
    r"\DaVinci (A5_CGKA_8K1907401K_0008_BACKUP_MICRO.FLS(_LAMBDA_))__noCHK.BIN"
)
CLIENT = Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN")
OUT_NAME = "A5_516657_V1.1_S1named_DPF_EGR_noCHK.fls"

FLAG_LO, FLAG_HI = 0x185000, 0x186200
IDS = [b"516657", b"8K1907401K", b"0008", b"B3UX", b"CGKA", b"1037516657"]
PROTECT = [
    (0x000000, 0x000100),
    (0x001A00, 0x001B00),
    (0x1A6EA0, 0x1A6F20),
    (0x183000, 0x183080),
]

# High-km 0AW caps (factor on used cells only).
CAPS = {
    "torque": 1.08,
    "iq": 1.07,
    "boost": 1.06,
    "rail": 1.05,
}


def intern_from_kp(kp: bytes) -> bytes:
    off = kp.find(b"PK\x03\x04")
    if off < 0:
        raise ValueError("not a WinOLS .kp")
    (
        _sig,
        _ver,
        _flags,
        method,
        _mt,
        _md,
        _crc,
        csize,
        _usize,
        nlen,
        elen,
    ) = struct.unpack_from("<IHHHHHIIIHH", kp, off)
    data = kp[off + 30 + nlen + elen : off + 30 + nlen + elen + csize]
    if method == 8:
        return zlib.decompress(data, -15)
    if method == 0:
        return data
    raise ValueError(f"zip method {method}")


def name_records(intern: bytes) -> list[tuple[int, int, str]]:
    recs = []
    i, n = 0, len(intern)
    while i + 8 < n:
        (ln,) = struct.unpack_from("<I", intern, i)
        if 4 <= ln <= 120 and i + 4 + ln <= n:
            nb = intern[i + 4 : i + 4 + ln]
            if all(32 <= b < 127 for b in nb) and sum(65 <= b <= 122 for b in nb) >= 3:
                name = nb.decode("ascii")
                if sum(c.isalpha() for c in name) / max(len(name), 1) >= 0.35:
                    recs.append((i, ln, name))
                    i = i + 4 + ln
                    continue
        i += 1
    return recs


def addrs_in(chunk: bytes) -> list[int]:
    seen = []
    got = set()
    for k in range(0, len(chunk) - 3):
        v = struct.unpack_from("<I", chunk, k)[0]
        if 0x180000 <= v < 0x1F0000 and (v & 1) == 0 and v not in got:
            if v & (v - 1) == 0:
                continue
            got.add(v)
            seen.append(v)
    return seen


def classify(name: str) -> str | None:
    n = name.lower()
    if any(x in n for x in ("correction", "timing", "injection time", "vgt", "wastegate", "idle", "rpm limiter", "cranking")):
        return None
    if "smoke" in n:
        return None
    if "gearbox input" in n:
        return None
    if "rail pressure" in n:
        return "rail"
    if "turbo pressure" in n:
        return "boost"
    if "fuel quantity" in n:
        return "iq"
    if "torque" in n:
        return "torque"
    return None


def parse_maps(intern: bytes) -> list[dict]:
    recs = name_records(intern)
    out = []
    for i, (off, ln, name) in enumerate(recs):
        nxt = recs[i + 1][0] if i + 1 < len(recs) else len(intern)
        ads = addrs_in(intern[off:nxt])
        fam = classify(name)
        if fam is None or not ads:
            continue
        start = ads[0]
        end = ads[1] if len(ads) > 1 and ads[1] > start else None
        size = (end - start) if end else 0
        if fam == "torque" and 2 <= size <= 20:
            end = start + 2
            size = 2
        elif size < 16 or size > 2048:
            continue
        if start & 0xFFF == 0:
            continue
        out.append({"name": name, "fam": fam, "start": start, "end": start + size, "size": size, "cap": CAPS[fam]})
    return out


def protected(i: int) -> bool:
    return any(lo <= i < hi for lo, hi in PROTECT) or FLAG_LO <= i < FLAG_HI


def u16(b: bytes, i: int) -> int:
    return b[i] | (b[i + 1] << 8)


def put_u16(buf: bytearray, i: int, v: int) -> None:
    v = max(0, min(0xFFFF, int(v)))
    buf[i] = v & 0xFF
    buf[i + 1] = (v >> 8) & 0xFF


def main() -> None:
    ori = ORI.read_bytes()
    s2 = S2.read_bytes()
    dav = DAV.read_bytes()
    intern = intern_from_kp(KP.read_bytes())
    n = len(ori)
    assert n == 2_097_152 == len(s2) == len(dav)

    maps = parse_maps(intern)
    dav_set = {i for i in range(n) if ori[i] != dav[i]}

    out = bytearray(ori)
    for i in dav_set:
        out[i] = dav[i]

    claimed: dict[int, str] = {}
    cells: list[dict] = []
    skipped = Counter()

    for m in maps:
        i = m["start"]
        if i & 1:
            i += 1
        while i + 1 < m["end"]:
            if i in claimed:
                skipped["overlap"] += 1
                i += 2
                continue
            if protected(i) or i in dav_set or (i + 1) in dav_set:
                skipped["protect"] += 1
                i += 2
                continue
            o = u16(ori, i)
            if o == 0:
                skipped["ori0"] += 1
                i += 2
                continue
            cap = m["cap"]
            t = u16(s2, i)
            new = math.floor(o * cap)
            if o and 1.02 <= (t / o) <= 1.20 and t > o:
                new = min(t, new)
            new = min(new, 0xFFFF)
            if new <= o:
                skipped["no_gain"] += 1
                i += 2
                continue
            put_u16(out, i, new)
            claimed[i] = m["fam"]
            cells.append(
                {
                    "addr": i,
                    "ori": o,
                    "s2": t,
                    "v11": new,
                    "pct": round(100 * (new / o - 1), 2),
                    "fam": m["fam"],
                    "map": m["name"],
                }
            )
            i += 2

    tva = TVA.read_bytes() if TVA.exists() else None
    lam = LAMBDA.read_bytes() if LAMBDA.exists() else None
    tva_hit = (
        [i for i in range(n) if ori[i] != tva[i] and i not in dav_set and out[i] == tva[i] and out[i] != ori[i]]
        if tva
        else []
    )
    lam_hit = (
        [i for i in range(n) if ori[i] != lam[i] and i not in dav_set and out[i] == lam[i] and out[i] != ori[i]]
        if lam
        else []
    )
    missing_dav = [i for i in dav_set if out[i] != dav[i]]
    extra_low = [i for i in range(0x180000) if out[i] != ori[i] and i not in dav_set]
    id_ok = all(out.find(x) >= 0 for x in IDS)
    id_moved = any(out.find(x) != ori.find(x) for x in IDS)
    max_pct = max((c["pct"] for c in cells), default=0)
    max_factor = max((c["v11"] / c["ori"] for c in cells), default=1)
    rpm_hit = any("rpm limiter" in c["map"].lower() or "idle" in c["map"].lower() for c in cells)

    errors = []
    if missing_dav:
        errors.append(f"davinci_missing {len(missing_dav)}")
    if extra_low:
        errors.append(f"extra_lowflash {len(extra_low)}")
    if tva_hit:
        errors.append(f"tva {len(tva_hit)}")
    if lam_hit:
        errors.append(f"lambda {len(lam_hit)}")
    if not id_ok:
        errors.append("ids_missing")
    if id_moved:
        errors.append("ids_moved")
    if max_factor > 1.0805:
        errors.append(f"cap {max_factor}")
    if any(c["ori"] == 0 for c in cells):
        errors.append("filled_zero")
    if rpm_hit:
        errors.append("rpm_or_idle_touched")
    if len(cells) < 50:
        errors.append(f"too_few {len(cells)}")

    by_fam = Counter(c["fam"] for c in cells)
    by_map = Counter(c["map"] for c in cells)
    changed = sum(1 for i in range(n) if out[i] != ori[i])
    report = {
        "file": OUT_NAME,
        "ok": not errors,
        "errors": errors,
        "bytes_changed": changed,
        "davinci_dpf_egr_flaps_bytes": len(dav_set),
        "stage1_u16_cells": len(cells),
        "stage1_pct_max": max_pct,
        "caps": CAPS,
        "maps_used": len(maps),
        "cells_by_family": dict(by_fam),
        "maps_touched": dict(by_map.most_common()),
        "skipped": dict(skipped),
        "ids_ok": id_ok,
        "ids_unmoved": not id_moved,
        "tva_not_applied": True,
        "lambda_not_applied": True,
        "no_launch": True,
        "no_hardcut": True,
        "note": (
            "noCHK — checksum WinOLS/KESS avant flash. "
            "Maps nommées (mappack ami) + DaVinci DPF/EGR/FLAPS. "
            "Pas de TVA/lambda/launch/hardcut. "
            "Ne pas flasher si G83 123C / EGT S3 non traites."
        ),
        "cells_top": sorted(cells, key=lambda c: -c["pct"])[:12],
    }
    (ROOT / "A5_516657_V1.1_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k != "cells_top"}, indent=2))
    if errors:
        raise SystemExit("VERIFY FAIL: " + ", ".join(errors))
    dest = ROOT / OUT_NAME
    dest.write_bytes(out)
    (CLIENT / OUT_NAME).write_bytes(out)
    print(f"wrote {dest}")
    print(f"wrote {CLIENT / OUT_NAME}")


if __name__ == "__main__":
    main()
