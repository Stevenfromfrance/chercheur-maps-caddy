# -*- coding: utf-8 -*-
"""Decode MHH attachment dumps saved as CDP JSON (base64)."""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "mhh"


def filename_from_cd(cd: str, aid: str) -> str:
    m = re.search(r'filename="([^"]+)"', cd or "")
    if m:
        return m.group(1)
    return f"aid_{aid}.bin"


def decode_one(path: Path) -> Path:
    data = json.loads(path.read_text(encoding="utf-8"))
    v = data["result"]["value"]
    name = filename_from_cd(v.get("cd") or "", str(v.get("aid") or "unk"))
    raw = base64.b64decode(v["b64"])
    dest = OUT / name
    dest.write_bytes(raw)
    print(f"{v.get('aid')} -> {dest.name}  {len(raw)} bytes  magic={raw[:4]!r}")
    return dest


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for arg in sys.argv[1:]:
        decode_one(Path(arg))


if __name__ == "__main__":
    main()
