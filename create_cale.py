"""
Génère une cale calée sur la version manuelle Onshape :
https://cad.onshape.com/documents/1949a3eff8d0532716c1e442/w/8fce890e626c947d8d8cd2db/e/4a013ce2f5e63c3c7caacd6b

Cotes mesurées via l'API (bbox + centres des trous).
Pour la prochaine pièce depuis un scan A4 : voir scan_scale.py
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import cadquery as cq
from dotenv import load_dotenv
from onshape_client.client import Client

# --- Cotes = version manuelle Onshape (mm) ---
OUTER_W = 27.643
OUTER_H = 23.814
THICKNESS = 5.0
HOLE_D = 2.52
LOBE_R = 3.6
CORNER_R = 2.5
INNER_W = 16.0
INNER_H = 13.0
INNER_CORNER_R = 1.2
NOTCH_R = 1.0
NOTCH_SPACING = 6.0

# Centres des trous / oreilles relatifs au centre de la bbox manuelle
# Symétrie 180° (haut-gauche / bas-droite, etc.)
HOLE_CENTERS = [
    (-3.657, 9.442),    # haut
    (11.306, 1.541),    # droite
    (3.728, -9.437),    # bas
    (-11.306, -1.535),  # gauche
]

OUTPUT_STEP = Path(__file__).resolve().parent / "cale_generee.step"
DOC_NAME = "Cale recalibree manuelle"


def build_cale() -> cq.Workplane:
    hole_r = HOLE_D / 2

    body = (
        cq.Workplane("XY")
        .rect(OUTER_W, OUTER_H)
        .extrude(THICKNESS)
        .edges("|Z")
        .fillet(CORNER_R)
    )

    lobes = cq.Workplane("XY")
    for cx, cy in HOLE_CENTERS:
        lobes = lobes.moveTo(cx, cy).circle(LOBE_R)
    body = body.union(lobes.extrude(THICKNESS))

    cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .rect(INNER_W, INNER_H)
        .extrude(THICKNESS + 0.2)
        .edges("|Z")
        .fillet(INNER_CORNER_R)
    )
    notches = cq.Workplane("XY").workplane(offset=-0.1)
    for nx in (-NOTCH_SPACING / 2, NOTCH_SPACING / 2):
        notches = notches.moveTo(nx, INNER_H / 2).circle(NOTCH_R)
    body = body.cut(cut.union(notches.extrude(THICKNESS + 0.2)))

    holes = cq.Workplane("XY").workplane(offset=-0.1)
    for cx, cy in HOLE_CENTERS:
        holes = holes.moveTo(cx, cy).circle(hole_r)
    body = body.cut(holes.extrude(THICKNESS + 0.2))

    return body


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


def upload_step_to_onshape(client: Client, step_path: Path) -> str:
    from onshape_client.oas.models.bt_document_params import BTDocumentParams

    print(f"Création du document Onshape « {DOC_NAME} »…")
    doc = client.documents_api.create_document(
        BTDocumentParams(name=DOC_NAME, is_public=True)
    )
    dd = doc.to_dict()
    did = dd["id"]
    wid = dd["default_workspace"]["id"]
    print(f"Document créé did={did} wid={wid}")

    print("Import du STEP → Part Studio Onshape…")
    with open(step_path, "rb") as f:
        translation = client.translation_api.create_translation(
            did,
            wid,
            file=f,
            store_in_document=True,
            notify_user=False,
            allow_faulty_parts=True,
            encoded_filename=step_path.name,
        )

    tid = translation.id
    print(f"Translation id={tid} état={translation.request_state}")
    deadline = time.time() + 600
    while time.time() < deadline:
        info = client.translation_api.get_translation(tid)
        print(f"  Statut : {info.request_state}")
        if info.request_state == "DONE":
            break
        if info.request_state == "FAILED":
            raise RuntimeError(f"Import STEP échoué : {info.to_dict()}")
        time.sleep(2)
    else:
        raise TimeoutError("Timeout import STEP")

    url = f"https://cad.onshape.com/documents/{did}/w/{wid}"
    print(f"Cale disponible : {url}")
    return url


def main():
    print(
        f"Cale manuelle : {OUTER_W}×{OUTER_H}×{THICKNESS} mm, "
        f"trous Ø{HOLE_D}, oreilles R={LOBE_R}"
    )
    part = build_cale()
    cq.exporters.export(part, str(OUTPUT_STEP))
    bb = part.val().BoundingBox()
    print(
        f"STEP {OUTPUT_STEP} ({OUTPUT_STEP.stat().st_size} o) "
        f"bbox {bb.xlen:.3f}×{bb.ylen:.3f}×{bb.zlen:.3f} mm"
    )

    client = make_client()
    url = upload_step_to_onshape(client, OUTPUT_STEP)
    print("Terminé.")
    print(url)


if __name__ == "__main__":
    main()
