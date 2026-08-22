# -*- coding: utf-8 -*-
"""Rebuild PCR2.1 inventory from atlas/ + bins/ + phase2 reports."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas"
BINS = ROOT / "bins"
REPORTS = ROOT / "reports"

OLD = {"4875", "5249", "6927", "6929", "8790", "9971", "9972", "9979", "9980"}


def load_atlas(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    ident = data.get("identity") or {}
    counts = data.get("counts") or {}
    conf = counts.get("confidence") or {}
    return {
        "soft": str(data.get("soft") or path.stem),
        "family": data.get("family"),
        "project": data.get("project") or ident.get("project"),
        "hw": data.get("hw") or ident.get("hw"),
        "engine": ident.get("engine"),
        "ori_file": data.get("ori_file"),
        "flash_size": data.get("flash_size"),
        "maps": counts.get("maps"),
        "confidence": conf,
        "atlas": str(path.relative_to(ROOT)).replace("\\", "/"),
    }


def phase2_summary(soft: str) -> dict | None:
    p = REPORTS / f"{soft}-phase2.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    s = data.get("summary") or {}
    return {
        "atlas_soft": data.get("atlas_soft"),
        "any": s.get("hit_rate_any"),
        "exact": s.get("hit_rate_exact"),
        "total": s.get("total"),
    }


def main() -> None:
    rows = [load_atlas(p) for p in sorted(ATLAS.glob("*.json"))]
    for r in rows:
        r["phase2"] = phase2_summary(r["soft"])
        r["bank"] = "old" if r["soft"] in OLD else "new"

    js = {
        "unique_softs": len(rows),
        "old": sorted(OLD),
        "new": sorted(r["soft"] for r in rows if r["bank"] == "new"),
        "softs": rows,
    }
    (REPORTS / "pcr21-bin-inventory.json").write_text(
        json.dumps(js, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# PCR 2.1 / Continental SM2* — banque de softs",
        "",
        f"Généré localement. **{len(rows)} softs uniques** (9 avant + {len(js['new'])} ajoutés depuis Damos-Big-Archive / MHH).",
        "",
        "## Tous les softs",
        "",
        "| Soft | Banque | Famille | HW | Engine | Taille | Atlas | Phase2 any/exact |",
        "|------|--------|---------|----|--------|--------|-------|------------------|",
    ]
    for r in rows:
        p2 = r.get("phase2") or {}
        any_r = p2.get("any")
        exact_r = p2.get("exact")
        rate = "—"
        if any_r is not None:
            rate = f"{100*any_r:.1f}% / {100*(exact_r or 0):.1f}%"
        size = r.get("flash_size") or ""
        lines.append(
            f"| **{r['soft']}** | {r['bank']} | {r.get('family') or ''} | "
            f"{r.get('hw') or ''} | {r.get('engine') or ''} | {size} | "
            f"`{r['atlas']}` | {rate} |"
        )
    lines += [
        "",
        "## Softs ajoutés cette passe",
        "",
        ", ".join(f"`{s}`" for s in js["new"]),
        "",
        "Bins dans `map-finder/bins/{soft}-{hw}-{fam}.bin`. "
        "Plusieurs dumps archive sont **TUN** (EGR/DPF/Stage1) : utiles pour les adresses, "
        "pas comme ORI à flasher.",
        "",
        "### Notes",
        "",
        "- `4875` a maintenant un cal **2 Mo** (`4875-03L906023A-SM2E0DB-2MB.bin`) en plus du dump 1 Mo.",
        "- `0874` : stamp ECU `0874---` sur Touran 03L906023PH Exclusive (Stage1). Inhabituel, conservé.",
        "- `2527` : seule famille `SM2G0LG` (Touran PH).",
        "- `9977` : déjà dans `bins/` MHH, atlas créé maintenant.",
        "- Ibiza Stage1 `SM2G0P3` / 03L906023LC est aussi stamp **9980** — non ingéré pour ne pas écraser l’atlas Golf 9980.",
        "",
    ]
    (REPORTS / "pcr21-bin-inventory.md").write_text("\n".join(lines), encoding="utf-8")

    status = [
        "# PCR2.1 soft bank status",
        "",
        f"Source : `reports/pcr21-bin-inventory.json`. **{len(rows)} atlas.**",
        "",
        "| Soft | Atlas | Famille | HW | Note |",
        "|------|-------|---------|----|------|",
    ]
    notes = {r["soft"]: r for r in json.loads((REPORTS / "pcr21-archive-ingest.json").read_text(encoding="utf-8"))}
    for r in rows:
        n = (notes.get(r["soft"]) or {}).get("note") or ("banque initiale" if r["bank"] == "old" else "")
        status.append(
            f"| **{r['soft']}** | `{r['atlas']}` | {r.get('family') or ''} | {r.get('hw') or ''} | {n} |"
        )
    (REPORTS / "pcr21-soft-bank-status.md").write_text("\n".join(status), encoding="utf-8")
    print(f"{len(rows)} softs  new={js['new']}")
    print("wrote inventory md/json + status")


if __name__ == "__main__":
    main()
