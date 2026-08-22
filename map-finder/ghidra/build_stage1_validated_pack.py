# -*- coding: utf-8 -*-
"""Build curated Stage1 validated pack for Golf 9980 PCR2.1.

Uses:
  1) hub-grid identification (HIGH + best MEDIUM per family)
  2) atlas START fingerprint pass (identify_atlas_starts.py) — promotes
     clutch / rail / duration / vmax / DTC / smoke starts that hubs miss

Outputs:
  golf9980_stage1_validated.csv / .txt / .json
  ../reports/golf9980-stage1-validated.json
  ../a2l/PCR21_Golf9980_STAGE1_VALIDATED.a2l  (atlas dims when known)
  sync CSV/TXT/A2L to ghidra_scripts

Does not invent OEM names. Does not flash.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS = ROOT.parents[1]
ATLAS = WS / "map-finder" / "atlas" / "9979.json"
IN_CSV = ROOT / "golf9980_hub_grids_identified.csv"
ATLAS_STARTS = ROOT / "golf9980_atlas_starts_identified.csv"
OUT_CSV = ROOT / "golf9980_stage1_validated.csv"
OUT_TXT = ROOT / "golf9980_stage1_validated.txt"
OUT_JSON = WS / "map-finder" / "reports" / "golf9980-stage1-validated.json"
OUT_A2L = WS / "map-finder" / "a2l" / "PCR21_Golf9980_STAGE1_VALIDATED.a2l"
GHIDRA_SCRIPTS = Path(r"C:\Users\theda\ghidra_scripts")
FLASH80 = 0x80000000

# family prefix -> category for Stage1 atelier pack
CAT_PREFIXES: list[tuple[str, str, int]] = [
    ("accped", "AccPed", 10),
    ("tqlim_cluth", "clutch_prot", 20),
    ("tqlim_base", "tqlim", 30),
    ("tqlim_", "tqlim_other", 40),
    ("smoke_maf", "smoke_maf", 50),
    ("smoke_", "smoke", 55),
    ("turbo_base", "turbo", 60),
    ("turbo_int", "turbo_corr", 65),
    ("turbo_", "turbo_other", 70),
    ("rail_", "rail", 80),
    ("soi_", "soi", 90),
    ("duration_", "duration", 100),
    ("vmax", "speed_limiter", 110),
    ("airctl", "egr_control", 120),
    ("dtc_", "dtc", 130),
]

# Checklist: best MEDIUM families to surface after all HIGH
CHECKLIST_MED_CATS = (
    "clutch_prot",
    "rail",
    "duration",
    "soi",
    "smoke",
    "smoke_maf",
    "tqlim",
    "speed_limiter",
    "egr_control",
    "dtc",
)

CAT_ORDER = [
    "AccPed",
    "clutch_prot",
    "tqlim",
    "tqlim_other",
    "smoke",
    "smoke_maf",
    "turbo",
    "turbo_corr",
    "turbo_other",
    "rail",
    "soi",
    "duration",
    "speed_limiter",
    "egr_control",
    "dtc",
    "dtc_dpf",
    "dtc_egr",
    "dtc_egt",
    "dtc_egr_dpf",
    "dtc_egr_com",
    "dtc_dpf_o2",
    "dtc_other",
]


def family_id(name: str) -> str:
    """Strip CH_ / @addr only. Keep banque_NN and AccPed_trq4A intact."""
    s = re.sub(r"^CH_", "", name or "")
    s = re.sub(r"@.*$", "", s)
    return s


def categorize(idn: str, hint_cat: str | None = None) -> tuple[str, int] | None:
    # Prefer explicit category from atlas-start pass (dtc_dpf, speed_limiter, ...)
    if hint_cat:
        for prefix, cat, rank in CAT_PREFIXES:
            if hint_cat == cat:
                return cat, rank
        # dtc_* subcats not in CAT_PREFIXES ranks
        dtc_ranks = {
            "dtc_dpf": 131,
            "dtc_egr": 132,
            "dtc_egt": 133,
            "dtc_egr_dpf": 134,
            "dtc_egr_com": 135,
            "dtc_dpf_o2": 136,
            "dtc_other": 137,
            "speed_limiter": 110,
            "egr_control": 120,
        }
        if hint_cat in dtc_ranks:
            return hint_cat, dtc_ranks[hint_cat]
        if hint_cat in CAT_ORDER:
            return hint_cat, 50 + CAT_ORDER.index(hint_cat)
    f = family_id(idn).lower()
    for prefix, cat, rank in CAT_PREFIXES:
        if f.startswith(prefix):
            return cat, rank
    return None


def parse_delta(notes: str) -> int:
    m = re.search(r"\+\s*(0x[0-9A-Fa-f]+)", notes or "")
    if not m:
        # also accept delta=0xN in notes
        m = re.search(r"delta\s*=\s*(0x[0-9A-Fa-f]+)", notes or "", re.I)
    if not m:
        return 0x7FFFFFFF
    try:
        return int(m.group(1), 16)
    except ValueError:
        return 0x7FFFFFFF


def parse_map_start(notes: str) -> str:
    m = re.search(r"@0x([0-9A-Fa-f]+)", notes or "")
    return ("0x" + m.group(1).upper()) if m else ""


def ascii_safe(s: str) -> str:
    return (
        (s or "")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2026", "...")
        .encode("ascii", "replace")
        .decode("ascii")
    )


def conf_rank(c: str) -> int:
    c = (c or "").lower()
    if c == "high":
        return 0
    if c == "medium":
        return 1
    return 9


def a2l_ident(s: str, maxlen: int = 31) -> str:
    s = re.sub(r"[^A-Za-z0-9_]", "_", s or "")
    if not s or s[0].isdigit():
        s = "M_" + s
    return s[:maxlen]


def find_atlas_for_hit(atlas_maps: list[dict], idn: str, hit_addr: int) -> dict | None:
    """Prefer atlas instance containing hit_addr; else base family id; else any same family."""
    fam = family_id(idn)
    containing = [
        m
        for m in atlas_maps
        if family_id(m["id"]) == fam
        and int(m["addr"]) <= hit_addr <= int(m.get("end") or m["addr"])
    ]
    if containing:
        # prefer longest (tightest) instance, then exact id match
        containing.sort(key=lambda m: (-int(m.get("length") or 0), m["id"]))
        return containing[0]
    by_id = {m["id"]: m for m in atlas_maps}
    if idn in by_id:
        return by_id[idn]
    if fam in by_id:
        return by_id[fam]
    same = [m for m in atlas_maps if family_id(m["id"]) == fam]
    return same[0] if same else None


def row_from_hub(r: dict, atlas_maps: list[dict]) -> dict | None:
    idn = r.get("id_name") or ""
    cat = categorize(idn)
    if not cat:
        return None
    conf = (r.get("confidence") or "").lower()
    if conf not in ("high", "medium"):
        return None
    category, rank = cat
    addr = int(r["addr"], 16)
    out = dict(r)
    out["category"] = category
    out["cat_rank"] = str(rank)
    out["family"] = family_id(idn)
    out["delta_i"] = parse_delta(r.get("notes") or "")
    out["delta"] = "0x%X" % out["delta_i"] if out["delta_i"] != 0x7FFFFFFF else ""
    out["map_start"] = parse_map_start(r.get("notes") or "")
    out["winols"] = "0x%X" % addr
    out["ghidra"] = "0x%X" % (addr + FLASH80)
    out["same_9979"] = "1" if r.get("same_9979") == "1" else "0"
    out["notes"] = ascii_safe(r.get("notes") or "")
    out["confidence"] = conf
    out["source"] = "hub"
    am = find_atlas_for_hit(atlas_maps, idn, addr)
    if am and am.get("cols") and am.get("rows"):
        out["atlas_id"] = am["id"]
        out["atlas_addr"] = am.get("addr_hex") or ("%X" % int(am["addr"]))
        out["atlas_length"] = str(am.get("length") or "")
        out["atlas_cols"] = str(am.get("cols") or "")
        out["atlas_rows"] = str(am.get("rows") or "")
    else:
        out["atlas_id"] = ""
        out["atlas_addr"] = out["atlas_length"] = out["atlas_cols"] = out["atlas_rows"] = ""
    return out


def row_from_atlas_start(r: dict, atlas_maps: list[dict]) -> dict | None:
    idn = r.get("id_name") or ""
    hint = (r.get("category") or "").strip() or None
    cat = categorize(idn, hint_cat=hint)
    if not cat:
        return None
    conf = (r.get("confidence") or "").lower()
    if conf not in ("high", "medium"):
        return None
    category, rank = cat
    addr = int(r["addr"], 16)
    out = {
        "hub": r.get("hub") or "atlas_start",
        "fam_label": "",
        "addr": "0x%06X" % addr,
        "grid80": "0x%08X" % (addr + FLASH80),
        "id_name": idn,
        "new_name": r.get("new_name") or "",
        "confidence": conf,
        "notes": ascii_safe(r.get("notes") or ""),
        "call_site": "",
        "axis_x": "",
        "axis_y": "",
        "folder": r.get("folder") or "",
        "same_9979": "1" if r.get("same_9979") == "1" else "0",
        "family_id_re": "",
        "category": category,
        "cat_rank": str(rank),
        "family": family_id(idn),
        "delta_i": 0,
        "delta": "0x0",
        "map_start": "0x%06X" % addr,
        "winols": "0x%X" % addr,
        "ghidra": "0x%X" % (addr + FLASH80),
        "source": "atlas_start",
        "atlas_id": r.get("atlas_id") or idn,
        "atlas_addr": r.get("atlas_addr") or ("%X" % addr),
        "atlas_length": r.get("atlas_length") or "",
        "atlas_cols": r.get("atlas_cols") or "",
        "atlas_rows": r.get("atlas_rows") or "",
    }
    if not out["atlas_cols"] or not out["atlas_rows"]:
        am = find_atlas_for_hit(atlas_maps, idn, addr)
        if am and am.get("cols") and am.get("rows"):
            out["atlas_id"] = am["id"]
            out["atlas_addr"] = am.get("addr_hex") or ("%X" % int(am["addr"]))
            out["atlas_length"] = str(am.get("length") or "")
            out["atlas_cols"] = str(am.get("cols") or "")
            out["atlas_rows"] = str(am.get("rows") or "")
    return out


def main() -> None:
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    atlas_maps: list[dict] = atlas.get("maps") or []
    atlas_by_id = {m["id"]: m for m in atlas_maps}

    candidates: list[dict] = []
    hub_rows = list(csv.DictReader(IN_CSV.open(newline="", encoding="utf-8")))
    for r in hub_rows:
        out = row_from_hub(r, atlas_maps)
        if out:
            candidates.append(out)

    n_atlas = 0
    if ATLAS_STARTS.exists():
        for r in csv.DictReader(ATLAS_STARTS.open(newline="", encoding="utf-8")):
            out = row_from_atlas_start(r, atlas_maps)
            if out:
                candidates.append(out)
                n_atlas += 1
        print("Merged atlas-start rows:", n_atlas)
    else:
        print("WARN: missing", ATLAS_STARTS.name, "- hub-only pack")

    # Best row per (family, cal addr): prefer HIGH, then smaller delta, then same_9979
    # Prefer atlas_start (delta 0) over hub mid-map when confidence equal
    candidates.sort(
        key=lambda r: (
            int(r["cat_rank"]),
            conf_rank(r.get("confidence") or ""),
            r["delta_i"],
            0 if r.get("source") == "atlas_start" else 1,
            0 if r.get("same_9979") == "1" else 1,
            int(r["addr"], 16),
        )
    )

    # Dedup: one row per cal address (best already first)
    by_addr: dict[str, dict] = {}
    for r in candidates:
        a = r["addr"].upper()
        if a not in by_addr:
            by_addr[a] = r

    # Best HIGH per family
    best_high_family: dict[str, dict] = {}
    for r in candidates:
        if (r.get("confidence") or "").lower() != "high":
            continue
        fam = r["family"]
        if fam not in best_high_family:
            best_high_family[fam] = r

    # Best MEDIUM per family (for checklist / A2L confidence tag)
    best_med_family: dict[str, dict] = {}
    for r in candidates:
        if (r.get("confidence") or "").lower() != "medium":
            continue
        fam = r["family"]
        if fam not in best_med_family:
            best_med_family[fam] = r

    validated = list(by_addr.values())
    validated.sort(
        key=lambda r: (
            int(r["cat_rank"]),
            conf_rank(r.get("confidence") or ""),
            r["delta_i"],
            int(r["addr"], 16),
        )
    )
    for i, r in enumerate(validated, 1):
        r["rank"] = str(i)

    fields = [
        "rank",
        "category",
        "confidence",
        "id_name",
        "family",
        "winols",
        "ghidra",
        "hub",
        "delta",
        "map_start",
        "same_9979",
        "source",
        "atlas_id",
        "atlas_addr",
        "atlas_cols",
        "atlas_rows",
        "atlas_length",
        "folder",
        "fam_label",
        "call_site",
        "notes",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(validated)

    by_cat: dict[str, list] = defaultdict(list)
    for r in validated:
        by_cat[r["category"]].append(r)

    high_rows = [r for r in validated if r["confidence"] == "high"]
    med_checklist: list[dict] = []
    seen_fam: set[str] = set()
    for r in validated:
        if r["confidence"] != "medium":
            continue
        if r["category"] not in CHECKLIST_MED_CATS:
            continue
        fam = r["family"]
        if fam in seen_fam:
            continue
        seen_fam.add(fam)
        med_checklist.append(r)

    lines = [
        "Golf 9980 - Stage1 VALIDATED pack (auto)",
        "Source: hub grids + atlas START fingerprints vs atlas 9979 / A2L",
        "HIGH = rename OK (skip AccPed if already labeled) | MEDIUM = comment only",
        "",
        "counts: unique_addrs=%d  high=%d  medium=%d"
        % (
            len(validated),
            sum(1 for r in validated if r["confidence"] == "high"),
            sum(1 for r in validated if r["confidence"] == "medium"),
        ),
        "",
        "=== CHECKLIST: HIGH (all) ===",
        "  conf   Ghidra      WinOLS     category      id_name",
    ]
    for r in high_rows:
        lines.append(
            "  %-6s %-10s %-10s %-13s %s"
            % (
                r["confidence"],
                r["ghidra"].replace("0x", ""),
                r["winols"].replace("0x", ""),
                r["category"],
                r["id_name"],
            )
        )
    lines += [
        "",
        "=== CHECKLIST: best MEDIUM per family (clutch/rail/duration/soi/smoke/tqlim/vmax) ===",
        "  conf   Ghidra      WinOLS     category      id_name  delta",
    ]
    for r in med_checklist:
        lines.append(
            "  %-6s %-10s %-10s %-13s %s  %s"
            % (
                r["confidence"],
                r["ghidra"].replace("0x", ""),
                r["winols"].replace("0x", ""),
                r["category"],
                r["id_name"],
                r.get("delta") or "",
            )
        )
    lines.append("")

    for cat in CAT_ORDER:
        rs = by_cat.get(cat) or []
        if not rs:
            continue
        lines.append("=== %s (%d) ===" % (cat, len(rs)))
        lines.append("  conf   Ghidra      WinOLS     id_name                  atlas")
        for r in rs[:12]:
            dims = ""
            if r.get("atlas_cols") and r.get("atlas_rows"):
                dims = "%sx%s" % (r["atlas_cols"], r["atlas_rows"])
            lines.append(
                "  %-6s %-10s %-10s %-24s %s"
                % (
                    r["confidence"],
                    r["ghidra"].replace("0x", ""),
                    r["winols"].replace("0x", ""),
                    r["id_name"][:24],
                    dims,
                )
            )
        if len(rs) > 12:
            lines.append("  ... +%d more" % (len(rs) - 12))
        lines.append("")

    lines += [
        "Ghidra one-shot: NameHubStage1Validated.py (CSV next to script)",
        "CSV: %s" % OUT_CSV.name,
        "A2L validated: %s" % OUT_A2L.name,
        "Do not flash.",
    ]
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # JSON for site
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "title": "PCR2.1 Golf 9980 - Stage1 maps validees",
        "soft": "9980",
        "atlas_ref": "9979",
        "warning_fr": (
            "Reverse / identification hub. HIGH = IdName probable solide. "
            "MEDIUM = pointeur dans la map (pas forcement le debut). Ne pas flasher."
        ),
        "addr_rule_fr": "WinOLS 1CF9C0 -> Ghidra 801CF9C0 (prefixe 80)",
        "counts": {
            "unique_addrs": len(validated),
            "high": sum(1 for r in validated if r["confidence"] == "high"),
            "medium": sum(1 for r in validated if r["confidence"] == "medium"),
            "by_category": {
                k: {
                    "total": len(v),
                    "high": sum(1 for r in v if r["confidence"] == "high"),
                    "medium": sum(1 for r in v if r["confidence"] == "medium"),
                }
                for k, v in by_cat.items()
            },
        },
        "categories": {
            cat: [
                {
                    "rank": int(r["rank"]),
                    "confidence": r["confidence"],
                    "id_name": r["id_name"],
                    "winols": r["winols"],
                    "ghidra": r["ghidra"],
                    "hub": r.get("hub"),
                    "delta": r.get("delta"),
                    "same_9979": r.get("same_9979") == "1",
                    "atlas_id": r.get("atlas_id") or None,
                    "atlas_cols": r.get("atlas_cols") or None,
                    "atlas_rows": r.get("atlas_rows") or None,
                }
                for r in by_cat[cat]
            ]
            for cat in CAT_ORDER
            if by_cat.get(cat)
        },
        "checklist": [
            {
                "ghidra": r["ghidra"].replace("0x", ""),
                "winols": r["winols"].replace("0x", ""),
                "id_name": r["id_name"],
                "confidence": r["confidence"],
                "category": r["category"],
                "delta": r.get("delta") or "",
                "atlas_cols": r.get("atlas_cols") or None,
                "atlas_rows": r.get("atlas_rows") or None,
            }
            for r in (high_rows + med_checklist)
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    n_a2l = write_validated_a2l(
        validated,
        atlas_maps,
        atlas_by_id,
        best_high_family,
        best_med_family,
    )

    print("Wrote", OUT_CSV)
    print("Wrote", OUT_TXT)
    print("Wrote", OUT_JSON)
    print("Wrote", OUT_A2L)
    print(
        "unique=%d high=%d medium=%d a2l=%d cats=%s"
        % (
            len(validated),
            payload["counts"]["high"],
            payload["counts"]["medium"],
            n_a2l,
            {k: v["total"] for k, v in payload["counts"]["by_category"].items()},
        )
    )

    if GHIDRA_SCRIPTS.is_dir():
        for src in (OUT_CSV, OUT_TXT, OUT_A2L):
            if src.exists():
                dest = GHIDRA_SCRIPTS / src.name
                shutil.copy2(src, dest)
                print("Copied ->", dest)


def write_validated_a2l(
    validated: list[dict],
    atlas_maps: list[dict],
    atlas_by_id: dict,
    best_high: dict,
    best_med: dict,
) -> int:
    """ASAP2: one CHARACTERISTIC per atlas map instance for Stage1 hit families.

    Prefer families with at least one HIGH hit; also include best MEDIUM families
    that have atlas cols/rows. Emit ALL atlas instances (base + @addr) with dims.
    """
    hit_families: dict[str, dict] = {}
    for fam, r in best_high.items():
        hit_families[fam] = r
    for fam, r in best_med.items():
        if fam not in hit_families:
            hit_families[fam] = r
    # also any validated row whose family was not in best_* (edge)
    for r in validated:
        fam = r["family"]
        if fam not in hit_families:
            hit_families[fam] = r

    entries: list[tuple[dict, dict]] = []  # (atlas_map, hit_row)
    used_addrs: set[int] = set()
    for am in atlas_maps:
        if not am.get("cols") or not am.get("rows"):
            continue
        fam = family_id(am["id"])
        if fam not in hit_families:
            continue
        # skip Stage1-irrelevant atlas families that share prefix accidentally: none
        a2l_addr = int(am["addr"])
        if a2l_addr in used_addrs:
            continue
        used_addrs.add(a2l_addr)
        entries.append((am, hit_families[fam]))

    # Sort by category rank then address
    def sort_key(pair: tuple[dict, dict]):
        am, r = pair
        return (int(r.get("cat_rank") or 999), int(am["addr"]), am["id"])

    entries.sort(key=sort_key)

    lines = [
        "ASAP2_VERSION 1 60",
        "/*",
        " * PCR2.1 Golf SW 9980 - STAGE1 VALIDATED subset",
        " * Addresses = atlas 9979 map START (WinOLS offset). Dims from atlas.",
        " * One CHARACTERISTIC per atlas instance for Stage1 hit families.",
        " * NOT Continental OEM. Do not flash.",
        " */",
        '/begin PROJECT PCR21_Golf9980_STAGE1 "RE Stage1 validated 9980 - NOT OEM"',
        '/begin MODULE PCR21_SM2G0P_9980_S1 "Stage1 validated maps only"',
        "",
    ]
    used_names: set[str] = set()
    n = 0
    for am, r in entries:
        cols, rows = int(am["cols"]), int(am["rows"])
        a2l_addr = int(am["addr"])
        raw = a2l_ident(am["id"], 31)
        name = raw
        if name in used_names:
            # disambiguate with addr suffix
            suffix = "_%X" % a2l_addr
            name = a2l_ident(am["id"], 31 - len(suffix)) + suffix
        used_names.add(name)
        desc = ascii_safe(
            "%s %s hub=%s hit=0x%X atlas=%s"
            % (
                r.get("confidence") or "?",
                r.get("category") or "?",
                r.get("hub") or "?",
                int(r["addr"], 16),
                am["id"],
            )
        )[:80]
        if rows > 1 and cols > 1:
            lines += [
                '/begin CHARACTERISTIC %s "%s" MAP 0x%X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0 %d %d'
                % (name, desc, a2l_addr, cols, rows),
                '  FORMAT "%%5.0"',
                "/end CHARACTERISTIC",
                "",
            ]
        else:
            npts = max(cols, rows, 2)
            lines += [
                '/begin CHARACTERISTIC %s "%s" CURVE 0x%X RL_IDENTITY 0 NO_INPUT_QUANTITY 1.0 %d'
                % (name, desc, a2l_addr, npts),
                '  FORMAT "%%5.0"',
                "/end CHARACTERISTIC",
                "",
            ]
        n += 1
    lines += [
        "/end MODULE",
        "/end PROJECT",
        "",
    ]
    OUT_A2L.parent.mkdir(parents=True, exist_ok=True)
    OUT_A2L.write_text("\n".join(lines), encoding="ascii", errors="replace")
    print("A2L characteristics:", n)
    return n


if __name__ == "__main__":
    main()
