"""
Crée une copie ÉDITABLE d'un document Onshape (arbre Sketch / Extrude / Parts),
au lieu d'un import STEP « mort ».

Usage:
  python make_editable_copy.py
  python make_editable_copy.py --did ... --wid ... --name "Ma copie"
"""

from __future__ import annotations

import argparse
import os
import random
import string
import datetime
import json
import base64
import hmac
import hashlib
import urllib.request

from dotenv import load_dotenv

# Document « cale final » (référence utilisateur)
DEFAULT_DID = "5cc42b294eb99d49a3bb8a88"
DEFAULT_WID = "aa52e1d9f9b6ecfdf4680687"


def api(ak: str, sk: str, path: str, method: str = "get", body=None, qs: str = ""):
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
        return json.loads(r.read().decode())


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--did", default=DEFAULT_DID)
    p.add_argument("--wid", default=DEFAULT_WID)
    p.add_argument("--name", default="Cale final EDITABLE")
    args = p.parse_args()

    ak = os.getenv("ONSHAPE_ACCESS_KEY")
    sk = os.getenv("ONSHAPE_SECRET_KEY")

    print(f"Copie workspace {args.did} / {args.wid} …")
    res = api(
        ak,
        sk,
        f"/api/documents/{args.did}/workspaces/{args.wid}/copy",
        method="post",
        body={"newName": args.name, "isPublic": True},
    )
    new_did = res["newDocumentId"]
    new_wid = res["newWorkspaceId"]
    url = f"https://cad.onshape.com/documents/{new_did}/w/{new_wid}"
    print("Copie créée :", url)

    elems = api(ak, sk, f"/api/documents/d/{new_did}/w/{new_wid}/elements")
    for e in elems:
        et = e.get("elementType") or e.get("type")
        print(f"  {et}: {e.get('name')}")
        if et == "PARTSTUDIO":
            eid = e["id"]
            feats = api(
                ak, sk, f"/api/partstudios/d/{new_did}/w/{new_wid}/e/{eid}/features"
            )
            for f in feats.get("features") or []:
                m = f["message"]
                print(f"    - {m.get('featureType')} / {m.get('name')}")
            parts = api(ak, sk, f"/api/parts/d/{new_did}/w/{new_wid}/e/{eid}")
            for part in parts:
                print(f"    part: {part.get('name')} ({part.get('partId')})")

    print("\nArbre éditable conservé (Sketch / Extrude / Part).")
    print(url)


if __name__ == "__main__":
    main()
