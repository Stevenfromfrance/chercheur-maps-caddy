#!/usr/bin/env python3
"""
Corrige la géométrie avant reverse-engineering :

1) Plans par 3 points ESPACÉS sur le maillage (pas un offset/PCA bancal)
2) Validation type « vue en coupe » (distances signées p10/p90/rms)
3) Transform du mesh : plan de joint → plan Right (X=0) + origine
4) Pads B-Rep (cylindre / joint / allumage) dans ce repère propre
5) Upload ENSEMBLE mesh aligné + B-Reps (focus loc moteur, pas cale)

Usage :
  python align_and_reverse_faces.py --upload
"""

from __future__ import annotations

import argparse
import json
import os
from collections import deque
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"


# ---------------------------------------------------------------------------
# 3-point planes
# ---------------------------------------------------------------------------

def build_adjacency(mesh: trimesh.Trimesh):
    nbrs = [[] for _ in range(len(mesh.faces))]
    for a, b in mesh.face_adjacency:
        nbrs[int(a)].append(int(b))
        nbrs[int(b)].append(int(a))
    return nbrs


def grow_region(mesh, nbrs, seed: int, *, ang_deg=5.0, dist_tol=0.7):
    fn, fc = mesh.face_normals, mesh.triangles_center
    n0 = fn[seed] / (np.linalg.norm(fn[seed]) + 1e-12)
    d0 = float(n0 @ fc[seed])
    cos_th = float(np.cos(np.radians(ang_deg)))
    region: list[int] = []
    q = deque([seed])
    seen = np.zeros(len(mesh.faces), dtype=bool)
    seen[seed] = True
    while q:
        fi = q.popleft()
        n = fn[fi] / (np.linalg.norm(fn[fi]) + 1e-12)
        if float(n @ n0) < cos_th:
            continue
        if abs(float(n0 @ fc[fi]) - d0) > dist_tol:
            continue
        region.append(fi)
        for nb in nbrs[fi]:
            if not seen[nb]:
                seen[nb] = True
                q.append(nb)
    return region, n0


def farthest_triplet(pts: np.ndarray, *, min_edge=15.0):
    rng = np.random.default_rng(0)
    P = pts if len(pts) <= 900 else pts[rng.choice(len(pts), 900, replace=False)]
    c = P.mean(0)
    _, _, vh = np.linalg.svd(P - c, full_matrices=False)
    s1 = (P - c) @ vh[0]
    s2 = (P - c) @ vh[1]
    cand = np.unique(
        np.concatenate(
            [
                np.argsort(s1)[:8],
                np.argsort(s1)[-8:],
                np.argsort(s2)[:8],
                np.argsort(s2)[-8:],
                rng.choice(len(P), min(50, len(P)), replace=False),
            ]
        )
    )
    C = P[cand]
    best = None
    for i in range(len(C)):
        for j in range(i + 1, len(C)):
            for k in range(j + 1, len(C)):
                a, b, c3 = C[i], C[j], C[k]
                area = 0.5 * float(np.linalg.norm(np.cross(b - a, c3 - a)))
                edges = [
                    float(np.linalg.norm(b - a)),
                    float(np.linalg.norm(c3 - b)),
                    float(np.linalg.norm(a - c3)),
                ]
                if min(edges) < min_edge:
                    continue
                if best is None or area > best[0]:
                    best = (area, a, b, c3, edges)
    return best


def plane_from_3(a, b, c, hint=None):
    n = np.cross(b - a, c - a)
    n = n / (np.linalg.norm(n) + 1e-12)
    if hint is not None and float(n @ hint) < 0:
        n = -n
    d = float(n @ a)
    return n, d


def section_stats(pts, n, d):
    dist = pts @ n - d
    return {
        "median": float(np.median(dist)),
        "p10": float(np.percentile(dist, 10)),
        "p90": float(np.percentile(dist, 90)),
        "rms": float(np.sqrt(np.mean(dist**2))),
        "mean": float(dist.mean()),
    }


def pick_seed_region(mesh, nbrs, mask, *, ang=5.0, dist_tol=0.7, top=40):
    fa = mesh.area_faces
    seeds = np.where(mask)[0]
    if len(seeds) == 0:
        return None
    seeds = seeds[np.argsort(-fa[seeds])]
    best = None
    for seed in seeds[:top]:
        region, n0 = grow_region(mesh, nbrs, int(seed), ang_deg=ang, dist_tol=dist_tol)
        area = float(fa[region].sum())
        if best is None or area > best[0]:
            best = (area, region, n0)
    return best


def _plane_result(name, area, vids, trip, n, d, st, n0=None):
    tarea, a, b, c, edges = trip
    tilt = None
    if n0 is not None:
        tilt = float(np.degrees(np.arccos(np.clip(abs(float(n @ n0)), -1.0, 1.0))))
    print(
        f"{name}: area={area:.0f} verts={len(vids)} "
        f"edges={[round(e, 1) for e in edges]} "
        f"section med={st['median']:.3f} rms={st['rms']:.3f} "
        f"p10={st['p10']:.3f} p90={st['p90']:.3f}"
        + (f" tilt={tilt:.1f}°" if tilt is not None else "")
    )
    ok = (
        st["rms"] < 1.0
        and abs(st["median"]) < 0.8
        and abs(st["p10"]) < 2.5
        and abs(st["p90"]) < 2.5
    )
    if not ok:
        print(f"  WARN section douteuse pour {name}")
    return {
        "name": name,
        "normal": n,
        "d": d,
        "points": np.vstack([a, b, c]),
        "edges": edges,
        "triangle_area": tarea,
        "section": st,
        "region_area": area,
        "ok": ok,
        "tilt_deg": tilt,
    }


def make_3point_plane(mesh, nbrs, mask, hint, *, name, min_edge=20.0, ang=5.0, dist_tol=0.7):
    picked = pick_seed_region(mesh, nbrs, mask, ang=ang, dist_tol=dist_tol)
    if picked is None:
        raise RuntimeError(f"{name}: aucun seed")
    area, region, n0 = picked
    vids = np.unique(mesh.faces[region].reshape(-1))
    pts = mesh.vertices[vids]
    trip = farthest_triplet(pts, min_edge=min_edge)
    if trip is None:
        trip = farthest_triplet(pts, min_edge=min_edge * 0.6)
    if trip is None:
        raise RuntimeError(f"{name}: pas de triplet 3 points")
    n, d = plane_from_3(trip[1], trip[2], trip[3], hint if hint is not None else n0)
    st = section_stats(pts, n, d)
    return _plane_result(name, area, vids, trip, n, d, st, hint)


def best_3point_plane(
    mesh,
    nbrs,
    mask,
    hint,
    *,
    name,
    min_edges=(15.0, 20.0, 25.0),
    angs=((5.0, 0.6), (7.0, 0.9), (9.0, 1.2)),
    top_seeds=80,
    min_area=500.0,
    max_tilt_deg=8.0,
):
    """
    Cherche plusieurs régions / triplets 3 points et garde celui qui :
    - reste tangente (rms / médiane section OK)
    - reste proche du hint (évite un plan de travers sur une bosse)
    - a une grande aire de région
    """
    fa = mesh.area_faces
    seeds = np.where(mask)[0]
    if len(seeds) == 0:
        raise RuntimeError(f"{name}: aucun seed")
    seeds = seeds[np.argsort(-fa[seeds])][:top_seeds]
    hint = hint / (np.linalg.norm(hint) + 1e-12)
    seen: set[int] = set()
    best = None
    for seed in seeds:
        if int(seed) in seen:
            continue
        for ang, dist_tol in angs:
            region, n0 = grow_region(
                mesh, nbrs, int(seed), ang_deg=ang, dist_tol=dist_tol
            )
            for fi in region:
                seen.add(int(fi))
            area = float(fa[region].sum())
            if area < min_area:
                continue
            vids = np.unique(mesh.faces[region].reshape(-1))
            pts = mesh.vertices[vids]
            for me in min_edges:
                trip = farthest_triplet(pts, min_edge=me)
                if trip is None:
                    continue
                n, d = plane_from_3(trip[1], trip[2], trip[3], hint)
                st = section_stats(pts, n, d)
                if st["rms"] > 0.8 or abs(st["median"]) > 0.6:
                    continue
                if abs(st["p10"]) > 2.0 or abs(st["p90"]) > 2.0:
                    continue
                agree = float(n @ hint)
                tilt = float(np.degrees(np.arccos(np.clip(abs(agree), -1.0, 1.0))))
                if tilt > max_tilt_deg:
                    continue
                # score: low tilt, low rms, large spaced triangle, large region
                score = tilt + 5.0 * st["rms"] + 2.0 * abs(st["median"]) - 0.001 * area
                score -= 0.01 * float(trip[0])  # triangle area
                cand = (score, area, vids, trip, n, d, st, tilt)
                if best is None or score < best[0]:
                    best = cand
    if best is None:
        # fallback: single-region path (may warn)
        return make_3point_plane(
            mesh,
            nbrs,
            mask,
            hint,
            name=name,
            min_edge=min_edges[0],
            ang=angs[-1][0],
            dist_tol=angs[-1][1],
        )
    _, area, vids, trip, n, d, st, _tilt = best
    return _plane_result(name, area, vids, trip, n, d, st, hint)


def detect_planes_3point(mesh: trimesh.Trimesh) -> dict:
    nbrs = build_adjacency(mesh)
    fn, fc = mesh.face_normals, mesh.triangles_center

    # Deck cylindre : exiger quasi-+Y (sinon le secondary-rotate penche tout le carter)
    cyl = best_3point_plane(
        mesh,
        nbrs,
        (fn[:, 1] > 0.8) & (fc[:, 1] > 370) & (fc[:, 1] < 480),
        np.array([0.0, 1.0, 0.0]),
        name="cylindre",
        min_edges=(15.0, 20.0, 25.0),
        angs=((5.0, 0.6), (7.0, 0.9)),
        max_tilt_deg=6.0,
        min_area=600.0,
    )

    # Face allumage : antiparallèle au cylindre, bout bas du carter
    ign = best_3point_plane(
        mesh,
        nbrs,
        (fn[:, 1] < -0.85)
        & (fc[:, 1] > -50)
        & (fc[:, 1] < 60)
        & (fc[:, 0] > 0)
        & (fc[:, 0] < 140),
        -cyl["normal"],  # hint = opposé cylindre
        name="allumage",
        min_edges=(15.0, 20.0, 25.0),
        angs=((5.0, 0.6), (7.0, 0.9)),
        max_tilt_deg=12.0,  # scan un peu bruité côté allumage
        min_area=500.0,
    )

    # Joint vertical (demi-carters) — 3 points espacés, pas un offset Z bancal
    joint = best_3point_plane(
        mesh,
        nbrs,
        (np.abs(fn[:, 0]) > 0.95)
        & (fc[:, 1] > 40)
        & (fc[:, 1] < 280)
        & (np.abs(fc[:, 0] + 10) < 40),
        np.array([1.0, 0.0, 0.0]),
        name="joint",
        min_edges=(25.0, 30.0, 40.0),
        angs=((4.0, 0.55), (5.0, 0.7)),
        max_tilt_deg=5.0,
        min_area=800.0,
    )
    return {"cylindre": cyl, "allumage": ign, "joint": joint}


# ---------------------------------------------------------------------------
# Align mesh: joint → Right (X=0), origin at joint center
# ---------------------------------------------------------------------------

def rotation_align(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """R such that R @ a_hat ≈ b_hat (Rodrigues)."""
    a = a / (np.linalg.norm(a) + 1e-12)
    b = b / (np.linalg.norm(b) + 1e-12)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.999999:
        # 180° — pick orthogonal axis
        axis = np.array([1.0, 0.0, 0.0])
        if abs(a[0]) > 0.9:
            axis = np.array([0.0, 1.0, 0.0])
        axis = axis - a * np.dot(axis, a)
        axis /= np.linalg.norm(axis)
        K = np.array(
            [[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]],
            float,
        )
        return np.eye(3) + 2 * K @ K
    s = np.linalg.norm(v)
    if s < 1e-12:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]], float)
    return np.eye(3) + K + K @ K * ((1 - c) / (s**2))


def align_mesh_to_origin(mesh: trimesh.Trimesh, planes: dict) -> tuple[trimesh.Trimesh, np.ndarray, dict]:
    """
    Comme Mate Connector + Transform by connectors :
    - joint normal → +X (plan Right)
    - centre du triangle joint → origine
    - rotation secondaire pour amener l'axe cylindre vers +Y
    """
    joint = planes["joint"]
    cyl = planes["cylindre"]
    n_j = joint["normal"]
    c_j = joint["points"].mean(0)

    R1 = rotation_align(n_j, np.array([1.0, 0.0, 0.0]))
    # cylinder direction after R1
    n_c = R1 @ cyl["normal"]
    # rotate around X so n_c → +Y (project to YZ)
    yz = n_c[1:]
    if np.linalg.norm(yz) < 1e-8:
        R2 = np.eye(3)
    else:
        ang = np.arctan2(yz[1], yz[0])  # angle from +Y toward +Z
        # we want yz → (1,0) i.e. +Y
        ca, sa = np.cos(-ang), np.sin(-ang)
        R2 = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]], float)

    R = R2 @ R1
    T = -R @ c_j  # joint center → origin

    out = mesh.copy()
    out.vertices = (R @ mesh.vertices.T).T + T

    def xform_plane(p):
        n = R @ p["normal"]
        n = n / (np.linalg.norm(n) + 1e-12)
        pts = (R @ p["points"].T).T + T
        d = float(n @ pts.mean(0))
        return {
            **{k: v for k, v in p.items() if k not in ("normal", "d", "points")},
            "normal": n,
            "d": d,
            "points": pts,
            "center": pts.mean(0),
        }

    aligned_planes = {k: xform_plane(p) for k, p in planes.items()}
    print("Alignement: joint → X=0, cylindre ≈ +Y")
    for k, p in aligned_planes.items():
        print(f"  {k}: n={p['normal'].round(4)} d={p['d']:.3f} c={p['center'].round(2)}")

    return out, np.vstack([np.hstack([R, T.reshape(3, 1)]), [0, 0, 0, 1]]), aligned_planes


# ---------------------------------------------------------------------------
# B-Rep pads in aligned frame
# ---------------------------------------------------------------------------

def basis(n):
    n = n / (np.linalg.norm(n) + 1e-12)
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0.0, 1, 0])
    x = np.cross(a, n)
    x /= np.linalg.norm(x) + 1e-12
    y = np.cross(n, x)
    return n, x, y


def extrude_pad(n, center, *, size, thickness, holes=None, circular=False):
    n, xdir, ydir = basis(n)
    plane = cq.Plane(
        origin=cq.Vector(*map(float, center)),
        normal=cq.Vector(*map(float, n)),
        xDir=cq.Vector(*map(float, xdir)),
    )

    def to2(p):
        q = np.asarray(p, float) - center
        return float(q @ xdir), float(q @ ydir)

    wp = cq.Workplane(plane)
    if circular:
        solid = wp.circle(float(size) / 2).extrude(-abs(thickness))
    elif isinstance(size, tuple):
        solid = wp.rect(float(size[0]), float(size[1])).extrude(-abs(thickness))
    else:
        solid = wp.rect(float(size), float(size)).extrude(-abs(thickness))

    result = solid
    for c3, dia in holes or []:
        u, v = to2(c3)
        hole = (
            cq.Workplane(plane)
            .transformed(offset=cq.Vector(0, 0, 0.5))
            .moveTo(u, v)
            .circle(dia / 2)
            .extrude(-(abs(thickness) + 2))
        )
        result = result.cut(hole)
    return result


def detect_studs_aligned(mesh: trimesh.Trimesh, cyl_plane: dict):
    """4 goujons côté cylindre dans le repère aligné (Y haut)."""
    v = mesh.vertices
    n = cyl_plane["normal"]
    d = cyl_plane["d"]
    # tips: far along cylinder normal
    along = v @ n
    tips = v[along > np.percentile(along, 98)]
    if len(tips) < 20:
        return []
    # NMS in plane coords
    _, xdir, ydir = basis(n)
    uv = np.column_stack([(tips - tips.mean(0)) @ xdir, (tips - tips.mean(0)) @ ydir])
    # grid peaks
    cells = {}
    for p, (u, w) in zip(tips, uv):
        key = (round(u / 4) * 4, round(w / 4) * 4)
        al = float(p @ n)
        if key not in cells or al > cells[key][0]:
            cells[key] = (al, p)
    peaks = sorted(cells.values(), key=lambda t: -t[0])
    studs = []
    for al, p in peaks:
        p_plane = p - n * ((p @ n) - d)
        if all(np.linalg.norm(p_plane - s) > 25 for s in studs):
            studs.append(p_plane)
        if len(studs) >= 4:
            break
    return studs


def build_breps(mesh: trimesh.Trimesh, planes: dict) -> tuple[dict, dict]:
    cyl = planes["cylindre"]
    joint = planes["joint"]
    ign = planes["allumage"]

    studs = detect_studs_aligned(mesh, cyl)
    print(f"Goujons détectés: {len(studs)}")
    bore = 47.0
    pad_cyl = 120.0
    if len(studs) >= 4:
        # pad from stud span
        _, xdir, ydir = basis(cyl["normal"])
        uv = np.array([[(s - cyl["center"]) @ xdir, (s - cyl["center"]) @ ydir] for s in studs])
        pad_cyl = max(float(np.ptp(uv[:, 0])), float(np.ptp(uv[:, 1]))) + 30.0
        pad_cyl = float(np.clip(pad_cyl, 100.0, 160.0))

    holes = [(s, 8.5) for s in studs]
    holes.append((cyl["center"], bore))
    shapes = {
        "cylindre": extrude_pad(
            cyl["normal"], cyl["center"], size=pad_cyl, thickness=8.0, holes=holes, circular=True
        ),
        "joint": extrude_pad(
            joint["normal"],
            joint["center"],
            size=(140.0, 200.0),
            thickness=3.0,
        ),
        "allumage": extrude_pad(
            ign["normal"],
            ign["center"],
            size=120.0,
            thickness=6.0,
            holes=[(ign["center"], 28.0)],
        ),
    }
    meta = {
        "cylindre": {
            "normal": cyl["normal"].tolist(),
            "d": cyl["d"],
            "center": cyl["center"].tolist(),
            "points_3": cyl["points"].tolist(),
            "section": cyl["section"],
            "studs": [s.tolist() for s in studs],
            "bore": bore,
            "pad": pad_cyl,
        },
        "joint": {
            "normal": joint["normal"].tolist(),
            "d": joint["d"],
            "center": joint["center"].tolist(),
            "points_3": joint["points"].tolist(),
            "section": joint["section"],
        },
        "allumage": {
            "normal": ign["normal"].tolist(),
            "d": ign["d"],
            "center": ign["center"].tolist(),
            "points_3": ign["points"].tolist(),
            "section": ign["section"],
        },
    }
    return shapes, meta


def upload(mesh_stl: Path, steps: dict[str, Path], name: str) -> str:
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
    eng = trimesh.load(mesh_stl, force="mesh")
    eng_m = eng.copy()
    eng_m.apply_scale(0.001)
    mesh_m = OUT / "mina_aligned_meters.stl"
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

    print("Upload mesh aligné…")
    imp(mesh_m)
    for k, p in steps.items():
        print(f"Upload {k}…")
        imp(p)

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
            print(f"  insert {e['name']} vol={best_vol:.4e}")
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
            label = "ENSEMBLE aligné joint/cylindre/allumage"
        elif "cylindre" in nm:
            label = "_face cylindre B-Rep"
        elif "joint" in nm:
            label = "_plan joint B-Rep"
        elif "allumage" in nm:
            label = "_face allumage B-Rep"
        elif "mina_" in nm or nm.endswith(".stl") or "mesh" in nm:
            label = "_mesh aligné (joint=Right)"
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
    ap.add_argument("--stl", default=str(OUT / "mina_piece_80000.stl"))
    ap.add_argument("--upload", action="store_true")
    ap.add_argument(
        "--name",
        default="MINARELLI aligné 3-points — joint/cylindre/allumage",
    )
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")

    print("=== Plans 3 points + alignement origine ===")
    mesh = trimesh.load(args.stl, force="mesh")
    planes = detect_planes_3point(mesh)

    aligned, M, planes_a = align_mesh_to_origin(mesh, planes)
    # re-validate section after align on joint
    j = planes_a["joint"]
    # sample near origin
    dist = aligned.vertices @ j["normal"] - j["d"]
    near = np.abs(dist) < 3
    print(
        f"Post-align joint@origin: n={j['normal'].round(4)} "
        f"vertex|d|<3mm count={near.sum()} median_d={np.median(dist[near]) if near.any() else None}"
    )

    out_mesh = OUT / "mina_aligned_joint_right.stl"
    aligned.export(out_mesh)
    print(f"Mesh aligné → {out_mesh}")

    shapes, meta = build_breps(aligned, planes_a)
    steps = {}
    for k, sh in shapes.items():
        p = OUT / f"carter_{k}_aligned_brep.step"
        cq.exporters.export(sh, str(p))
        cq.exporters.export(sh, str(p.with_suffix(".stl")))
        bb = sh.val().BoundingBox()
        print(f"  B-Rep {k}: {bb.xlen:.1f}×{bb.ylen:.1f}×{bb.zlen:.1f}")
        steps[k] = p

    report = {
        "method": "three_point_planes_then_align_joint_to_right",
        "note": (
            "Planes from 3 spaced mesh vertices + section validation; "
            "mesh transformed so joint mates to Right/X=0 (mate-connector style)."
        ),
        "planes_before_align": {
            k: {
                "normal": v["normal"].tolist(),
                "d": v["d"],
                "points": v["points"].tolist(),
                "section": v["section"],
                "edges": v["edges"],
                "ok": v["ok"],
            }
            for k, v in planes.items()
        },
        "breps": meta,
        "transform_4x4": M.tolist(),
    }

    if args.upload:
        url = upload(out_mesh, steps, args.name)
        report["onshape_url"] = url
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")

    (OUT / "align_reverse_report.json").write_text(json.dumps(report, indent=2))
    (ROOT / "align_reverse_report.json").write_text(json.dumps(report, indent=2))
    print("Rapport → align_reverse_report.json")


if __name__ == "__main__":
    main()
