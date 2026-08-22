# -*- coding: utf-8 -*-
"""Find PCR2.1 dumps in Damos-Big-Archive and classify by soft ID."""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from detect import extract_soft_id, family_from_project  # noqa: E402

ARCHIVE = Path(r"D:\STEVEN\Damos-Big-Archive")
OUT = ROOT / "reports" / "_pcr21_archive_scan.json"

KNOWN = {"4875", "5249", "6927", "6929", "8790", "9971", "9972", "9979", "9980", "9977"}

NAME_HINTS = (
    "pcr2",
    "pcr 2",
    "sm2e",
    "sm2f",
    "sm2g",
    "03l906023",
    "03l99755",
    "cayc",
    "cayb",
    "caye",
    "caya",
    "1.6 tdi",
    "1.6tdi",
    "16tdi",
    "simos pcr",
    "simospcr",
)
SKIP_EXT = {
    ".a2l",
    ".hex",
    ".ols",
    ".kp",
    ".pdf",
    ".txt",
    ".html",
    ".xml",
    ".jpg",
    ".png",
    ".pdx",
    ".odx",
    ".csv",
    ".rar",
    ".zip",
    ".7z",
    ".exe",
    ".dll",
}
DUMP_EXT = {
    ".bin",
    ".ori",
    ".fls",
    ".mpc",
    ".mod",
    ".dkp",
    ".bcc",
    ".mhr",
    ".layton",
    "",
}
# typical PCR cal sizes
SIZES_OK = {2097152, 1048576, 1006592, 1044544, 2097152 + 131072}


def path_hint(rel: str) -> bool:
    low = rel.lower()
    return any(h in low for h in NAME_HINTS)


def looks_dump(name: str, size: int) -> bool:
    ext = Path(name).suffix.lower()
    if ext in SKIP_EXT:
        return False
    if size in SIZES_OK:
        return True
    if 900_000 <= size <= 2_200_000 and (ext in DUMP_EXT or ext == ""):
        return True
    return False


def ori_score(rel: str) -> int:
    low = rel.lower()
    score = 0
    if any(k in low for k in ("original", "orig", "(ori", "_ori", "flash_org", "flashorg", "orgig")):
        score += 5
    if "stage" in low or "tun" in low or "egr" in low or "dpf" in low:
        score -= 3
    if size_from_rel := 0:
        pass
    return score


def md5_file(path: Path, n: int = 2_097_152) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        h.update(f.read(n))
    return h.hexdigest()


def main() -> None:
    import json

    hits = []
    n_cand = 0
    n_read = 0
    for dirpath, dirnames, filenames in os.walk(ARCHIVE):
        rel_dir = os.path.relpath(dirpath, ARCHIVE)
        hinted = path_hint(rel_dir)
        for name in filenames:
            full = Path(dirpath) / name
            rel = str(Path(rel_dir) / name)
            try:
                size = full.stat().st_size
            except OSError:
                continue
            if not looks_dump(name, size):
                continue
            if not hinted and not path_hint(name):
                continue
            n_cand += 1
            try:
                blob = full.read_bytes()
            except OSError:
                continue
            n_read += 1
            ident = extract_soft_id(blob)
            proj = ident.get("project") or ""
            if not proj.startswith("SM2"):
                continue
            ident.update(
                {
                    "path": str(full),
                    "rel": rel,
                    "name": name,
                    "size": size,
                    "family": family_from_project(proj),
                    "md5": hashlib.md5(blob).hexdigest(),
                    "ori_score": ori_score(rel),
                    "known": ident.get("soft_guess") in KNOWN,
                }
            )
            hits.append(ident)

    hits.sort(key=lambda r: (r.get("soft_guess") or "zzzz", -r.get("ori_score", 0), -r["size"], r["rel"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"candidates": n_cand, "read": n_read, "pcr21": hits}, indent=2), encoding="utf-8")

    by_soft: dict[str, list] = {}
    for h in hits:
        by_soft.setdefault(h.get("soft_guess") or "?", []).append(h)

    print(f"candidates={n_cand} read={n_read} pcr21_hits={len(hits)} unique_softs={len(by_soft)}")
    print(f"wrote {OUT}")
    for soft, rows in sorted(by_soft.items(), key=lambda kv: kv[0]):
        best = rows[0]
        flag = "KNOWN" if best.get("known") else "NEW "
        print(
            f"  {flag}  {soft:6s}  n={len(rows):2d}  {best.get('project','?'):22s}  "
            f"{best.get('hw','?'):14s}  {best['size']:7d}  {best['name'][:70]}"
        )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
