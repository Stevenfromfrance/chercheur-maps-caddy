# -*- coding: utf-8 -*-
"""Inject V2 (friend hardcut + launch) into MAP_GRIDS + hex-atlas.json."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
INDEX = SITE / "index.html"
ATLAS = SITE / "data" / "hex-atlas.json"

ROOT = Path(r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules\Caddy-CAYE-2013-03L906023PA-2531")
JSON_PATH = ROOT / "A2L" / "Volkswagen_Golf_2008_(VI)_1.6_TDI_CR_105_hp_Siemens_PCR2.1_OBD_NR.json"
ORI_PATH = ROOT / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
ACE_PATH = ROOT / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_ACE_stage1_dpf_egr.NOCS"
V1_PATH = ROOT / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V1_350wot_smooth.NOCS"
V2_PATH = ROOT / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V2_hardcut_launch.NOCS"

# Clutch-prot RPM axis (friend remapped for launch 2.5k + hardcut 4.8k)
CLUTCH_AXIS_START = 0x1A612A
CLUTCH_AXIS_N = 8  # u16 values after optional header handled separately
CLUTCH_AXIS_WINDOW = 0x1A6120  # include small header context
CLUTCH_AXIS_WINDOW_LEN = 32


def parse_factor(s: str) -> float:
    return float(s.replace(",", ".")) if s else 1.0


def read_raw(blob: bytes, addr: int, n: int, org: str, signed: bool) -> list[int]:
    out = []
    cs = 1 if org == "eByte" else 2
    for i in range(n):
        off = addr + i * cs
        if org == "eByte":
            v = blob[off]
            if signed and v >= 0x80:
                v -= 0x100
        else:
            v = blob[off] | (blob[off + 1] << 8)
            if signed and v >= 0x8000:
                v -= 0x10000
        out.append(v)
    return out


def phys(raw: list[int], factor: float, offset: float) -> list[float]:
    return [r * factor + offset for r in raw]


def round_vals(vals: list[float], prec: int) -> list[float]:
    return [round(v, prec) for v in vals]


def read_axis_u16(blob: bytes, addr: int, n: int, factor: float, offset: float) -> list[float]:
    vals = []
    for i in range(n):
        off = addr + i * 2
        raw = blob[off] | (blob[off + 1] << 8)
        vals.append(raw * factor + offset)
    return vals


def main() -> None:
    if not V2_PATH.exists():
        raise SystemExit(f"V2 missing: {V2_PATH}")

    ori = ORI_PATH.read_bytes() if ORI_PATH.exists() else None
    ace = ACE_PATH.read_bytes()
    v1 = V1_PATH.read_bytes()
    v2 = V2_PATH.read_bytes()
    if ori is None:
        # fallback path used on this machine
        ori = Path(
            r"C:\Users\theda\OneDrive\Bureau\caddy cartho\ORI CADDY STEVEN\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27"
        ).read_bytes()

    maps = json.loads(JSON_PATH.read_text(encoding="utf-8"))["maps"]
    by_addr = {int(m["Fieldvalues.StartAddr"]): m for m in maps}

    html = INDEX.read_text(encoding="utf-8")
    m = re.search(r"const MAP_GRIDS = (\[.*?\]);", html, re.S)
    if not m:
        raise SystemExit("MAP_GRIDS not found")
    grids = json.loads(m.group(1))

    for g in grids:
        addr = int(g["addr"], 16)
        am = by_addr.get(addr)
        prec = int(g.get("precision", 1))
        if not am:
            base = g.get("v1") or g["ace"]
            g["v2"] = list(base)
            g["v2Max"] = max(g["v2"]) if g["v2"] else 0.0
            g["changedCellsV2V1"] = 0
            g["changedCellsV2Ori"] = g.get("changedCellsV1Ori", g.get("changedCells", 0))
            g["changedCellsV2Ace"] = g.get("changedCellsV1Ace", 0)
            continue

        cols = int(am["Columns"])
        rows = int(am["Rows"])
        t = am["Type"]
        n = 1 if t == "eEinzel" else (max(cols, rows) if t == "eEindim" else cols * rows)
        org = am["DataOrg"]
        factor = parse_factor(am.get("Fieldvalues.Factor", "1"))
        offset = parse_factor(am.get("Fieldvalues.Offset", "0") or "0")
        signed = am.get("Fieldvalues.bSigned", "0") == "1" or am.get("bSigned", "0") == "1"
        v2_p = round_vals(phys(read_raw(v2, addr, n, org, signed), factor, offset), prec)
        if len(v2_p) != len(g["ori"]):
            v2_p = v2_p[: len(g["ori"])]
            while len(v2_p) < len(g["ori"]):
                v2_p.append(g.get("v1", g["ace"])[len(v2_p)])
        g["v2"] = v2_p
        g["v2Max"] = max(v2_p) if v2_p else 0.0
        v1_s = g.get("v1") or g["ace"]
        g["changedCellsV2V1"] = sum(1 for a, b in zip(v1_s, v2_p) if abs(a - b) > 1e-9)
        g["changedCellsV2Ori"] = sum(1 for a, b in zip(g["ori"], v2_p) if abs(a - b) > 1e-9)
        g["changedCellsV2Ace"] = sum(1 for a, b in zip(g["ace"], v2_p) if abs(a - b) > 1e-9)

        # Friend remapped clutch-prot Y axis (launch 2.5k / hardcut 4.8k)
        if addr == 0x1D0860 and am.get("AxisY.DataAddr"):
            y_addr = int(am["AxisY.DataAddr"])
            y_factor = parse_factor(am.get("AxisY.Factor", "1"))
            y_offset = parse_factor(am.get("AxisY.Offset", "0") or "0")
            g["axisY"] = round_vals(read_axis_u16(ori, y_addr, rows, y_factor, y_offset), 0)
            g["axisY_v2"] = round_vals(read_axis_u16(v2, y_addr, rows, y_factor, y_offset), 0)
            g["axisYNoteV2"] = "V2: axe RPM clutch-prot = launch ~2500 + hardcut ~4800"

    new_json = json.dumps(grids, ensure_ascii=False, separators=(",", ":"))
    html = html[: m.start(1)] + new_json + html[m.end(1) :]

    # Patch COMPARE object (replace hints/sides/label + series helpers via markers)
    html = patch_compare_block(html)
    html = patch_header_and_guide(html)
    html = patch_hex_helpers(html)
    html = patch_axis_y_v2_render(html)
    INDEX.write_text(html, encoding="utf-8")
    print(f"Updated MAP_GRIDS ({len(grids)} maps) with v2")

    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    for w in atlas["windows"]:
        start = w["start"]
        ori_b = base64.b64decode(w["ori"])
        n = len(ori_b)
        w["v2"] = base64.b64encode(v2[start : start + n]).decode("ascii")

    # Ensure clutch axis window exists for hex / dump2d
    starts = {w["start"] for w in atlas["windows"]}
    if CLUTCH_AXIS_WINDOW not in starts:
        s = CLUTCH_AXIS_WINDOW
        n = CLUTCH_AXIS_WINDOW_LEN
        atlas["windows"].append(
            {
                "start": s,
                "ori": base64.b64encode(ori[s : s + n]).decode("ascii"),
                "ace": base64.b64encode(ace[s : s + n]).decode("ascii"),
                "v1": base64.b64encode(v1[s : s + n]).decode("ascii"),
                "v2": base64.b64encode(v2[s : s + n]).decode("ascii"),
                "label": "clutch-prot RPM axis (launch/hardcut)",
            }
        )
        atlas["windows"].sort(key=lambda w: w["start"])
        atlas["windowCount"] = len(atlas["windows"])

    atlas["hasV2"] = True
    atlas["v2Note"] = (
        "V2 = V1 + friend: undo AccPed/tqlim soft-zero, hardcut via tqlim_cluth_prot @4800, "
        "launch test via clutch-prot axis ~2500"
    )
    ATLAS.write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Updated hex-atlas.json ({len(atlas['windows'])} windows) with v2")

    acc = next(g for g in grids if g["id"] == "AccPed_trq4A")
    clutch = next(g for g in grids if g["id"] == "tqlim_cluth_prot")
    print("AccPed max ORI/ACE/V1/V2", acc["oriMax"], acc["aceMax"], acc.get("v1Max"), acc.get("v2Max"))
    print("AccPed V2!=V1 cells", acc.get("changedCellsV2V1"))
    print("Clutch V2!=V1 cells", clutch.get("changedCellsV2V1"), "axisY_v2", clutch.get("axisY_v2"))
    print("V2 vs V1 bytes", sum(1 for a, b in zip(v2, v1) if a != b))


def patch_compare_block(html: str) -> str:
    old = """window.COMPARE = {
  pair: 'ori-ace',
  hints: {
    'ori-ace': 'Stage1 ACE (réf. préparateur)',
    'ori-v1': 'Ta carto V1 vs stock (partiels soft · WOT 350 · hardcut 4800)',
    'ace-v1': 'Écart V1 sur base ACE (ce que tu as retouché)'
  },
  sides: function () {
    if (this.pair === 'ori-v1') return ['ori', 'v1'];
    if (this.pair === 'ace-v1') return ['ace', 'v1'];
    return ['ori', 'ace'];
  },
  label: function (key) {
    return ({ ori: 'ORI', ace: 'ACE', v1: 'V1' })[key] || key.toUpperCase();
  }
};"""
    new = """window.COMPARE = {
  pair: 'ori-ace',
  hints: {
    'ori-ace': 'Stage1 ACE (réf. préparateur)',
    'ori-v1': 'Ta carto V1 vs stock (partiels soft · WOT 350 · softcut AccPed)',
    'ace-v1': 'Écart V1 sur base ACE (ce que tu as retouché)',
    'v1-v2': 'Ami : hardcut clutch-prot 4800 + launch 2500 (test)',
    'ori-v2': 'V2 complète vs stock',
    'ace-v2': 'V2 vs ACE'
  },
  sides: function () {
    if (this.pair === 'ori-v1') return ['ori', 'v1'];
    if (this.pair === 'ace-v1') return ['ace', 'v1'];
    if (this.pair === 'v1-v2') return ['v1', 'v2'];
    if (this.pair === 'ori-v2') return ['ori', 'v2'];
    if (this.pair === 'ace-v2') return ['ace', 'v2'];
    return ['ori', 'ace'];
  },
  label: function (key) {
    return ({ ori: 'ORI', ace: 'ACE', v1: 'V1', v2: 'V2' })[key] || key.toUpperCase();
  }
};"""
    if old not in html:
        # tolerant replace on sides/label only if accents differ
        html2, n = re.subn(
            r"window\.COMPARE = \{.*?\n\};",
            new,
            html,
            count=1,
            flags=re.S,
        )
        if n != 1:
            raise SystemExit("COMPARE block not patched")
        html = html2
    else:
        html = html.replace(old, new, 1)

    # series / seriesMax / changedCount
    html = re.sub(
        r"function series\(g, key\) \{.*?\n\}",
        """function series(g, key) {
  if (key === 'v1') return (g.v1 && g.v1.length) ? g.v1 : g.ace;
  if (key === 'v2') return (g.v2 && g.v2.length) ? g.v2 : ((g.v1 && g.v1.length) ? g.v1 : g.ace);
  return g[key];
}""",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"function seriesMax\(g, key\) \{.*?\n\}",
        """function seriesMax(g, key) {
  if (key === 'v2') return (g.v2Max != null) ? g.v2Max : seriesMax(g, 'v1');
  if (key === 'v1') return (g.v1Max != null) ? g.v1Max : g.aceMax;
  if (key === 'ori') return g.oriMax;
  return g.aceMax;
}""",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"function changedCount\(g\) \{.*?\n\}",
        """function changedCount(g) {
  const sides = window.COMPARE.sides();
  const L = sides[0], R = sides[1];
  if (L === 'ori' && R === 'ace') return g.changedCells;
  if (L === 'ori' && R === 'v1') return g.changedCellsV1Ori != null ? g.changedCellsV1Ori : g.changedCells;
  if (L === 'ace' && R === 'v1') return g.changedCellsV1Ace != null ? g.changedCellsV1Ace : 0;
  if (L === 'v1' && R === 'v2') return g.changedCellsV2V1 != null ? g.changedCellsV2V1 : 0;
  if (L === 'ori' && R === 'v2') return g.changedCellsV2Ori != null ? g.changedCellsV2Ori : g.changedCells;
  if (L === 'ace' && R === 'v2') return g.changedCellsV2Ace != null ? g.changedCellsV2Ace : 0;
  return g.changedCells;
}""",
        html,
        count=1,
        flags=re.S,
    )
    return html


def patch_header_and_guide(html: str) -> str:
    html = html.replace(
        "Chercheur maps · ORI / ACE / V1",
        "Chercheur maps · ORI / ACE / V1 / V2",
        1,
    )
    html = html.replace(
        "Caddy 9979 ORI / ACE / V1",
        "Caddy 9979 ORI / ACE / V1 / V2",
        1,
    )
    # pair buttons
    old_bar = """    <button type="button" class="pair-btn on" data-pair="ori-ace">ORI vs ACE</button>
    <button type="button" class="pair-btn" data-pair="ori-v1">ORI vs V1</button>
    <button type="button" class="pair-btn" data-pair="ace-v1">ACE vs V1</button>"""
    new_bar = """    <button type="button" class="pair-btn on" data-pair="ori-ace">ORI vs ACE</button>
    <button type="button" class="pair-btn" data-pair="ori-v1">ORI vs V1</button>
    <button type="button" class="pair-btn" data-pair="ace-v1">ACE vs V1</button>
    <button type="button" class="pair-btn" data-pair="v1-v2">V1 vs V2</button>
    <button type="button" class="pair-btn" data-pair="ori-v2">ORI vs V2</button>
    <button type="button" class="pair-btn" data-pair="ace-v2">ACE vs V2</button>"""
    if old_bar not in html:
        raise SystemExit("pair bar not found")
    html = html.replace(old_bar, new_bar, 1)

    old_lead = (
        "Trois fichiers : <b>ORI</b> (stock), <b>ACE</b> (Stage1 prépa + FAP/EGR off), "
        "<b>V1</b> (ta carto = ACE retravaillé). Choisis la paire en haut pour comparer."
    )
    new_lead = (
        "Quatre fichiers : <b>ORI</b> (stock), <b>ACE</b> (Stage1 + FAP/EGR off), "
        "<b>V1</b> (ta carto soft), <b>V2</b> (ami : hardcut clutch-prot 4800 + launch 2500 à tester). "
        "Paire <b>V1 vs V2</b> = uniquement les 272 octets de l’ami."
    )
    if old_lead in html:
        html = html.replace(old_lead, new_lead, 1)

    # Insert V2 bullet after V1 bullet if missing
    v1_li = (
        "<li><b>V1</b> : part de ACE, mais <b>adoucit les partiels</b>, plafonne le WOT à ~<b>350 Nm</b>, "
        "rail ~1620 bar, smoke progressive (cap 360), hardcut <b>4800 rpm</b>. "
        "Turbo / nm2iq / SOI / deletes = <b>inchangés vs ACE</b>.</li>"
    )
    v2_li = (
        "<li><b>V2</b> (ami, +25€) : part de <b>V1</b>. Annule le softcut AccPed/tqlim (zéros haute régime), "
        "met un <b>vrai hardcut</b> via <code>tqlim_cluth_prot</code> (axe RPM → 4800/4801 = 0 Nm), "
        "et un <b>launch test ~2500 rpm</b> (même map, ratio vitesse/régime ≈ 0). "
        "À valider au log VCDS — ne pas considérer le launch comme validé.</li>"
    )
    if v1_li in html and v2_li not in html:
        html = html.replace(v1_li, v1_li + "\n    " + v2_li, 1)

    how_old = (
        "<li>Paire <b>ACE vs V1</b> = uniquement ce que tu as adouci / plafonné sur ACE.</li>"
    )
    how_new = (
        "<li>Paire <b>ACE vs V1</b> = uniquement ce que tu as adouci / plafonné sur ACE.</li>\n"
        "    <li>Paire <b>V1 vs V2</b> = correction ami (hardcut + launch test).</li>"
    )
    if how_old in html and "V1 vs V2" not in html[html.find("Comment lire le site") : html.find("Comment lire le site") + 800]:
        html = html.replace(how_old, how_new, 1)
    return html


def patch_hex_helpers(html: str) -> str:
    html2, n = re.subn(
        r"function sideBytes\(w, key\) \{\n    if \(key === 'v1'\) return w\.v1 \|\| w\.ace;\n    return w\[key\];\n  \}",
        "function sideBytes(w, key) {\n    if (key === 'v2') return w.v2 || w.v1 || w.ace;\n    if (key === 'v1') return w.v1 || w.ace;\n    return w[key];\n  }",
        html,
        count=1,
    )
    if n != 1:
        print("warn: hex sideBytes not patched", n)
    else:
        html = html2
    old = "v1: b64ToBytes(w.v1 || w.ace),"
    new = "v1: b64ToBytes(w.v1 || w.ace),\n        v2: b64ToBytes(w.v2 || w.v1 || w.ace),"
    if old in html and "v2: b64ToBytes" not in html:
        html = html.replace(old, new, 1)
    return html


def patch_axis_y_v2_render(html: str) -> str:
    """When comparing V2, show remapped clutch-prot RPM axis if present."""
    old = "const yv = g.axisY && g.axisY[r] != null ? g.axisY[r] : r;"
    new = (
        "const axisYUse = (window.COMPARE && window.COMPARE.sides "
        "&& window.COMPARE.sides().indexOf('v2') >= 0 && g.axisY_v2 && g.axisY_v2.length) "
        "? g.axisY_v2 : g.axisY;\n"
        "    const yv = axisYUse && axisYUse[r] != null ? axisYUse[r] : r;"
    )
    if old in html and "axisY_v2" not in html.split("const yv =")[0][-200:]:
        html = html.replace(old, new, 1)
    return html


if __name__ == "__main__":
    main()
