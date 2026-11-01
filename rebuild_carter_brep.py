#!/usr/bin/env python3
"""
Reproduit le carter moteur en B-Rep (CadQuery) à partir du scan aligné.

Repère (déjà calé) :
  - plan de joint = Right / X=0
  - axe cylindre ≈ +Y
  - scan = calque sous le solide

Méthode (plans → esquisses → extrusions / trous), peaufinée :
  1) Contour joint plus fin (simplify 1.2) + vis de fermeture détectées
  2) Corps en paliers d'épaisseur X selon zones Y (ign / mid / cyl)
  3) Deck cylindre : goujons recalés, alésage fité sur paroi radiale, collar
  4) Tunnel vilo moyenné sur plusieurs coupes X
  5) Face allumage = vraie silhouette de section (plus un cercle)
  6) Upload ENSEMBLE : mesh aligné + carter B-Rep

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


def section_polygon_3d(mesh, origin, normal, *, simplify=1.5):
    """Plus grand polygone d'une coupe → liste de points 3D + aire."""
    sec = mesh.section(plane_origin=origin, plane_normal=normal)
    if sec is None:
        return None, None, None
    path2, tf = sec.to_2D()
    if not path2.polygons_full:
        return None, None, None
    main = max(path2.polygons_full, key=lambda p: p.area)
    simp = main.simplify(simplify, preserve_topology=True)
    coords2 = np.asarray(simp.exterior.coords, float)
    ones = np.ones((len(coords2), 1))
    pts = (tf @ np.hstack([coords2, np.zeros((len(coords2), 1)), ones]).T).T[:, :3]
    if np.linalg.norm(pts[0] - pts[-1]) < 1e-6:
        pts = pts[:-1]
    return pts, float(simp.area), tf


def joint_silhouette_yz(mesh: trimesh.Trimesh, *, simplify=1.2):
    pts, area, _ = section_polygon_3d(
        mesh, [0, 0, 0], [1, 0, 0], simplify=simplify
    )
    if pts is None:
        raise RuntimeError("pas de section joint X=0")
    pts = pts.copy()
    pts[:, 0] = 0.0
    return pts, area


def zone_x_range(mesh: trimesh.Trimesh, y0: float, y1: float) -> tuple[float, float]:
    v = mesh.vertices
    x = v[(v[:, 1] > y0) & (v[:, 1] < y1), 0]
    if len(x) < 50:
        return -40.0, 40.0
    lo, hi = np.percentile(x, [6, 94])
    return float(lo), float(hi)


def refine_studs(mesh: trimesh.Trimesh, seed_studs: list[np.ndarray]) -> list[np.ndarray]:
    """Recale les 4 goujons sur les pointes hautes du mesh."""
    v = mesh.vertices
    hi = v[v[:, 1] > np.percentile(v[:, 1], 97.5)]
    cells: dict = {}
    for p in hi:
        key = (round(float(p[0]) / 4) * 4, round(float(p[2]) / 4) * 4)
        if key not in cells or p[1] > cells[key][1]:
            cells[key] = p.copy()
    peaks = sorted(cells.values(), key=lambda p: -p[1])
    out = []
    for seed in seed_studs[:4]:
        best = None
        best_d = 1e9
        for p in peaks:
            d = float(np.linalg.norm(p[[0, 2]] - seed[[0, 2]]))
            if d < best_d and d < 18:
                best_d, best = d, p
        out.append(best if best is not None else seed.copy())
    # NMS if duplicates
    cleaned = []
    for p in out:
        if all(np.linalg.norm(p[[0, 2]] - q[[0, 2]]) > 15 for q in cleaned):
            cleaned.append(p)
    while len(cleaned) < 4 and peaks:
        p = peaks.pop(0)
        if all(np.linalg.norm(p[[0, 2]] - q[[0, 2]]) > 22 for q in cleaned):
            cleaned.append(p)
    return cleaned[:4]


def detect_cylinder_bore(mesh: trimesh.Trimesh, studs: list[np.ndarray]) -> dict:
    """Centre + rayon d'alésage par fit sur paroi radiale près du deck."""
    c0 = np.mean(np.vstack(studs), axis=0)
    deck_y = float(np.median([s[1] for s in studs]))
    fn, fc = mesh.face_normals, mesh.triangles_center
    radial = (np.abs(fn[:, 1]) < 0.4) & (fc[:, 1] > deck_y - 55) & (fc[:, 1] < deck_y - 2)
    pts = fc[radial]
    d = np.linalg.norm(pts[:, [0, 2]] - c0[[0, 2]], axis=1)
    best = None
    for r0 in np.linspace(18.0, 28.0, 21):
        wall = pts[(d > r0 - 2.2) & (d < r0 + 2.2)][:, [0, 2]]
        if len(wall) < 50:
            continue
        x, y = wall[:, 0], wall[:, 1]
        A = np.c_[2 * x, 2 * y, np.ones_like(x)]
        sol, *_ = np.linalg.lstsq(A, x * x + y * y, rcond=None)
        cx, cy = float(sol[0]), float(sol[1])
        rr = float(np.sqrt(max(sol[2] + cx * cx + cy * cy, 0.0)))
        resid = float(np.std(np.linalg.norm(wall - np.array([cx, cy]), axis=1) - rr))
        score = resid + 0.01 * abs(rr - 23.5)  # légère préférence ~Ø47 Minarelli
        cand = {
            "center": np.array([cx, deck_y, cy]),
            "radius": rr,
            "resid": resid,
            "n": len(wall),
            "score": score,
        }
        if best is None or score < best["score"]:
            best = cand
    if best is None:
        return {
            "center": np.array([c0[0], deck_y, c0[2]]),
            "radius": 23.5,
            "resid": None,
            "n": 0,
        }
    return best


def detect_crank_bore(mesh: trimesh.Trimesh) -> dict | None:
    """Moyenne des cercles propres près du joint (Y~0–60)."""
    samples = []
    for t in np.linspace(-40, 40, 41):
        try:
            sec = mesh.section(plane_origin=[t, 0, 0], plane_normal=[1, 0, 0])
        except Exception:
            continue
        if sec is None:
            continue
        path2, tf = sec.to_2D()
        for poly in path2.polygons_full:
            for ring in [poly.exterior, *poly.interiors]:
                xy = np.asarray(ring.coords, float)
                if len(xy) < 24:
                    continue
                c = xy.mean(0)
                r = np.linalg.norm(xy - c, axis=1)
                rm, rs = float(r.mean()), float(r.std())
                if not (20.0 <= rm <= 26.0) or rs > rm * 0.05:
                    continue
                p3 = (tf @ np.array([c[0], c[1], 0, 1.0]))[:3]
                if -15 < p3[1] < 70 and abs(p3[2]) < 45:
                    samples.append((rm, p3, float(t), rs / rm))
    if not samples:
        return None
    rs = np.array([s[0] for s in samples])
    cs = np.array([s[1] for s in samples])
    xs = np.array([s[2] for s in samples])
    return {
        "center": np.array([0.0, float(cs[:, 1].mean()), float(cs[:, 2].mean())]),
        "radius": float(rs.mean()),
        "roundness": float(np.mean([s[3] for s in samples])),
        "x_span": [float(xs.min()), float(xs.max())],
        "n": len(samples),
    }


def detect_joint_bolts(mesh: trimesh.Trimesh) -> list[dict]:
    """Petits trous circulaires au plan de joint (vis de fermeture)."""
    holes = []
    for t in np.linspace(-4, 4, 5):
        try:
            sec = mesh.section(plane_origin=[t, 0, 0], plane_normal=[1, 0, 0])
        except Exception:
            continue
        if sec is None:
            continue
        path2, tf = sec.to_2D()
        for poly in path2.polygons_full:
            rings = list(poly.interiors)
            if poly.area < 120:
                rings = [poly.exterior, *rings]
            for ring in rings:
                xy = np.asarray(ring.coords, float)
                if len(xy) < 10:
                    continue
                c = xy.mean(0)
                r = np.linalg.norm(xy - c, axis=1)
                rm, rs = float(r.mean()), float(r.std())
                if 2.2 <= rm <= 5.0 and rs < 0.9:
                    p3 = (tf @ np.array([c[0], c[1], 0, 1.0]))[:3]
                    holes.append((rm, p3))
    # cluster YZ
    clusters: list[dict] = []
    for rm, p3 in holes:
        placed = False
        for cl in clusters:
            if np.linalg.norm(p3[1:] - cl["c"][1:]) < 8:
                cl["pts"].append(p3)
                cl["rs"].append(rm)
                placed = True
                break
        if not placed:
            clusters.append({"c": p3.copy(), "pts": [p3], "rs": [rm]})
    out = []
    for cl in clusters:
        if len(cl["pts"]) < 1:
            continue
        c = np.mean(cl["pts"], axis=0)
        out.append({"center": np.array([0.0, c[1], c[2]]), "radius": float(np.mean(cl["rs"]))})
    return out


def load_aligned_meta():
    rep = json.loads((ROOT / "align_reverse_report.json").read_text())
    return rep


def extrude_poly_x(pts_yz: np.ndarray, x0: float, x1: float) -> cq.Workplane:
    pts2 = [(float(p[1]), float(p[2])) for p in pts_yz]
    plane0 = cq.Plane(
        origin=cq.Vector(float(x0), 0, 0),
        normal=cq.Vector(1, 0, 0),
        xDir=cq.Vector(0, 1, 0),
    )
    return cq.Workplane(plane0).polyline(pts2).close().extrude(float(x1 - x0))


def build_carter(mesh: trimesh.Trimesh, meta: dict) -> tuple[cq.Workplane, dict]:
    # 1) Silhouette joint plus fine
    sil, sil_area = joint_silhouette_yz(mesh, simplify=1.2)
    print(f"Silhouette joint: {len(sil)} pts, area={sil_area:.0f} mm²")

    # 2) Corps en paliers (épaisseur X selon zone Y)
    x_ign = zone_x_range(mesh, -60, 50)
    x_mid = zone_x_range(mesh, 50, 280)
    x_cyl = zone_x_range(mesh, 280, 420)
    print(f"X ign {x_ign[0]:.1f}→{x_ign[1]:.1f} | mid {x_mid[0]:.1f}→{x_mid[1]:.1f} | cyl {x_cyl[0]:.1f}→{x_cyl[1]:.1f}")

    # base = extrusion joint sur plage crank/ign (traverse le plan X=0)
    x0 = min(x_ign[0], x_mid[0], -8.0)
    x1 = max(x_ign[1], 8.0)
    body = extrude_poly_x(sil, x0, x1)

    # renfort côté +X (demi-carter plus épais / cylindre)
    x_plus0 = max(5.0, x_mid[0] if x_mid[0] > 0 else 5.0)
    x_plus1 = max(x_mid[1], x_cyl[1])
    if x_plus1 > x_plus0 + 10:
        # section à Y médian pour bulk +X : réutilise silhouette joint (approx)
        bulk = extrude_poly_x(sil, x_plus0, x_plus1)
        body = body.union(bulk)

    carter = body

    # 3) Deck cylindre peaufiné
    seed_studs = [np.array(s, float) for s in (meta["breps"]["cylindre"].get("studs") or [])]
    studs = refine_studs(mesh, seed_studs) if seed_studs else seed_studs
    bore_info = detect_cylinder_bore(mesh, studs if studs else seed_studs)
    bore_c = bore_info["center"]
    bore_r = float(bore_info["radius"])
    # clamp Ø40–50
    bore_r = float(np.clip(bore_r, 20.0, 25.0))
    deck_y = float(bore_c[1])
    print(
        f"Cylindre: centre=({bore_c[0]:.1f},{bore_c[2]:.1f}) Ø={2*bore_r:.1f} "
        f"deck Y={deck_y:.1f} studs={len(studs)} resid={bore_info.get('resid')}"
    )

    if len(studs) >= 4:
        xs = [s[0] for s in studs]
        zs = [s[2] for s in studs]
        pad_x = float(np.ptp(xs) + 32.0)
        pad_z = float(np.ptp(zs) + 32.0)
        pad_cx = float(np.mean(xs))
        pad_cz = float(np.mean(zs))
    else:
        pad_x = pad_z = 140.0
        pad_cx, pad_cz = float(bore_c[0]), float(bore_c[2])
    pad_x = float(np.clip(pad_x, 110, 180))
    pad_z = float(np.clip(pad_z, 90, 160))
    boss_h = 62.0

    deck_plane = cq.Plane(
        origin=cq.Vector(pad_cx, deck_y, pad_cz),
        normal=cq.Vector(0, 1, 0),
        xDir=cq.Vector(1, 0, 0),
    )
    # boss avec filet léger (chamfer via rounded rect approx: circle hull of studs)
    boss = cq.Workplane(deck_plane).rect(pad_x, pad_z).extrude(-boss_h)
    # collar cylindrique autour de l'alésage
    collar = (
        cq.Workplane(
            cq.Plane(
                origin=cq.Vector(float(bore_c[0]), deck_y, float(bore_c[2])),
                normal=cq.Vector(0, 1, 0),
                xDir=cq.Vector(1, 0, 0),
            )
        )
        .circle(bore_r + 14.0)
        .extrude(-boss_h)
    )
    carter = carter.union(boss).union(collar)

    bore_plane = cq.Plane(
        origin=cq.Vector(float(bore_c[0]), deck_y + 0.5, float(bore_c[2])),
        normal=cq.Vector(0, 1, 0),
        xDir=cq.Vector(1, 0, 0),
    )
    carter = carter.cut(cq.Workplane(bore_plane).circle(bore_r).extrude(-(boss_h + 100)))

    stud_dia = 8.5
    for s in studs[:4]:
        sp = cq.Plane(
            origin=cq.Vector(float(s[0]), deck_y + 1.0, float(s[2])),
            normal=cq.Vector(0, 1, 0),
            xDir=cq.Vector(1, 0, 0),
        )
        carter = carter.cut(cq.Workplane(sp).circle(stud_dia / 2).extrude(-(boss_h + 25)))

    # 4) Tunnel vilo peaufiné
    crank = detect_crank_bore(mesh)
    if crank is None:
        print("WARN: tunnel vilo non détecté — Ø47 secours")
        crank = {
            "center": np.array([0.0, 10.0, -10.0]),
            "radius": 23.5,
            "roundness": None,
            "x_span": [-20.0, 20.0],
            "n": 0,
        }
    else:
        print(
            f"Tunnel vilo: Ø{2*crank['radius']:.1f} @ "
            f"Y={crank['center'][1]:.1f} Z={crank['center'][2]:.1f} "
            f"X={crank['x_span']} n={crank['n']}"
        )
    cc = crank["center"]
    crank_plane = cq.Plane(
        origin=cq.Vector(0.0, float(cc[1]), float(cc[2])),
        normal=cq.Vector(1, 0, 0),
        xDir=cq.Vector(0, 1, 0),
    )
    # traverse tout le corps (roulement G→D)
    half = float(max(abs(x0), abs(x_plus1), abs(x1)) + 20.0)
    carter = carter.cut(
        cq.Workplane(crank_plane).circle(float(crank["radius"])).extrude(half, both=True)
    )

    # 5) Vis de joint (si détectées)
    bolts = detect_joint_bolts(mesh)
    print(f"Vis joint détectées: {len(bolts)}")
    for b in bolts:
        bp = cq.Plane(
            origin=cq.Vector(0.0, float(b["center"][1]), float(b["center"][2])),
            normal=cq.Vector(1, 0, 0),
            xDir=cq.Vector(0, 1, 0),
        )
        carter = carter.cut(
            cq.Workplane(bp).circle(float(b["radius"])).extrude(abs(x0) + 8, both=True)
        )

    # 6) Face allumage = vraie silhouette (plus un cercle générique)
    ign = meta["breps"]["allumage"]
    ign_n = np.array(ign["normal"], float)
    ign_n /= np.linalg.norm(ign_n) + 1e-12
    ign_d = float(ign["d"])
    ign_pts, ign_area, _ = section_polygon_3d(
        mesh, ign_n * ign_d, ign_n, simplify=1.8
    )
    ign_c = np.array(ign["center"], float)
    if ign_pts is not None and len(ign_pts) >= 4:
        # plan local allumage
        # xDir ≈ +X
        xdir = np.array([1.0, 0.0, 0.0])
        xdir = xdir - ign_n * (xdir @ ign_n)
        xdir /= np.linalg.norm(xdir) + 1e-12
        ydir = np.cross(ign_n, xdir)
        origin = ign_pts.mean(0)
        ign_plane = cq.Plane(
            origin=cq.Vector(*map(float, origin)),
            normal=cq.Vector(*map(float, ign_n)),
            xDir=cq.Vector(*map(float, xdir)),
        )

        def to2(p):
            q = p - origin
            return float(q @ xdir), float(q @ ydir)

        poly2 = [to2(p) for p in ign_pts]
        end_pad = cq.Workplane(ign_plane).polyline(poly2).close().extrude(-7.0)
        # trou central ~ stator / vilo
        end_hole = cq.Workplane(ign_plane).circle(14.0).extrude(-22.0)
        carter = carter.union(end_pad).cut(end_hole)
        print(f"Allumage: silhouette {len(ign_pts)} pts, area={ign_area:.0f} mm²")
    else:
        ign_plane = cq.Plane(
            origin=cq.Vector(*map(float, ign_c)),
            normal=cq.Vector(0, -1, 0),
            xDir=cq.Vector(1, 0, 0),
        )
        carter = carter.union(cq.Workplane(ign_plane).circle(55).extrude(-6)).cut(
            cq.Workplane(ign_plane).circle(14).extrude(-20)
        )
        ign_area = None
        print("Allumage: fallback cercle")

    bb = carter.val().BoundingBox()
    print(
        f"Carter B-Rep: {bb.xlen:.1f}×{bb.ylen:.1f}×{bb.zlen:.1f} mm "
        f"vol≈{carter.val().Volume()/1000:.0f} cm³"
    )

    info = {
        "silhouette_points": len(sil),
        "silhouette_area_mm2": sil_area,
        "x_zones": {"ign": list(x_ign), "mid": list(x_mid), "cyl": list(x_cyl)},
        "x_range_body": [x0, x1],
        "cylinder": {
            "center": bore_c.tolist(),
            "bore": 2 * bore_r,
            "pad": [pad_x, pad_z],
            "pad_center": [pad_cx, pad_cz],
            "boss_h": boss_h,
            "studs": [s.tolist() for s in studs],
            "stud_dia": stud_dia,
            "fit_resid": bore_info.get("resid"),
        },
        "crank": {
            "center": crank["center"].tolist(),
            "diameter": float(2 * crank["radius"]),
            "x_span": crank.get("x_span"),
            "n_samples": crank.get("n"),
        },
        "joint_bolts": [
            {"center": b["center"].tolist(), "diameter": 2 * b["radius"]} for b in bolts
        ],
        "ignition": {
            "center": ign_c.tolist(),
            "silhouette_points": int(len(ign_pts) if ign_pts is not None else 0),
            "area_mm2": ign_area,
            "hole_dia": 28.0,
        },
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
