#!/usr/bin/env python3
"""
Reproduit le carter moteur en B-Rep (CadQuery) à partir du scan aligné.

Repère (déjà calé) :
  - plan de joint = Right / X=0
  - axe cylindre ≈ +Y
  - scan = calque sous le solide

Méthode (plans → esquisses → extrusions / trous) :
  1) Contour du carter au plan de joint (section X=0, simplifié)
  2) Extrusion du corps le long de X (épaisseur réelle du scan)
  3) Boss / deck cylindre + alésage + 4 goujons
  4) Tunnel vilo (alésage transversal détecté près du joint)
  5) Face allumage (bout −Y)
  6) Upload ENSEMBLE : mesh aligné + carter B-Rep (+ pads de ref)

Usage :
  python rebuild_carter_brep.py --upload
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from dotenv import load_dotenv
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"


def joint_silhouette_yz(mesh: trimesh.Trimesh, *, simplify=2.0):
    """Polygone YZ du plan de joint (X=0), coords 3D (x=0,y,z)."""
    sec = mesh.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0])
    if sec is None:
        raise RuntimeError("pas de section joint X=0")
    path2, tf = sec.to_2D()
    main = max(path2.polygons_full, key=lambda p: p.area)
    simp = main.simplify(simplify, preserve_topology=True)
    coords2 = np.asarray(simp.exterior.coords, float)
    # 2D → 3D
    ones = np.ones((len(coords2), 1))
    pts = (tf @ np.hstack([coords2, np.zeros((len(coords2), 1)), ones]).T).T[:, :3]
    # force X=0
    pts[:, 0] = 0.0
    # drop closing duplicate
    if np.linalg.norm(pts[0] - pts[-1]) < 1e-6:
        pts = pts[:-1]
    return pts, float(simp.area)


def body_x_range(mesh: trimesh.Trimesh) -> tuple[float, float]:
    """Épaisseur utile du carter (ignore extrémités goujons / artefacts)."""
    v = mesh.vertices
    core = v[(v[:, 1] > -30) & (v[:, 1] < 320)]
    lo, hi = np.percentile(core[:, 0], [3, 92])
    return float(lo), float(hi)


def detect_crank_bore(mesh: trimesh.Trimesh) -> dict | None:
    """Alésage vilo / roulement près du joint (cercle rond dans une coupe X)."""
    best = None
    for t in np.linspace(-25, 25, 21):
        try:
            sec = mesh.section(
                plane_origin=[t, 0, 0], plane_normal=[1, 0, 0]
            )
        except Exception:
            continue
        if sec is None:
            continue
        path2, tf = sec.to_2D()
        for poly in path2.polygons_full:
            for ring in [poly.exterior, *poly.interiors]:
                xy = np.asarray(ring.coords, float)
                if len(xy) < 16:
                    continue
                c = xy.mean(0)
                r = np.linalg.norm(xy - c, axis=1)
                rm, rs = float(r.mean()), float(r.std())
                if not (16.0 <= rm <= 32.0) or rs > rm * 0.08:
                    continue
                # prefer near mid-height of carter (not far cylinder)
                p3 = (tf @ np.array([c[0], c[1], 0, 1.0]))[:3]
                score = rs / rm + 0.002 * abs(p3[1] - 40)  # prefer Y~40
                cand = {
                    "x": float(t),
                    "center": np.array([float(t), float(p3[1]), float(p3[2])]),
                    "radius": rm,
                    "roundness": rs / rm,
                    "score": score,
                }
                if best is None or cand["score"] < best["score"]:
                    best = cand
    return best


def load_aligned_meta():
    rep = json.loads((ROOT / "align_reverse_report.json").read_text())
    return rep


def build_carter(mesh: trimesh.Trimesh, meta: dict) -> tuple[cq.Workplane, dict]:
    sil, sil_area = joint_silhouette_yz(mesh, simplify=2.2)
    x0, x1 = body_x_range(mesh)
    # ensure extrusion goes both sides of joint
    x0 = min(x0, -5.0)
    x1 = max(x1, 5.0)
    thickness = x1 - x0

    print(f"Silhouette joint: {len(sil)} pts, area={sil_area:.0f} mm²")
    print(f"Extrusion X: {x0:.1f} → {x1:.1f} (épaisseur {thickness:.1f} mm)")

    # Corps : esquisse YZ au plan X=x0, extrusion jusqu'à x1
    pts2 = [(float(p[1]), float(p[2])) for p in sil]
    plane0 = cq.Plane(
        origin=cq.Vector(float(x0), 0, 0),
        normal=cq.Vector(1, 0, 0),
        xDir=cq.Vector(0, 1, 0),
    )
    body = cq.Workplane(plane0).polyline(pts2).close().extrude(float(thickness))

    # --- Boss / deck cylindre ---
    cyl = meta["breps"]["cylindre"]
    cyl_c = np.array(cyl["center"], float)
    studs = [np.array(s, float) for s in cyl.get("studs") or []]
    bore = float(cyl.get("bore") or 47.0)
    deck_y = float(cyl_c[1])
    if len(studs) >= 4:
        xs = [s[0] for s in studs] + [cyl_c[0]]
        zs = [s[2] for s in studs] + [cyl_c[2]]
        pad_x = max(xs) - min(xs) + 28.0
        pad_z = max(zs) - min(zs) + 28.0
    else:
        pad_x, pad_z = 130.0, 130.0
    pad_x = float(np.clip(pad_x, 110, 170))
    pad_z = float(np.clip(pad_z, 110, 170))
    boss_h = 55.0

    deck_plane = cq.Plane(
        origin=cq.Vector(float(cyl_c[0]), deck_y, float(cyl_c[2])),
        normal=cq.Vector(0, 1, 0),
        xDir=cq.Vector(1, 0, 0),
    )
    boss = cq.Workplane(deck_plane).rect(pad_x, pad_z).extrude(-boss_h)
    carter = body.union(boss)

    bore_cut = cq.Workplane(deck_plane).circle(bore / 2).extrude(-(boss_h + 90))
    carter = carter.cut(bore_cut)

    stud_dia = 8.5
    for s in studs[:4]:
        sp = cq.Plane(
            origin=cq.Vector(float(s[0]), deck_y + 1.0, float(s[2])),
            normal=cq.Vector(0, 1, 0),
            xDir=cq.Vector(1, 0, 0),
        )
        hole = cq.Workplane(sp).circle(stud_dia / 2).extrude(-(boss_h + 20))
        carter = carter.cut(hole)

    # --- Tunnel vilo (axe ≈ X, à travers le joint) ---
    crank = detect_crank_bore(mesh)
    if crank is None:
        print("WARN: tunnel vilo non détecté — Ø47 de secours")
        crank = {
            "center": np.array([0.0, 40.0, 0.0]),
            "radius": 23.5,
            "roundness": None,
            "score": None,
        }
    else:
        print(
            f"Tunnel vilo: Ø{2 * crank['radius']:.1f} @ "
            f"Y={crank['center'][1]:.1f} Z={crank['center'][2]:.1f} "
            f"(roundness {crank['roundness']:.3f})"
        )
    cc = crank["center"]
    crank_plane = cq.Plane(
        origin=cq.Vector(0.0, float(cc[1]), float(cc[2])),
        normal=cq.Vector(1, 0, 0),
        xDir=cq.Vector(0, 1, 0),
    )
    half = float(max(abs(x0), abs(x1)) + 15.0)
    tun = cq.Workplane(crank_plane).circle(float(crank["radius"])).extrude(half, both=True)
    carter = carter.cut(tun)

    # --- Face allumage (bout −Y) ---
    ign = meta["breps"]["allumage"]
    ign_c = np.array(ign["center"], float)
    ign_plane = cq.Plane(
        origin=cq.Vector(float(ign_c[0]), float(ign_c[1]), float(ign_c[2])),
        normal=cq.Vector(0, -1, 0),
        xDir=cq.Vector(1, 0, 0),
    )
    end_pad = cq.Workplane(ign_plane).circle(55.0).extrude(-6.0)
    end_hole = cq.Workplane(ign_plane).circle(14.0).extrude(-20.0)
    carter = carter.union(end_pad).cut(end_hole)

    bb = carter.val().BoundingBox()
    print(
        f"Carter B-Rep: {bb.xlen:.1f}×{bb.ylen:.1f}×{bb.zlen:.1f} mm "
        f"vol≈{carter.val().Volume()/1000:.0f} cm³"
    )

    info = {
        "silhouette_points": len(sil),
        "silhouette_area_mm2": sil_area,
        "x_range": [x0, x1],
        "thickness_mm": thickness,
        "cylinder": {
            "center": cyl_c.tolist(),
            "bore": bore,
            "pad": [pad_x, pad_z],
            "boss_h": boss_h,
            "studs": [s.tolist() for s in studs],
            "stud_dia": stud_dia,
        },
        "crank": {
            "center": crank["center"].tolist(),
            "diameter": float(2 * crank["radius"]),
        },
        "ignition": {"center": ign_c.tolist(), "pad_dia": 110.0, "hole_dia": 28.0},
        "bbox": {
            "xlen": bb.xlen,
            "ylen": bb.ylen,
            "zlen": bb.zlen,
            "volume_mm3": float(carter.val().Volume()),
        },
    }
    return carter, info


def upload(mesh_stl: Path, step: Path, name: str) -> str:
    import base64
    import datetime
    import hashlib
    import hmac
    import random
    import string
    import urllib.request

    from onshape_client.client import Client
    from onshape_client.oas.models.bt_document_params import BTDocumentParams

    load_dotenv(ROOT / ".env")
    eng = trimesh.load(mesh_stl, force="mesh")
    eng_m = eng.copy()
    eng_m.apply_scale(0.001)
    mesh_m = OUT / "mina_carter_rebuild_mesh_meters.stl"
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
    doc = client.documents_api.create_document(BTDocumentParams(name=name, is_public=True))
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
    print("Upload carter B-Rep…")
    imp(step)

    ak, sk = os.getenv("ONSHAPE_ACCESS_KEY"), os.getenv("ONSHAPE_SECRET_KEY")

    def api(path, qs="", method="get", body=None):
        n = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(25))
        date = datetime.datetime.now(datetime.UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")
        ctype = "application/json"
        hmac_str = (
            method + "\n" + n + "\n" + date + "\n" + ctype + "\n" + path + "\n" + qs + "\n"
        ).lower().encode()
        sig = base64.b64encode(hmac.new(sk.encode(), hmac_str, hashlib.sha256).digest()).decode()
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
            mp = api(
                f"/api/partstudios/d/{did}/w/{wid}/e/{e['id']}/massproperties",
                qs="massAsGroup=false",
            )
            bodies = mp.get("bodies") or {}
            best_vol, best = -1.0, solids[0]
            for p in solids:
                b = bodies.get(p["partId"]) or {}
                vol = b.get("volume")
                vol = vol[0] if isinstance(vol, list) else vol
                vol = float(vol or 0)
                if vol > best_vol:
                    best_vol, best = vol, p
            solid = best
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
        nm = (e.get("name") or "").lower()
        if e["elementType"] == "ASSEMBLY":
            label = "ENSEMBLE carter B-Rep + mesh"
        elif "carter" in nm and "brep" in nm:
            label = "_carter moteur B-Rep"
        elif "mina_" in nm or "mesh" in nm or nm.endswith(".stl"):
            label = "_mesh calque aligné"
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stl", default=str(OUT / "mina_aligned_joint_right.stl"))
    ap.add_argument("--upload", action="store_true")
    ap.add_argument(
        "--name",
        default="MINARELLI carter moteur B-Rep — joint/cylindre/vilo",
    )
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")

    print("=== Reconstruction carter B-Rep ===")
    mesh = trimesh.load(args.stl, force="mesh")
    meta = load_aligned_meta()
    solid, info = build_carter(mesh, meta)

    step = OUT / "carter_moteur_brep.step"
    stl_out = OUT / "carter_moteur_brep.stl"
    cq.exporters.export(solid, str(step))
    cq.exporters.export(solid, str(stl_out))
    print(f"STEP → {step}")

    report = {
        "method": "joint_silhouette_extrude_plus_cyl_boss_crank_tunnel",
        "goal": "reproduce carter moteur as editable B-Rep (scan as underlay)",
        "frame": "joint=Right/X=0, cylinder≈+Y (from align_and_reverse_faces)",
        "carter": info,
        "step": str(step),
    }

    if args.upload:
        url = upload(Path(args.stl), step, args.name)
        report["onshape_url"] = url
        (OUT / "carter_rebuild_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")

    (OUT / "carter_rebuild_report.json").write_text(json.dumps(report, indent=2))
    (ROOT / "carter_rebuild_report.json").write_text(json.dumps(report, indent=2))
    print("Rapport → carter_rebuild_report.json")


if __name__ == "__main__":
    main()
