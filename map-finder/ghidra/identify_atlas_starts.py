# -*- coding: utf-8 -*-
"""Identify Stage1-critical atlas map STARTS on Golf 9980 fullflash.

Hub interpolators often land *inside* maps (MEDIUM). This offline pass probes
atlas 9979 map starts (and ORI fingerprint) directly on the Golf bin so we can
promote clutch / rail / duration / tqlim / smoke / vmax / DTC / EGR when the
payload fingerprint matches.

Outputs:
  golf9980_atlas_starts_identified.csv
  golf9980_atlas_starts_HIGH.txt

Does not invent OEM names. Does not flash.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS = ROOT.parents[1]
GOLF = Path(r"C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin")
VEH = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules"
    r"\Caddy-CAYE-2013-03L906023PA-2531"
)
ORI_CANDIDATES = [
    VEH / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin",
    Path(
        r"C:\Users\theda\OneDrive\Bureau\caddy cartho\ORI CADDY STEVEN"
        r"\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27"
    ),
]
ATLAS = WS / "map-finder" / "atlas" / "9979.json"
OUT_CSV = ROOT / "golf9980_atlas_starts_identified.csv"
OUT_TXT = ROOT / "golf9980_atlas_starts_HIGH.txt"
GHIDRA_SCRIPTS = Path(r"C:\Users\theda\ghidra_scripts")

FLASH80 = 0x80000000
CAL0, CAL1 = 0x180000, 0x200000
FP_N = 64

# (id_prefix_or_folder_rule, category, priority)
# Matched against atlas id / folder / group
FAMILY_RULES: list[tuple[str, str, int]] = [
    ("tqlim_cluth", "clutch_prot", 10),
    ("accped", "AccPed", 15),
    ("tqlim_base", "tqlim", 20),
    ("tqlim_", "tqlim_other", 25),
    ("smoke_", "smoke", 30),
    ("turbo_base", "turbo", 40),
    ("turbo_int", "turbo_corr", 45),
    ("turbo_", "turbo_other", 50),
    ("rail_", "rail", 60),
    ("soi_", "soi", 70),
    ("duration_", "duration", 80),
    ("vmax", "speed_limiter", 90),
    ("airctl", "egr_control", 100),
]

# folder/group based for DTC packs
DTC_FOLDERS = {
    "DPF": "dtc_dpf",
    "EGR": "dtc_egr",
    "EGT": "dtc_egt",
    "EGR/DPF": "dtc_egr_dpf",
    "EGR com": "dtc_egr_com",
    "DPF/O2": "dtc_dpf_o2",
}


def find_ori() -> Path | None:
    for p in ORI_CANDIDATES:
        if p.exists():
            return p
    return None


def family_id(name: str) -> str:
    s = re.sub(r"^CH_", "", name or "")
    s = re.sub(r"@.*$", "", s)
    return s


def ghidra_safe(name: str) -> str:
    s = "".join(ch if ch.isalnum() or ch in "._" else "_" for ch in (name or ""))
    s = s.strip("_") or "unnamed"
    if s[0].isdigit():
        s = "m_" + s
    return s[:60]


def categorize(m: dict) -> tuple[str, int] | None:
    mid = (m.get("id") or "").lower()
    folder = m.get("folder") or ""
    group = (m.get("group") or "").lower()
    if group == "dtc" or mid.startswith("dtc_"):
        cat = DTC_FOLDERS.get(folder)
        if cat:
            return cat, 110
        return "dtc_other", 120
    for prefix, cat, rank in FAMILY_RULES:
        if mid.startswith(prefix):
            return cat, rank
    return None


def u16s(blob: bytes, off: int, n: int) -> list[int]:
    raw = blob[off : off + n * 2]
    if len(raw) < 2:
        return []
    return list(struct.unpack_from("<%dH" % (len(raw) // 2), raw))


def looks_ptr(vals: list[int]) -> bool:
    if len(vals) < 4:
        return False
    return sum(1 for v in vals[:8] if v in (0x8000, 0xA000, 0x0000)) >= 6


def ascii_safe(s: str) -> str:
    return (
        (s or "")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2026", "...")
        .encode("ascii", "replace")
        .decode("ascii")
    )


def probe_start(
    m: dict,
    golf: bytes,
    ori: bytes | None,
    cat: str,
    rank: int,
) -> dict | None:
    addr = int(m["addr"])
    if not (CAL0 <= addr < CAL1):
        return None
    ln = int(m.get("length") or 0)
    fp_hex = (m.get("fingerprint") or {}).get("hex") or ""
    # DTC / vmax scalars may be tiny
    probe_n = min(FP_N, max(ln, 2) if ln else FP_N)
    if fp_hex:
        try:
            fp_bytes = bytes.fromhex(fp_hex)
        except ValueError:
            fp_bytes = b""
    else:
        fp_bytes = b""
    if fp_bytes:
        probe_n = min(len(fp_bytes), FP_N, max(ln, len(fp_bytes)) if ln else FP_N)
        probe_n = max(probe_n, min(2, len(fp_bytes)))

    if addr + probe_n > len(golf):
        return None

    got = golf[addr : addr + probe_n]
    vals = u16s(golf, addr, min(16, probe_n // 2 or 1))
    uniq = len(set(vals)) if vals else len(set(got))
    ptr = looks_ptr(vals) if probe_n >= 8 else False
    sha = hashlib.sha256(got[: min(32, len(got))]).hexdigest()[:12]

    same_ori = False
    if ori is not None and addr + probe_n <= len(ori):
        same_ori = got == ori[addr : addr + probe_n]

    exact_fp = False
    if fp_bytes and len(fp_bytes) >= 2:
        n = min(len(fp_bytes), probe_n, len(got))
        exact_fp = got[:n] == fp_bytes[:n]

    # Relocate search: if start differs, scan cal for unique fingerprint
    relocated: int | None = None
    if not exact_fp and fp_bytes and len(fp_bytes) >= 16 and not ptr:
        needle = fp_bytes[: min(32, len(fp_bytes))]
        # only search if rare enough — count occurrences
        hits = []
        start = CAL0
        while True:
            i = golf.find(needle, start, CAL1)
            if i < 0:
                break
            hits.append(i)
            if len(hits) > 4:
                break
            start = i + 1
        if len(hits) == 1:
            relocated = hits[0]
            got = golf[relocated : relocated + probe_n]
            exact_fp = True
            addr = relocated
            same_ori = False

    conf = "low"
    notes: list[str] = []
    id_name = m.get("id") or ""

    # HIGH: exact atlas fingerprint (or unique relocate) at map START.
    # Torque/smoke plateaus often have low u16 diversity — fingerprint match
    # at the known atlas start is enough; do not demote for uniq.
    # Pointer-fill heuristic only blocks when there is NO fingerprint/ORI match.
    if exact_fp:
        if ln and ln <= 8:
            conf = "high"
            notes.append(
                "high: scalar/mask exact fp (%d bytes) folder=%s"
                % (probe_n, m.get("folder") or "")
            )
        else:
            conf = "high"
            notes.append(
                "high: atlas start fingerprint match cols=%s rows=%s src=atlas"
                % (m.get("cols"), m.get("rows"))
            )
            if uniq < 4:
                notes.append("note: low u16 diversity (plateau OK at known start)")
    elif same_ori and not ptr:
        conf = "high"
        notes.append("high: identical to ORI 9979 at same offset (no atlas fp)")
        if uniq < 4:
            notes.append("note: low u16 diversity (plateau OK vs ORI)")
    elif same_ori and ptr:
        conf = "medium"
        notes.append("medium: same as ORI but looks like ptr fill — comment only")
    else:
        conf = "low"
        notes.append("low: start differs from atlas/ORI fingerprint")
        if ptr:
            notes.append("looks_ptr")

    if relocated is not None:
        notes.append("relocated from atlas 0x%06X -> 0x%06X" % (int(m["addr"]), relocated))
    if same_ori:
        notes.append("identique vs ORI 9979")
    else:
        notes.append("differe de ORI 9979" if ori is not None else "ORI absent")
    notes.append("fp=%s uniq=%d len=%d" % (sha, uniq, ln or probe_n))

    return {
        "category": cat,
        "cat_rank": str(rank),
        "confidence": conf,
        "id_name": id_name,
        "family": family_id(id_name),
        "addr": "0x%06X" % addr,
        "winols": "0x%X" % addr,
        "ghidra": "0x%X" % (addr + FLASH80),
        "atlas_id": m.get("id") or "",
        "atlas_addr": m.get("addr_hex") or ("%X" % int(m["addr"])),
        "atlas_cols": str(m.get("cols") or ""),
        "atlas_rows": str(m.get("rows") or ""),
        "atlas_length": str(ln or ""),
        "folder": m.get("folder") or "",
        "group": m.get("group") or "",
        "same_9979": "1" if same_ori else "0",
        "exact_fp": "1" if exact_fp else "0",
        "new_name": ghidra_safe(family_id(id_name)) if conf == "high" else "",
        "delta": "0x0",
        "hub": "atlas_start",
        "notes": ascii_safe("; ".join(notes).replace(",", ";")),
        "relocated": "1" if relocated is not None else "0",
    }


def main() -> None:
    if not GOLF.exists():
        raise SystemExit("Golf fullflash not found: %s" % GOLF)
    golf = GOLF.read_bytes()
    ori_path = find_ori()
    ori = ori_path.read_bytes() if ori_path else None
    print("ORI:", ori_path or "NONE")

    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    maps = atlas.get("maps") or []

    rows: list[dict] = []
    counts: dict[str, int] = defaultdict(int)
    by_cat: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for m in maps:
        cat_info = categorize(m)
        if not cat_info:
            continue
        cat, rank = cat_info
        hit = probe_start(m, golf, ori, cat, rank)
        if not hit:
            continue
        rows.append(hit)
        counts[hit["confidence"]] += 1
        by_cat[cat][hit["confidence"]] += 1

    # Prefer HIGH over lower at same addr; prefer smaller cat_rank
    rows.sort(
        key=lambda r: (
            int(r["cat_rank"]),
            0 if r["confidence"] == "high" else 1 if r["confidence"] == "medium" else 2,
            int(r["addr"], 16),
        )
    )
    by_addr: dict[str, dict] = {}
    for r in rows:
        a = r["addr"].upper()
        if a not in by_addr:
            by_addr[a] = r
        else:
            old = by_addr[a]
            rank_new = {"high": 0, "medium": 1, "low": 2}[r["confidence"]]
            rank_old = {"high": 0, "medium": 1, "low": 2}[old["confidence"]]
            if rank_new < rank_old:
                by_addr[a] = r

    out_rows = list(by_addr.values())
    out_rows.sort(key=lambda r: (int(r["cat_rank"]), int(r["addr"], 16)))

    fields = [
        "category",
        "cat_rank",
        "confidence",
        "id_name",
        "family",
        "addr",
        "winols",
        "ghidra",
        "hub",
        "delta",
        "atlas_id",
        "atlas_addr",
        "atlas_cols",
        "atlas_rows",
        "atlas_length",
        "folder",
        "group",
        "same_9979",
        "exact_fp",
        "relocated",
        "new_name",
        "notes",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out_rows)

    high = [r for r in out_rows if r["confidence"] == "high"]
    lines = [
        "Golf 9980 atlas START identification (offline)",
        "HIGH = fingerprint/ORI match at map start — safe label candidate",
        "counts high=%d medium=%d low=%d unique=%d"
        % (
            sum(1 for r in out_rows if r["confidence"] == "high"),
            sum(1 for r in out_rows if r["confidence"] == "medium"),
            sum(1 for r in out_rows if r["confidence"] == "low"),
            len(out_rows),
        ),
        "",
        "addr      category          id_name",
        "-" * 72,
    ]
    for r in high:
        lines.append(
            "%s  %-16s  %s"
            % (r["addr"], r["category"], r["id_name"])
        )
    # weak families summary
    lines += ["", "=== by category (high/medium/low) ==="]
    for cat in sorted(by_cat.keys()):
        c = by_cat[cat]
        lines.append(
            "  %-16s  high=%d medium=%d low=%d"
            % (cat, c.get("high", 0), c.get("medium", 0), c.get("low", 0))
        )
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote", OUT_CSV)
    print("Wrote", OUT_TXT)
    print(
        "unique=%d high=%d medium=%d low=%d"
        % (
            len(out_rows),
            sum(1 for r in out_rows if r["confidence"] == "high"),
            sum(1 for r in out_rows if r["confidence"] == "medium"),
            sum(1 for r in out_rows if r["confidence"] == "low"),
        )
    )
    print("--- HIGH highlights ---")
    for want in (
        "clutch_prot",
        "rail",
        "duration",
        "tqlim",
        "speed_limiter",
        "dtc_dpf",
        "dtc_egr",
        "egr_control",
        "smoke",
        "turbo",
        "soi",
    ):
        hs = [r for r in high if r["category"] == want]
        print("  %s: %d" % (want, len(hs)))
        for r in hs[:5]:
            print("    %s  %s  same9979=%s" % (r["addr"], r["id_name"], r["same_9979"]))

    if GHIDRA_SCRIPTS.is_dir():
        dest = GHIDRA_SCRIPTS / OUT_CSV.name
        dest.write_bytes(OUT_CSV.read_bytes())
        dest2 = GHIDRA_SCRIPTS / OUT_TXT.name
        dest2.write_bytes(OUT_TXT.read_bytes())
        print("Copied ->", dest)


if __name__ == "__main__":
    main()
