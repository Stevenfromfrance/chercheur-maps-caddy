# -*- coding: utf-8 -*-
"""Copy new PCR2.1 softs from Damos-Big-Archive into bins/, scan, export atlas."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from detect import extract_soft_id, family_from_project  # noqa: E402

BINS = ROOT / "bins"
REPORTS = ROOT / "reports"
ATLAS = ROOT / "atlas"

# Best dump per NEW (or upgraded) soft. Prefer ORI / original when available.
PICKS = [
    {
        "soft": "2527",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Touran 1.6 TDI CR EGR off Sw SM2G0LG0 Hw 03L906023PH\WinOLS (VW Touran ( egr off_disconnect ) as - SM2G0LG0)",
        "note": "TUN EGR-off Touran SM2G0LG0 (seul dump)",
    },
    {
        "soft": "0874",
        "src": str(BINS / r"_extracted_pcr_rars\VW_Touran_1.6 TDI CR_PCR2.1_03L906023PH_stage1_nodpf_noegr\VW_Touran_1.6 TDI CR_PCR2.1_03L906023PH_stage1_nodpf_noegr.bin"),
        "note": "TUN Stage1 Touran Exclusive 03L906023PH SM2F0L95 (SW stamp 0874)",
    },
    {
        "soft": "4881",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Golf 6 1.6 TDI Stage 1 Sw SM2E0DB000000 Hw 03L906023AN PCR2.1\03L906620AN.v1.bin",
        "note": "TUN Stage1 Golf SM2E0DB 03L906023AN",
    },
    {
        "soft": "5687",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Polo 1.6 TDI DPF off Sw SM2E0DG000000 Hw 03L906023G PCR 2.1\flash_org",
        "note": "TUN DPF-off Polo (fichier flash_org = même md5 que dpf-off)",
    },
    {
        "soft": "5697",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\Skoda\Octavia 1.6 TDI CR Sw SM2E0DG Hw 03L906023AG\WinOLS (Skoda Octavia (Original) - SM2E0DG000000)",
        "note": "ORI Octavia SM2E0DG 03L906023AG",
    },
    {
        "soft": "5862",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\VAG\VAG pcr2.1\03L906023A_03L906023A_5862_CAYB_(Orig).bin",
        "note": "ORI CAYB 03L906023A",
    },
    {
        "soft": "5863",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Golf 6 1.6 TDI DPF off EGR off Sw SM2E0DG000000 Hw 03L906023A\CAYC ORIGINAL.bin",
        "note": "ORI CAYC (dossier DPF mais bin ORIGINAL distinct)",
    },
    {
        "soft": "6302",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Golf 6 1.6 TDI DPF off EGR off Sw SM2F0K3000000 Hw 03L906023DQ\flash_org",
        "note": "probable ORI Golf 03L906023DQ (md5 != tun)",
    },
    {
        "soft": "8799",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\Skoda\Octavia 1.6 TDI EGR off Sw SM2F0L950 Hw 03L906023NF\orgigflash",
        "note": "TUN EGR-off Octavia (orgigflash = même md5 que egr-off)",
    },
    {
        "soft": "8843",
        "src": str(BINS / r"_extracted_pcr_rars\VW Golf 6 1.6 TDI CR Siemens PCR2.1-03L906023MS  SM2F0L9500000 EGR OFF\VW Golf 6 1.6 TDI CR Siemens PCR2.1-03L906023MS  SM2F0L9500000 EGR OFF.bin"),
        "note": "TUN EGR-off Golf 03L906023MS Exclusive",
    },
    {
        "soft": "8866",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Golf 6 1.6 TDI EGR off Sw SM2F0L9500000 Hw 03L906023MM\fhasorg",
        "note": "TUN EGR-off Golf 03L906023MM",
    },
    {
        "soft": "9970",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Polo 1.6 TDI Stage 2 Sw SM2G0M Hw 03L906023G PCR 2.1\flash_orginal_77kw_105pk",
        "note": "probable ORI Polo 03L906023G SM2G0M",
    },
    {
        "soft": "9973",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Passat 1.6 TDI EGR off Sw SM2G0M0000000 Hw 03L906023FS PCR2.1\Passat 1.6 TDI EGR off Sw SM2G0M0000000 Hw 03L906023FS PCR2.1",
        "note": "TUN EGR-off Passat 03L906023FS",
    },
    {
        "soft": "9977",
        "src": str(BINS / "9977-03L906023N-SM2G0P.bin"),
        "note": "MHH déjà en bins, atlas manquant",
        "skip_copy": True,
    },
    {
        "soft": "9978",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\VAG\VAG simos pcr2.1\VAG simos pcr2.1",
        "note": "cal 2MB unlabeled SM2G0P 03L906023AR",
    },
    {
        "soft": "9983",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Tuning DPF EGR off files\VW\Golf 6 1.6 TDI Stage 1 EGR off Sw SM2G0P2000000 Hw 03L997557M   PCR 2.1\03L997557M.Bin",
        "note": "TUN Stage1+EGR Golf 03L997557M",
    },
    {
        "soft": "4875",
        "src": r"D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\VAG\VAG SIMOS_PCR2.1\dalibor golf 6 90 hp",
        "dest_name": "4875-03L906023A-SM2E0DB-2MB.bin",
        "note": "upgrade 1MB -> 2MB Golf 90hp SM2E0DB",
    },
]


def dest_name(ident: dict, override: str | None = None) -> str:
    if override:
        return override
    soft = ident.get("soft_guess") or "unk"
    hw = ident.get("hw") or "nohw"
    fam = family_from_project(ident.get("project")) or (ident.get("project") or "SM2")[:8]
    return f"{soft}-{hw}-{fam}.bin"


def run(cmd: list[str]) -> int:
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, cwd=str(ROOT))
    return r.returncode


def main() -> None:
    BINS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    ingested = []
    for pick in PICKS:
        src = Path(pick["src"])
        if not src.exists():
            print("MISSING", pick["soft"], src)
            continue
        blob = src.read_bytes()
        ident = extract_soft_id(blob)
        soft = pick["soft"]
        if ident.get("soft_guess") and ident["soft_guess"] != soft:
            print(f"WARN {soft}: extract_soft_id={ident.get('soft_guess')} (on garde le stamp fichier)")
        name = dest_name(ident, pick.get("dest_name"))
        dest = BINS / name
        if not pick.get("skip_copy"):
            if dest.resolve() != src.resolve():
                shutil.copy2(src, dest)
                print(f"COPY {soft} -> {dest.name}  {len(blob)}  {ident}")
        else:
            dest = src
            print(f"KEEP {soft} {dest.name}  {ident}")

        report = REPORTS / f"{soft}-phase2.json"
        atlas_out = ATLAS / f"{soft}.json"
        rc1 = run(
            [
                sys.executable,
                str(ROOT / "scan_phase2.py"),
                str(dest),
                "--pack",
                "stage1",
                "--json",
                str(report),
            ]
        )
        rc2 = 1
        if report.exists():
            rc2 = run(
                [
                    sys.executable,
                    str(ROOT / "export_atlas_family.py"),
                    "--ori",
                    str(dest),
                    "--report",
                    str(report),
                    "--soft",
                    soft,
                    "--out",
                    str(atlas_out),
                ]
            )
        ingested.append(
            {
                "soft": soft,
                "dest": str(dest),
                "size": len(blob),
                "identity": ident,
                "family": family_from_project(ident.get("project")),
                "note": pick["note"],
                "phase2_ok": rc1 == 0,
                "atlas_ok": rc2 == 0,
                "atlas": str(atlas_out) if atlas_out.exists() else None,
            }
        )

    out = REPORTS / "pcr21-archive-ingest.json"
    out.write_text(json.dumps(ingested, indent=2), encoding="utf-8")
    print(f"\nIngested {len(ingested)} -> {out}")
    for row in ingested:
        print(
            f"  {row['soft']:6s}  {row['family'] or '?':8s}  "
            f"phase2={row['phase2_ok']} atlas={row['atlas_ok']}  {row['note'][:60]}"
        )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
