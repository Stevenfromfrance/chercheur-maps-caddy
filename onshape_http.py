"""Auth HMAC Onshape (sans SDK) pour download blob / copy workspace."""

from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import os
import random
import string
import urllib.error
import urllib.request
from typing import Any


def _nonce(n: int = 25) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def api(
    access_key: str,
    secret_key: str,
    path: str,
    *,
    method: str = "get",
    body: Any | None = None,
    qs: str = "",
    accept: str = "application/json",
    content_type: str = "application/json",
    base_url: str | None = None,
) -> Any:
    base = (base_url or os.getenv("ONSHAPE_BASE_URL") or "https://cad.onshape.com").rstrip(
        "/"
    )
    method = method.lower()
    n = _nonce()
    date = datetime.datetime.now(datetime.UTC).strftime("%a, %d %b %Y %H:%M:%S GMT")
    hmac_str = (
        method + "\n" + n + "\n" + date + "\n" + content_type + "\n" + path + "\n" + qs + "\n"
    ).lower().encode()
    sig = base64.b64encode(
        hmac.new(secret_key.encode(), hmac_str, hashlib.sha256).digest()
    ).decode()
    data = None if body is None else json.dumps(body).encode()
    url = base + path + (("?" + qs) if qs else "")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Date": date,
            "On-Nonce": n,
            "Authorization": f"On {access_key}:HmacSHA256:{sig}",
            "Content-Type": content_type,
            "Accept": accept,
        },
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:800]
        raise RuntimeError(f"Onshape {e.code} {path}: {detail}") from e
    if "json" in accept.lower():
        return json.loads(raw.decode()) if raw else None
    return raw
