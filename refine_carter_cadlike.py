#!/usr/bin/env python3
"""
Affine le carter Minarelli scan → aspect CAD-like (mesh) :
  - bride d'admission plane (pose cale user / 4 trous)
  - trous cylindriques parfaits (cotes calle vl14)
  - autres faces d'appui adoucies
  - ENSEMBLE Onshape avec cale baked à la pose USER (pas de recentrage +X)

Réfs :
  pose user : documents/2c6f5dc90c562912ee912772/...
  calle vl14 : documents/a21e5846c7f0224fd076feed/...

Usage :
  python refine_carter_cadlike.py
  python refine_carter_cadlike.py --upload
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import trimesh
from dotenv import load_dotenv

import flatten_from_user_cale as fuc

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"
REF_PATH = ROOT / "cale_admission_ref.json"
POSE_PATH = ROOT / "user_cale_pose.json"
USER_DOC = fuc.USER_DOC


def _basis(n: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = n / (np.linalg.norm(n) + 1e-12)
    a = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    t1 = np.cross(n, a)
    t1 /= np.linalg.norm(t1) + 1e-12
    t2 = np.cross(n, t1)
    return t1, t2


def hole_specs_from_ref(ref: dict, pose: dict, n: np.ndarray, d: float) -> list[dict]:
    """4 coins + 2 oreilles ; centres projetés sur le plan bride mesh."""
    specs = []
    corners_w = pose.get("corner_holes_world_mm")
    ears_w = pose.get("ear_holes_world_mm")
    if not corners_w:
        # fallback : trous détectés section cale
        M = np.array(pose["transform_rowmajor"], float).reshape(4, 4)
        loc = fuc.detect_cale_holes_local(OUT / "cale_aligned.stl")
        corners_w = ((M[:3, :3] @ (loc / 1000.0).T).T + M[:3, 3]) * 1000.0
        corners_w = corners_w.tolist()
        ears_w = []

    for h, spec in zip(corners_w, ref["corner_holes_xy_mm"]):
        specs.append(
            {
                "kind": "corner",
                "center_world_mm": list(h),
                "diameter_mm": float(spec["diameter"]),
            }
        )
    for h, spec in zip(ears_w or [], ref["ear_holes_xy_mm"]):
        specs.append(
            {
                "kind": "ear",
                "center_world_mm": list(h),
                "diameter_mm": float(spec["diameter"]),
            }
        )

    out = []
    for s in specs:
        c = np.asarray(s["center_world_mm"], float)
        c_plane = c - n * ((c @ n) - d)
        out.append(
            {
                **s,
                "center_on_flange_mm": c_plane.tolist(),
                "radius_mm": 0.5 * s["diameter_mm"],
            }
        )
    return out


def measure_hole_radius(
    mesh: trimesh.Trimesh, center: np.ndarray, n: np.ndarray, radius: float, depth: float = 10.0
) -> dict:
    v = mesh.vertices
    d = v - center
    along = d @ n
    rad_vec = d - np.outer(along, n)
    r = np.linalg.norm(rad_vec, axis=1)
    mask = (along < 1.5) & (along > -depth) & (r > radius * 0.55) & (r < radius * 1.55)
    if mask.sum() < 8:
        return {"n": int(mask.sum()), "rms": None, "median": None, "span": None}
    rr = r[mask]
    return {
        "n": int(mask.sum()),
        "rms": float(np.sqrt(np.mean((rr - radius) ** 2))),
        "median": float(np.median(rr)),
        "span": float(np.ptp(rr)),
    }


def snap_holes_to_cylinders(
    mesh: trimesh.Trimesh,
    holes: list[dict],
    n: np.ndarray,
    *,
    depth: float = 12.0,
    wall_band: float = 2.2,
) -> tuple[trimesh.Trimesh, list[dict]]:
    """
    Projette les sommets des parois de trou sur un cylindre parfait.
    Plus sûr qu'un boolean (pas de fragmentation Onshape).
    """
    v = mesh.vertices.copy()
    reports = []
    for h in holes:
        c = np.asarray(h["center_on_flange_mm"], float)
        radius = float(h["radius_mm"])
        before = measure_hole_radius(mesh, c, n, radius, depth=depth)

        dvec = v - c
        along = dvec @ n
        rad_vec = dvec - np.outer(along, n)
        r = np.linalg.norm(rad_vec, axis=1)

        # paroi : bande autour du rayon cible, dans la profondeur du trou
        wall = (
            (along < 1.2)
            & (along > -depth)
            & (r > max(0.8, radius - wall_band))
            & (r < radius + wall_band)
        )
        # rim bride : quasi sur le plan, près du cercle
        rim = (np.abs(along) < 1.0) & (r > radius - 1.2) & (r < radius + 1.8)

        idx = np.where(wall | rim)[0]
        moved = 0
        for i in idx:
            if r[i] < 1e-8:
                continue
            # garder la profondeur, forcer rayon ; rim aussi collé au plan
            along_i = float(along[i])
            if rim[i] and not wall[i]:
                along_i = 0.0
            elif rim[i] and abs(along_i) < 0.6:
                along_i = 0.0
            dir_r = rad_vec[i] / r[i]
            v[i] = c + along_i * n + dir_r * radius
            moved += 1

        tmp = mesh.copy()
        tmp.vertices = v
        after = measure_hole_radius(tmp, c, n, radius, depth=depth)
        reports.append(
            {
                "kind": h["kind"],
                "center_on_flange_mm": c.tolist(),
                "diameter_mm": h["diameter_mm"],
                "n_verts_moved": moved,
                "radius_rms_before": before["rms"],
                "radius_rms_after": after["rms"],
                "radius_span_before": before["span"],
                "radius_span_after": after["span"],
                "radius_median_before": before["median"],
                "radius_median_after": after["median"],
            }
        )

    out = mesh.copy()
    out.vertices = v
    out.fix_normals()
    return out, reports


def detect_support_planes(
    mesh: trimesh.Trimesh,
    *,
    min_area: float = 2500.0,
    min_faces: int = 80,
    ang_deg: float = 8.0,
    dist_tol: float = 1.0,
) -> list[dict]:
    """Gros patchs plans (hors bride déjà gérée)."""
    fn = mesh.face_normals
    fa = mesh.area_faces
    fc = mesh.triangles_center
    faces = mesh.faces
    verts = mesh.vertices
    adj = mesh.face_adjacency
    nbrs = [[] for _ in range(len(faces))]
    for a, b in adj:
        nbrs[int(a)].append(int(b))
        nbrs[int(b)].append(int(a))

    used = np.zeros(len(faces), dtype=bool)
    order = np.argsort(-fa)
    patches = []

    def grow(seed: int):
        n0 = fn[seed] / (np.linalg.norm(fn[seed]) + 1e-12)
        d0 = float(n0 @ fc[seed])
        cos_th = float(np.cos(np.radians(ang_deg)))
        region: list[int] = []
        q = deque([seed])
        seen = np.zeros(len(faces), dtype=bool)
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
        return region, n0

    for seed in order:
        seed = int(seed)
        if used[seed] or fa[seed] < 1.5:
            if fa[seed] < 1.5:
                break
            continue
        region, n0 = grow(seed)
        if len(region) < min_faces:
            continue
        area = float(fa[region].sum())
        if area < min_area:
            continue
        used[np.array(region, dtype=np.int32)] = True
        pts = verts[faces[region]].reshape(-1, 3)
        rng = np.random.default_rng(0)
        sample = pts if len(pts) < 6000 else pts[rng.choice(len(pts), 6000, replace=False)]
        c = sample.mean(0)
        _, _, vh = np.linalg.svd(sample - c, full_matrices=False)
        n = vh[-1]
        n /= np.linalg.norm(n) + 1e-12
        if n @ n0 < 0:
            n = -n
        d = float(n @ c)
        dist = sample @ n - d
        patches.append(
            {
                "faces": np.array(region, dtype=np.int32),
                "area": area,
                "normal": n,
                "d": d,
                "center": c,
                "rms": float(np.sqrt(np.mean(dist**2))),
                "span": float(np.ptp(dist)),
            }
        )
    patches.sort(key=lambda p: -p["area"])
    return patches


def iterative_flatten_planes(
    mesh: trimesh.Trimesh,
    planes: list[dict],
    *,
    iters: int = 25,
    step: float = 0.28,
    max_abs: float = 2.0,
    min_frac: float = 0.75,
) -> tuple[trimesh.Trimesh, list[dict]]:
    f = mesh.faces
    v = mesh.vertices.copy()
    v2f: dict[int, list[int]] = defaultdict(list)
    for fi, tri in enumerate(f):
        for vid in tri:
            v2f[int(vid)].append(fi)

    reports = []
    for p in planes:
        face_ids = np.asarray(p["faces"], dtype=np.int32)
        n = np.asarray(p["normal"], float)
        n /= np.linalg.norm(n) + 1e-12
        d = float(p["d"])
        faceset = set(map(int, face_ids))
        vids = np.unique(f[face_ids].reshape(-1))
        fracs = {
            int(vid): sum(1 for fi in v2f[int(vid)] if fi in faceset)
            / max(len(v2f[int(vid)]), 1)
            for vid in vids
        }

        def stats():
            conf = [int(i) for i in vids if fracs[int(i)] >= min_frac]
            if not conf:
                return 0.0, 0.0
            dist = v[conf] @ n - d
            return float(np.sqrt(np.mean(dist**2))), float(np.ptp(dist))

        rms0, span0 = stats()
        for _ in range(iters):
            for vid in vids:
                frac = fracs[int(vid)]
                if frac < min_frac:
                    continue
                dist = float(v[vid] @ n - d)
                if abs(dist) > max_abs:
                    continue
                v[vid] = v[vid] - (step * frac * dist) * n
        rms1, span1 = stats()
        reports.append(
            {
                "area": float(p["area"]),
                "normal": n.tolist(),
                "d": d,
                "rms_before": rms0,
                "rms_after": rms1,
                "span_before": span0,
                "span_after": span1,
            }
        )
    out = mesh.copy()
    out.vertices = v
    out.fix_normals()
    return out, reports


def save_preview_images(
    before: trimesh.Trimesh,
    after: trimesh.Trimesh,
    n: np.ndarray,
    d: float,
    center: np.ndarray,
    holes: list[dict],
) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    art = Path("/opt/cursor/artifacts/screenshots")
    art.mkdir(parents=True, exist_ok=True)
    paths = []

    def flange_cloud(mesh):
        vv = mesh.vertices
        planar = vv - center
        r = np.linalg.norm(planar - np.outer(planar @ n, n), axis=1)
        along = vv @ n - d
        m = (r < 50) & (np.abs(along) < 5)
        return vv[m]

    pb, pa = flange_cloud(before), flange_cloud(after)
    # project to 2D
    t1, t2 = _basis(n)

    def to2(P):
        q = P - center
        return np.column_stack([q @ t1, q @ t2]), P @ n

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, P, title in [
        (axes[0], pb, "Bride AVANT"),
        (axes[1], pa, "Bride APRÈS refine"),
    ]:
        if len(P) == 0:
            continue
        uv, along = to2(P)
        sc = ax.scatter(uv[:, 0], uv[:, 1], c=along, s=3, cmap="coolwarm", vmin=d - 3, vmax=d + 3)
        for h in holes:
            c = np.asarray(h["center_on_flange_mm"])
            q = c - center
            ax.add_patch(
                plt.Circle(
                    (q @ t1, q @ t2),
                    h["radius_mm"],
                    fill=False,
                    ec="k",
                    lw=1.0,
                )
            )
        ax.set_aspect("equal")
        ax.set_title(f"{title}\nspan n≈{np.ptp(along):.2f} mm")
        fig.colorbar(sc, ax=ax, fraction=0.046, label="along normal mm")
    fig.suptitle("Carter Minarelli — bride admission (cale user 4 trous)")
    fig.tight_layout()
    p1 = art / "carter_flange_before_after.png"
    fig.savefig(p1, dpi=140)
    paths.append(p1)

    # one hole zoom after
    if holes:
        h0 = holes[0]
        c = np.asarray(h0["center_on_flange_mm"], float)
        fig2, axes = plt.subplots(1, 2, figsize=(10, 4.5))
        for ax, mesh, title in [
            (axes[0], before, "Trou AVANT"),
            (axes[1], after, "Trou APRÈS cylindre"),
        ]:
            vv = mesh.vertices
            dvec = vv - c
            along = dvec @ n
            rad_vec = dvec - np.outer(along, n)
            r = np.linalg.norm(rad_vec, axis=1)
            m = (r < h0["radius_mm"] + 4) & (along < 2) & (along > -12)
            pts = vv[m]
            if len(pts) == 0:
                continue
            uv = np.column_stack([(pts - c) @ t1, (pts - c) @ t2])
            ax.scatter(uv[:, 0], uv[:, 1], s=4, c=(pts @ n), cmap="viridis")
            ax.add_patch(plt.Circle((0, 0), h0["radius_mm"], fill=False, ec="r", lw=1.5))
            ax.set_aspect("equal")
            ax.set_title(title)
        fig2.suptitle(
            f"Trou {h0['kind']} Ø{h0['diameter_mm']:.2f} mm — cible cercle rouge"
        )
        fig2.tight_layout()
        p2 = art / "carter_hole_before_after.png"
        fig2.savefig(p2, dpi=140)
        paths.append(p2)

    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--stl",
        default=str(
            OUT / "mina_flattened.stl"
            if (OUT / "mina_flattened.stl").exists()
            else OUT / "mina_piece_80000.stl"
        ),
    )
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--name", default="MINARELLI carter CAD-like + calle vl14 — ENSEMBLE")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    ref = json.loads(REF_PATH.read_text())
    pose = json.loads(POSE_PATH.read_text())
    M = np.array(pose["transform_rowmajor"], float).reshape(4, 4)

    print("=== refine_carter_cadlike ===")
    print("Pose cale USER (ne pas recentrer):", USER_DOC)
    print("Cale:", ref["name"], ref["size_mm"])

    # Prefer original clean watertight as base if flattened may already be partial
    base_path = Path(args.stl)
    if not base_path.exists():
        base_path = OUT / "mina_piece_80000.stl"
    # Always start from watertight 80k for hole snap reliability
    if (OUT / "mina_piece_80000.stl").exists():
        base_path = OUT / "mina_piece_80000.stl"

    before = trimesh.load(base_path, force="mesh")
    print(f"Mesh base: {base_path.name} faces={len(before.faces)} wt={before.is_watertight}")

    # --- A. Bride plane from user cale ---
    holes_local = fuc.detect_cale_holes_local(OUT / "cale_aligned.stl")
    holes_world = ((M[:3, :3] @ (holes_local / 1000.0).T).T + M[:3, 3]) * 1000.0
    n_hint = M[:3, :3] @ np.array([1.0, 0.0, 0.0])
    n_hint /= np.linalg.norm(n_hint)
    n, d, center, gap = fuc.flange_from_user_pose(before, holes_world, n_hint)
    print(f"Plan bride: n={n} d={d:.3f} gap_cale≈{gap:.1f} mm")

    holes_on_plane = holes_world - np.outer((holes_world @ n) - d, n)
    mesh, flange_report = fuc.flatten_flange_to_plane(
        before, n, d, center, holes_on_plane, radius=55.0, max_dist=3.5
    )
    print(
        f"Flatten bride: core={flange_report['n_core']} "
        f"rms→{flange_report['rms_core_after']}"
    )

    # --- B. Perfect cylinders from cale dims ---
    hole_specs = hole_specs_from_ref(ref, pose, n, d)
    print(f"Trous à cylindrer: {len(hole_specs)}")
    for h in hole_specs:
        print(
            f"  {h['kind']:7s} Ø{h['diameter_mm']:.3f}  center={np.array(h['center_on_flange_mm']).round(2)}"
        )

    mesh, hole_reports = snap_holes_to_cylinders(mesh, hole_specs, n, depth=12.0)
    for hr in hole_reports:
        print(
            f"  snap {hr['kind']:7s}: rms {hr['radius_rms_before']}→{hr['radius_rms_after']} "
            f"span {hr['radius_span_before']}→{hr['radius_span_after']} moved={hr['n_verts_moved']}"
        )

    # --- C. Other support planes (soft) ---
    patches = detect_support_planes(mesh, min_area=2800.0)
    # skip planes aligned with flange (already done)
    other = []
    for p in patches[:12]:
        if abs(float(p["normal"] @ n)) > 0.85:
            continue
        if p["rms"] > 0.7:
            continue
        other.append(p)
    print(f"Plans secondaires: {len(other)}")
    mesh, plane_reports = iterative_flatten_planes(mesh, other)

    mesh = fuc.repair_single_body(mesh)
    if not mesh.is_watertight:
        print("WARN: non watertight après refine")

    out_stl = OUT / "mina_carter_cadlike.stl"
    mesh.export(out_stl)
    print(f"STL → {out_stl} faces={len(mesh.faces)} wt={mesh.is_watertight} vol={mesh.volume:.0f}")

    # Bake cale user pose
    cale_src = OUT / "cale_aligned.step"
    if not cale_src.exists():
        cale_src = OUT / "cale_admission.step"
    cale_baked = OUT / "cale_user_pose.step"
    fuc.bake_cale_with_user_transform(cale_src, M, cale_baked)

    # Previews
    try:
        imgs = save_preview_images(before, mesh, n, d, center, hole_specs)
        print("Artifacts:", [str(p) for p in imgs])
    except Exception as e:
        imgs = []
        print("preview warn", e)

    meta = {
        "method": "refine_carter_cadlike",
        "user_doc": USER_DOC,
        "cale_ref": ref,
        "source_stl": str(base_path),
        "flange_plane": {"normal": n.tolist(), "d_mm": d, "center_mm": center.tolist()},
        "gap_cale_to_mesh_mm": gap,
        "flange_flatten": flange_report,
        "holes": hole_reports,
        "other_planes": plane_reports,
        "n_faces_out": len(mesh.faces),
        "watertight": bool(mesh.is_watertight),
        "volume_mm3": float(mesh.volume),
        "note": "Cale pose USER préservée; trous snappés cylindriques; pas de recentrage +X.",
    }

    if args.upload:
        import align_cale_admission as ac

        old = ac.ENGINE_STL
        ac.ENGINE_STL = out_stl
        try:
            url = ac.upload_ensemble(cale_baked, args.name)
        finally:
            ac.ENGINE_STL = old
        meta["onshape_url"] = url
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")

        # Verify volume
        import os
        from onshape_http import api

        ak, sk = os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"]
        did, wid = url.split("/")[4], url.split("/")[6]
        for e in api(ak, sk, f"/api/documents/d/{did}/w/{wid}/elements"):
            nm = e.get("name") or ""
            if e.get("elementType") != "PARTSTUDIO":
                continue
            if not any(k in nm.lower() for k in ("mina", "moteur", "carter")):
                continue
            parts = api(ak, sk, f"/api/parts/d/{did}/w/{wid}/e/{e['id']}")
            mp = api(
                ak,
                sk,
                f"/api/partstudios/d/{did}/w/{wid}/e/{e['id']}/massproperties",
                qs="massAsGroup=false",
            )
            vols = []
            for pid, b in (mp.get("bodies") or {}).items():
                vol = b.get("volume")
                vol = vol[0] if isinstance(vol, list) else vol
                if vol:
                    vols.append(float(vol))
            vols.sort(reverse=True)
            meta["onshape_n_solids"] = sum(1 for p in parts if p.get("bodyType") == "solid")
            meta["onshape_n_sheets"] = sum(1 for p in parts if p.get("bodyType") == "sheet")
            meta["onshape_top_volume_m3"] = vols[0] if vols else None
            print(
                f"Onshape moteur ({nm}): solids={meta['onshape_n_solids']} "
                f"sheets={meta['onshape_n_sheets']} top_vol={meta['onshape_top_volume_m3']}"
            )
            if not vols or vols[0] < 1e-4:
                raise SystemExit("ECHEC: volume Onshape trop petit — mesh fragmenté")

    (OUT / "refine_carter_report.json").write_text(json.dumps(meta, indent=2))
    (ROOT / "refine_carter_report.json").write_text(json.dumps(meta, indent=2))
    print("Rapport → refine_carter_report.json")


if __name__ == "__main__":
    main()
