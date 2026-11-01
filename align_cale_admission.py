#!/usr/bin/env python3
"""
Aligne la cale d'admission (cotes réelles) sur la bride du scan Minarelli.

Méthode
-------
1. Localise la face plane +X (~X=53.7 mm) avec orifice ~Ø43 et enveloppe ~75×78
2. Détecte les 2 creux d'oreilles espacés de ~64.3 mm (cotes cale)
3. Pose la cale : face de joint sur la bride, rotation/mirroir pour coller les oreilles
4. Exporte STEP aligné + (option) document Onshape assemblage

Usage
-----
  python align_cale_admission.py
  python align_cale_admission.py --upload
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

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mina_scan"
CALE_STEP = OUT / "cale_admission.step"
ENGINE_STL = OUT / "mina_piece_80000.stl"
REF = ROOT / "cale_admission_ref.json"


def fit_pose(engine: trimesh.Trimesh) -> dict:
    """Retourne R (3x3), T (3,), et meta d'alignement."""
    t_face = 53.7
    sec = engine.section(plane_origin=[t_face, 0, 0], plane_normal=[1, 0, 0])
    if sec is None:
        raise RuntimeError("Pas de section bride à X=53.7")
    path2, tf = sec.to_2D()
    center3 = None
    for poly in path2.polygons_full:
        for ring in poly.interiors:
            xs = np.asarray(ring.xy[0])
            ys = np.asarray(ring.xy[1])
            d = 0.5 * ((xs.max() - xs.min()) + (ys.max() - ys.min()))
            if 35 <= d <= 50:
                center3 = tf.dot([xs.mean(), ys.mean(), 0, 1])[:3]
                break
        if center3 is not None:
            break
    if center3 is None:
        raise RuntimeError("Orifice central bride introuvable")

    # Cibles oreilles (creux mesh) — fit empirique validé ~±3 mm
    targets = np.array([[84.2, 18.5], [39.8, -27.5]])
    tabs = np.array([[3.619, 32.042], [-3.731, -31.874]])
    port_yz = center3[1:]

    best = None
    for deg in range(-180, 180):
        for reflect in (False, True):
            ang = np.radians(deg)
            c, s = np.cos(ang), np.sin(ang)
            Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
            Ref = np.diag([-1.0, 1.0, 1.0]) if reflect else np.eye(3)
            R0 = np.array([[0.0, 0, -1], [0, 1, 0], [1, 0, 0]])
            R = R0 @ Rz @ Ref
            mapped = []
            for cx, cy in tabs:
                w = R @ np.array([cx, cy, 0.0])
                mapped.append([w[1] + port_yz[0], w[2] + port_yz[1]])
            mapped = np.array(mapped)
            d1 = np.linalg.norm(mapped[0] - targets[0]) + np.linalg.norm(
                mapped[1] - targets[1]
            )
            d2 = np.linalg.norm(mapped[0] - targets[1]) + np.linalg.norm(
                mapped[1] - targets[0]
            )
            sc = min(d1, d2)
            if best is None or sc < best[0]:
                best = (sc, deg, reflect, R, mapped)

    score, deg, reflect, R, mapped = best
    T = center3 + np.array([0.3, 0.0, 0.0])
    return {
        "R": R,
        "T": T,
        "rotation_deg": deg,
        "reflect_x": reflect,
        "fit_error_mm_total": float(score),
        "port_center_3d_mm": center3.tolist(),
        "mapped_tabs_yz": mapped.tolist(),
        "target_tabs_yz": targets.tolist(),
    }


def export_aligned(pose: dict, out_step: Path) -> Path:
    import cadquery as cq
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf

    if not CALE_STEP.exists():
        raise SystemExit(f"Manque {CALE_STEP} — exporte d'abord la cale Onshape")
    cale = cq.importers.importStep(str(CALE_STEP))
    R, T = pose["R"], pose["T"]
    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = T
    tr = gp_Trsf()
    tr.SetValues(
        M[0, 0], M[0, 1], M[0, 2], M[0, 3],
        M[1, 0], M[1, 1], M[1, 2], M[1, 3],
        M[2, 0], M[2, 1], M[2, 2], M[2, 3],
    )
    aligned = cq.Shape.cast(
        BRepBuilderAPI_Transform(cale.val().wrapped, tr, True).Shape()
    )
    out_step.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(aligned, str(out_step))
    cq.exporters.export(aligned, str(out_step.with_suffix(".stl")))
    return out_step


def upload_assembly(engine_stl: Path, cale_step: Path, name: str) -> str:
    from onshape_client.client import Client
    from onshape_client.oas.models.bt_document_params import BTDocumentParams
    import random
    import string
    import datetime
    import urllib.request
    import hmac
    import hashlib
    import base64

    load_dotenv()
    # STL Onshape = mètres
    eng = trimesh.load(engine_stl, force="mesh")
    eng_m = eng.copy()
    eng_m.apply_scale(0.001)
    eng_meters = OUT / "mina_piece_80000_meters.stl"
    eng_m.export(eng_meters)

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

    imp(eng_meters)
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
        solid = next((p for p in parts if p.get("bodyType") == "solid"), None)
        if not solid:
            continue
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
    return f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{aid}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upload", action="store_true")
    p.add_argument("--name", default="MINARELLI — cale sur bride admission")
    args = p.parse_args()

    if not ENGINE_STL.exists():
        raise SystemExit(f"Manque {ENGINE_STL} — lance d'abord scan_to_engine.py")

    print("Fit pose bride…")
    engine = trimesh.load(ENGINE_STL, force="mesh")
    pose = fit_pose(engine)
    print(
        f"  rot={pose['rotation_deg']}° reflect_x={pose['reflect_x']} "
        f"err_tabs={pose['fit_error_mm_total']:.2f} mm"
    )
    out = export_aligned(pose, OUT / "cale_aligned.step")
    meta = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in pose.items()}
    if REF.exists():
        meta["cale_ref"] = json.loads(REF.read_text())
    (OUT / "align_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"STEP aligné → {out}")

    if args.upload:
        url = upload_assembly(ENGINE_STL, out, args.name)
        meta["onshape_url"] = url
        (OUT / "align_meta.json").write_text(json.dumps(meta, indent=2))
        print(f"Onshape → {url}")


if __name__ == "__main__":
    main()
