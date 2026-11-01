"""
Compare / twin de la cale Onshape « cale final ».

Référence :
https://cad.onshape.com/documents/5cc42b294eb99d49a3bb8a88/w/aa52e1d9f9b6ecfdf4680687/e/32ca01a3073e3a948ad21fb3

Ce script :
1. Mesure le scan Calle Rand d.png @ 300 DPI vs la bbox Onshape
2. Exporte le STEP exact du Part Studio (même géométrie / mêmes cotes)
3. Le réimporte dans un nouveau document pour contrôle

IMPORTANT : ne pas « inventer » le profil (échancrure, arcs). Une approx
CadQuery simplifiée déforme la pièce (comme la version orange ratée).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from onshape_client.client import Client
from onshape_client.oas.models.bt_document_params import BTDocumentParams
from onshape_client.oas.models.bt_translate_format_params import BTTranslateFormatParams
from PIL import Image

REF_DID = "5cc42b294eb99d49a3bb8a88"
REF_WID = "aa52e1d9f9b6ecfdf4680687"
REF_EID = "32ca01a3073e3a948ad21fb3"
SCAN = Path(__file__).resolve().parent / "cmp_cale2_scan.png"
OUT_STEP = Path(__file__).resolve().parent / "cale2_exact.step"


def make_client() -> Client:
    load_dotenv()
    Client.singleton_instance = None
    return Client(
        configuration={
            "base_url": os.getenv("ONSHAPE_BASE_URL"),
            "access_key": os.getenv("ONSHAPE_ACCESS_KEY"),
            "secret_key": os.getenv("ONSHAPE_SECRET_KEY"),
        },
        keys_file=None,
    )


def compare_scan_to_onshape(client: Client) -> None:
    bb = client.part_studios_api.get_part_studio_bounding_boxes(
        REF_DID, "w", REF_WID, REF_EID
    )
    b = bb.to_dict()
    ow = (b["high_x"] - b["low_x"]) * 1000
    oh = (b["high_y"] - b["low_y"]) * 1000
    ot = (b["high_z"] - b["low_z"]) * 1000
    print("\n=== Onshape référence ===")
    print(f"  hors-tout : {ow:.3f} × {oh:.3f} × {ot:.3f} mm")

    if SCAN.exists():
        im = Image.open(SCAN)
        dpi = (im.info.get("dpi") or (300, 300))[0]
        mpp = 25.4 / float(dpi)
        sw, sh = im.size[0] * mpp, im.size[1] * mpp
        print(f"\n=== Scan {SCAN.name} @ {dpi:.0f} DPI ===")
        print(f"  image     : {sw:.3f} × {sh:.3f} mm")
        print(f"  écart W   : {(sw - ow) / ow * 100:.2f}%")
        print(f"  écart H   : {(sh - oh) / oh * 100:.2f}%")
    else:
        print("(scan local absent — skip comparaison DPI)")


def export_exact_step(client: Client) -> Path:
    print("\nExport STEP exact depuis Onshape…")
    params = BTTranslateFormatParams(
        format_name="STEP",
        store_in_document=False,
        notify_user=False,
        destination_name="cale2_exact",
    )
    tr = client.part_studios_api.create_part_studio_translation(
        REF_DID, "w", REF_WID, REF_EID, params
    )
    while True:
        info = client.translation_api.get_translation(tr.id)
        print(" ", info.request_state)
        if info.request_state in ("DONE", "FAILED"):
            break
        time.sleep(2)
    if info.request_state != "DONE":
        raise RuntimeError(info.to_dict())
    fid = info.result_external_data_ids[0]
    resp = client.documents_api.download_external_data(
        REF_DID, fid, _preload_content=False
    )
    OUT_STEP.write_bytes(resp.data)
    print(f"STEP écrit : {OUT_STEP} ({OUT_STEP.stat().st_size} o)")
    return OUT_STEP


def reimport(client: Client, step: Path) -> str:
    doc = client.documents_api.create_document(
        BTDocumentParams(name="Cale2 EXACT export (meme cotes)", is_public=True)
    )
    dd = doc.to_dict()
    did, wid = dd["id"], dd["default_workspace"]["id"]
    with open(step, "rb") as f:
        tr = client.translation_api.create_translation(
            did,
            wid,
            file=f,
            store_in_document=True,
            notify_user=False,
            allow_faulty_parts=True,
            encoded_filename=step.name,
        )
    while True:
        info = client.translation_api.get_translation(tr.id)
        print("import", info.request_state)
        if info.request_state in ("DONE", "FAILED"):
            break
        time.sleep(2)
    if info.request_state != "DONE":
        raise RuntimeError(info.to_dict())
    url = f"https://cad.onshape.com/documents/{did}/w/{wid}"
    print(url)
    return url


def main():
    client = make_client()
    compare_scan_to_onshape(client)
    step = export_exact_step(client)
    reimport(client, step)


if __name__ == "__main__":
    main()
