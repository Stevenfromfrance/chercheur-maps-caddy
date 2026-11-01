#!/usr/bin/env python3
"""
Rétro-ingénierie B-Rep du carter (phase 1) : le scan reste un calque,
on crée des solides paramétriques propres (plans → esquisses → extrusions).

Méthode (comme en Onshape UI) :
  1. Plan de référence = bride admission (normale + d depuis pose cale user / mesh)
  2. Esquisse idéale : contour bride + 4 trous coins + 2 oreilles + lumière centrale
  3. Extrusion solide (pad d'appui propre, trous cylindriques parfaits)
  4. Publish ENSEMBLE : mesh calque + B-Rep + calle vl14 (pose USER, pas +X)

Limite assumée : Onshape ne convertit pas le mesh→B-Rep ; on génère le B-Rep
en CadQuery puis on l'importe STEP à côté du mesh.

Usage :
  python reverse_carter_brep.py --upload
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from dotenv import load_dotenv

import flatten_from_user_cale as fuc

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"
REF_PATH = ROOT / "cale_admission_ref.json"
POSE_PATH = ROOT / "user_cale_pose.json"
REPORT_PATH = ROOT / "refine_carter_report.json"
USER_DOC = fuc.USER_DOC


def basis_from_normal(n: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = n / (np.linalg.norm(n) + 1e-12)
    a = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = np.cross(a, n)
    x /= np.linalg.norm(x) + 1e-12
    y = np.cross(n, x)
    return x, y


def load_flange_frame(pose: dict, ref: dict, mesh: trimesh.Trimesh):
    """Plan bride : priorité rapport refine, sinon recalcul pose user."""
    if REPORT_PATH.exists():
        rep = json.loads(REPORT_PATH.read_text())
        fp = rep.get("flange_plane") or {}
        if fp.get("normal") is not None:
            n = np.array(fp["normal"], float)
            d = float(fp["d_mm"])
            center = np.array(fp["center_mm"], float)
            gap = float(rep.get("gap_cale_to_mesh_mm") or 0)
            return n, d, center, gap

    M = np.array(pose["transform_rowmajor"], float).reshape(4, 4)
    holes_local = fuc.detect_cale_holes_local(OUT / "cale_aligned.stl")
    holes_world = ((M[:3, :3] @ (holes_local / 1000.0).T).T + M[:3, 3]) * 1000.0
    n_hint = M[:3, :3] @ np.array([1.0, 0.0, 0.0])
    n_hint /= np.linalg.norm(n_hint)
    return fuc.flange_from_user_pose(mesh, holes_world, n_hint)


def holes_on_plane(pose: dict, ref: dict, n: np.ndarray, d: float) -> list[dict]:
    out = []
    for h, spec in zip(pose.get("corner_holes_world_mm") or [], ref["corner_holes_xy_mm"]):
        c = np.asarray(h, float)
        c = c - n * ((c @ n) - d)
        out.append({"kind": "corner", "center": c, "diameter": float(spec["diameter"])})
    for h, spec in zip(pose.get("ear_holes_world_mm") or [], ref["ear_holes_xy_mm"]):
        c = np.asarray(h, float)
        c = c - n * ((c @ n) - d)
        out.append({"kind": "ear", "center": c, "diameter": float(spec["diameter"])})
    return out


def build_intake_flange_brep(
    n: np.ndarray,
    center: np.ndarray,
    holes: list[dict],
    ref: dict,
    *,
    thickness_mm: float = 8.0,
    port_diameter_mm: float = 43.0,
) -> cq.Workplane:
    """
    Esquisse idéale sur le plan bride + extrusion solide.
    Contour ≈ taille cale (68×78) ; trous = cotes vl14 ; lumière ≈ Ø43.
    Extrusion vers l'intérieur du carter (-normale sortante).
    """
    n = n / (np.linalg.norm(n) + 1e-12)
    xdir, ydir = basis_from_normal(n)

    def to2(p: np.ndarray) -> tuple[float, float]:
        q = p - center
        return float(q @ xdir), float(q @ ydir)

    # Orientation du rectangle : axes principaux du patron de trous
    uv = np.array([to2(h["center"]) for h in holes], float)
    # PCA 2D pour aligner le pad sur le patron
    uv0 = uv - uv.mean(0)
    _, _, vh = np.linalg.svd(uv0, full_matrices=False)
    a0, a1 = vh[0], vh[1]
    # dimensions cale
    w = float(ref["size_mm"]["x"])  # 68.2
    h = float(ref["size_mm"]["y"])  # 78.3
    # s'assurer que le plus grand côté suit le plus grand span des trous
    span0 = float(np.ptp(uv0 @ a0))
    span1 = float(np.ptp(uv0 @ a1))
    if span0 < span1:
        a0, a1 = a1, a0
        w, h = h, w

    # CadQuery plane with xDir = a0 in world
    x_world = a0[0] * xdir + a0[1] * ydir
    x_world /= np.linalg.norm(x_world) + 1e-12
    # origin = flange center on plane
    plane = cq.Plane(
        origin=cq.Vector(float(center[0]), float(center[1]), float(center[2])),
        normal=cq.Vector(float(n[0]), float(n[1]), float(n[2])),
        xDir=cq.Vector(float(x_world[0]), float(x_world[1]), float(x_world[2])),
    )

    def to_plane2(p: np.ndarray) -> tuple[float, float]:
        """Coords in CadQuery plane local 2D."""
        # Plane local: x along xDir, y = normal × xDir
        y_world = np.cross(n, x_world)
        y_world /= np.linalg.norm(y_world) + 1e-12
        q = p - center
        return float(q @ x_world), float(q @ y_world)

    wp = cq.Workplane(plane)
    # Contour rectangle idéalisé (légèrement plus grand que la cale pour l'appui)
    pad_w, pad_h = w + 2.0, h + 2.0
    solid = wp.rect(pad_w, pad_h).extrude(-abs(thickness_mm))

    # Trous cylindriques (cut through)
    centers2 = [to_plane2(h["center"]) for h in holes]
    diams = [h["diameter"] for h in holes]
    # Port central
    centers2.append((0.0, 0.0))
    diams.append(port_diameter_mm)

    cut_wp = cq.Workplane(plane)
    for (u, v), dia in zip(centers2, diams):
        cut_wp = (
            cut_wp.moveTo(u, v)
            .circle(dia / 2.0)
            .moveTo(0, 0)  # reset for next? better separate faces
        )
    # Build cuts one by one for reliability
    result = solid
    for (u, v), dia in zip(centers2, diams):
        hole = (
            cq.Workplane(plane)
            .transformed(offset=cq.Vector(0, 0, 0.5))  # start slightly outside
            .moveTo(u, v)
            .circle(dia / 2.0)
            .extrude(-(abs(thickness_mm) + 2.0))
        )
        result = result.cut(hole)

    return result


def export_step(shape: cq.Workplane, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path))
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stl", default=str(OUT / "mina_piece_80000.stl"))
    ap.add_argument("--thickness", type=float, default=8.0, help="épaisseur pad bride mm")
    ap.add_argument("--port", type=float, default=43.0, help="Ø lumière admission mm")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument(
        "--name",
        default="MINARELLI reverse B-Rep bride + mesh + calle — ENSEMBLE",
    )
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    ref = json.loads(REF_PATH.read_text())
    pose = json.loads(POSE_PATH.read_text())
    M = np.array(pose["transform_rowmajor"], float).reshape(4, 4)

    print("=== reverse_carter_brep (rétro-ingénierie) ===")
    print("Pose cale USER (ne pas recentrer):", USER_DOC)
    print(
        "Méthode: plan réf → esquisse idéale → extrusion solide "
        "(scan = calque mesh, pas de mesh→B-Rep Onshape)"
    )

    mesh = trimesh.load(args.stl, force="mesh")
    n, d, center, gap = load_flange_frame(pose, ref, mesh)
    print(f"Plan bride: n={n} d={d:.3f} center={center} gap_cale≈{gap:.1f} mm")

    holes = holes_on_plane(pose, ref, n, d)
    print(f"Trous esquisse: {len(holes)}")
    for h in holes:
        print(f"  {h['kind']:7s} Ø{h['diameter']:.3f} @ {h['center'].round(2)}")

    print("Construction B-Rep pad admission…")
    solid = build_intake_flange_brep(
        n, center, holes, ref, thickness_mm=args.thickness, port_diameter_mm=args.port
    )
    step_path = OUT / "carter_intake_flange_brep.step"
    export_step(solid, step_path)
    # also STL preview
    cq.exporters.export(solid, str(OUT / "carter_intake_flange_brep.stl"))
    bb = solid.val().BoundingBox()
    print(
        f"STEP → {step_path}  bbox mm "
        f"{bb.xlen:.1f}×{bb.ylen:.1f}×{bb.zlen:.1f}"
    )

    # Bake cale user pose
    cale_src = OUT / "cale_aligned.step"
    if not cale_src.exists():
        cale_src = OUT / "cale_admission.step"
    cale_baked = OUT / "cale_user_pose.step"
    fuc.bake_cale_with_user_transform(cale_src, M, cale_baked)

    meta = {
        "method": "reverse_engineering_brep_intake_flange",
        "user_doc": USER_DOC,
        "workflow": [
            "1. Plan de référence = bride (normale/d mesh sous cale user)",
            "2. Esquisse idéale (rect + cercles) — pas le bruit du scan",
            "3. Extrusion solide CadQuery → STEP",
            "4. Mesh scan gardé comme calque dans l'ensemble",
            "5. Cale pose USER préservée (pas côté roulement +X)",
        ],
        "flange_plane": {
            "normal": n.tolist(),
            "d_mm": d,
            "center_mm": center.tolist(),
        },
        "gap_cale_to_mesh_mm": gap,
        "holes": [
            {
                "kind": h["kind"],
                "diameter_mm": h["diameter"],
                "center_mm": h["center"].tolist(),
            }
            for h in holes
        ],
        "brep_step": str(step_path),
        "thickness_mm": args.thickness,
        "port_diameter_mm": args.port,
        "onshape_limit": (
            "Onshape ne convertit pas nativement mesh→B-Rep ; "
            "le solide propre est généré en CadQuery puis importé STEP."
        ),
    }

    if args.upload:
        url = upload_reverse_ensemble(
            mesh_stl=Path(args.stl),
            brep_step=step_path,
            cale_step=cale_baked,
            name=args.name,
        )
        meta["onshape_url"] = url
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")
        print("Onglets: _mesh calque / _bride B-Rep / _cale / ENSEMBLE")

    (OUT / "reverse_carter_report.json").write_text(json.dumps(meta, indent=2))
    (ROOT / "reverse_carter_report.json").write_text(json.dumps(meta, indent=2))
    print("Rapport → reverse_carter_report.json")


def upload_reverse_ensemble(
    mesh_stl: Path, brep_step: Path, cale_step: Path, name: str
) -> str:
    """Upload mesh (calque) + B-Rep bride + cale user → ENSEMBLE."""
    import base64
    import datetime
    import hashlib
    import hmac
    import random
    import string
    import time
    import urllib.request

    from onshape_client.client import Client
    from onshape_client.oas.models.bt_document_params import BTDocumentParams

    load_dotenv()
    # mesh mm → m
    eng = trimesh.load(mesh_stl, force="mesh")
    eng_m = eng.copy()
    eng_m.apply_scale(0.001)
    mesh_m = OUT / "mina_mesh_ref_meters.stl"
    eng_m.export(mesh_m)

    Client.singleton_instance = None
    client = Client(
        configuration={
            "base_url": os.getenv("ONSHAPE_BASE_URL"),
            "access_key": os.getenv("ONSHAPE_ACCESS_KEY"),
            "secret_key": os.getenv("ONSHAPE_SECRET_KEY"),
        },
        keys_file=None,
    )
    doc = client.documents_api.create_document(
        BTDocumentParams(name=name, is_public=True)
    )
    dd = doc.to_dict()
    did, wid = dd["id"], dd["default_workspace"]["id"]

    def imp(path: Path):
        with open(path, "rb") as f:
            tr = client.translation_api.create_translation(
                did,
                wid,
                file=f,
                store_in_document=True,
                notify_user=False,
                allow_faulty_parts=True,
                encoded_filename=path.name,
            )
        while True:
            info = client.translation_api.get_translation(tr.id)
            if info.request_state == "DONE":
                return
            if info.request_state == "FAILED":
                raise RuntimeError(info.to_dict())
            time.sleep(2)

    print("Upload mesh calque…")
    imp(mesh_m)
    print("Upload bride B-Rep…")
    imp(brep_step)
    print("Upload cale user…")
    imp(cale_step)

    ak, sk = os.getenv("ONSHAPE_ACCESS_KEY"), os.getenv("ONSHAPE_SECRET_KEY")

    def api(path, qs="", method="get", body=None):
        n = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(25))
        date = datetime.datetime.now(datetime.UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")
        ctype = "application/json"
        hmac_str = (
            method + "\n" + n + "\n" + date + "\n" + ctype + "\n" + path + "\n" + qs + "\n"
        ).lower().encode()
        sig = base64.b64encode(
            hmac.new(sk.encode(), hmac_str, hashlib.sha256).digest()
        ).decode()
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            "https://cad.onshape.com" + path + (("?" + qs) if qs else ""),
            data=data,
            headers={
                "Date": date,
                "On-Nonce": n,
                "Authorization": f"On {ak}:HmacSHA256:{sig}",
                "Content-Type": ctype,
                "Accept": "application/json",
            },
            method=method.upper(),
        )
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw.decode()) if raw else None

    elems = api(f"/api/documents/d/{did}/w/{wid}/elements")
    aid = next(e["id"] for e in elems if e["elementType"] == "ASSEMBLY")

    for e in elems:
        if e["elementType"] != "PARTSTUDIO" or e["name"] == "Part Studio 1":
            continue
        parts = api(f"/api/parts/d/{did}/w/{wid}/e/{e['id']}")
        solids = [p for p in parts if p.get("bodyType") == "solid"]
        if not solids:
            continue
        solid = solids[0]
        if len(solids) > 1:
            try:
                mp = api(
                    f"/api/partstudios/d/{did}/w/{wid}/e/{e['id']}/massproperties",
                    qs="massAsGroup=false",
                )
                bodies = mp.get("bodies") or {}
                best_vol, best = -1.0, solids[0]
                for p in solids:
                    b = bodies.get(p["partId"]) or {}
                    vol = b.get("volume")
                    if isinstance(vol, list):
                        vol = vol[0]
                    vol = float(vol or 0.0)
                    if vol > best_vol:
                        best_vol, best = vol, p
                solid = best
                print(f"  insert {e['name']}: {solid.get('name')} vol={best_vol:.4e}")
            except Exception as ex:
                print("  massproperties warn", ex)
        api(
            f"/api/assemblies/d/{did}/w/{wid}/e/{aid}/instances",
            method="post",
            body={
                "documentId": did,
                "elementId": e["id"],
                "workspaceId": wid,
                "isAssembly": False,
                "isWholePartStudio": False,
                "partId": solid["partId"],
            },
        )

    NAME_PROP = "57f3fb8efa3416c06701d60d"
    for e in api(f"/api/documents/d/{did}/w/{wid}/elements"):
        nm = e.get("name") or ""
        if e["elementType"] == "ASSEMBLY":
            label = "ENSEMBLE mesh + bride B-Rep + cale"
        elif "mina_mesh" in nm or "mina_piece" in nm or "meters" in nm:
            label = "_mesh calque"
        elif "carter_intake" in nm or "flange_brep" in nm:
            label = "_bride B-Rep (modifiable)"
        elif "cale_" in nm:
            label = "_cale seule"
        else:
            continue
        api(
            f"/api/metadata/d/{did}/w/{wid}/e/{e['id']}",
            method="post",
            body={
                "jsonType": "metadata",
                "properties": [{"propertyId": NAME_PROP, "value": label}],
            },
        )

    return f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{aid}"


if __name__ == "__main__":
    main()
