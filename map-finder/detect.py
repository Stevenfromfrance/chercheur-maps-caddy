# -*- coding: utf-8 -*-
"""Detect PCR2.1 project family and pick the matching atlas."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ATLAS_DIR = ROOT / "atlas"

# Project stamp → family key used in atlas JSON
FAMILY_PREFIXES = (
    ("SM2G0LG", "SM2G0LG"),
    ("SM2G0P", "SM2G0P"),
    ("SM2G0M", "SM2G0M"),
    ("SM2F0", "SM2F0"),
    ("SM2E0", "SM2E0"),
    ("SM2G0", "SM2G0"),
)


def extract_soft_id(blob: bytes) -> dict:
    info: dict = {}
    if len(blob) < 0x181000:
        window = blob
        base = 0
    else:
        window = blob[0x180000:0x181000]
        base = 0x180000
    for pat, key in [
        (rb"SM2[A-Z0-9]{4,16}", "project"),
        (rb"CASM2[A-Z0-9]{2,10}", "cas"),
        (rb"03L906023[A-Z0-9]{0,4}", "hw"),
        (rb"CAY[A-Z0-9]{0,6}", "engine"),
    ]:
        m = re.search(pat, window)
        if m and key not in info:
            info[key] = m.group(0).decode("ascii", errors="ignore")
    m = re.search(rb"([0-9]{4})---\x00CAY", window)
    if m:
        info["soft_guess"] = m.group(1).decode("ascii")
    else:
        m = re.search(rb"([0-9]{4})---", window)
        if m:
            info["soft_guess"] = m.group(1).decode("ascii")
    info["_header_off"] = base
    return {k: v for k, v in info.items() if not str(k).startswith("_")}


def family_from_project(project: str | None) -> str | None:
    if not project:
        return None
    p = project.upper()
    for prefix, fam in FAMILY_PREFIXES:
        if p.startswith(prefix):
            return fam
    return None


def list_atlases() -> list[dict]:
    out = []
    if not ATLAS_DIR.exists():
        return out
    for path in sorted(ATLAS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        project = data.get("project") or ""
        family = data.get("family") or family_from_project(project) or path.stem
        out.append(
            {
                "path": path,
                "soft": str(data.get("soft") or path.stem),
                "family": family,
                "project": project,
                "hw": data.get("hw"),
                "maps": len(data.get("maps") or []),
            }
        )
    return out


def _probe_exact_hits(blob: bytes, atlas_path: Path, sample: int = 12) -> int:
    """Cheap score: how many sampled map payloads sit in this dump."""
    data = json.loads(atlas_path.read_text(encoding="utf-8"))
    maps = data.get("maps") or []
    hits = 0
    n = 0
    for m in maps:
        roles = m.get("roles") or []
        if not any(
            r in roles
            for r in ("stage1_core", "clutch_prot", "speed_limiter", "dtc_dpf", "dtc_egr")
        ):
            continue
        fp = (m.get("fingerprint") or {}).get("hex")
        if not fp:
            continue
        n += 1
        if blob.find(bytes.fromhex(fp)) >= 0:
            hits += 1
        if n >= sample:
            break
    return hits


def resolve_atlas(
    blob: bytes,
    explicit: Path | None = None,
) -> dict:
    """Return {path, atlas, identity, family, reason, auto}."""
    identity = extract_soft_id(blob)
    family = family_from_project(identity.get("project"))
    catalogs = list_atlases()
    if not catalogs and not explicit:
        raise SystemExit(f"No atlas in {ATLAS_DIR}")

    if explicit:
        path = Path(explicit)
        atlas = json.loads(path.read_text(encoding="utf-8"))
        return {
            "path": path,
            "atlas": atlas,
            "identity": identity,
            "family": family or atlas.get("family"),
            "reason": "manual --atlas",
            "auto": False,
        }

    # 1) exact soft match
    soft = identity.get("soft_guess")
    if soft:
        for c in catalogs:
            if c["soft"] == soft:
                atlas = json.loads(c["path"].read_text(encoding="utf-8"))
                return {
                    "path": c["path"],
                    "atlas": atlas,
                    "identity": identity,
                    "family": c["family"],
                    "reason": f"soft {soft} = atlas {c['path'].name}",
                    "auto": True,
                }

    # 2) family / project prefix
    if family:
        fam_hits = [c for c in catalogs if c["family"] == family]
        if fam_hits:
            # Prefer atlas whose project prefix matches longest
            fam_hits.sort(key=lambda c: len(c.get("project") or ""), reverse=True)
            c = fam_hits[0]
            atlas = json.loads(c["path"].read_text(encoding="utf-8"))
            return {
                "path": c["path"],
                "atlas": atlas,
                "identity": identity,
                "family": family,
                "reason": f"project {identity.get('project')} family {family} -> {c['path'].name}",
                "auto": True,
            }

    # 3) probe fingerprints across atlases
    if catalogs:
        scored = [( _probe_exact_hits(blob, c["path"]), c) for c in catalogs]
        scored.sort(key=lambda x: (x[0], x[1]["soft"] == "9979"), reverse=True)
        best_n, c = scored[0]
        atlas = json.loads(c["path"].read_text(encoding="utf-8"))
        why = f"fingerprint probe ({best_n} key-map hits) -> {c['path'].name}"
        if family and family not in {x["family"] for x in catalogs}:
            why = f"no atlas for family {family}; " + why
        return {
            "path": c["path"],
            "atlas": atlas,
            "identity": identity,
            "family": family or c["family"],
            "reason": why,
            "auto": True,
        }

    raise SystemExit("Could not resolve atlas")
