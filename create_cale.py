"""
Génère une cale/joint identique à la photo (cadre carré + 4 oreilles + 4 trous + découpe centrale)
puis l'importe dans un nouveau document Onshape.

Cotes dérivées des proportions de la photo (échelle basée sur trous Ø5 mm).
Ajuste les constantes ci-dessous si tu as les cotes réelles au pied à coulisse.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import cadquery as cq
from dotenv import load_dotenv
from onshape_client.client import Client

# --- Cotes paramétriques (mm) ---
OUTER_SIDE = 68.0          # côté du carré principal (hors oreilles)
WALL = 7.5                 # épaisseur de paroi du cadre
LOBE_R = 9.0               # rayon des 4 oreilles
HOLE_D = 5.0               # diamètre des trous de fixation
CORNER_R = 4.0             # congé coins extérieurs
INNER_CORNER_R = 0.8       # coins intérieurs plus anguleux (comme la photo)
NOTCH_R = 2.2              # rayon des 2 encoches hautes (intérieur)
NOTCH_SPACING = 18.0       # entraxe des 2 encoches
THICKNESS = 2.0            # épaisseur de la cale

# Décalage des oreilles latérales (photo = symétrie 180°, PAS miroir 4 côtés)
# Oreille gauche vers le bas, oreille droite vers le haut (~37% du demi-côté)
LOBE_SIDE_OFFSET = 12.5
# Léger décalage des oreilles haut/bas (même symétrie 180°)
LOBE_TB_OFFSET = 4.5

OUTPUT_STEP = Path(__file__).resolve().parent / "cale_generee.step"
OUTPUT_SVG = Path(__file__).resolve().parent / "cale_generee_preview.svg"
DOC_NAME = "Cale generee v3 asym"


def lobe_centers(half: float):
    """Centres des 4 oreilles / trous — rotation 180° autour de l'origine."""
    return [
        (-LOBE_TB_OFFSET, half),                 # haut (légèrement à gauche)
        (LOBE_TB_OFFSET, -half),                 # bas (légèrement à droite)
        (half, LOBE_SIDE_OFFSET),                # droite (vers le haut)
        (-half, -LOBE_SIDE_OFFSET),              # gauche (vers le bas)
    ]


def build_cale() -> cq.Workplane:
    half = OUTER_SIDE / 2
    inner = OUTER_SIDE - 2 * WALL
    inner_half = inner / 2
    hole_r = HOLE_D / 2
    centers = lobe_centers(half)

    # Carré principal avec congés d'angle
    square = (
        cq.Workplane("XY")
        .rect(OUTER_SIDE, OUTER_SIDE)
        .extrude(THICKNESS)
        .edges("|Z")
        .fillet(CORNER_R)
    )

    # 4 oreilles (positions asymétriques = photo réelle)
    lobes = cq.Workplane("XY")
    for cx, cy in centers:
        lobes = lobes.moveTo(cx, cy).circle(LOBE_R)
    body = square.union(lobes.extrude(THICKNESS))

    # Découpe centrale
    cut = (
        cq.Workplane("XY")
        .workplane(offset=-0.1)
        .rect(inner, inner)
        .extrude(THICKNESS + 0.2)
        .edges("|Z")
        .fillet(INNER_CORNER_R)
    )
    # 2 encoches sur le bord intérieur haut
    notches = cq.Workplane("XY").workplane(offset=-0.1)
    for nx in (-NOTCH_SPACING / 2, NOTCH_SPACING / 2):
        notches = notches.moveTo(nx, inner_half).circle(NOTCH_R)
    body = body.cut(cut.union(notches.extrude(THICKNESS + 0.2)))

    # Trous de fixation au centre de chaque oreille
    holes = cq.Workplane("XY").workplane(offset=-0.1)
    for cx, cy in centers:
        holes = holes.moveTo(cx, cy).circle(hole_r)
    body = body.cut(holes.extrude(THICKNESS + 0.2))

    return body


def export_preview(part: cq.Workplane, path: Path) -> None:
    """Export SVG vue de dessus pour comparaison visuelle."""
    # Section / projection approximative : exporter les wires du face top
    try:
        exporters = cq.exporters
        exporters.export(part, str(path), exporters.ExportTypes.SVG)
        print(f"Preview SVG : {path}")
    except Exception as e:
        print(f"Preview SVG indisponible ({e})")


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
    """Crée un document Onshape et y importe le STEP. Retourne l'URL du document."""
    from onshape_client.oas.models.bt_document_params import BTDocumentParams

    print(f"Création du document Onshape « {DOC_NAME} »…")
    # Compte Free Onshape : documents publics uniquement
    doc = client.documents_api.create_document(
        BTDocumentParams(name=DOC_NAME, is_public=True)
    )
    dd = doc.to_dict()
    did = dd["id"]
    wid = dd["default_workspace"]["id"]
    print(f"Document créé did={did} wid={wid}")

    print("Import du STEP → Part Studio Onshape…")
    with open(step_path, "rb") as f:
        # Ne pas passer format_name : sinon Onshape stocke un blob
        # au lieu de créer un Part Studio éditable.
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
        f"Construction cale : outer={OUTER_SIDE} wall={WALL} lobeR={LOBE_R} "
        f"holeØ={HOLE_D} thickness={THICKNESS} mm"
    )
    part = build_cale()
    cq.exporters.export(part, str(OUTPUT_STEP))
    print(f"STEP écrit : {OUTPUT_STEP} ({OUTPUT_STEP.stat().st_size} octets)")
    export_preview(part, OUTPUT_SVG)

    client = make_client()
    url = upload_step_to_onshape(client, OUTPUT_STEP)
    print("Terminé.")
    print(url)


if __name__ == "__main__":
    main()
