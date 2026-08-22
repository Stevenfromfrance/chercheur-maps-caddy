# -*- coding: utf-8 -*-
"""Identify MHH PCR dumps and run Phase 2 Stage1 scan."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from detect import extract_soft_id  # noqa: E402

MHH = Path(__file__).resolve().parent / "mhh"
REPORTS = ROOT / "reports"


def iter_payloads() -> list[Path]:
    skip_ext = {".rar", ".zip", ".py"}
    out = []
    for p in MHH.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in skip_ext:
            continue
        if p.parent == MHH:
            continue
        out.append(p)
    return sorted(out)


def sniff(path: Path) -> dict:
    blob = path.read_bytes()
    ident = extract_soft_id(blob)
    magic = blob[:8]
    kind = "unknown"
    if blob[:4] == b"Rar!":
        kind = "rar"
    elif blob[:2] == b"PK":
        kind = "zip"
    elif b"<FLASH" in blob[:200] or blob[:3] == b"FRF" or path.suffix.lower() == ".frf" or b"ODX" in blob[:400]:
        kind = "frf-or-container"
    elif len(blob) == 2097152:
        kind = "cal-2mb"
    elif len(blob) > 0x100000:
        kind = "large-dump"
    # FRF often starts with XML
    if blob.lstrip()[:5] in (b"<?xml", b"<FLAS") or b"<DATABLOCK" in blob[:2000]:
        kind = "frf-xml"
    ident.update(
        {
            "path": str(path),
            "name": path.name,
            "size": len(blob),
            "kind": kind,
            "magic": magic.hex(),
        }
    )
    return ident


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = [sniff(p) for p in iter_payloads()]
    print("=== IDENTITY ===")
    for r in rows:
        print(
            f"{r['size']:8d}  {r.get('kind'):16s}  "
            f"soft={r.get('soft_guess','?'):6s}  "
            f"proj={r.get('project','?'):22s}  "
            f"hw={r.get('hw','?'):14s}  "
            f"{r['name']}"
        )
    (REPORTS / "mhh-bins-identity.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )

    to_scan = [r for r in rows if r["size"] >= 1_000_000 and r["kind"] not in ("frf-xml", "rar", "zip")]
    print("\n=== PHASE2 STAGE1 ===")
    for r in to_scan:
        src = Path(r["path"])
        soft = r.get("soft_guess") or "unk"
        out = REPORTS / f"mhh-{soft}-phase2.json"
        cmd = [
            sys.executable,
            str(ROOT / "scan_phase2.py"),
            str(src),
            "--pack",
            "stage1",
            "--json",
            str(out),
        ]
        print(" ".join(cmd))
        subprocess.run(cmd, cwd=str(ROOT), check=False)


if __name__ == "__main__":
    main()
