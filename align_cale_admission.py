#!/usr/bin/env python3
"""
Aligne la cale d'admission « calle vl14 » sur la bride du scan Minarelli.

Référence :
  https://cad.onshape.com/documents/a21e5846c7f0224fd076feed/w/f27de36333f4b344289a56ea/e/25eaf2b3c944d6feceef6161
  68.2 × 78.3 × 19.5 mm — oreilles entraxe ≈ 64.03 mm

Usage
-----
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
ENGINE_STL = OUT / "mina_piece_80000.stl"
CALE_STEP = OUT / "cale_admission.step"
REF = ROOT / "cale_admission_ref.json"

CALE_DID = "a21e5846c7f0224fd076feed"
CALE_WID = "f27de36333f4b344289a56ea"
CALE_EID = "25eaf2b3c944d6feceef6161"

# Oreilles Ø~6.7 (Sketch 1) — entraxe 64.033 mm
EARS = np.array([[-5.516, 33.098], [2.505, -30.431]])


def export_cale_step() -> Path:
    import base64
    import datetime
    import hashlib
    import hmac
    import random
    import string
    import urllib.request

    load_dotenv()
    ak, sk = os.getenv("ONSHAPE_ACCESS_KEY"), os.getenv("ONSHAPE_SECRET_KEY")

    def api(path, method="get", body=None, accept="application/json"):
        n = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(25))
        date = datetime.datetime.now(datetime.UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")
        ctype = "application/json"
        hmac_str = (
            method + "\n" + n + "\n" + date + "\n" + ctype + "\n" + path + "\n\n"
        ).lower().encode()
        sig = base64.b64encode(
            hmac.new(sk.encode(), hmac_str, hashlib.sha256).digest()
        ).decode()
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            "https://cad.onshape.com" + path,
            data=data,
            headers={
                "Date": date,
                "On-Nonce": n,
                "Authorization": f"On {ak}:HmacSHA256:{sig}",
                "Content-Type": ctype,
                "Accept": accept,
            },
            method=method.upper(),
        )
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw.decode()) if "json" in accept else raw

    OUT.mkdir(parents=True, exist_ok=True)
    res = api(
        f"/api/partstudios/d/{CALE_DID}/w/{CALE_WID}/e/{CALE_EID}/translations",
        method="post",
        body={"formatName": "STEP", "storeInDocument": False},
    )
    tid = res["id"]
    while True:
        info = api(f"/api/translations/{tid}")
        if info.get("requestState") == "DONE":
            break
        if info.get("requestState") == "FAILED":
            raise RuntimeError(info)
        time.sleep(1)
    fid = info["resultExternalDataIds"][0]
    raw = api(f"/api/documents/d/{CALE_DID}/externaldata/{fid}", accept="*/*")
    CALE_STEP.write_bytes(raw)
    print(f"STEP cale → {CALE_STEP} ({len(raw)/1e3:.0f} Ko)")
    return CALE_STEP


def align() -> tuple[Path, dict]:
    import cadquery as cq
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf
    from collections import defaultdict

    if not CALE_STEP.exists():
        export_cale_step()
    if not ENGINE_STL.exists():
        raise SystemExit(f"Manque {ENGINE_STL}")

    cale_shape = cq.importers.importStep(str(CALE_STEP))
    bb = cale_shape.val().BoundingBox()
    cx, cy = float(bb.center.x), float(bb.center.y)
    z_mate = float(bb.zmax)
    ears_local = EARS - np.array([cx, cy])

    eng = trimesh.load(ENGINE_STL, force="mesh")
    t_face = 53.7
    sec = eng.section(plane_origin=[t_face, 0, 0], plane_normal=[1, 0, 0])
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
        raise RuntimeError("Bride introuvable")

    # Mesh bolt pits
    v = eng.vertices
    mask = (
        (np.abs(v[:, 0] - 53.7) < 4)
        & (np.abs(v[:, 1] - center3[1]) < 55)
        & (np.abs(v[:, 2] - center3[2]) < 55)
    )
    pts = v[mask]
    face_x = np.percentile(pts[:, 0], 85)
    mins = []
    for y in np.linspace(center3[1] - 50, center3[1] + 50, 90):
        for z in np.linspace(center3[2] - 50, center3[2] + 50, 90):
            d2 = (pts[:, 1] - y) ** 2 + (pts[:, 2] - z) ** 2
            near = d2 < 2.2**2
            if near.sum() < 4:
                continue
            if pts[near, 0].min() < face_x - 1.0:
                mins.append((y, z))
    bins = defaultdict(list)
    for y, z in mins:
        bins[(round(y / 4) * 4, round(z / 4) * 4)].append((y, z))
    bolts = []
    for vals in bins.values():
        if len(vals) < 5:
            continue
        a = np.array(vals)
        if np.ptp(a[:, 0]) < 18 and np.ptp(a[:, 1]) < 18:
            bolts.append([a[:, 0].mean(), a[:, 1].mean()])
    bolts = np.array(bolts)

    best = None
    for deg in range(-180, 180):
        for reflect in (False, True):
            ang = np.radians(deg)
            c, s = np.cos(ang), np.sin(ang)
            R2 = np.array([[c, -s], [s, c]])
            loc = ears_local.copy()
            if reflect:
                loc[:, 0] *= -1
            mapped = (loc @ R2.T) + center3[1:]
            sc = 0.0
            if len(bolts):
                for p in mapped:
                    sc += min(float(np.linalg.norm(bolts - p, axis=1).min()), 35.0)
            sc += float(np.linalg.norm(mapped.mean(0) - center3[1:])) * 0.3
            if best is None or sc < best[0]:
                best = (sc, deg, reflect, mapped)

    deg, reflect = best[1], best[2]
    ang = np.radians(deg)
    c, s = np.cos(ang), np.sin(ang)
    Ref = np.diag([-1.0, 1.0, 1.0]) if reflect else np.eye(3)
    R_xy = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    S = np.diag([1.0, 1.0, -1.0])  # thickness into body from z_mate
    R_axes = np.array([[0, 0, 1.0], [1, 0, 0], [0, 1, 0]])
    R = R_axes @ R_xy @ Ref @ S
    origin = np.array([cx, cy, z_mate])
    T = np.array([t_face + 0.3, center3[1], center3[2]])
    Trans = T - R @ origin

    tr = gp_Trsf()
    tr.SetValues(
        R[0, 0], R[0, 1], R[0, 2], Trans[0],
        R[1, 0], R[1, 1], R[1, 2], Trans[1],
        R[2, 0], R[2, 1], R[2, 2], Trans[2],
    )
    aligned = cq.Shape.cast(
        BRepBuilderAPI_Transform(cale_shape.val().wrapped, tr, True).Shape()
    )
    out = OUT / "cale_aligned.step"
    cq.exporters.export(aligned, str(out))
    cq.exporters.export(aligned, str(OUT / "cale_aligned.stl"))

    meta = {
        "cale_source": f"https://cad.onshape.com/documents/{CALE_DID}/w/{CALE_WID}/e/{CALE_EID}",
        "cale_name": "calle vl14",
        "size_mm": [float(bb.xlen), float(bb.ylen), float(bb.zlen)],
        "ear_spacing_mm": float(np.linalg.norm(EARS[0] - EARS[1])),
        "alignment": {
            "method": "ear_holes_64mm",
            "rotation_deg": deg,
            "reflect_x": reflect,
            "fit_score": float(best[0]),
            "flange_x_mm": t_face,
            "port_center_3d_mm": center3.tolist(),
            "offset_outward_mm": 0.3,
        },
    }
    return out, meta


def upload_ensemble(cale_step: Path, name: str) -> str:
    import base64
    import datetime
    import hashlib
    import hmac
    import random
    import string
    import urllib.request

    from onshape_client.client import Client
    from onshape_client.oas.models.bt_document_params import BTDocumentParams

    load_dotenv()
    eng = trimesh.load(ENGINE_STL, force="mesh")
    eng_m = eng.copy()
    eng_m.apply_scale(0.001)
    eng_path = OUT / "mina_piece_80000_meters.stl"
    eng_m.export(eng_path)

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
                did, wid, file=f, store_in_document=True, notify_user=False,
                allow_faulty_parts=True, encoded_filename=path.name,
            )
        while True:
            info = client.translation_api.get_translation(tr.id)
            if info.request_state == "DONE":
                return
            if info.request_state == "FAILED":
                raise RuntimeError(info.to_dict())
            time.sleep(2)

    imp(eng_path)
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
                "Date": date, "On-Nonce": n,
                "Authorization": f"On {ak}:HmacSHA256:{sig}",
                "Content-Type": ctype, "Accept": "application/json",
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
                "documentId": did, "elementId": e["id"], "workspaceId": wid,
                "isAssembly": False, "isWholePartStudio": False, "partId": solid["partId"],
            },
        )

    NAME_PROP = "57f3fb8efa3416c06701d60d"
    for e in api(f"/api/documents/d/{did}/w/{wid}/elements"):
        if e["elementType"] == "ASSEMBLY":
            nm = "ENSEMBLE moteur + cale"
        elif "mina_" in e["name"]:
            nm = "_moteur seul"
        elif "cale_" in e["name"]:
            nm = "_cale seule"
        else:
            continue
        api(
            f"/api/metadata/d/{did}/w/{wid}/e/{e['id']}",
            method="post",
            body={"jsonType": "metadata", "properties": [{"propertyId": NAME_PROP, "value": nm}]},
        )
    return f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{aid}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upload", action="store_true")
    p.add_argument("--name", default="MINARELLI + calle vl14 — ENSEMBLE")
    args = p.parse_args()

    print("Alignement calle vl14…")
    out, meta = align()
    if REF.exists():
        meta["cale_ref"] = json.loads(REF.read_text())
    (OUT / "align_meta.json").write_text(json.dumps(meta, indent=2))
    print(
        f"  size={meta['size_mm']} ears={meta['ear_spacing_mm']:.2f}mm "
        f"rot={meta['alignment']['rotation_deg']}° score={meta['alignment']['fit_score']:.1f}"
    )
    print(f"STEP → {out}")

    if args.upload:
        url = upload_ensemble(out, args.name)
        meta["onshape_url"] = url
        (OUT / "align_meta.json").write_text(json.dumps(meta, indent=2))
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape → {url}")
        print("Ouvre l'onglet « ENSEMBLE moteur + cale ».")


if __name__ == "__main__":
    main()
