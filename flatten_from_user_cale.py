#!/usr/bin/env python3
"""
Aplatit le carter Minarelli en gardant la pose cale de l'utilisateur.

Référence (NE PAS reposicionner la cale sur le côté roulement vilo) :
  https://cad.onshape.com/documents/2c6f5dc90c562912ee912772/w/6ced650506796055997a4293/e/bc2e37baa9202f63561df6c0

- Les 4 trous de la calle vl14 = patron de référence des 4 trous carter
- Normal / orientation du plan = face d'appui de la cale (pose user)
- Position du plan (d) = surface mesh sous la cale (proximité), pour
  désarrasaser l'ondulation sans coller le mesh à 15 mm dans le vide
- La cale est publiée avec la transform user (bake STEP), pas recentrée en +X
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"
REF_PATH = ROOT / "cale_admission_ref.json"
POSE_PATH = ROOT / "user_cale_pose.json"
USER_DOC = (
    "https://cad.onshape.com/documents/2c6f5dc90c562912ee912772/"
    "w/6ced650506796055997a4293/e/bc2e37baa9202f63561df6c0"
)


def detect_cale_holes_local(cale_stl: Path) -> np.ndarray:
    cale = trimesh.load(cale_stl, force="mesh")
    # mating face ~ xmin
    x0 = float(cale.bounds[0, 0]) + 0.05
    sec = cale.section(plane_origin=[x0, 0, 0], plane_normal=[1, 0, 0])
    if sec is None:
        raise RuntimeError("section cale impossible")
    path2, tf = sec.to_2D()
    holes = []
    for poly in path2.polygons_full:
        for ring in poly.interiors:
            xs = np.asarray(ring.xy[0])
            ys = np.asarray(ring.xy[1])
            diam = 0.5 * (float(np.ptp(xs)) + float(np.ptp(ys)))
            if 5.5 < diam < 9.5:
                p3 = tf.dot([xs.mean(), ys.mean(), 0, 1])[:3]
                holes.append(p3)
    if len(holes) < 4:
        raise RuntimeError(f"trous cale détectés: {len(holes)}")
    return np.asarray(holes[:4], dtype=float)


def bake_cale_with_user_transform(src_step: Path, M_row: np.ndarray, out_step: Path) -> Path:
    """Bake assemble transform into STEP (Onshape mm via CadQuery)."""
    import cadquery as cq
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf

    shape = cq.importers.importStep(str(src_step))
    # M maps local meters -> world meters; CadQuery STEP is mm
    # p_world_mm = R @ p_local_mm + T_mm
    R = M_row[:3, :3]
    T_mm = M_row[:3, 3] * 1000.0
    tr = gp_Trsf()
    tr.SetValues(
        float(R[0, 0]), float(R[0, 1]), float(R[0, 2]), float(T_mm[0]),
        float(R[1, 0]), float(R[1, 1]), float(R[1, 2]), float(T_mm[1]),
        float(R[2, 0]), float(R[2, 1]), float(R[2, 2]), float(T_mm[2]),
    )
    aligned = cq.Shape.cast(
        BRepBuilderAPI_Transform(shape.val().wrapped, tr, True).Shape()
    )
    out_step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(aligned, str(out_step))
    cq.exporters.export(aligned, str(out_step.with_suffix(".stl")))
    return out_step


def flange_from_user_pose(engine: trimesh.Trimesh, holes_world_mm: np.ndarray, n_hint: np.ndarray):
    """Plan bride = orientation cale, d = surface mesh sous la cale."""
    n_hint = np.asarray(n_hint, float)
    n_hint = n_hint / (np.linalg.norm(n_hint) + 1e-12)
    C = holes_world_mm.mean(0)

    rng = np.random.default_rng(0)
    samples = [C]
    for h in holes_world_mm:
        samples.append(h)
        for _ in range(8):
            t1 = np.cross(n_hint, [1.0, 0, 0])
            if np.linalg.norm(t1) < 0.1:
                t1 = np.cross(n_hint, [0.0, 1.0, 0])
            t1 /= np.linalg.norm(t1)
            t2 = np.cross(n_hint, t1)
            samples.append(h + t1 * rng.normal(0, 12) + t2 * rng.normal(0, 12))
    samples = np.asarray(samples, float)
    prox = trimesh.proximity.ProximityQuery(engine)
    closest, dist, tid = prox.on_surface(samples)
    ok = np.abs(dist) < 40
    nearest = closest[ok] if ok.any() else closest
    sample_ok = samples[ok] if ok.any() else samples
    # Direction moteur → cale (= normale bride sortante)
    push = (sample_ok - nearest).mean(0)
    push = push / (np.linalg.norm(push) + 1e-12)

    c = nearest.mean(0)
    _, _, vh = np.linalg.svd(nearest - c, full_matrices=False)
    n_fit = vh[-1]
    n_fit /= np.linalg.norm(n_fit) + 1e-12
    # Orientation : aligner sur push (vers la cale), pas sur le sens ±X local ambigu
    n_use = n_fit.copy()
    if n_use @ push < 0:
        n_use = -n_use
    # Si le fit SVD dérive trop du plan des 4 trous, garder l'axe des trous (sens push)
    n_holes = n_hint.copy()
    if n_holes @ push < 0:
        n_holes = -n_holes
    if abs(float(n_use @ n_holes)) < 0.85:
        n_use = n_holes
    along = nearest @ n_use
    d = float(np.median(along))
    gap = float(np.mean(np.abs(dist[ok]))) if ok.any() else float(np.mean(np.abs(dist)))
    return n_use, d, c, gap


def flatten_flange_to_plane(
    mesh: trimesh.Trimesh,
    n: np.ndarray,
    d: float,
    center: np.ndarray,
    holes: np.ndarray,
    *,
    radius: float = 55.0,
    min_align: float = 0.7,
    max_dist: float = 4.0,
    min_frac: float = 0.75,
) -> tuple[trimesh.Trimesh, dict]:
    """Projection cœur + blend sur la bride (safe Onshape)."""
    v = mesh.vertices.copy()
    f = mesh.faces
    fn = mesh.face_normals
    fc = mesh.triangles_center

    # faces bride
    planar = fc - center
    r = np.linalg.norm(planar - np.outer(planar @ n, n), axis=1)
    along = fc @ n - d
    region = (fn @ n > min_align) & (r < radius) & (np.abs(along) < 8.0)
    face_ids = np.where(region)[0]
    if len(face_ids) < 30:
        region = (fn @ n > 0.5) & (r < radius + 10) & (np.abs(along) < 12.0)
        face_ids = np.where(region)[0]
    flange_set = set(map(int, face_ids))

    v2f: dict[int, list[int]] = defaultdict(list)
    for fi, tri in enumerate(f):
        for vid in tri:
            v2f[int(vid)].append(int(fi))
    nbrs: dict[int, set[int]] = defaultdict(set)
    for tri in f:
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        nbrs[a].update((b, c))
        nbrs[b].update((a, c))
        nbrs[c].update((a, b))

    vids = np.unique(f[face_ids].reshape(-1)).astype(int) if len(face_ids) else np.array([], int)
    core = []
    for vid in vids:
        faces_of = v2f[int(vid)]
        frac = sum(1 for fi in faces_of if fi in flange_set) / max(len(faces_of), 1)
        dist = float(v[vid] @ n - d)
        if frac < min_frac or abs(dist) > max_dist:
            continue
        v[vid] = v[vid] - dist * n
        core.append(int(vid))

    core_set = set(core)
    ring: set[int] = set()
    frontier = set(core)
    for _ in range(3):
        nxt: set[int] = set()
        for vid in frontier:
            for nb in nbrs[vid]:
                if nb not in core_set and nb not in ring:
                    nxt.add(nb)
        ring |= nxt
        frontier = nxt

    for _ in range(12):
        v2 = v.copy()
        for vid in ring:
            nbs = list(nbrs[vid])
            if not nbs:
                continue
            avg = v[nbs].mean(0)
            dist = float(v[vid] @ n - d)
            if abs(dist) < 6 and np.linalg.norm((v[vid] - center) - n * ((v[vid] - center) @ n)) < radius + 5:
                target = v[vid] - 0.45 * dist * n
            else:
                target = v[vid]
            v2[vid] = 0.55 * v[vid] + 0.25 * avg + 0.20 * target
        v = v2

    out = mesh.copy()
    out.vertices = v
    out.fix_normals()
    core_arr = np.array(core, int)
    if len(core_arr):
        rms = float(np.sqrt(np.mean((out.vertices[core_arr] @ n - d) ** 2)))
        span = float(np.ptp(out.vertices[core_arr] @ n))
    else:
        rms, span = None, None
    report = {
        "n_faces": int(len(face_ids)),
        "n_core": len(core),
        "n_blend": len(ring),
        "rms_core_after": rms,
        "span_core_after": span,
        "normal": n.tolist(),
        "d_mm": d,
        "center_mm": center.tolist(),
        "holes_ref_mm": holes.tolist(),
    }
    return out, report


def repair_single_body(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    try:
        mesh = mesh.copy()
        mesh.merge_vertices()
        trimesh.repair.fix_normals(mesh)
    except Exception:
        pass
    parts = mesh.split(only_watertight=False)
    parts = sorted(parts, key=lambda p: len(p.faces), reverse=True)
    out = parts[0]
    print(f"  repair: {len(parts)} composants → {len(out.faces)} faces wt={out.is_watertight}")
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stl", default=str(OUT / "mina_piece_80000.stl"))
    p.add_argument("--upload", action="store_true")
    p.add_argument("--name", default="MINARELLI + calle user-pose — ENSEMBLE")
    args = p.parse_args()

    load_dotenv(ROOT / ".env")
    ref = json.loads(REF_PATH.read_text())
    pose = json.loads(POSE_PATH.read_text())
    M = np.array(pose["transform_rowmajor"], float).reshape(4, 4)
    print("Réf user doc:", USER_DOC)
    print("Cale:", ref["name"], "trous coin entraxe ~", ref["ear_spacing_mm"], "mm (oreilles)")

    holes_local = detect_cale_holes_local(OUT / "cale_aligned.stl")
    holes_world = ((M[:3, :3] @ (holes_local / 1000.0).T).T + M[:3, 3]) * 1000.0
    print("4 trous cale → world mm:\n", holes_world)

    # Normal = thickness direction of cale (+X local), = outward from mating into cale
    n_out = M[:3, :3] @ np.array([1.0, 0, 0])
    n_out /= np.linalg.norm(n_out)
    # Engine flange outward normal ≈ same as direction engine→cale ≈ -n_out? 
    # +X local goes mating→cale body (away from engine). Engine flange outward = +X local dir = n_out
    n_flange = n_out.copy()

    engine = trimesh.load(args.stl, force="mesh")
    print(f"Mesh {len(engine.faces)} faces wt={engine.is_watertight}")

    n, d, center, gap = flange_from_user_pose(engine, holes_world, n_flange)
    print(f"Plan bride: n={n} d={d:.3f} center={center} gap_cale≈{gap:.1f} mm")

    # Project hole refs onto flange plane (patron 4 trous sur le carter)
    holes_on_plane = holes_world - np.outer((holes_world @ n) - d, n)
    print("4 trous projetés sur plan carter:\n", holes_on_plane)

    flat, report = flatten_flange_to_plane(
        engine, n, d, center, holes_on_plane, radius=55.0, max_dist=3.5
    )
    print(
        f"Flatten bride: faces={report['n_faces']} core={report['n_core']} "
        f"rms→{report['rms_core_after']} span→{report['span_core_after']}"
    )
    flat = repair_single_body(flat)
    out_stl = OUT / "mina_flattened.stl"
    flat.export(out_stl)
    print(f"STL → {out_stl} wt={flat.is_watertight} vol={flat.volume:.0f}")

    # Bake cale at USER pose (do not reseat on +X)
    cale_src = OUT / "cale_aligned.step"
    if not cale_src.exists():
        cale_src = OUT / "cale_admission.step"
    cale_baked = OUT / "cale_user_pose.step"
    bake_cale_with_user_transform(cale_src, M, cale_baked)
    print(f"Cale baked (user pose) → {cale_baked}")

    meta = {
        "method": "user_cale_four_holes_reference",
        "user_doc": USER_DOC,
        "cale_ref": ref,
        "transform_rowmajor": pose["transform_rowmajor"],
        "holes_cale_world_mm": holes_world.tolist(),
        "holes_on_flange_mm": holes_on_plane.tolist(),
        "flange_plane": {"normal": n.tolist(), "d_mm": d, "center_mm": center.tolist()},
        "gap_cale_to_mesh_mm": gap,
        "flatten": report,
        "watertight": bool(flat.is_watertight),
        "note": "Cale NOT moved to crankshaft-bearing/+X side; user assembly pose preserved.",
    }
    (OUT / "flatten_report.json").write_text(json.dumps(meta, indent=2))
    (ROOT / "flatten_report.json").write_text(json.dumps(meta, indent=2))
    (ROOT / "user_cale_pose.json").write_text(json.dumps({**pose, **meta}, indent=2))

    if args.upload:
        import align_cale_admission as ac

        old = ac.ENGINE_STL
        ac.ENGINE_STL = out_stl
        try:
            url = ac.upload_ensemble(cale_baked, args.name)
        finally:
            ac.ENGINE_STL = old
        meta["onshape_url"] = url
        (OUT / "flatten_report.json").write_text(json.dumps(meta, indent=2))
        (ROOT / "flatten_report.json").write_text(json.dumps(meta, indent=2))
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")
        print("Onglet ENSEMBLE — cale = ta pose, moteur aplati sur le plan des 4 trous.")


if __name__ == "__main__":
    main()
