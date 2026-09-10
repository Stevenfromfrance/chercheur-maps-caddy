# -*- coding: utf-8 -*-
"""A5 Bertin — viewer type WinOLS (pas WinOLS, pas de checksum, pas d'édition).

Lit le .kp ami + ORI + V1.5, sort des grilles 2D (ORI vs V1.5) et détecte
si une plage .kp mange un axe (watch_dim / watch_axis).

  python tools/a5_winols_standin.py
"""
from __future__ import annotations

import json
import re
import struct
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ECU = ROOT / "map-finder" / "ecu" / "edc17cp14" / "516657"
WEB = ROOT / "data" / "edc17cp14-516657"
ORI = ECU / "ORI_FLS.fls"
STAGE = ECU / "A5_516657_V1.5_0AW_injtime_cruiseIQ_vmaxoff_nosmoke_fill400_DPF_EGR_HC_SOI_noCHK.fls"
MANIFEST = ECU / "A5_516657_V1.5_0AW_manifest.json"
PAIR_LABEL = "ORI vs V1.5"
KP_CANDIDATES = [
    ECU / "516657.kp",
    Path(r"C:\Users\theda\OneDrive\Bureau\AUDI A5 BERTIN\friendmap pack\WinOLS (Audi A5 (Mappackj) - 516657).kp"),
]

CLASSIC = {
    20,
    32,
    40,
    48,
    64,
    80,
    90,
    96,
    105,
    128,
    160,
    192,
    210,
    240,
    256,
    320,
    384,
    512,
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
    seen, got = [], set()
    for k in range(0, len(chunk) - 3):
        v = struct.unpack_from("<I", chunk, k)[0]
        if 0x180000 <= v < 0x1F0000 and (v & 1) == 0 and v not in got:
            if v & (v - 1) == 0:
                continue
            got.add(v)
            seen.append(v)
    return seen


def folder_of(name: str) -> str:
    n = name.lower()
    if "fuel quantity" in n:
        return "IQ"
    if "turbo pressure" in n:
        return "Turbo"
    if "rail" in n:
        return "Rail"
    if "vgt" in n or "wastegate" in n:
        return "VGT/WG"
    if "timing" in n or "injection time" in n:
        return "SOI / duree"
    if "smoke" in n:
        return "Smoke"
    if "idle" in n:
        return "Idle"
    if "rpm limiter" in n:
        return "Limiteur RPM"
    if "correction" in n or "correctioin" in n:
        return "Correction"
    if "cranking" in n:
        return "Cranking"
    if "gearbox" in n:
        return "Boite"
    if "torque" in n:
        return "Couple"
    return "Autre"


def u16s(buf: bytes, start: int, nbytes: int) -> list[int]:
    end = min(len(buf), start + nbytes)
    n = (end - start) // 2
    return [buf[start + 2 * i] | (buf[start + 2 * i + 1] << 8) for i in range(n)]


def monotonic(vals: list[int]) -> bool:
    if len(vals) < 6:
        return False
    diffs = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    pos = sum(d > 0 for d in diffs)
    neg = sum(d < 0 for d in diffs)
    zeros = sum(d == 0 for d in diffs)
    if zeros > len(diffs) * 0.35:
        return False
    if pos / len(diffs) < 0.75 and neg / len(diffs) < 0.75:
        return False
    span = abs(vals[-1] - vals[0])
    if span < 40:
        return False
    return True


def factorize(n: int, folder: str) -> tuple[int, int]:
    if n <= 1:
        return 1, n or 1
    prefer = {
        "IQ": [(16, 16), (16, 15), (15, 16), (16, 12), (12, 16)],
        "Turbo": [(16, 10), (10, 16), (16, 8), (8, 16), (15, 10), (10, 15)],
        "Rail": [(16, 16), (16, 8), (8, 16), (10, 8), (15, 8), (16, 7)],
        "Couple": [(16, 8), (8, 16), (16, 16), (10, 8), (8, 10), (5, 16)],
    }.get(folder, [])
    for c, r in prefer:
        if c * r == n:
            return c, r
    cands = [(c, n // c) for c in range(2, min(33, n + 1)) if n % c == 0 and 1 <= n // c <= 40]
    if not cands:
        return n, 1
    def score(cr: tuple[int, int]) -> tuple:
        c, r = cr
        classic = 0 if c in (8, 10, 12, 15, 16, 20) and r in (8, 10, 12, 15, 16, 20) else 1
        return (classic, abs(c - 16) + abs(r - 16))
    return min(cands, key=score)


def looks_like_axis(vals: list[int]) -> bool:
    """True axis: mostly rising, fairly regular steps — not a map's last row."""
    if not monotonic(vals):
        return False
    diffs = [d for d in (vals[i + 1] - vals[i] for i in range(len(vals) - 1)) if d > 0]
    if len(diffs) < len(vals) - 3:
        return False
    mean = sum(diffs) / len(diffs)
    if mean < 8:
        return False
    var = sum((d - mean) ** 2 for d in diffs) / len(diffs)
    cv = (var ** 0.5) / mean
    return cv < 0.65


def split_axes(
    vals: list[int], nbytes: int
) -> tuple[list[int], list[int] | None, list[int] | None, str]:
    n = len(vals)
    if n <= 2:
        return vals, None, None, "scalar"
    # 512 / 320 / 256 o = already a classic EDC grid. Last row is data, not an axis.
    if nbytes in CLASSIC or n in CLASSIC:
        return vals, None, None, ""
    # Prefer a single trailing axis (minimal strip) before two axes.
    for ax in (16, 15, 12, 10, 8, 20):
        if n > ax and looks_like_axis(vals[-ax:]):
            grid = vals[: n - ax]
            if len(grid) in CLASSIC:
                return grid, vals[-ax:], None, f"1 axe {ax} colle apres la grille"
    for ax in (16, 15, 12, 10, 8, 20):
        if n > 2 * ax and looks_like_axis(vals[-ax:]) and looks_like_axis(vals[-2 * ax : -ax]):
            grid = vals[: n - 2 * ax]
            if len(grid) in CLASSIC:
                return grid, vals[-2 * ax : -ax], vals[-ax:], f"2 axes {ax}+{ax} colles apres la grille"
    return vals, None, None, ""


def find_kp() -> Path:
    for p in KP_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError("mappack .kp introuvable (dossier client ou " + str(ECU / "516657.kp") + ")")


def main() -> None:
    if not STAGE.exists():
        raise SystemExit(f"missing stage file: {STAGE}")
    kp_path = find_kp()
    intern = intern_from_kp(kp_path.read_bytes())
    recs = name_records(intern)
    ori = ORI.read_bytes()
    stage = STAGE.read_bytes()
    if len(ori) != len(stage):
        raise SystemExit(f"size mismatch ORI={len(ori)} STAGE={len(stage)}")
    man = {}
    if MANIFEST.exists():
        man = json.loads(MANIFEST.read_text(encoding="utf-8"))

    raw = []
    for i, (off, ln, name) in enumerate(recs):
        nxt = recs[i + 1][0] if i + 1 < len(recs) else len(intern)
        ads = addrs_in(intern[off:nxt])
        start = ads[0] if ads else None
        end = None
        if start is not None and len(ads) > 1 and ads[1] > start:
            sz = ads[1] - start
            if 2 <= sz <= 2048:
                end = ads[1]
        raw.append({"name": name, "start": start, "end": end, "naddr": len(ads), "folder": folder_of(name)})

    starts = sorted({m["start"] for m in raw if m["start"] is not None})
    maps = []
    for m in raw:
        start, end = m["start"], m["end"]
        size = (end - start) if start is not None and end is not None else None
        if start is not None and size is None:
            nxts = [s for s in starts if s > start]
            if nxts:
                gap = nxts[0] - start
                if 2 <= gap <= 2048:
                    end = start + gap
                    size = gap
        if start is None:
            maps.append(
                {
                    "id": re.sub(r"[^A-Za-z0-9]+", "_", m["name"]).strip("_")[:56],
                    "name": m["name"],
                    "folder": m["folder"],
                    "addr": None,
                    "cols": None,
                    "rows": None,
                    "kp_size": None,
                    "used": False,
                    "verdict": "unused",
                    "why": "pas d'adresse dans le .kp",
                    "ori": None,
                    "v11": None,
                }
            )
            continue
        if size is None:
            size = 2 if "limiter of maximum torque" in m["name"].lower() else 32
            end = start + size
        if start & 1:
            start += 1
            size = max(2, size - 1)
        vals_o = u16s(ori, start, size)
        vals_v = u16s(stage, start, size)
        grid_o, ax, ay, axis_note = split_axes(vals_o, size)
        grid_v = vals_v[: len(grid_o)]
        extra_v = vals_v[len(grid_o) :]
        cols, rows = (1, 1) if len(grid_o) <= 2 else factorize(len(grid_o), m["folder"])
        chg = sum(1 for a, b in zip(grid_o, grid_v) if a != b)
        used = chg > 0
        pcts = [100 * (b / a - 1) for a, b in zip(grid_o, grid_v) if a and b != a]
        pct_med = round(sorted(pcts)[len(pcts) // 2], 2) if pcts else None
        classic = size in CLASSIC or len(grid_o) in CLASSIC
        if used and (axis_note.startswith("1 axe") or axis_note.startswith("2 axes")):
            verdict = "watch_axis"
        elif used and size <= 20:
            verdict = "ok_scalar"
        elif used and not classic and len(grid_o) not in CLASSIC:
            verdict = "watch_dim"
        elif used:
            verdict = "ok_scalar" if len(grid_o) <= 2 else "ok_grid"
        else:
            verdict = "unused"
        axis_changed = bool(extra_v) and extra_v != vals_o[len(grid_o) :]
        maps.append(
            {
                "id": re.sub(r"[^A-Za-z0-9]+", "_", m["name"]).strip("_")[:56] + f"_{start:X}",
                "name": m["name"],
                "folder": m["folder"],
                "addr": f"{start:X}",
                "addr_int": start,
                "end": f"{(end or start + size):X}",
                "kp_size": size,
                "view_cells": len(grid_o),
                "cols": cols,
                "rows": rows,
                "axis_x": ax,
                "axis_y": ay,
                "axis_note": axis_note or None,
                "axis_changed": axis_changed,
                "used": used,
                "verdict": verdict,
                "why": None,
                "changed": chg,
                "pct_med": pct_med,
                "ori": grid_o,
                "v11": grid_v,  # kept key for a5-winols.html (means "stage" side)
                "naddr": m["naddr"],
            }
        )

    counts = Counter(m["verdict"] for m in maps)
    ids = [b"516657", b"8K1907401K", b"0008", b"B3UX", b"CGKA", b"1037516657"]
    ids_ok = all(ori.find(x) >= 0 and ori.find(x) == stage.find(x) for x in ids)
    bytes_changed = sum(1 for a, b in zip(ori, stage) if a != b)
    stage1_cells = sum(m.get("changed") or 0 for m in maps if m.get("used"))
    payload = {
        "schema": 1,
        "pair": PAIR_LABEL,
        "stage_file": STAGE.name,
        "ecu": "Bosch EDC17CP14",
        "soft": "516657",
        "vehicle": "Audi A5 Sportback CGKA",
        "source_kp": kp_path.name,
        "manifest": man,
        "ids_unmoved": ids_ok,
        "bytes_changed": bytes_changed,
        "note": (
            "Pas WinOLS : lecture des grilles depuis le .kp + dumps. "
            "Pas de checksum, pas d'edition. "
            "used = cellules differentes vs ORI. "
            "watch_axis = la plage .kp contient un axe colle (on affiche la grille sans l'axe)."
        ),
        "counts": dict(counts),
        "map_count": len(maps),
        "maps_with_addr": sum(1 for m in maps if m.get("addr")),
        "maps_touched": sum(1 for m in maps if m.get("used")),
        "maps": maps,
    }
    WEB.mkdir(parents=True, exist_ok=True)
    json_path = WEB / "winols-view.json"
    js_path = WEB / "winols-view.js"
    json_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
    js_path.write_text(
        "window.A5WINOLS = " + json.dumps(payload, ensure_ascii=True) + ";\n",
        encoding="utf-8",
    )
    (ECU / "winols-view.json").write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")

    # Light table for fiche Bertin (no full grids)
    compare = {
        "pair": PAIR_LABEL,
        "stage_file": STAGE.name,
        "ids_unmoved": ids_ok,
        "bytes_changed": bytes_changed,
        "stage1_cells": stage1_cells,
        "maps_touched": payload["maps_touched"],
        "verdicts": dict(counts),
        "note": (
            "KP bancal = taille (lignes x cols), pas le nom. "
            "V1.5 = soft 0AW sous plafond couple ORI + fill/nosmoke/InjTime/SOI/HC/pollution."
        ),
        "maps": [
            {
                "name": m["name"],
                "folder": m.get("folder"),
                "start": m.get("addr_int"),
                "size": m.get("kp_size"),
                "cells": m.get("changed") or 0,
                "pct_med": m.get("pct_med"),
                "verdict": m["verdict"],
                "naddr": m.get("naddr"),
            }
            for m in maps
            if m.get("used")
        ],
    }
    compare_path = ECU / "v15_kp_compare.json"
    compare_path.write_text(json.dumps(compare, ensure_ascii=True, indent=2), encoding="utf-8")

    print(f"kp {kp_path}")
    print(f"pair {PAIR_LABEL}")
    print(f"maps {len(maps)} touched {payload['maps_touched']} counts {dict(counts)}")
    print(f"bytes_changed {bytes_changed} ids_ok {ids_ok}")
    print(f"wrote {json_path}")
    print(f"wrote {js_path}")
    print(f"wrote {compare_path}")
    print("--- touched (top by cells) ---")
    touched = sorted((m for m in maps if m.get("used")), key=lambda x: -(x.get("changed") or 0))
    for m in touched[:25]:
        print(
            f"  {m['addr']} {m['changed']:4d}c  "
            f"{(str(m['pct_med']) + '%') if m['pct_med'] is not None else '—':>7}  "
            f"{m['folder']:<12} {m['name'][:52]}"
        )
    print("--- watch ---")
    for m in maps:
        if m["verdict"] in ("watch_axis", "watch_dim"):
            print(
                f"  {m['addr']} {m['kp_size']}o view={m['view_cells']} "
                f"{m['cols']}x{m['rows']} {m['verdict']} axis_chg={m['axis_changed']} "
                f"{m['axis_note']}  {m['name'][:56]}"
            )


if __name__ == "__main__":
    main()
