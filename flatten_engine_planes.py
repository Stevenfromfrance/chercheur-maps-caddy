#!/usr/bin/env python3
"""
Aplatit les surfaces planes du mesh Minarelli (brides, plans de joint, faces
d'appui) pour supprimer les ondulations du scan.

Référence dimensionnelle : calle vl14 (cale_admission_ref.json) + pose manuelle
utilisateur dans l'assemblage Onshape si disponible (mina_scan/user_cale_pose.json).

Usage
-----
  python flatten_engine_planes.py
  python flatten_engine_planes.py --stl mina_scan/mina_clean_200k.stl --upload
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"
REF_PATH = ROOT / "cale_admission_ref.json"
POSE_PATH = OUT / "user_cale_pose.json"

# Bride admission (repère mesh mm) — affinée via cale
INTAKE_SEED = np.array([53.7, 60.0, -6.6])
INTAKE_HALF = np.array([6.0, 48.0, 48.0])


def load_ref() -> dict:
    return json.loads(REF_PATH.read_text())


def build_adjacency(n_faces: int, face_adjacency: np.ndarray) -> list[list[int]]:
    nbrs: list[list[int]] = [[] for _ in range(n_faces)]
    for a, b in face_adjacency:
        nbrs[int(a)].append(int(b))
        nbrs[int(b)].append(int(a))
    return nbrs


def grow_patch(
    seed: int,
    *,
    used: np.ndarray,
    fn: np.ndarray,
    fc: np.ndarray,
    fa: np.ndarray,
    nbrs: list[list[int]],
    ang_deg: float = 8.0,
    dist_tol: float = 1.0,
) -> tuple[list[int], np.ndarray, float]:
    n0 = fn[seed] / (np.linalg.norm(fn[seed]) + 1e-12)
    d0 = float(n0 @ fc[seed])
    cos_th = float(np.cos(np.radians(ang_deg)))
    region: list[int] = []
    q: deque[int] = deque([seed])
    seen = np.zeros(len(fn), dtype=bool)
    seen[seed] = True
    while q:
        f = q.popleft()
        if used[f]:
            continue
        n = fn[f] / (np.linalg.norm(fn[f]) + 1e-12)
        if float(n @ n0) < cos_th:
            continue
        if abs(float(n0 @ fc[f]) - d0) > dist_tol:
            continue
        region.append(f)
        for nb in nbrs[f]:
            if not seen[nb] and not used[nb]:
                seen[nb] = True
                q.append(nb)
    return region, n0, d0


def fit_plane(points: np.ndarray, n_hint: np.ndarray | None = None):
    c = points.mean(0)
    _, _, vh = np.linalg.svd(points - c, full_matrices=False)
    n = vh[-1]
    n = n / (np.linalg.norm(n) + 1e-12)
    if n_hint is not None and float(n @ n_hint) < 0:
        n = -n
    d = float(n @ c)
    dist = points @ n - d
    return n, d, c, float(np.sqrt(np.mean(dist**2))), float(np.ptp(dist))


def detect_patches(mesh: trimesh.Trimesh, *, min_area: float = 900.0, min_faces: int = 80):
    fn = mesh.face_normals
    fa = mesh.area_faces
    fc = mesh.triangles_center
    verts = mesh.vertices
    faces = mesh.faces
    nbrs = build_adjacency(len(faces), mesh.face_adjacency)
    used = np.zeros(len(faces), dtype=bool)
    order = np.argsort(-fa)
    patches = []
    for seed in order:
        seed = int(seed)
        if used[seed]:
            continue
        if fa[seed] < 1.2:
            break
        region, n0, _ = grow_patch(seed, used=used, fn=fn, fc=fc, fa=fa, nbrs=nbrs)
        if len(region) < min_faces:
            continue
        area = float(fa[region].sum())
        if area < min_area:
            continue
        used[np.array(region, dtype=np.int32)] = True
        pts = verts[faces[region]].reshape(-1, 3)
        rng = np.random.default_rng(0)
        sample = pts if len(pts) < 9000 else pts[rng.choice(len(pts), 9000, replace=False)]
        n, d, c, rms, span = fit_plane(sample, n0)
        patches.append(
            {
                "faces": np.array(region, dtype=np.int32),
                "area": area,
                "normal": n,
                "d": d,
                "center": c,
                "rms": rms,
                "span": span,
            }
        )
    patches.sort(key=lambda p: -p["area"])
    return patches


def merge_levels(patches: list[dict], *, ang_deg: float = 6.0, dist_tol: float = 1.2):
    """Regroupe des patchs coplanaires → un seul niveau (même n, même d)."""
    cos_th = float(np.cos(np.radians(ang_deg)))
    levels: list[dict] = []
    for p in patches:
        placed = False
        for lv in levels:
            if abs(float(p["normal"] @ lv["normal"])) < cos_th:
                continue
            # aligner le sens
            n = p["normal"]
            if float(n @ lv["normal"]) < 0:
                n = -n
                d = -p["d"]
            else:
                d = p["d"]
            if abs(d - lv["d"]) > dist_tol:
                continue
            lv["faces"] = np.concatenate([lv["faces"], p["faces"]])
            lv["area"] += p["area"]
            lv["members"] += 1
            # re-pondérer d / n légèrement
            w = p["area"]
            lv["normal"] = lv["normal"] * lv["area_acc"] + n * w
            lv["normal"] /= np.linalg.norm(lv["normal"]) + 1e-12
            lv["d"] = (lv["d"] * lv["area_acc"] + d * w) / (lv["area_acc"] + w)
            lv["area_acc"] += w
            placed = True
            break
        if not placed:
            levels.append(
                {
                    "faces": p["faces"].copy(),
                    "area": p["area"],
                    "area_acc": p["area"],
                    "normal": p["normal"].copy(),
                    "d": float(p["d"]),
                    "center": p["center"].copy(),
                    "members": 1,
                    "rms0": p["rms"],
                    "span0": p["span"],
                }
            )
    levels.sort(key=lambda x: -x["area"])
    return levels


def intake_flange_level(mesh: trimesh.Trimesh, ref: dict) -> dict:
    """Bride d'admission : plan forcé +X, d = médiane robuste, calé sur cotes cale."""
    v = mesh.vertices
    f = mesh.faces
    fn = mesh.face_normals
    fa = mesh.area_faces
    fc = mesh.triangles_center
    seed = INTAKE_SEED
    half = INTAKE_HALF
    mask = (
        (np.abs(fc[:, 0] - seed[0]) < half[0] + 2)
        & (np.abs(fc[:, 1] - seed[1]) < half[1])
        & (np.abs(fc[:, 2] - seed[2]) < half[2])
        & (fn[:, 0] > 0.75)
    )
    if mask.sum() < 50:
        # élargir
        mask = (
            (np.abs(fc[:, 0] - seed[0]) < 10)
            & (np.abs(fc[:, 1] - seed[1]) < 55)
            & (np.abs(fc[:, 2] - seed[2]) < 55)
            & (fn[:, 0] > 0.65)
        )
    face_ids = np.where(mask)[0].astype(np.int32)
    pts = v[f[face_ids]].reshape(-1, 3)
    # d cible = percentile haut de X (face d'appui externe) — plus stable que mean
    x = pts[:, 0]
    d = float(np.percentile(x, 70))
    n = np.array([1.0, 0.0, 0.0])
    c = np.array([d, float(np.median(pts[:, 1])), float(np.median(pts[:, 2]))])
    dist = pts @ n - d
    return {
        "name": "intake_flange",
        "faces": face_ids,
        "area": float(fa[face_ids].sum()),
        "normal": n,
        "d": d,
        "center": c,
        "rms0": float(np.sqrt(np.mean(dist**2))),
        "span0": float(np.ptp(dist)),
        "cale_ear_spacing_mm": ref.get("ear_spacing_mm"),
        "cale_size_mm": ref.get("size_mm"),
        "members": 1,
    }


def _vertex_faces(faces: np.ndarray) -> dict[int, list[int]]:
    from collections import defaultdict

    v2f: dict[int, list[int]] = defaultdict(list)
    for fi, tri in enumerate(faces):
        for vid in tri:
            v2f[int(vid)].append(fi)
    return v2f


def _vertex_neighbors(faces: np.ndarray) -> dict[int, set[int]]:
    from collections import defaultdict

    nbrs: dict[int, set[int]] = defaultdict(set)
    for tri in faces:
        a, b, c = (int(tri[0]), int(tri[1]), int(tri[2]))
        nbrs[a].update((b, c))
        nbrs[b].update((a, c))
        nbrs[c].update((a, b))
    return nbrs


def flatten_intake_core_blend(
    mesh: trimesh.Trimesh,
    intake: dict,
    *,
    min_frac: float = 0.85,
    max_dist: float = 6.0,
    blend_hops: int = 3,
) -> tuple[trimesh.Trimesh, dict]:
    """
    Aplatit la bride admission sans casser le manifold Onshape :
    - projection dure des sommets « cœur » (quasi 100 % faces bride)
    - anneau de blend autour pour éviter les plis
    Une projection brutale de toute la zone bride (parois de trous incluses)
    explosait le mesh en fragments à l'import Onshape.
    """
    d = float(intake["d"])
    face_ids = np.asarray(intake["faces"], dtype=np.int32)
    f = mesh.faces
    v = mesh.vertices.copy()
    flange_set = set(map(int, face_ids))
    v2f = _vertex_faces(f)
    nbrs = _vertex_neighbors(f)
    vids = np.unique(f[face_ids].reshape(-1)).astype(int)

    core: list[int] = []
    for vid in vids:
        faces_of = v2f[int(vid)]
        frac = sum(1 for fi in faces_of if fi in flange_set) / max(len(faces_of), 1)
        dist = float(v[vid, 0] - d)
        if frac < min_frac or abs(dist) > max_dist:
            continue
        v[vid, 0] = d
        core.append(int(vid))

    core_set = set(core)
    ring: set[int] = set()
    frontier = set(core)
    for _ in range(blend_hops):
        nxt: set[int] = set()
        for vid in frontier:
            for nb in nbrs[vid]:
                if nb not in core_set and nb not in ring:
                    nxt.add(nb)
        ring |= nxt
        frontier = nxt

    cy, cz = float(intake["center"][1]), float(intake["center"][2])
    for _ in range(12):
        v2 = v.copy()
        for vid in ring:
            nbs = list(nbrs[vid])
            if not nbs:
                continue
            avg = v[nbs].mean(0)
            near = (
                abs(v[vid, 0] - d) < 8
                and abs(v[vid, 1] - cy) < 55
                and abs(v[vid, 2] - cz) < 55
            )
            target_x = (0.5 * v[vid, 0] + 0.5 * d) if near else v[vid, 0]
            v2[vid, 0] = 0.55 * v[vid, 0] + 0.45 * target_x
            v2[vid, 1] = 0.7 * v[vid, 1] + 0.3 * avg[1]
            v2[vid, 2] = 0.7 * v[vid, 2] + 0.3 * avg[2]
        v = v2

    out = mesh.copy()
    out.vertices = v
    out.fix_normals()
    core_x = out.vertices[core, 0] if core else np.array([d])
    report = {
        "name": "intake_flange",
        "area": float(intake["area"]),
        "members": 1,
        "normal": [1.0, 0.0, 0.0],
        "d": d,
        "center": np.asarray(intake["center"]).tolist(),
        "n_core": len(core),
        "n_blend": len(ring),
        "rms_before": float(intake.get("rms0", 0)),
        "span_before": float(intake.get("span0", 0)),
        "rms_after": float(np.sqrt(np.mean((core_x - d) ** 2))),
        "span_after": float(np.ptp(core_x)),
        "mean_abs_move_mm": None,
        "max_abs_move_mm": None,
    }
    return out, report


def flatten_levels_iterative(
    mesh: trimesh.Trimesh,
    levels: list[dict],
    *,
    iters: int = 20,
    step: float = 0.3,
    max_abs: float = 2.0,
    min_frac: float = 0.75,
) -> tuple[trimesh.Trimesh, list[dict]]:
    """Petits pas vers le plan (hors bride) — safe pour Onshape."""
    f = mesh.faces
    v = mesh.vertices.copy()
    v2f = _vertex_faces(f)
    reports = []
    for lv in levels:
        if lv.get("name") == "intake_flange":
            continue
        face_ids = np.asarray(lv["faces"], dtype=np.int32)
        n = np.asarray(lv["normal"], dtype=np.float64)
        n = n / (np.linalg.norm(n) + 1e-12)
        d = float(lv["d"])
        faceset = set(map(int, face_ids))
        vids = np.unique(f[face_ids].reshape(-1))
        fracs = {
            int(vid): sum(1 for fi in v2f[int(vid)] if fi in faceset)
            / max(len(v2f[int(vid)]), 1)
            for vid in vids
        }

        def _stats():
            conf = [int(vid) for vid in vids if fracs[int(vid)] >= min_frac]
            if not conf:
                return 0.0, 0.0
            dist = v[conf] @ n - d
            return float(np.sqrt(np.mean(dist**2))), float(np.ptp(dist))

        rms0, span0 = _stats()
        for _ in range(iters):
            for vid in vids:
                frac = fracs[int(vid)]
                if frac < min_frac:
                    continue
                dist = float(v[vid] @ n - d)
                if abs(dist) > max_abs:
                    continue
                v[vid] = v[vid] - (step * frac * dist) * n
        rms1, span1 = _stats()
        reports.append(
            {
                "name": lv.get("name", "plane"),
                "area": float(lv.get("area", 0)),
                "members": int(lv.get("members", 1)),
                "normal": n.tolist(),
                "d": d,
                "center": np.asarray(lv.get("center", [0, 0, 0])).tolist(),
                "rms_before": rms0,
                "span_before": span0,
                "rms_after": rms1,
                "span_after": span1,
            }
        )
    out = mesh.copy()
    out.vertices = v
    out.fix_normals()
    return out, reports


def select_levels_to_flatten(patches: list[dict], intake: dict, *, top_n: int = 25) -> list[dict]:
    levels = merge_levels(patches[:60], ang_deg=5.0, dist_tol=1.0)
    # garder les plus grandes + bride
    keep = []
    for lv in levels[:top_n]:
        # ignorer les patchs déjà très plats et minuscules
        if lv["area"] < 1200:
            continue
        keep.append(lv)
    # remplacer / ajouter intake en tête (prioritaire)
    keep = [lv for lv in keep if abs(float(lv["normal"][0])) < 0.9 or abs(lv["d"] - intake["d"]) > 8]
    keep.insert(0, intake)
    return keep


def realign_cale_to_flange(flange_d: float, flange_center_yz: np.ndarray) -> Path:
    """Recrée un STEP cale assis sur la bride aplatie (épaisseur vers +X)."""
    import cadquery as cq
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf

    from align_cale_admission import CALE_STEP, EARS, export_cale_step

    if not CALE_STEP.exists():
        export_cale_step()
    shape = cq.importers.importStep(str(CALE_STEP))
    bb = shape.val().BoundingBox()
    cx, cy = float(bb.center.x), float(bb.center.y)
    z_mate = float(bb.zmax)
    # Rotation: Z_cale -> -X_world (épaisseur sortante +X), Y conservée à peu près
    # Même convention que align_cale_admission (oreilles)
    ears_local = EARS - np.array([cx, cy])
    # angle pour aligner entraxe oreilles sur Z monde (scan) — rot -83° validée + reflect
    deg, reflect = -83, True
    ang = np.radians(deg)
    c, s = np.cos(ang), np.sin(ang)
    Ref = np.diag([-1.0, 1.0, 1.0]) if reflect else np.eye(3)
    R_xy = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    S = np.diag([1.0, 1.0, -1.0])
    R_axes = np.array([[0, 0, 1.0], [1, 0, 0], [0, 1, 0]])
    R = R_axes @ R_xy @ Ref @ S
    origin = np.array([cx, cy, z_mate])
    T = np.array([flange_d + 0.05, flange_center_yz[0], flange_center_yz[1]])
    Trans = T - R @ origin
    tr = gp_Trsf()
    tr.SetValues(
        R[0, 0], R[0, 1], R[0, 2], Trans[0],
        R[1, 0], R[1, 1], R[1, 2], Trans[1],
        R[2, 0], R[2, 1], R[2, 2], Trans[2],
    )
    aligned = cq.Shape.cast(BRepBuilderAPI_Transform(shape.val().wrapped, tr, True).Shape())
    out = OUT / "cale_on_flat_flange.step"
    cq.exporters.export(aligned, str(out))
    cq.exporters.export(aligned, str(OUT / "cale_on_flat_flange.stl"))
    return out


def repair_single_body(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Garde un seul corps, normals OK — critique pour l'import Onshape."""
    mesh = mesh.copy()
    try:
        mesh.merge_vertices()
    except Exception:
        pass
    try:
        trimesh.repair.fix_normals(mesh)
        trimesh.repair.fix_inversion(mesh)
    except Exception:
        pass
    parts = mesh.split(only_watertight=False)
    if not parts:
        return mesh
    parts = sorted(parts, key=lambda p: (len(p.faces), abs(getattr(p, "volume", 0) or 0)), reverse=True)
    out = parts[0]
    try:
        out.process(validate=True)
    except Exception:
        pass
    print(
        f"  repair: {len(parts)} composants → keep {len(out.faces)} faces "
        f"watertight={out.is_watertight}"
    )
    return out


def main():
    p = argparse.ArgumentParser()
    # 80k watertight de préférence (200k non-manifold → Onshape éclate en fragments)
    p.add_argument("--stl", default=str(OUT / "mina_piece_80000.stl"))
    p.add_argument("--faces", type=int, default=80000, help="décimation sortie")
    p.add_argument("--upload", action="store_true")
    p.add_argument("--name", default="MINARELLI aplati + calle vl14 — ENSEMBLE")
    args = p.parse_args()

    ref = load_ref()
    print(f"Réf cale: {ref['name']} {ref['size_mm']} ears={ref['ear_spacing_mm']} mm")
    if POSE_PATH.exists():
        pose = json.loads(POSE_PATH.read_text())
        print(f"Pose manuelle lue: mating center {pose.get('mating_face_center_mm')}")

    mesh = trimesh.load(args.stl, force="mesh")
    print(f"Mesh in: {len(mesh.faces)} faces, watertight={mesh.is_watertight}, extents {mesh.extents}")

    print("Détection des plans…")
    patches = detect_patches(mesh, min_area=700, min_faces=40)
    print(f"  {len(patches)} patchs")
    intake = intake_flange_level(mesh, ref)
    print(
        f"  Bride admission: d={intake['d']:.3f} rms={intake['rms0']:.2f} "
        f"span={intake['span0']:.2f} area={intake['area']:.0f}"
    )

    levels = select_levels_to_flatten(patches, intake, top_n=20)
    # hors bride : seulement plans déjà assez réguliers
    other = [
        lv
        for lv in levels
        if lv.get("name") != "intake_flange" and float(lv.get("rms0", lv.get("rms", 99))) <= 0.7
    ]
    print(f"Niveaux secondaires: {len(other)} (+ bride cœur/blend)")

    print("Aplatissement bride (cœur + blend)…")
    flat, intake_report = flatten_intake_core_blend(mesh, intake)
    print(
        f"  intake core={intake_report['n_core']} blend={intake_report['n_blend']} "
        f"rms {intake_report['rms_before']:.2f}→{intake_report['rms_after']:.2f}"
    )
    flat, reports = flatten_levels_iterative(flat, other)
    reports = [intake_report] + reports
    print("Aplatissement autres plans:")
    for r in reports[1:12]:
        print(
            f"  {r['name']:16s} rms {r['rms_before']:.2f}→{r['rms_after']:.2f}  "
            f"span {r['span_before']:.2f}→{r['span_after']:.2f}"
        )

    flat = repair_single_body(flat)
    if not flat.is_watertight:
        print("WARN: mesh non watertight — Onshape peut fragmenter l'import")

    # Décimer pour Onshape (après repair, pour rester manifold)
    if args.faces and len(flat.faces) > args.faces:
        flat = flat.simplify_quadric_decimation(face_count=args.faces)
        flat = repair_single_body(flat)
        print(f"Décimé → {len(flat.faces)} faces watertight={flat.is_watertight}")

    OUT.mkdir(parents=True, exist_ok=True)
    out_stl = OUT / "mina_flattened.stl"
    flat.export(out_stl)
    print(f"STL → {out_stl} faces={len(flat.faces)} watertight={flat.is_watertight}")

    meta = {
        "source_stl": args.stl,
        "cale_ref": ref,
        "user_pose": json.loads(POSE_PATH.read_text()) if POSE_PATH.exists() else None,
        "intake_flange_d_mm": intake["d"],
        "intake_center_mm": intake["center"].tolist(),
        "levels": reports,
        "n_faces_out": len(flat.faces),
        "watertight": bool(flat.is_watertight),
    }
    (OUT / "flatten_report.json").write_text(json.dumps(meta, indent=2))

    # Cale sur bride aplatie
    print("Recalage cale sur bride aplatie…")
    cale_step = realign_cale_to_flange(intake["d"], intake["center"][1:])
    print(f"  STEP cale → {cale_step}")

    if args.upload:
        import align_cale_admission as ac

        old = ac.ENGINE_STL
        ac.ENGINE_STL = out_stl
        try:
            url = ac.upload_ensemble(cale_step, args.name)
        finally:
            ac.ENGINE_STL = old
        meta["onshape_url"] = url
        (OUT / "flatten_report.json").write_text(json.dumps(meta, indent=2))
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")
        print("Ouvre l'onglet « ENSEMBLE moteur + cale ».")


if __name__ == "__main__":
    main()
