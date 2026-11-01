#!/usr/bin/env python3
"""
Peaufinage suite : split carter G / D + nervures + bossages fonderie.

Part du solide `build_carter()` (repère joint=X=0), puis :
  1) Bossages roulement / côtés (cercles détectés sur coupes X)
  2) Nervures structurelles autour du vilo + vers le cylindre
  3) Congés de fonderie sur arêtes extérieures
  4) Split G (X≤0) / D (X≥0) avec face de joint
  5) Upload ENSEMBLE : mesh + carter G + carter D

Usage :
  python rebuild_carter_halves.py --upload
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

import rebuild_carter_brep as base

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"


def detect_side_bosses(mesh: trimesh.Trimesh) -> list[dict]:
    """Cercles latéraux (logements roulement / bossages) hors du plan de joint."""
    bosses = []
    for t in list(np.linspace(45, 120, 16)) + list(np.linspace(-80, -40, 9)):
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
                if len(xy) < 20:
                    continue
                c = xy.mean(0)
                r = np.linalg.norm(xy - c, axis=1)
                rm, rs = float(r.mean()), float(r.std())
                if not (10.0 <= rm <= 40.0) or rs > rm * 0.08:
                    continue
                p3 = (tf @ np.array([c[0], c[1], 0, 1.0]))[:3]
                if not (-30 < p3[1] < 130):
                    continue
                bosses.append(
                    {
                        "x": float(t),
                        "center": np.array([float(t), float(p3[1]), float(p3[2])]),
                        "radius": rm,
                        "roundness": rs / rm,
                    }
                )
    # cluster by YZ + side
    clusters: list[dict] = []
    for b in bosses:
        side = "D" if b["x"] > 0 else "G"
        placed = False
        for cl in clusters:
            if cl["side"] != side:
                continue
            if np.linalg.norm(b["center"][1:] - cl["center"][1:]) < 18:
                cl["samples"].append(b)
                placed = True
                break
        if not placed:
            clusters.append({"side": side, "center": b["center"].copy(), "samples": [b]})

    out = []
    for cl in clusters:
        xs = [s["x"] for s in cl["samples"]]
        rs = [s["radius"] for s in cl["samples"]]
        cs = np.mean([s["center"] for s in cl["samples"]], axis=0)
        out.append(
            {
                "side": cl["side"],
                "center": np.array([float(np.mean(xs)), float(cs[1]), float(cs[2])]),
                "radius": float(np.median(rs)),
                "x_min": float(min(xs)),
                "x_max": float(max(xs)),
                "n": len(cl["samples"]),
            }
        )
    out.sort(key=lambda b: -b["n"])
    return out


def add_bearing_bosses(solid: cq.Workplane, bosses: list[dict], crank: dict) -> cq.Workplane:
    """Union de bossages cylindriques + alésage au diamètre détecté."""
    result = solid
    crank_c = np.array(crank["center"], float)
    for b in bosses[:6]:
        # Prefer bosses near crank axis in YZ
        dist = float(np.linalg.norm(b["center"][1:] - crank_c[1:]))
        if dist > 35 and b["n"] < 3:
            continue
        r_out = float(b["radius"] + 10.0)
        r_in = float(max(b["radius"] - 0.2, 8.0))
        x0, x1 = float(b["x_min"] - 3), float(b["x_max"] + 3)
        if abs(x1 - x0) < 8:
            if b["side"] == "D":
                x0, x1 = float(b["center"][0] - 8), float(b["center"][0] + 18)
            else:
                x0, x1 = float(b["center"][0] - 18), float(b["center"][0] + 8)
        # build along X
        plane = cq.Plane(
            origin=cq.Vector(float(x0), float(b["center"][1]), float(b["center"][2])),
            normal=cq.Vector(1, 0, 0),
            xDir=cq.Vector(0, 1, 0),
        )
        boss = cq.Workplane(plane).circle(r_out).extrude(float(x1 - x0))
        hole = cq.Workplane(plane).circle(r_in).extrude(float(x1 - x0) + 2)
        result = result.union(boss).cut(hole)
        print(
            f"  boss {b['side']}: Øext={2*r_out:.1f} Øint={2*r_in:.1f} "
            f"X={x0:.0f}→{x1:.0f} @ YZ=({b['center'][1]:.1f},{b['center'][2]:.1f})"
        )
    return result


def add_ribs(solid: cq.Workplane, crank: dict, cyl: dict) -> cq.Workplane:
    """Nervures fonderie : radiales autour vilo + liaison vers cylindre."""
    result = solid
    cc = np.array(crank["center"], float)
    bore_c = np.array(cyl["center"], float)
    rib_t = 4.5  # épaisseur nervure
    rib_h = 18.0  # hauteur depuis plan médian

    # Radial ribs in YZ around crank, extruded thinly in ±X near joint
    angles = np.linspace(0, 180, 7)[:-1]  # 6 nervures demi-carter
    for ang in angles:
        rad = np.radians(ang)
        # rib as thin box from r=28 to r=55
        direction = np.array([0.0, np.cos(rad), np.sin(rad)])
        mid = cc + direction * 42.0
        # local frame: rib plane contains X and radial dir
        xdir = np.array([0.0, -np.sin(rad), np.cos(rad)])  # tangential
        plane = cq.Plane(
            origin=cq.Vector(0.0, float(mid[1]), float(mid[2])),
            normal=cq.Vector(*map(float, xdir)),
            xDir=cq.Vector(1, 0, 0),
        )
        # rect: length along radial≈30, height along X≈22 (both sides of joint)
        rib = cq.Workplane(plane).rect(24.0, 30.0).extrude(rib_t / 2, both=True)
        result = result.union(rib)

    # Longitudinal rib crank → cylinder (along Y, thin in Z, across joint X)
    y0, y1 = float(cc[1] + 30), float(bore_c[1] - 40)
    if y1 > y0 + 20:
        z = float(0.5 * (cc[2] + bore_c[2]))
        spine = (
            cq.Workplane("XY")
            .workplane(offset=z)
            .center(0, (y0 + y1) / 2)
            .rect(28.0, (y1 - y0))
            .extrude(rib_t / 2, both=True)
        )
        result = result.union(spine)
        # two side spines offset in Z
        for dz in (-28.0, 28.0):
            side = (
                cq.Workplane("XY")
                .workplane(offset=z + dz)
                .center(0, (y0 + y1) / 2)
                .rect(18.0, (y1 - y0) * 0.7)
                .extrude(rib_t / 2, both=True)
            )
            result = result.union(side)
        print(f"  nervure longitudinale Y={y0:.0f}→{y1:.0f}")

    print(f"  nervures radiales: {len(angles)}")
    return result


def add_casting_fillets(solid: cq.Workplane, radius: float = 1.5) -> cq.Workplane:
    """Congés fonderie (best-effort) sur arêtes droites moyennes."""
    try:
        return solid.edges("%Line").fillet(radius)
    except Exception:
        pass
    try:
        # repli : seulement arêtes // axes
        return solid.edges("|Z").fillet(radius)
    except Exception as exc:
        print(f"  WARN fillet skip: {exc}")
        return solid


def split_halves(solid: cq.Workplane) -> tuple[cq.Workplane, cq.Workplane]:
    """Coupe au plan de joint X=0 → carter G (X≤0) et D (X≥0)."""
    # Boîtes axis-aligned claires (repère monde) :
    #  - cutter +X centré en x=+1000, taille 2000 → couvre ]0, 2000]
    #  - cutter −X centré en x=−1000, taille 2000 → couvre [−2000, 0[
    cutter_plus = cq.Workplane("XY").box(2000, 5000, 5000).translate((1000.05, 0, 0))
    cutter_minus = cq.Workplane("XY").box(2000, 5000, 5000).translate((-1000.05, 0, 0))
    carter_g = solid.cut(cutter_plus)  # garde X ≤ 0
    carter_d = solid.cut(cutter_minus)  # garde X ≥ 0
    return carter_g, carter_d


def upload_halves(mesh_stl: Path, steps: dict[str, Path], name: str) -> str:
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
    mesh_m = OUT / "mina_carter_halves_mesh_meters.stl"
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

    print("Upload mesh…")
    imp(mesh_m)
    for key, path in steps.items():
        print(f"Upload {key}…")
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
            label = "ENSEMBLE carter G + D + mesh"
        elif "carter_g" in nm or nm.endswith("_g.step") or "gauche" in nm:
            label = "_carter G (X≤0)"
        elif "carter_d" in nm or nm.endswith("_d.step") or "droit" in nm:
            label = "_carter D (X≥0)"
        elif "full" in nm or ("carter" in nm and "brep" in nm):
            label = "_carter complet (avant split)"
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
    ap.add_argument("--no-fillet", action="store_true")
    ap.add_argument(
        "--name",
        default="MINARELLI carter G/D — split + nervures",
    )
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")

    print("=== Carter G/D + nervures + bossages ===")
    mesh = trimesh.load(args.stl, force="mesh")
    meta = base.load_aligned_meta()

    solid, info = base.build_carter(mesh, meta)

    print("Bossages latéraux…")
    bosses = detect_side_bosses(mesh)
    print(f"  détectés: {len(bosses)}")
    solid = add_bearing_bosses(solid, bosses, info["crank"])

    print("Nervures…")
    solid = add_ribs(solid, info["crank"], info["cylinder"])

    # Export full before split
    step_full = OUT / "carter_moteur_full_brep.step"
    cq.exporters.export(solid, str(step_full))
    cq.exporters.export(solid, str(OUT / "carter_moteur_full_brep.stl"))
    bb = solid.val().BoundingBox()
    print(f"Complet: {bb.xlen:.1f}×{bb.ylen:.1f}×{bb.zlen:.1f} vol≈{solid.val().Volume()/1000:.0f} cm³")

    print("Split G/D…")
    carter_g, carter_d = split_halves(solid)

    if not args.no_fillet:
        print("Congés fonderie (par demi-carter)…")
        carter_g = add_casting_fillets(carter_g, radius=1.5)
        carter_d = add_casting_fillets(carter_d, radius=1.5)

    step_g = OUT / "carter_g_brep.step"
    step_d = OUT / "carter_d_brep.step"
    cq.exporters.export(carter_g, str(step_g))
    cq.exporters.export(carter_d, str(step_d))
    cq.exporters.export(carter_g, str(OUT / "carter_g_brep.stl"))
    cq.exporters.export(carter_d, str(OUT / "carter_d_brep.stl"))
    bg, bd = carter_g.val().BoundingBox(), carter_d.val().BoundingBox()
    print(
        f"  G: X[{bg.xmin:.1f},{bg.xmax:.1f}] Y[{bg.ymin:.1f},{bg.ymax:.1f}] "
        f"vol≈{carter_g.val().Volume()/1000:.0f} cm³"
    )
    print(
        f"  D: X[{bd.xmin:.1f},{bd.xmax:.1f}] Y[{bd.ymin:.1f},{bd.ymax:.1f}] "
        f"vol≈{carter_d.val().Volume()/1000:.0f} cm³"
    )

    report = {
        "method": "build_carter_then_bosses_ribs_fillet_split_GD",
        "goal": "carter G + D éditables avec nervures/bossages fonderie",
        "carter_base": info,
        "side_bosses": [
            {
                "side": b["side"],
                "center": b["center"].tolist(),
                "radius": b["radius"],
                "x_span": [b["x_min"], b["x_max"]],
                "n": b["n"],
            }
            for b in bosses
        ],
        "halves": {
            "G": {"bbox": [bg.xlen, bg.ylen, bg.zlen], "volume_mm3": float(carter_g.val().Volume())},
            "D": {"bbox": [bd.xlen, bd.ylen, bd.zlen], "volume_mm3": float(carter_d.val().Volume())},
        },
        "files": {
            "full": str(step_full),
            "G": str(step_g),
            "D": str(step_d),
        },
    }

    steps = {
        "carter_g_brep": step_g,
        "carter_d_brep": step_d,
        "carter_moteur_full_brep": step_full,
    }
    if args.upload:
        url = upload_halves(Path(args.stl), steps, args.name)
        report["onshape_url"] = url
        (OUT / "carter_halves_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")

    (OUT / "carter_halves_report.json").write_text(json.dumps(report, indent=2))
    (ROOT / "carter_halves_report.json").write_text(json.dumps(report, indent=2))
    print("Rapport → carter_halves_report.json")


if __name__ == "__main__":
    main()
