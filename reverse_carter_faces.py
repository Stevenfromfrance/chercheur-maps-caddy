#!/usr/bin/env python3
"""
Rétro-ingénierie B-Rep du LOC MOTEUR (pas la cale clapet) :
  plan → esquisse idéale → extrusion pour :
    1) Face cylindre (goujons)
    2) Plan de joint carter
    3) Face allumage / bout vilo

Le mesh reste un calque. Solides CadQuery → STEP → Onshape.

Usage :
  python reverse_carter_faces.py --upload
"""

from __future__ import annotations

import argparse
import json
import os
from itertools import combinations
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"


def basis(n: np.ndarray):
    n = n / (np.linalg.norm(n) + 1e-12)
    a = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    x = np.cross(a, n)
    x /= np.linalg.norm(x) + 1e-12
    y = np.cross(n, x)
    return n, x, y


def fit_plane_from_faces(mesh, face_mask: np.ndarray, outward_hint: np.ndarray | None = None):
    pts = mesh.vertices[mesh.faces[face_mask]].reshape(-1, 3)
    if len(pts) < 30:
        raise RuntimeError("pas assez de points pour fit plan")
    # robust: keep points near median along hint or first PCA
    c0 = pts.mean(0)
    _, _, vh = np.linalg.svd(pts - c0, full_matrices=False)
    n = vh[-1]
    n /= np.linalg.norm(n) + 1e-12
    if outward_hint is not None and n @ outward_hint < 0:
        n = -n
    along = pts @ n
    d = float(np.percentile(along, 70 if outward_hint is not None else 50))
    # refine with band
    band = pts[np.abs(along - d) < 2.5]
    if len(band) > 30:
        c = band.mean(0)
        _, _, vh = np.linalg.svd(band - c, full_matrices=False)
        n2 = vh[-1]
        n2 /= np.linalg.norm(n2) + 1e-12
        if n2 @ n < 0:
            n2 = -n2
        n = n2
        d = float(np.median(band @ n))
        c = band.mean(0)
        rms = float(np.sqrt(np.mean((band @ n - d) ** 2)))
    else:
        c = c0
        rms = float(np.sqrt(np.mean((pts @ n - d) ** 2)))
    return n, d, c, rms


def detect_cylinder_plane(mesh: trimesh.Trimesh) -> dict:
    fn, fa, fc = mesh.face_normals, mesh.area_faces, mesh.triangles_center
    v = mesh.vertices
    # Deck: +Y faces high Y
    mask = (fn[:, 1] > 0.88) & (fc[:, 1] > 390) & (fc[:, 1] < 455)
    n, d, c, rms = fit_plane_from_faces(mesh, mask, outward_hint=np.array([0.0, 1.0, 0.0]))

    # Stud tips → 4-goujons pattern
    reg = v[(v[:, 1] > 420) & (v[:, 0] > 0) & (v[:, 0] < 140) & (v[:, 2] > -100) & (v[:, 2] < 100)]
    cells = []
    for x in np.arange(5, 135, 3):
        for z in np.arange(-90, 90, 3):
            m = (np.abs(reg[:, 0] - x) < 2.5) & (np.abs(reg[:, 2] - z) < 2.5)
            if m.sum() < 2:
                continue
            cells.append([x, z, float(reg[m, 1].max())])
    cells = np.array(cells)
    order = np.argsort(-cells[:, 2])
    peaks = []
    for i in order:
        x, z, ymax = cells[i]
        if ymax < 435:
            continue
        if all((x - p[0]) ** 2 + (z - p[1]) ** 2 > 28**2 for p in peaks):
            peaks.append([float(x), float(z), float(ymax)])
        if len(peaks) >= 8:
            break

    best = None
    for comb in combinations(range(len(peaks)), 4):
        pts = np.array([peaks[i][:2] for i in comb])
        cen = pts.mean(0)
        ang = np.arctan2(pts[:, 1] - cen[1], pts[:, 0] - cen[0])
        pts = pts[np.argsort(ang)]
        sides = [float(np.linalg.norm(pts[i] - pts[(i + 1) % 4])) for i in range(4)]
        diags = [
            float(np.linalg.norm(pts[0] - pts[2])),
            float(np.linalg.norm(pts[1] - pts[3])),
        ]
        score = abs(sides[0] - sides[2]) + abs(sides[1] - sides[3]) + abs(diags[0] - diags[1])
        area = 0.5 * abs(
            sum(pts[i, 0] * pts[(i + 1) % 4, 1] - pts[(i + 1) % 4, 0] * pts[i, 1] for i in range(4))
        )
        score -= 0.02 * area  # prefer larger
        if best is None or score < best[0]:
            best = (score, pts, [peaks[i] for i in comb], sides, diags)

    studs = []
    if best:
        for p in best[2]:
            tip = np.array([p[0], p[2], p[1]], float)  # x,y,z
            # project to deck
            studs.append(tip - n * ((tip @ n) - d))

    # Bore guess: circle through stud centroid, Ø from stud span
    bore_c = np.mean(studs, axis=0) if studs else c
    if studs:
        # average half-diagonal of stud rectangle as outer; bore ~ 0.55 of min side
        uv = np.array([[s[0], s[2]] for s in studs])
        side = min(
            float(np.linalg.norm(best[1][0] - best[1][1])),
            float(np.linalg.norm(best[1][1] - best[1][2])),
        )
        bore_d = max(40.0, min(56.0, side * 0.9))
        stud_span = (
            float(np.linalg.norm(best[1][0] - best[1][2])),
            float(np.linalg.norm(best[1][1] - best[1][3])),
        )
        pad = max(stud_span) + 28.0
    else:
        bore_d = 47.0
        pad = 110.0
        stud_span = None

    return {
        "name": "cylindre",
        "normal": n,
        "d": d,
        "center": bore_c,
        "rms": rms,
        "studs": studs,
        "bore_diameter": bore_d,
        "stud_diameter": 8.5,
        "pad_size": pad,
        "stud_span": stud_span,
        "quad_score": None if not best else float(best[0]),
    }


def detect_joint_plane(mesh: trimesh.Trimesh) -> dict:
    """Plan de joint idéalisé : grande face quasi-Z au milieu du carter."""
    fn, fa, fc = mesh.face_normals, mesh.area_faces, mesh.triangles_center
    # Prefer near-horizontal joint (common on some HOR) OR vertical mid
    # Use densest thin Z-band with high |nz|
    best = None
    for z0 in np.linspace(-30, 30, 25):
        mask = (np.abs(fn[:, 2]) > 0.92) & (np.abs(fc[:, 2] - z0) < 4) & (fc[:, 1] > 20) & (
            fc[:, 1] < 320
        )
        area = float(fa[mask].sum()) if mask.any() else 0.0
        if area < 1500:
            continue
        if best is None or area > best[0]:
            best = (area, z0, mask)

    if best is None:
        # fallback idealized Z=0
        n = np.array([0.0, 0.0, 1.0])
        d = 0.0
        c = mesh.bounds.mean(0)
        c[2] = 0.0
        rms = 0.0
    else:
        n, d, c, rms = fit_plane_from_faces(
            mesh, best[2], outward_hint=np.array([0.0, 0.0, 1.0])
        )

    # Pad covers main body mid-section
    body = mesh.vertices[
        (mesh.vertices[:, 1] > 20)
        & (mesh.vertices[:, 1] < 320)
        & (np.abs(mesh.vertices[:, 2] - c[2]) < 40)
    ]
    if len(body) > 100:
        pad_x = float(np.ptp(body[:, 0])) * 0.55
        pad_y = float(np.ptp(body[:, 1])) * 0.55
        c = np.array([float(np.median(body[:, 0])), float(np.median(body[:, 1])), c[2]])
    else:
        pad_x, pad_y = 120.0, 180.0

    return {
        "name": "joint",
        "normal": n,
        "d": d,
        "center": c,
        "rms": rms,
        "pad_w": max(80.0, pad_x),
        "pad_h": max(100.0, pad_y),
        "thickness": 3.0,
    }


def detect_ignition_plane(mesh: trimesh.Trimesh) -> dict:
    fn, fa, fc = mesh.face_normals, mesh.area_faces, mesh.triangles_center
    mask = (
        (fn[:, 1] < -0.9)
        & (fc[:, 1] > -40)
        & (fc[:, 1] < 50)
        & (fc[:, 0] > 10)
        & (fc[:, 0] < 130)
    )
    n, d, c, rms = fit_plane_from_faces(mesh, mask, outward_hint=np.array([0.0, -1.0, 0.0]))
    pts = mesh.vertices[mesh.faces[mask]].reshape(-1, 3)
    # size from face extent in plane
    _, x, y = basis(n)
    uv = np.column_stack([(pts - c) @ x, (pts - c) @ y])
    pad = max(float(np.ptp(uv[:, 0])), float(np.ptp(uv[:, 1]))) * 0.75
    pad = float(np.clip(pad, 80.0, 140.0))
    return {
        "name": "allumage",
        "normal": n,
        "d": d,
        "center": c,
        "rms": rms,
        "pad_size": pad,
        "thickness": 6.0,
        "center_hole": 28.0,  # passage / roulement approx
    }


def extrude_pad_on_plane(
    n: np.ndarray,
    center: np.ndarray,
    *,
    size: float | tuple[float, float],
    thickness: float,
    holes: list[tuple[np.ndarray, float]] | None = None,
    circle_outer: float | None = None,
) -> cq.Workplane:
    n, xdir, ydir = basis(n)
    # xDir for cq plane
    plane = cq.Plane(
        origin=cq.Vector(*map(float, center)),
        normal=cq.Vector(*map(float, n)),
        xDir=cq.Vector(*map(float, xdir)),
    )

    def to2(p):
        q = np.asarray(p, float) - center
        return float(q @ xdir), float(q @ ydir)

    wp = cq.Workplane(plane)
    if circle_outer is not None:
        solid = wp.circle(circle_outer / 2.0).extrude(-abs(thickness))
    else:
        if isinstance(size, tuple):
            w, h = size
        else:
            w = h = size
        solid = wp.rect(w, h).extrude(-abs(thickness))

    result = solid
    for center3, dia in holes or []:
        u, v = to2(center3)
        hole = (
            cq.Workplane(plane)
            .transformed(offset=cq.Vector(0, 0, 0.6))
            .moveTo(u, v)
            .circle(dia / 2.0)
            .extrude(-(abs(thickness) + 2.0))
        )
        result = result.cut(hole)
    return result


def build_all(mesh: trimesh.Trimesh) -> tuple[dict[str, cq.Workplane], dict]:
    cyl = detect_cylinder_plane(mesh)
    joint = detect_joint_plane(mesh)
    ign = detect_ignition_plane(mesh)

    print(
        f"CYLINDRE: Y≈{cyl['center'][1]:.1f} rms={cyl['rms']:.2f} "
        f"boreØ{cyl['bore_diameter']:.1f} studs={len(cyl['studs'])} pad={cyl['pad_size']:.1f}"
    )
    print(
        f"JOINT:    c={joint['center'].round(1)} rms={joint['rms']:.2f} "
        f"pad={joint['pad_w']:.0f}x{joint['pad_h']:.0f}"
    )
    print(
        f"ALLUMAGE: Y≈{ign['center'][1]:.1f} rms={ign['rms']:.2f} pad={ign['pad_size']:.1f}"
    )

    shapes = {}
    # Cylindre: circular deck + bore + stud holes
    holes = [(s, cyl["stud_diameter"]) for s in cyl["studs"]]
    holes.append((cyl["center"], cyl["bore_diameter"]))
    shapes["cylindre"] = extrude_pad_on_plane(
        cyl["normal"],
        cyl["center"],
        size=cyl["pad_size"],
        thickness=8.0,
        holes=holes,
        circle_outer=cyl["pad_size"],
    )

    shapes["joint"] = extrude_pad_on_plane(
        joint["normal"],
        joint["center"],
        size=(joint["pad_w"], joint["pad_h"]),
        thickness=joint["thickness"],
        holes=None,
    )

    shapes["allumage"] = extrude_pad_on_plane(
        ign["normal"],
        ign["center"],
        size=ign["pad_size"],
        thickness=ign["thickness"],
        holes=[(ign["center"], ign["center_hole"])],
    )

    meta = {
        "cylindre": {
            k: (v.tolist() if isinstance(v, np.ndarray) else v)
            for k, v in cyl.items()
            if k != "studs"
        }
        | {"studs": [s.tolist() for s in cyl["studs"]]},
        "joint": {
            k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in joint.items()
        },
        "allumage": {
            k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in ign.items()
        },
    }
    return shapes, meta


def upload_ensemble(mesh_stl: Path, step_paths: dict[str, Path], name: str) -> str:
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
    for label, path in step_paths.items():
        print(f"Upload B-Rep {label}…")
        imp(path)

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
                print(f"  insert {e['name']}: vol={best_vol:.4e}")
            except Exception as ex:
                print("  mp warn", ex)
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
            label = "ENSEMBLE loc moteur B-Rep"
        elif "mina_mesh" in nm or "meters" in nm:
            label = "_mesh calque"
        elif "cylindre" in nm:
            label = "_face cylindre B-Rep"
        elif "joint" in nm:
            label = "_plan joint B-Rep"
        elif "allumage" in nm:
            label = "_face allumage B-Rep"
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
    ap.add_argument("--name", default="MINARELLI loc moteur — joint/cylindre/allumage B-Rep")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    print("=== reverse_carter_faces (LOC MOTEUR, pas cale clapet) ===")
    mesh = trimesh.load(args.stl, force="mesh")
    print(f"Mesh {len(mesh.faces)} faces")

    shapes, meta = build_all(mesh)
    steps: dict[str, Path] = {}
    for key, shape in shapes.items():
        path = OUT / f"carter_{key}_brep.step"
        cq.exporters.export(shape, str(path))
        cq.exporters.export(shape, str(path.with_suffix(".stl")))
        bb = shape.val().BoundingBox()
        print(f"  STEP {key}: {path.name}  bbox {bb.xlen:.1f}×{bb.ylen:.1f}×{bb.zlen:.1f}")
        steps[key] = path

    report = {
        "method": "reverse_engineering_loc_moteur_faces",
        "focus": "joint + cylindre + allumage (NOT cale clapet)",
        "workflow": [
            "1. Plan de référence sur zones planes du mesh",
            "2. Esquisse idéale (cercles/rects) — pas le bruit scan",
            "3. Extrusion solide CadQuery → STEP",
            "4. Mesh gardé comme calque",
        ],
        "planes": meta,
    }

    if args.upload:
        url = upload_ensemble(Path(args.stl), steps, args.name)
        report["onshape_url"] = url
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")

    (OUT / "reverse_faces_report.json").write_text(json.dumps(report, indent=2))
    (ROOT / "reverse_faces_report.json").write_text(json.dumps(report, indent=2))
    print("Rapport → reverse_faces_report.json")


if __name__ == "__main__":
    main()
