#!/usr/bin/env python3
"""
Aligne la cale (basetta Minarelli) sur la bride du scan moteur.

Cale de référence :
  https://cad.onshape.com/documents/abf25ddd7939c47991ad4c6b/w/070b3d29da40e7fe778d2d9f/e/4d14edf501f8ccd04846218a
  75.4 × 7.6 × 65 mm — orifice 38×44 — 4 trous Ø6.5

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
CALE_OBJ = OUT / "cale_new.obj"
REF = ROOT / "cale_admission_ref.json"

NEW_CALE_DID = "abf25ddd7939c47991ad4c6b"
NEW_CALE_WID = "070b3d29da40e7fe778d2d9f"
NEW_CALE_BLOB = "55811dbce77e492bc0cf954b"


def download_cale_obj() -> Path:
    import base64
    import datetime
    import hashlib
    import hmac
    import random
    import string
    import urllib.request

    load_dotenv()
    ak, sk = os.getenv("ONSHAPE_ACCESS_KEY"), os.getenv("ONSHAPE_SECRET_KEY")
    path = f"/api/blobelements/d/{NEW_CALE_DID}/w/{NEW_CALE_WID}/e/{NEW_CALE_BLOB}"
    n = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(25))
    date = datetime.datetime.now(datetime.UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")
    ctype = "application/json"
    hmac_str = ("get\n" + n + "\n" + date + "\n" + ctype + "\n" + path + "\n\n").lower().encode()
    sig = base64.b64encode(hmac.new(sk.encode(), hmac_str, hashlib.sha256).digest()).decode()
    req = urllib.request.Request(
        "https://cad.onshape.com" + path,
        headers={
            "Date": date,
            "On-Nonce": n,
            "Authorization": f"On {ak}:HmacSHA256:{sig}",
            "Content-Type": ctype,
            "Accept": "*/*",
        },
    )
    OUT.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req) as r:
        raw = r.read()
    CALE_OBJ.write_bytes(raw)
    print(f"Cale OBJ → {CALE_OBJ} ({len(raw)/1e6:.2f} Mo)")
    return CALE_OBJ


def align(cale: trimesh.Trimesh, engine: trimesh.Trimesh) -> tuple[trimesh.Trimesh, dict]:
    # Footprint center / mating face Y=0
    cx = float(cale.bounds[:, 0].mean())
    cz = float(cale.bounds[:, 2].mean())
    origin = np.array([cx, 0.0, cz])

    # 4 holes → PCA angle
    sec = cale.section(plane_origin=[0, 0.5, 0], plane_normal=[0, 1, 0])
    path2, tf = sec.to_2D()
    poly = max(path2.polygons_full, key=lambda p: p.area)
    holes = []
    port = None
    for ring in poly.interiors:
        xs = np.asarray(ring.xy[0])
        ys = np.asarray(ring.xy[1])
        iw, ih = xs.max() - xs.min(), ys.max() - ys.min()
        d = 0.5 * (iw + ih)
        c3 = tf.dot([xs.mean(), ys.mean(), 0, 1])[:3]
        if iw > 20 and ih > 20:
            port = [float(iw), float(ih)]
        elif 4 < d < 12:
            holes.append([c3[0] - cx, c3[2] - cz])
    holes = np.array(holes)
    uu, dd, vv = np.linalg.svd(holes)
    deg = -float(np.degrees(np.arctan2(vv[0, 1], vv[0, 0])))

    # Flange on engine
    t_face = 53.7
    sec_e = engine.section(plane_origin=[t_face, 0, 0], plane_normal=[1, 0, 0])
    path_e, tf_e = sec_e.to_2D()
    center3 = None
    for poly in path_e.polygons_full:
        for ring in poly.interiors:
            xs = np.asarray(ring.xy[0])
            ys = np.asarray(ring.xy[1])
            d = 0.5 * ((xs.max() - xs.min()) + (ys.max() - ys.min()))
            if 35 <= d <= 50:
                center3 = tf_e.dot([xs.mean(), ys.mean(), 0, 1])[:3]
                break
        if center3 is not None:
            break
    if center3 is None:
        raise RuntimeError("Bride admission introuvable sur le mesh moteur")

    ang = np.radians(deg)
    c, s = np.cos(ang), np.sin(ang)
    R_xz = np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
    R_axes = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1.0]])
    R = R_axes @ R_xz
    T = np.array([t_face + 0.3, center3[1], center3[2]])

    aligned = cale.copy()
    aligned.vertices = (R @ (aligned.vertices - origin).T).T + T

    meta = {
        "cale_source": f"https://cad.onshape.com/documents/{NEW_CALE_DID}/w/{NEW_CALE_WID}/e/4d14edf501f8ccd04846218a",
        "size_mm": [float(x) for x in cale.extents],
        "thickness_mm": float(cale.extents[1]),
        "port_mm": port,
        "n_holes": int(len(holes)),
        "alignment": {
            "method": "pca_hole_pattern",
            "rotation_deg": deg,
            "flange_x_mm": t_face,
            "port_center_3d_mm": center3.tolist(),
            "offset_outward_mm": 0.3,
        },
        "transform_R": R.tolist(),
        "transform_T": T.tolist(),
    }
    return aligned, meta


def upload_ensemble(engine_stl: Path, cale_stl_mm: Path, name: str) -> str:
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
    eng = trimesh.load(engine_stl, force="mesh")
    eng_m = eng.copy()
    eng_m.apply_scale(0.001)
    eng_path = OUT / "mina_piece_80000_meters.stl"
    eng_m.export(eng_path)

    cale = trimesh.load(cale_stl_mm, force="mesh")
    cale_m = cale.copy()
    cale_m.apply_scale(0.001)
    cale_path = OUT / "cale_aligned_meters.stl"
    cale_m.export(cale_path)

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

    imp(eng_path)
    imp(cale_path)

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

    # Rename tabs
    NAME_PROP = "57f3fb8efa3416c06701d60d"
    for e in api(f"/api/documents/d/{did}/w/{wid}/elements"):
        if e["elementType"] == "ASSEMBLY":
            nm = "ENSEMBLE moteur + cale"
        elif e["name"].startswith("mina_"):
            nm = "_moteur seul"
        elif e["name"].startswith("cale_"):
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
    p.add_argument("--name", default="MINARELLI + nouvelle cale (basetta) — ENSEMBLE")
    args = p.parse_args()

    if not ENGINE_STL.exists():
        raise SystemExit(f"Manque {ENGINE_STL} — lance scan_to_engine.py d'abord")
    if not CALE_OBJ.exists():
        download_cale_obj()

    print("Alignement…")
    cale = trimesh.load(CALE_OBJ, force="mesh")
    engine = trimesh.load(ENGINE_STL, force="mesh")
    aligned, meta = align(cale, engine)
    out = OUT / "cale_aligned.stl"
    aligned.export(out)
    if REF.exists():
        meta["cale_ref"] = json.loads(REF.read_text())
    (OUT / "align_meta.json").write_text(json.dumps(meta, indent=2))
    print(
        f"  size={meta['size_mm']} port={meta['port_mm']} "
        f"rot={meta['alignment']['rotation_deg']:.1f}°"
    )
    print(f"STL aligné → {out}")

    if args.upload:
        url = upload_ensemble(ENGINE_STL, out, args.name)
        meta["onshape_url"] = url
        (OUT / "align_meta.json").write_text(json.dumps(meta, indent=2))
        (OUT / "aligned_doc.txt").write_text(url + "\n")
        print(f"Onshape ENSEMBLE → {url}")
        print("Ouvre l'onglet « ENSEMBLE moteur + cale » (pas _moteur/_cale seule).")


if __name__ == "__main__":
    main()
