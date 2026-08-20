"""Parse WinOLS .kp → map catalog JSON (names, folders, flash addresses)."""
from __future__ import annotations

import json
import re
import struct
import zlib
from collections import Counter
from pathlib import Path


def extract_intern(kp: bytes) -> bytes:
    off = kp.find(b"PK\x03\x04")
    if off < 0:
        raise ValueError("no ZIP local header in .kp")
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
    data_start = off + 30 + nlen + elen
    data = kp[data_start : data_start + csize]
    if method == 8:
        return zlib.decompress(data, -15)
    if method == 0:
        return data
    raise ValueError(f"unsupported zip method {method}")


def find_name_records(intern: bytes) -> list[tuple[int, int, str]]:
    recs: list[tuple[int, int, str]] = []
    i = 0
    n = len(intern)
    while i + 8 < n:
        (ln,) = struct.unpack_from("<I", intern, i)
        if 4 <= ln <= 120 and i + 4 + ln <= n:
            nb = intern[i + 4 : i + 4 + ln]
            if all(32 <= b < 127 for b in nb) and sum(65 <= b <= 122 for b in nb) >= 3:
                name = nb.decode("ascii")
                if sum(c.isalpha() for c in name) / len(name) >= 0.35:
                    recs.append((i, ln, name))
                    i = i + 4 + ln
                    continue
        i += 1
    return recs


def _is_power2(v: int) -> bool:
    return v > 0 and (v & (v - 1)) == 0


def extract_addr_pair(chunk: bytes, flash_size: int = 0x400000) -> tuple[int | None, int | None]:
    """Pick start/end flash addresses from a map record blob."""
    # MEVD cal maps for this soft live mainly in ~0x18xxxx–0x2Axxxx.
    lo, hi = 0x180000, min(flash_size - 0x1000, 0x2C0000)
    cands: list[tuple[int, int]] = []
    for k in range(0, len(chunk) - 3, 2):
        v = struct.unpack_from("<I", chunk, k)[0]
        if lo <= v < hi and not _is_power2(v) and (v & 1) == 0:
            if (v & 0xFFFF) == 0xFFFF:
                continue
            cands.append((k, v))
    if not cands:
        return None, None
    # Prefer a start/end pair close together (same map payload)
    for i, (k1, a1) in enumerate(cands):
        for k2, a2 in cands[i + 1 : i + 8]:
            if a1 < a2 and 4 <= (a2 - a1) <= 0x8000 and (k2 - k1) <= 16:
                return a1, a2
    return cands[0][1], None


def guess_folder(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ("torque", "nm)", "wish", "driver", "monitoring (%)")):
        return "Engine Torque"
    if "rail" in n or "fuel pressure" in n:
        return "Rail"
    if any(x in n for x in ("turbo", "boost", "charge air", "wastegate")):
        return "Turbo System"
    if any(x in n for x in ("inj", "injection", "soi", "duration", "iq ")):
        return "Injection System"
    if any(x in n for x in ("limit", "limiter", "vmax", "vehicle speed")):
        return "Limiters"
    if any(x in n for x in ("spark", "ignition", "advance")):
        return "Spark Advance"
    if any(x in n for x in ("vvt", "vanos", "camshaft", "valve timing")):
        return "Variable Valve Timing (VVT)"
    if any(x in n for x in ("air ", "maf", "throttle", "load")):
        return "Air Control"
    if any(x in n for x in ("deact", "off", "dtc", "egr", "dpf", "disable")):
        return "Deactivations"
    return "Tables"


def parse_dims(chunk_after_name: bytes) -> tuple[int | None, int | None, int | None]:
    """Read type/cols/rows after name padding: … u32 type-ish, … cols, rows."""
    j = 0
    while j < len(chunk_after_name) and chunk_after_name[j] == 0:
        j += 1
    if j + 24 > len(chunk_after_name):
        return None, None, None
    vals = [struct.unpack_from("<I", chunk_after_name, j + 4 * k)[0] for k in range(8)]
    # Observed: [flags, 2, 3, 2, cols, rows, 0, 0] or similar
    cols = rows = mtype = None
    for i, v in enumerate(vals):
        if cols is None and 2 <= v <= 64 and i >= 3:
            cols = v
            continue
        if cols is not None and rows is None and 1 <= v <= 64:
            rows = v
            break
    if vals and 1 <= vals[0] <= 8:
        mtype = vals[0]
    return cols, rows, mtype


def parse_kp(kp_path: Path, flash_size: int = 0x400000) -> dict:
    kp = kp_path.read_bytes()
    intern = extract_intern(kp)
    recs = find_name_records(intern)
    maps = []
    for idx, (off, ln, name) in enumerate(recs):
        next_off = recs[idx + 1][0] if idx + 1 < len(recs) else len(intern)
        chunk = intern[off:next_off]
        after = intern[off + 4 + ln : next_off]
        addr, end = extract_addr_pair(chunk, flash_size=flash_size)
        cols, rows, mtype = parse_dims(after)
        maps.append(
            {
                "id": re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")[:56],
                "name": name,
                "folder": guess_folder(name),
                "addr": f"{addr:X}" if addr is not None else None,
                "addr_int": addr,
                "end": f"{end:X}" if end is not None else None,
                "end_int": end,
                "cols": cols,
                "rows": rows,
                "type_code": mtype,
                "source": "winols_kp",
            }
        )

    # Deduplicate by name+addr
    seen: set[tuple] = set()
    uniq = []
    for m in maps:
        key = (m["name"], m["addr"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(m)

    return {
        "schema": 1,
        "source_kp": kp_path.name,
        "intern_size": len(intern),
        "map_count": len(uniq),
        "maps_with_addr": sum(1 for m in uniq if m["addr"]),
        "folders": dict(Counter(m["folder"] for m in uniq)),
        "maps": uniq,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    src_kp = Path(
        r"c:\Users\theda\OneDrive\Bureau\BMW MAPPACK\WinOLS (BMW 1 Serie (Mappack) - 531049).kp"
    )
    src_ori = Path(
        r"c:\Users\theda\OneDrive\Bureau\BMW MAPPACK\WinOLS (BMW 1 Serie (Original File) - 531049).ori"
    )

    ecu_dir = root / "map-finder" / "ecu" / "mevd1725" / "531049"
    web_dir = root / "data" / "mevd1725-531049"
    ecu_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)

    # Copy sources into repo (database)
    dst_kp = ecu_dir / "531049.kp"
    dst_ori = ecu_dir / "531049_ORI.bin"
    if src_kp.exists():
        dst_kp.write_bytes(src_kp.read_bytes())
    if src_ori.exists():
        dst_ori.write_bytes(src_ori.read_bytes())

    catalog = parse_kp(dst_kp if dst_kp.exists() else src_kp)
    catalog.update(
        {
            "ecu": "Bosch MEVD17.2.5",
            "ecu_id": "mevd1725",
            "soft": "531049",
            "vehicle": "BMW 1 Series",
            "flash_size": 4194304,
            "ori_file": str(dst_ori.relative_to(root)).replace("\\", "/"),
            "kp_file": str(dst_kp.relative_to(root)).replace("\\", "/"),
            "note": "Catalogue importé depuis mappack WinOLS (.kp). Comparaison Stage ORI/ACE/V1 pas encore construite.",
        }
    )

    for path in (ecu_dir / "maps.json", web_dir / "maps.json"):
        path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
        print(f"wrote {path} maps={catalog['map_count']} with_addr={catalog['maps_with_addr']}")

    for m in catalog["maps"][:12]:
        print(f"  {m.get('addr') or '??????':>8}  {m['name'][:58]}")


if __name__ == "__main__":
    main()
