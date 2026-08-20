# -*- coding: utf-8 -*-
"""Filter hub-grid MEDIUM hits to Stage1-related atlas roles.

Reads golf9980_hub_grids_identified.csv + atlas/9979.json role_index / map roles.
MEDIUM = pointer INSIDE a known map (not unique start) - IdName is zone/family,
not always exact map origin. No rename; comment-only workflow.

Outputs (sorted by Stage1 usefulness):
  golf9980_hub_grids_MEDIUM_stage1.csv
  golf9980_hub_grids_MEDIUM_stage1.txt
  ../reports/golf9980-medium-stage1.json

Does not invent OEM names. Does not flash. Does not rename AccPed.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WS = ROOT.parents[1]
ATLAS = WS / "map-finder" / "atlas" / "9979.json"
PACKS = WS / "map-finder" / "packs.json"
IN_CSV = ROOT / "golf9980_hub_grids_identified.csv"
OUT_CSV = ROOT / "golf9980_hub_grids_MEDIUM_stage1.csv"
OUT_TXT = ROOT / "golf9980_hub_grids_MEDIUM_stage1.txt"
OUT_JSON = WS / "map-finder" / "reports" / "golf9980-medium-stage1.json"
GHIDRA_SCRIPTS = Path(r"C:\Users\theda\ghidra_scripts")

# Pack stage1 + related atelier packs (limiter / clutch for launch+hardcut)
STAGE1_ROLES = frozenset({"stage1_core", "stage1_support"})
RELATED_ROLES = frozenset({"clutch_prot", "speed_limiter"})
KEEP_ROLES = STAGE1_ROLES | RELATED_ROLES

# Lower score = more useful for Stage1 torque climb (ACE/V1 style)
FAMILY_RANK: list[tuple[str, int]] = [
    ("accped", 10),
    ("tqlim_base", 20),
    ("smoke_map", 30),
    ("smoke_maf", 35),
    ("smoke_", 40),
    ("turbo_base", 50),
    ("turbo_atm", 55),
    ("turbo_int", 60),
    ("turbo_", 65),
    ("rail_", 70),
    ("nm2iq", 80),
    ("tqlim_cluth", 90),
    ("tqlim_speed", 95),
    ("tqlim_tegt", 100),
    ("tqlim_", 110),
    ("vmax", 120),
    ("airctl", 130),
    ("soi_", 200),
]


def family_id(name: str) -> str:
    s = re.sub(r"^CH_", "", name or "")
    s = re.sub(r"@.*$", "", s)
    s = re.sub(r"_\d+$", "", s)
    return s


def fam_rank(idn: str) -> int:
    f = family_id(idn).lower()
    for prefix, score in FAMILY_RANK:
        if f.startswith(prefix):
            return score
    return 500


def role_rank(roles: set[str]) -> int:
    if "stage1_core" in roles:
        return 0
    if "clutch_prot" in roles:
        return 1
    if "speed_limiter" in roles:
        return 2
    if "stage1_support" in roles:
        return 3
    return 9


def parse_delta(notes: str) -> int:
    m = re.search(r"\+(\s*0x[0-9A-Fa-f]+)", notes or "")
    if not m:
        return 0x7FFFFFFF
    try:
        return int(m.group(1).strip(), 16)
    except ValueError:
        return 0x7FFFFFFF


def parse_uniq(notes: str) -> int:
    m = re.search(r"uniq_u16=(\d+)", notes or "")
    return int(m.group(1)) if m else 0


def parse_map_start(notes: str) -> str:
    m = re.search(r"@0x([0-9A-Fa-f]+)", notes or "")
    return ("0x" + m.group(1).upper()) if m else ""


def ascii_safe(s: str) -> str:
    """Strip curly dashes etc. so Jython NameHub scripts stay ASCII-safe."""
    return (
        (s or "")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2026", "...")
        .replace("\u00a0", " ")
    )


def load_id_roles() -> dict[str, set[str]]:
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    out: dict[str, set[str]] = defaultdict(set)
    for m in atlas.get("maps") or []:
        mid = m.get("id") or ""
        roles = set(m.get("roles") or [])
        if mid:
            out[mid] |= roles
            out[family_id(mid)] |= roles
    for role, ids in (atlas.get("role_index") or {}).items():
        for i in ids or []:
            out[i].add(role)
            out[family_id(i)].add(role)
    return out


def row_roles(row: dict, id_roles: dict[str, set[str]]) -> set[str]:
    idn = row.get("id_name") or ""
    roles: set[str] = set()
    roles |= id_roles.get(idn, set())
    roles |= id_roles.get(family_id(idn), set())
    return roles


def usefulness_key(row: dict) -> tuple:
    roles = set((row.get("roles") or "").split("|")) - {""}
    return (
        fam_rank(row.get("id_name") or ""),
        role_rank(roles),
        parse_delta(row.get("notes") or ""),
        -parse_uniq(row.get("notes") or ""),
        int(row.get("addr") or "0", 16),
        row.get("hub") or "",
    )


def main() -> None:
    if not IN_CSV.exists():
        raise SystemExit("missing %s" % IN_CSV)
    id_roles = load_id_roles()
    packs = json.loads(PACKS.read_text(encoding="utf-8")) if PACKS.exists() else {}

    all_rows = list(csv.DictReader(IN_CSV.open(newline="", encoding="utf-8")))
    medium = [r for r in all_rows if (r.get("confidence") or "").lower() == "medium"]

    kept: list[dict] = []
    for r in medium:
        roles = row_roles(r, id_roles)
        hit = roles & KEEP_ROLES
        if not hit:
            continue
        out = dict(r)
        out["roles"] = "|".join(sorted(hit))
        out["family"] = family_id(r.get("id_name") or "")
        out["delta"] = "0x%X" % parse_delta(r.get("notes") or "")
        out["map_start"] = parse_map_start(r.get("notes") or "")
        out["uniq_u16"] = str(parse_uniq(r.get("notes") or ""))
        out["usefulness"] = "%d" % fam_rank(r.get("id_name") or "")
        if "notes" in out:
            out["notes"] = ascii_safe(out.get("notes") or "")
        kept.append(out)

    kept.sort(key=usefulness_key)

    fields = [
        "rank",
        "hub",
        "addr",
        "grid80",
        "id_name",
        "family",
        "roles",
        "folder",
        "delta",
        "map_start",
        "uniq_u16",
        "usefulness",
        "same_9979",
        "call_site",
        "axis_x",
        "axis_y",
        "fam_label",
        "family_id_re",
        "notes",
    ]
    for i, r in enumerate(kept, 1):
        r["rank"] = str(i)

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)

    # Dedup by cal addr for top list (best usefulness wins)
    by_addr: dict[str, dict] = {}
    for r in kept:
        a = r["addr"]
        if a not in by_addr:
            by_addr[a] = r

    top_addrs = list(by_addr.values())  # already usefulness-sorted via kept order
    by_fam = Counter(r["family"] for r in kept)
    by_role = Counter()
    for r in kept:
        for role in (r.get("roles") or "").split("|"):
            if role:
                by_role[role] += 1

    lines = [
        "Golf 9980 hub grids - MEDIUM x Stage1 (atlas 9979)",
        "Filtre: roles stage1_core / stage1_support (+ clutch_prot / speed_limiter)",
        "",
        "=== Qu'est-ce que MEDIUM ? ===",
        "Le pointeur hub tombe DANS l'etendue d'une map A2L/atlas connue,",
        "mais PAS au debut (souvent delta > ~0x40) et sans empreinte unique de start.",
        "- IdName = famille / zone probable, PAS forcement l'origine exacte de la map.",
        "- Ne PAS renommer auto (surtout AccPed). Commentaire plate seulement.",
        "- Verifier a la main dans Ghidra les 15-20 premiers (Ctrl+G adresse).",
        "",
        "counts: medium_total=%d  stage1_related=%d  unique_addrs=%d"
        % (len(medium), len(kept), len(by_addr)),
        "par role: " + ", ".join("%s=%d" % x for x in by_role.most_common()),
        "par famille (top): "
        + ", ".join("%s=%d" % x for x in by_fam.most_common(12)),
        "",
        "=== Top candidats (addr unique, tri utilite Stage1) ===",
        "rank  addr      id_name                        hub  delta   roles",
        "-" * 78,
    ]
    for i, r in enumerate(top_addrs[:25], 1):
        lines.append(
            "%2d    %s  %-30s  %-3s  %-6s  %s"
            % (
                i,
                r["addr"],
                (r.get("id_name") or "")[:30],
                r.get("hub") or "",
                r.get("delta") or "",
                r.get("roles") or "",
            )
        )
    lines += [
        "",
        "Pourquoi MEDIUM (ex. rang 1): pointe DANS map_start+delta - pas le debut.",
        "Script commentaires: NameHubMediumStage1.py (aucun rename).",
        "CSV: %s" % OUT_CSV.name,
        "JSON site: map-finder/reports/golf9980-medium-stage1.json",
    ]
    OUT_TXT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # JSON for chercheur site (static load later)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "title": "Golf 9980 hub MEDIUM × Stage1",
        "soft_ref": "9979",
        "target": "Golf 9980 fullflash hubs",
        "confidence": "medium",
        "warning_fr": (
            "MEDIUM = pointeur a l'interieur d'une map connue, pas le debut unique. "
            "IdName = famille/zone probable - verifier manuellement dans Ghidra. "
            "Commentaires seulement, pas de rename AccPed."
        ),
        "packs": packs.get("packs", {}).get("stage1"),
        "roles_kept": sorted(KEEP_ROLES),
        "counts": {
            "medium_total": len(medium),
            "stage1_related": len(kept),
            "unique_addrs": len(by_addr),
            "by_role": dict(by_role),
            "by_family": dict(by_fam.most_common()),
        },
        "top": [
            {
                "rank": i,
                "addr": r["addr"],
                "grid80": r.get("grid80"),
                "id_name": r.get("id_name"),
                "family": r.get("family"),
                "hub": r.get("hub"),
                "roles": (r.get("roles") or "").split("|"),
                "folder": r.get("folder"),
                "delta": r.get("delta"),
                "map_start": r.get("map_start"),
                "why": "MEDIUM: inside known map (not unique start)",
            }
            for i, r in enumerate(top_addrs[:40], 1)
        ],
        "candidates": [
            {
                "rank": int(r["rank"]),
                "addr": r["addr"],
                "grid80": r.get("grid80"),
                "id_name": r.get("id_name"),
                "family": r.get("family"),
                "hub": r.get("hub"),
                "roles": (r.get("roles") or "").split("|"),
                "folder": r.get("folder"),
                "delta": r.get("delta"),
                "map_start": r.get("map_start"),
                "uniq_u16": int(r.get("uniq_u16") or 0),
                "same_9979": r.get("same_9979") == "1",
                "call_site": r.get("call_site"),
                "notes": r.get("notes"),
            }
            for r in kept
        ],
    }
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("Wrote", OUT_CSV)
    print("Wrote", OUT_TXT)
    print("Wrote", OUT_JSON)
    print(
        "medium=%d kept=%d unique_addr=%d"
        % (len(medium), len(kept), len(by_addr))
    )
    print("--- top 15 unique addr ---")
    for i, r in enumerate(top_addrs[:15], 1):
        print(
            "%2d %s %-28s hub=%-2s delta=%-6s %s"
            % (
                i,
                r["addr"],
                r.get("id_name") or "",
                r.get("hub") or "",
                r.get("delta") or "",
                r.get("roles") or "",
            )
        )

    if GHIDRA_SCRIPTS.is_dir():
        for src in (OUT_CSV, OUT_TXT):
            dest = GHIDRA_SCRIPTS / src.name
            dest.write_bytes(src.read_bytes())
            print("Copied ->", dest)


if __name__ == "__main__":
    main()
