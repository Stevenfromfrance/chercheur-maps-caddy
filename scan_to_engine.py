#!/usr/bin/env python3
"""
Pipeline scan 3D (STL mesh) → une pièce Onshape utilisable.

Objectif (phase 1)
------------------
À partir d'un scan type Minarelli HOR (STL importé dans Onshape), produire
**une seule pièce mesh nettoyée** que tu peaufines ensuite à la main
(pas de split carter G/D pour l'instant).

Ce que ce script automatise
---------------------------
1. Télécharge le STL source (blob Onshape ou fichier local)
2. Nettoie : garde le plus gros corps, jette les micro-fragments
3. (Option) Recalibre l'échelle avec UNE cote réelle connue
4. Décime (~80k faces par défaut) pour rester manipulable dans Onshape
5. Crée un document Onshape public + importe la pièce unique

Ce qui reste manuel (nécessaire pour un « vrai » moteur CAD)
------------------------------------------------------------
- Vérifier / corriger l'échelle (pied à coulisse sur 1 alésage connu)
- Reverse engineering paramétrique (sketches / extrudes) par-dessus le mesh
- Plus tard : séparer carter G / carter D, joints, alésages

Usage
-----
  # Depuis le document Minarelli (défaut) → doc Onshape prêt à peaufiner
  python scan_to_engine.py --upload

  # STL local déjà téléchargé
  python scan_to_engine.py --stl mina_scan/raw.stl --upload

  # Recalage échelle : l'axe Y du mesh doit faire 312 mm réels
  python scan_to_engine.py --stl mina_scan/raw.stl --scale-axis y --scale-mm 312 --upload

  # Seulement clean local (pas d'upload)
  python scan_to_engine.py --faces 120000
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import trimesh
from dotenv import load_dotenv

from onshape_http import api

# Document scan Minarelli (référence utilisateur)
DEFAULT_DID = "393e786d769846f9a2277f57"
DEFAULT_WID = "23b52a0fc2db5410b3057fe6"
DEFAULT_EID = "1561a4ef6b92ae7c09ccde9b"  # Part Studio MINARELLI HOR

OUT_DIR = Path(__file__).resolve().parent / "mina_scan"
AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def load_keys() -> tuple[str, str]:
    load_dotenv()
    ak = os.getenv("ONSHAPE_ACCESS_KEY")
    sk = os.getenv("ONSHAPE_SECRET_KEY")
    if not ak or not sk:
        raise SystemExit("Manque ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY dans .env")
    return ak, sk


def find_stl_blob(ak: str, sk: str, did: str, wid: str) -> tuple[str, str]:
    elems = api(ak, sk, f"/api/documents/d/{did}/w/{wid}/elements")
    blobs = [
        e
        for e in elems
        if e.get("elementType") == "BLOB"
        and "stl" in (e.get("name") or "").lower()
    ]
    if not blobs:
        raise RuntimeError("Aucun blob STL dans ce workspace")
    # Plusieurs blobs identiques possibles → on prend le premier
    e = blobs[0]
    return e["id"], e.get("name") or "scan.stl"


def download_stl(ak: str, sk: str, did: str, wid: str, out: Path) -> Path:
    eid, name = find_stl_blob(ak, sk, did, wid)
    print(f"Téléchargement blob STL {name} ({eid})…")
    raw = api(
        ak,
        sk,
        f"/api/blobelements/d/{did}/w/{wid}/e/{eid}",
        accept="*/*",
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    print(f"  → {out} ({len(raw) / 1e6:.1f} Mo)")
    return out


def clean_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    parts = mesh.split(only_watertight=False)
    if not parts:
        raise RuntimeError("Mesh vide après split")
    parts = sorted(parts, key=lambda p: len(p.faces), reverse=True)
    main = parts[0]
    junk = len(parts) - 1
    print(
        f"Corps principal : {len(main.faces)} faces / {len(main.vertices)} verts "
        f"(jetés {junk} fragments), watertight={main.is_watertight}"
    )
    print(f"  extents mm = {np.round(main.extents, 3).tolist()}")
    print(f"  volume mm³ = {float(main.volume) if main.is_watertight else 'n/a'}")
    return main


def apply_scale(
    mesh: trimesh.Trimesh, axis: str, target_mm: float
) -> tuple[trimesh.Trimesh, float]:
    idx = AXIS_INDEX[axis.lower()]
    current = float(mesh.extents[idx])
    if current <= 0:
        raise RuntimeError(f"Extent {axis} invalide : {current}")
    factor = target_mm / current
    mesh = mesh.copy()
    mesh.apply_scale(factor)
    print(
        f"Échelle ×{factor:.6f} (axis {axis}: {current:.3f} → {target_mm:.3f} mm)"
    )
    print(f"  new extents mm = {np.round(mesh.extents, 3).tolist()}")
    return mesh, factor


def decimate(mesh: trimesh.Trimesh, faces: int) -> trimesh.Trimesh:
    if len(mesh.faces) <= faces:
        print(f"Pas de décimation ({len(mesh.faces)} ≤ {faces})")
        return mesh
    print(f"Décimation {len(mesh.faces)} → ~{faces} faces…")
    t0 = time.time()
    out = mesh.simplify_quadric_decimation(face_count=faces)
    print(
        f"  → {len(out.faces)} faces en {time.time() - t0:.1f}s, "
        f"watertight={out.is_watertight}"
    )
    return out


def stl_for_onshape_meters(mesh_mm: trimesh.Trimesh, out_path: Path) -> Path:
    """Onshape interprète les coords STL comme des mètres.

    Nos scans / CadQuery travaillent en millimètres → on exporte un STL
    dont les nombres sont en mètres (×0.001) pour retomber sur la bonne taille.
    """
    m = mesh_mm.copy()
    m.apply_scale(0.001)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    m.export(out_path)
    print(
        f"STL Onshape (mètres) → {out_path} "
        f"extents_m={np.round(m.extents, 4).tolist()}"
    )
    return out_path


def upload_stl_to_onshape(stl_path: Path, doc_name: str) -> str:
    from onshape_client.client import Client
    from onshape_client.oas.models.bt_document_params import BTDocumentParams

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
    print(f"Création document Onshape « {doc_name} »…")
    doc = client.documents_api.create_document(
        BTDocumentParams(name=doc_name, is_public=True)
    )
    dd = doc.to_dict()
    did = dd["id"]
    wid = dd["default_workspace"]["id"]
    print(f"  did={did} wid={wid}")

    print(f"Import STL → Part Studio ({stl_path.name}, {stl_path.stat().st_size / 1e6:.1f} Mo)…")
    with open(stl_path, "rb") as f:
        translation = client.translation_api.create_translation(
            did,
            wid,
            file=f,
            store_in_document=True,
            notify_user=False,
            allow_faulty_parts=True,
            encoded_filename=stl_path.name,
        )
    tid = translation.id
    deadline = time.time() + 900
    while time.time() < deadline:
        info = client.translation_api.get_translation(tid)
        state = info.request_state
        print(f"  statut={state}")
        if state == "DONE":
            break
        if state == "FAILED":
            raise RuntimeError(f"Import STL échoué : {info.to_dict()}")
        time.sleep(3)
    else:
        raise TimeoutError("Timeout import STL")

    url = f"https://cad.onshape.com/documents/{did}/w/{wid}"
    print(f"Pièce disponible : {url}")
    return url


def write_meta(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2))
    print(f"Meta → {path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--did", default=DEFAULT_DID)
    p.add_argument("--wid", default=DEFAULT_WID)
    p.add_argument("--stl", type=Path, help="STL local (sinon download Onshape)")
    p.add_argument("--faces", type=int, default=80_000, help="Budget faces après décimation")
    p.add_argument("--scale-axis", choices=["x", "y", "z"], help="Axe à caler")
    p.add_argument("--scale-mm", type=float, help="Longueur réelle voulue sur cet axe (mm)")
    p.add_argument("--upload", action="store_true", help="Créer un doc Onshape avec la pièce")
    p.add_argument("--name", default="MINARELLI HOR — pièce unique (scan clean)")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    if (args.scale_axis is None) ^ (args.scale_mm is None):
        raise SystemExit("--scale-axis et --scale-mm doivent être fournis ensemble")

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.stl:
        raw_path = args.stl
        if not raw_path.exists():
            raise SystemExit(f"STL introuvable : {raw_path}")
    else:
        ak, sk = load_keys()
        raw_path = out_dir / "mina_raw.stl"
        if raw_path.exists() and raw_path.stat().st_size > 1_000_000:
            print(f"Réutilise STL local {raw_path}")
        else:
            download_stl(ak, sk, args.did, args.wid, raw_path)

    print(f"Chargement {raw_path}…")
    mesh = trimesh.load(raw_path, force="mesh")
    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError(f"Type mesh inattendu : {type(mesh)}")

    cleaned = clean_mesh(mesh)
    scale_factor = 1.0
    if args.scale_axis is not None:
        cleaned, scale_factor = apply_scale(cleaned, args.scale_axis, args.scale_mm)

    cleaned_path = out_dir / "mina_clean_full.stl"
    cleaned.export(cleaned_path)
    print(f"STL clean full → {cleaned_path} ({cleaned_path.stat().st_size / 1e6:.1f} Mo)")

    light = decimate(cleaned, args.faces)
    # Re-extraire le plus gros corps au cas où la décimation fragmente
    light = clean_mesh(light) if len(light.split(only_watertight=False)) > 1 else light
    light_path = out_dir / f"mina_piece_{len(light.faces)}.stl"
    light.export(light_path)
    print(f"STL pièce (mm) → {light_path} ({light_path.stat().st_size / 1e6:.1f} Mo)")

    onshape_stl = stl_for_onshape_meters(
        light, out_dir / f"mina_piece_{len(light.faces)}_meters.stl"
    )

    meta = {
        "source_stl": str(raw_path),
        "did": args.did,
        "wid": args.wid,
        "extents_mm": np.round(cleaned.extents, 4).tolist(),
        "bounds_mm": np.round(cleaned.bounds, 4).tolist(),
        "volume_mm3": float(cleaned.volume) if cleaned.is_watertight else None,
        "faces_clean": int(len(cleaned.faces)),
        "faces_piece": int(len(light.faces)),
        "watertight_clean": bool(cleaned.is_watertight),
        "watertight_piece": bool(light.is_watertight),
        "scale_factor": scale_factor,
        "scale_axis": args.scale_axis,
        "scale_mm": args.scale_mm,
        "piece_stl": str(light_path),
        "onshape_stl_meters": str(onshape_stl),
        "checklist": {
            "have_scan_stl": True,
            "mesh_cleaned": True,
            "scale_verified": bool(args.scale_mm),
            "onshape_piece_uploaded": False,
            "manual_refine_pending": True,
            "split_carter_gd_pending": True,
        },
        "still_needed_for_full_engine": [
            "1 cote réelle (pied à coulisse) pour --scale-mm",
            "Reverse CAD manuel (sketches) sur la pièce mesh",
            "Plus tard : plan de joint + carter G/D séparés",
            "Cotes fonctionnelles : alésage vilo, entraxe goujons, faces joint",
        ],
    }
    write_meta(out_dir / "pipeline_meta.json", meta)

    url = None
    if args.upload:
        url = upload_stl_to_onshape(onshape_stl, args.name)
        meta["onshape_url"] = url
        meta["checklist"]["onshape_piece_uploaded"] = True
        write_meta(out_dir / "pipeline_meta.json", meta)

    print("\n=== Résumé ===")
    print(f"Pièce locale (mm) : {light_path}")
    print(f"STL Onshape (m)   : {onshape_stl}")
    if url:
        print(f"Onshape           : {url}")
    if not args.scale_mm:
        print(
            "Échelle NON vérifiée — mesure une cote réelle puis relance avec "
            "--scale-axis y --scale-mm <valeur>"
        )


if __name__ == "__main__":
    main()
