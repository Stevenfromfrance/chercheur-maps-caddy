"""
Reproduit la cale du document Onshape « cale final » et compare les cotes.

Référence manuelle :
https://cad.onshape.com/documents/5cc42b294eb99d49a3bb8a88/w/aa52e1d9f9b6ecfdf4680687/e/32ca01a3073e3a948ad21fb3

Le scan associé (Calle Rand d.png) est en ~300 DPI :
  902×923 px → 76.4×78.1 mm  ≈  bbox Onshape 75.0×78.1 mm  (±1 %)
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import cadquery as cq
from dotenv import load_dotenv
from onshape_client.client import Client

# --- Cotes mesurées sur le Part Studio Onshape (mm) ---
OUTER_W = 75.0
OUTER_H = 70.0          # corps hors oreilles (oreilles ajoutées à part)
THICKNESS = 12.1
CORNER_R = 6.0
LOBE_R = 7.1
HOLE_D = 6.28

# Trous principaux (centres relatifs au centre de la bbox Onshape)
HOLES = [
    (3.62, 32.04),     # haut (oreille)
    (-3.73, -31.87),   # bas (oreille)
    (-26.35, 10.15),   # gauche
    (26.25, -9.98),    # droite
]

# Petits trous coins (carré central / fixations) Ø5
CORNER_HOLES = [
    (-35.0, 27.5),
    (35.0, 27.5),
    (-35.0, -27.5),
    (35.0, -27.5),
]
CORNER_HOLE_D = 5.0

OUTPUT_STEP = Path(__file__).resolve().parent / "cale2_repro.step"
DOC_NAME = "Cale2 repro DPI compare"

# Référence Onshape (pour le tableau comparatif)
REF = {
    "outer_w": 75.0,
    "outer_h": 78.054,
    "thickness": 12.1,
    "hole_spacing_v": 63.91,
    "top_hole": (3.62, 32.04),
    "bot_hole": (-3.73, -31.87),
}


def build() -> cq.Workplane:
    body = (
        cq.Workplane("XY")
        .rect(OUTER_W, OUTER_H)
        .extrude(THICKNESS)
        .edges("|Z")
        .fillet(CORNER_R)
    )

    # Oreilles haut/bas uniquement (comme le scan)
    lobes = cq.Workplane("XY")
    for cx, cy in (HOLES[0], HOLES[1]):
        lobes = lobes.moveTo(cx, cy).circle(LOBE_R)
    body = body.union(lobes.extrude(THICKNESS))

    # Échancrure gauche simplifiée (taille d'après le trou gauche)
    # On retire un disque large côté gauche pour créer la taille
    waist = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .moveTo(-45, 5)
        .circle(22)
        .extrude(THICKNESS + 0.2)
    )
    body = body.cut(waist)

    # Trous principaux
    holes = cq.Workplane("XY").workplane(offset=-0.1)
    for cx, cy in HOLES:
        holes = holes.moveTo(cx, cy).circle(HOLE_D / 2)
    body = body.cut(holes.extrude(THICKNESS + 0.2))

    # Trous coins Ø5
    ch = cq.Workplane("XY").workplane(offset=-0.1)
    for cx, cy in CORNER_HOLES:
        ch = ch.moveTo(cx, cy).circle(CORNER_HOLE_D / 2)
    body = body.cut(ch.extrude(THICKNESS + 0.2))

    return body


def compare(part: cq.Workplane) -> None:
    bb = part.val().BoundingBox()
    print("\n=== COMPARAISON DIMENSIONS ===")
    rows = [
        ("Largeur hors-tout (mm)", REF["outer_w"], bb.xlen),
        ("Hauteur hors-tout (mm)", REF["outer_h"], bb.ylen),
        ("Épaisseur (mm)", REF["thickness"], bb.zlen),
        (
            "Entraxe trous H/B (mm)",
            REF["hole_spacing_v"],
            abs(HOLES[0][1] - HOLES[1][1]),
        ),
    ]
    print(f"{'Mesure':<28} {'Onshape':>10} {'Repro':>10} {'Écart%':>8}")
    for name, ref, got in rows:
        err = 100.0 * (got - ref) / ref if ref else 0
        print(f"{name:<28} {ref:10.3f} {got:10.3f} {err:7.2f}%")

    # Scan DPI
    print("\n=== SCAN Calle Rand d.png @ 300 DPI ===")
    print("Image 902×923 px → 76.37×78.15 mm")
    print("Bbox pièce scan     → ~76.20×77.98 mm")
    print(f"Écart scan vs Onshape largeur : {(76.20-75)/75*100:.2f}%")
    print(f"Écart scan vs Onshape hauteur : {(77.98-78.054)/78.054*100:.2f}%")


def upload(step: Path) -> str:
    load_dotenv()
    Client.singleton_instance = None
    client = Client(
        configuration={
            "base_url": os.getenv("ONSHAPE_BASE_URL"),
            "access_key": os.getenv("ONSHAPE_ACCESS_KEY"),
            "secret_key": os.getenv("ONSHAPE_SECRET_KEY"),
        },
        keys_file=None,
    )
    from onshape_client.oas.models.bt_document_params import BTDocumentParams

    doc = client.documents_api.create_document(
        BTDocumentParams(name=DOC_NAME, is_public=True)
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
    part = build()
    cq.exporters.export(part, str(OUTPUT_STEP))
    print(f"STEP écrit : {OUTPUT_STEP} ({OUTPUT_STEP.stat().st_size} o)")
    compare(part)
    upload(OUTPUT_STEP)


if __name__ == "__main__":
    main()
