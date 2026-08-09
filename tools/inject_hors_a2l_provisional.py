# -*- coding: utf-8 -*-
"""Add provisional hors-A2L rail banks + limiters into Toutes maps + MAP_GRIDS."""
from __future__ import annotations

import json
import re
from pathlib import Path

SITE = Path(__file__).resolve().parents[1]
INDEX = SITE / "index.html"
CSS = SITE / "chercheur-theme.css"

ROOT = Path(
    r"C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules\Caddy-CAYE-2013-03L906023PA-2531"
)
ORI_PATH = ROOT / "ORI" / "Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin"
ACE_PATH = ROOT / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_ACE_stage1_dpf_egr.NOCS"
V1_PATH = ROOT / "MOD" / "Caddy_CAYE_03L906023TB_9979_MOD_V1_350wot_smooth.NOCS"

FACTOR = 0.0610359
PREC = 1
FOLDER = "Hors A2L / provisoire"


def read_u16(blob: bytes, addr: int, n: int) -> list[int]:
    out = []
    for i in range(n):
        off = addr + i * 2
        out.append(blob[off] | (blob[off + 1] << 8))
    return out


def phys(raw: list[int]) -> list[float]:
    return [round(r * FACTOR, PREC) for r in raw]


def changed_bytes(a: bytes, b: bytes, addr: int, size: int) -> int:
    return sum(1 for i in range(size) if a[addr + i] != b[addr + i])


def bank_entries(ori: bytes, ace: bytes, v1: bytes) -> tuple[list[dict], list[str]]:
    grids = []
    rows_html = []
    for i in range(14):
        addr = 0x1EA168 + i * 0x200
        end = addr + 511
        n = 256
        o_raw = read_u16(ori, addr, n)
        a_raw = read_u16(ace, addr, n)
        v_raw = read_u16(v1, addr, n)
        o = phys(o_raw)
        a = phys(a_raw)
        v = phys(v_raw)
        ch_cells = sum(1 for x, y in zip(o_raw, a_raw) if x != y)
        ch_b = changed_bytes(ori, ace, addr, 512)
        pct = round(100 * ch_b / 512)
        omax, amax, vmax = max(o), max(a), max(v)
        delta = round(amax - omax, PREC)
        bid = f"rail_request_horsA2L_banque_{i + 1:02d}"
        disp = f"Suite rail (hors A2L) banque {i + 1}"
        ah, eh = f"{addr:06X}", f"{end:06X}"
        grids.append(
            {
                "id": bid,
                "name": disp,
                "folder": FOLDER,
                "addr": ah,
                "end": eh,
                "cols": 16,
                "rows": 16,
                "unit": "bar",
                "type": "eZweidim",
                "group": "provisoire",
                "source": "provisoire",
                "axisXName": "Internal torque (estimé)",
                "axisYName": "Engine speed (estimé)",
                "axisXUnit": "Nm",
                "axisYUnit": "RPM",
                "axisX": [],
                "axisY": [],
                "ori": o,
                "ace": a,
                "v1": v,
                "changedCells": ch_cells,
                "changedCellsV1Ori": sum(1 for x, y in zip(o, v) if abs(x - y) > 1e-9),
                "changedCellsV1Ace": sum(1 for x, y in zip(a, v) if abs(x - y) > 1e-9),
                "oriMax": omax,
                "aceMax": amax,
                "v1Max": vmax,
                "precision": PREC,
            }
        )
        dclass = "up" if delta > 0 else ("down" if delta < 0 else "")
        dtxt = f"+{delta}" if delta > 0 else f"{delta}"
        text = f"{bid} {disp.lower()} rail hors a2l provisoire {ah.lower()}"
        rows_html.append(
            f'<tr data-folder="{FOLDER}" data-source="provisoire" data-text="{text}">'
            f'<td><button class="addr" data-addr="{ah}">{ah}</button></td>'
            f'<td><button class="addr" data-addr="{eh}" data-role="fin">{eh}</button></td>'
            f"<td>{bid}</td>"
            f"<td>{disp}</td>"
            f"<td>{FOLDER}</td>"
            f'<td><span class="src-badge src-prov">provisoire (bin)</span></td>'
            f'<td class="num">{ch_b}/512</td>'
            f'<td class="num">{pct}%</td>'
            f'<td class="num">{omax}</td>'
            f'<td class="num">{amax}</td>'
            f'<td class="num {dclass}">{dtxt}</td>'
            f"<td>bar</td></tr>"
        )
    return grids, rows_html


def lim_entries(ori: bytes, ace: bytes, v1: bytes) -> tuple[list[dict], list[str]]:
    grids = []
    rows_html = []
    for label, addr in (("A", 0x1EBDD8), ("B", 0x1EBE58)):
        # 55 × uint16 = 110 octets utiles ; span site = 111 (octet traînant)
        n = 55
        size = 111
        end = addr + size - 1
        o_raw = read_u16(ori, addr, n)
        a_raw = read_u16(ace, addr, n)
        v_raw = read_u16(v1, addr, n)
        o = phys(o_raw)
        a = phys(a_raw)
        v = phys(v_raw)
        ch_cells = sum(1 for x, y in zip(o_raw, a_raw) if x != y)
        ch_b = changed_bytes(ori, ace, addr, size)
        pct = round(100 * ch_b / size)
        omax, amax, vmax = max(o), max(a), max(v)
        delta = round(amax - omax, PREC)
        bid = f"rail_lim_horsA2L_{label}"
        disp = f"Limiteur rail (hors A2L) {label}"
        ah, eh = f"{addr:06X}", f"{end:06X}"
        grids.append(
            {
                "id": bid,
                "name": disp,
                "folder": FOLDER,
                "addr": ah,
                "end": eh,
                "cols": 55,
                "rows": 1,
                "unit": "bar",
                "type": "eEindim",
                "group": "provisoire",
                "source": "provisoire",
                "axisXName": "Index (sans A2L)",
                "axisYName": "Y",
                "axisXUnit": "",
                "axisYUnit": "",
                "axisX": [],
                "axisY": [],
                "ori": o,
                "ace": a,
                "v1": v,
                "changedCells": ch_cells,
                "changedCellsV1Ori": sum(1 for x, y in zip(o, v) if abs(x - y) > 1e-9),
                "changedCellsV1Ace": sum(1 for x, y in zip(a, v) if abs(x - y) > 1e-9),
                "oriMax": omax,
                "aceMax": amax,
                "v1Max": vmax,
                "precision": PREC,
            }
        )
        dclass = "up" if delta > 0 else ("down" if delta < 0 else "")
        dtxt = f"+{delta}" if delta > 0 else f"{delta}"
        text = f"{bid} {disp.lower()} limiteur rail hors a2l provisoire {ah.lower()}"
        rows_html.append(
            f'<tr data-folder="{FOLDER}" data-source="provisoire" data-text="{text}">'
            f'<td><button class="addr" data-addr="{ah}">{ah}</button></td>'
            f'<td><button class="addr" data-addr="{eh}" data-role="fin">{eh}</button></td>'
            f"<td>{bid}</td>"
            f"<td>{disp}</td>"
            f"<td>{FOLDER}</td>"
            f'<td><span class="src-badge src-prov">provisoire (bin)</span></td>'
            f'<td class="num">{ch_b}/{size}</td>'
            f'<td class="num">{pct}%</td>'
            f'<td class="num">{omax}</td>'
            f'<td class="num">{amax}</td>'
            f'<td class="num {dclass}">{dtxt}</td>'
            f"<td>bar</td></tr>"
        )
    return grids, rows_html


def add_source_column_to_existing(tbody: str) -> str:
    """Insert Source <td> after Famille (5th data cell) on each existing row."""

    def patch_row(m: re.Match) -> str:
        row = m.group(0)
        if 'data-source="' in row or "src-badge" in row:
            return row
        folder = m.group(1)
        if folder == "Deletes ACE":
            src = '<td><span class="src-badge src-dtc">Deletes</span></td>'
            src_attr = ' data-source="deletes"'
        else:
            src = '<td><span class="src-badge src-a2l">A2L</span></td>'
            src_attr = ' data-source="a2l"'
        # add data-source on <tr>
        row = row.replace("<tr ", f"<tr{src_attr} ", 1)
        # Famille cell is the 5th <td>...</td> after Id/Nom — insert Source after it.
        # Structure: Debut, Fin, Id, Nom, Famille, Octets, %, ORI, ACE, Delta, Unite
        cells = list(re.finditer(r"<td\b[^>]*>.*?</td>", row, re.S))
        if len(cells) < 5:
            return row
        fam = cells[4]
        insert_at = fam.end()
        return row[:insert_at] + src + row[insert_at:]

    return re.sub(
        r'<tr data-folder="([^"]+)" data-text="[^"]*">.*?</tr>',
        patch_row,
        tbody,
        flags=re.S,
    )


def patch_html(html: str, new_grids: list[dict], new_rows: list[str]) -> str:
    # —— MAP_GRIDS ——
    i = html.find("const MAP_GRIDS = ")
    if i < 0:
        raise SystemExit("MAP_GRIDS not found")
    start = i + len("const MAP_GRIDS = ")
    grids, end = json.JSONDecoder().raw_decode(html, start)
    # drop previous provisional inject if re-run
    grids = [g for g in grids if g.get("group") != "provisoire" and g.get("source") != "provisoire"]
    grids.extend(new_grids)
    html = html[:start] + json.dumps(grids, ensure_ascii=False, separators=(",", ":")) + html[end:]

    # —— table header Source ——
    old_head = (
        "<th>Début</th><th>Fin</th><th>Id</th><th>Nom</th><th>Famille</th>\n"
        "        <th>Octets</th><th>%</th><th>ORI max</th><th>ACE max</th><th>Delta</th><th>Unite</th>"
    )
    new_head = (
        "<th>Début</th><th>Fin</th><th>Id</th><th>Nom</th><th>Famille</th>\n"
        "        <th>Source</th><th>Octets</th><th>%</th><th>ORI max</th><th>ACE max</th><th>Delta</th><th>Unite</th>"
    )
    if "th>Source</th>" not in html:
        if old_head not in html:
            raise SystemExit("table header not found")
        html = html.replace(old_head, new_head, 1)

    # —— tbody: source col + provisional rows ——
    m = re.search(r'(<tbody id="rows">)(.*?)(</tbody>)', html, re.S)
    if not m:
        raise SystemExit("#rows tbody not found")
    body = m.group(2)
    # remove prior provisional rows
    body = re.sub(
        r'<tr data-folder="Hors A2L / provisoire"[^>]*>.*?</tr>\n?',
        "",
        body,
        flags=re.S,
    )
    body = add_source_column_to_existing(body)
    if "src-badge src-prov" not in body:
        body = body.rstrip() + "\n" + "\n".join(new_rows) + "\n"
    else:
        # already had badges; ensure provisional rows present
        if 'data-folder="Hors A2L / provisoire"' not in body:
            body = body.rstrip() + "\n" + "\n".join(new_rows) + "\n"
    html = html[: m.start(2)] + body + html[m.end(2) :]

    # —— sec head / lead ——
    html = html.replace(
        '<h2>Toutes les maps <span class="hint">liste complète · 139 A2L</span></h2>',
        '<h2>Toutes les maps <span class="hint">liste complète · 139 A2L + 16 provisoires</span></h2>',
        1,
    )
    html = html.replace(
        "Ici = <b>toutes</b> les maps nommées A2L touchées (pas seulement le Top 12).\n"
        "      Filtre par famille ou cherche un nom / adresse. Défaut = tout afficher.</p>",
        "Ici = les <b>139 maps A2L</b> + <b>16 maps provisoires</b> (suite rail / limiteurs hors A2L), "
        "plus les deletes DTC via le filtre.\n"
        "      Colonne <b>Source</b> : <code>A2L</code> = vrai nom OEM ; "
        "<code>provisoire (bin)</code> = nom donné par nous (pas un IdName DAMOS). "
        "Défaut = tout afficher.</p>",
        1,
    )
    html = html.replace(
        '<h3 class="maps-block-h" id="maps-a2l">1) Maps A2L (139)</h3>\n'
        '  <p class="note maps-block-lead">Maps avec un nom dans le fichier A2L / DAMOS. '
        "Le filtre « Deletes ACE » ajoute les masques DTC FAP/EGR (34 lignes).</p>",
        '<h3 class="maps-block-h" id="maps-a2l">Liste complète (A2L + provisoires)</h3>\n'
        '  <p class="note maps-block-lead">Les maps <b>A2L</b> ont un vrai nom OEM. '
        "Les <b>provisoires (bin)</b> sont la suite Stage1 rail + 2 limiteurs : on connaît la fonction "
        "par preuve binaire, pas le nom DAMOS — d’où le badge. "
        "Filtre « Hors A2L / provisoire » ou « Deletes ACE » pour cibler.</p>",
        1,
    )

    # folder select option
    if f'value="{FOLDER}"' not in html:
        html = html.replace(
            '<option value="Deletes ACE">Deletes ACE DTC FAP/EGR/EGT (34)</option></select>',
            '<option value="Deletes ACE">Deletes ACE DTC FAP/EGR/EGT (34)</option>'
            f'<option value="{FOLDER}">Hors A2L / provisoire (16)</option></select>',
            1,
        )

    # quick chip
    if 'data-folder="Hors A2L / provisoire"' not in html.split("quick-chips")[1][:800]:
        html = html.replace(
            '<button type="button" class="chip" data-folder="Rail pressure">Rail</button>',
            '<button type="button" class="chip" data-folder="Rail pressure">Rail</button>\n'
            f'    <button type="button" class="chip" data-folder="{FOLDER}">Hors A2L / provisoire</button>',
            1,
        )

    # filter count text
    html = html.replace(
        "count.textContent = total + ' lignes (toutes · 139 A2L + deletes DTC)';",
        "count.textContent = total + ' lignes (toutes · 139 A2L + 16 provisoires + deletes)';",
        1,
    )

    # view2d optgroup
    old_groups = """  const groups = [
    { key: 'priority', label: 'Top 12 Stage 1' },
    { key: 'a2l', label: 'Autres maps A2L touchées' },
    { key: 'dtc', label: 'DTC OFF (masques → 00)' }
  ];"""
    new_groups = """  const groups = [
    { key: 'priority', label: 'Top 12 Stage 1' },
    { key: 'a2l', label: 'Autres maps A2L touchées' },
    { key: 'provisoire', label: 'Hors A2L / provisoire (bin)' },
    { key: 'dtc', label: 'DTC OFF (masques → 00)' }
  ];"""
    if "{ key: 'provisoire'" not in html:
        if old_groups not in html:
            raise SystemExit("v2d groups block not found")
        html = html.replace(old_groups, new_groups, 1)

    # Guide copy
    old_guide = (
        '<p class="guide-p"><b>Zones hors A2L</b> (bas de <a href="#all-maps" data-nav="all-maps">Toutes maps</a>, §2) = suite Stage1 <b>rail + limiteurs</b>, pas des deletes FAP/EGR.\n'
        "  Juste après la dernière map nommée <code>rail_base_int_trq2B</code> (fin <code>1EA167</code>) : 14 banques de 512 octets sans nom DAMOS (dès <code>1EA168</code>), même facteur bar et même hausse 1600→1656 / 1450→1500.7.\n"
        "  Puis deux limiteurs jumeaux <code>1EBDD8</code> / <code>1EBE58</code> (ORI 1600/300 → ACE 1656/310.5 bar).\n"
        "  Les vrais deletes restent sous Deletes ACE / page DTC / <code>0x180xxx</code> / zone <code>19E–1A4</code>.</p>\n"
        "  <p class=\"guide-p\"><b>Comment on sait</b> : comparé sur bin ORI vs ACE Caddy 9979, puis contre-épreuve Passat FAP-only (même soft) — <b>0 octet</b> touché sur rail Stage1 + limiteurs, alors que la zone DTC <code>19E000–1A4000</code> change bien. Sans A2L complet, pas d’IdNames OEM exacts.</p>"
    )
    new_guide = (
        '<p class="guide-p"><b>Zones hors A2L → maps provisoires</b> : avant, elles étaient à part parce que les <b>139</b> viennent du fichier A2L '
        "(vrai nom OEM + axes + facteur), alors que hors-A2L = on connaît la <b>fonction</b> par preuve bin "
        "(14 banques rail + 2 limiteurs) mais <b>pas</b> l’IdName OEM — on ne pouvait pas les mélanger sans inventer un nom DAMOS.</p>\n"
        '  <p class="guide-p">Maintenant elles sont dans <a href="#all-maps" data-nav="all-maps">Toutes maps</a> avec un <b>nom provisoire</b> '
        "et le badge <code>Source: provisoire (bin)</code> (ex. « Suite rail (hors A2L) banque 1 », « Limiteur rail (hors A2L) A/B »). "
        "Le vrai nom OEM arrivera avec un A2L complet. Ce n’est <b>pas</b> un delete FAP/EGR "
        "(contre-épreuve Passat FAP-only : 0 octet ici ; deletes = filtre Deletes ACE / page DTC).</p>"
    )
    if old_guide in html:
        html = html.replace(old_guide, new_guide, 1)
    elif "nom provisoire" not in html:
        # softer fallback: replace first hors A2L guide paragraph block
        html = re.sub(
            r'<p class="guide-p"><b>Zones hors A2L</b>.*?</p>\s*<p class="guide-p"><b>Comment on sait</b>.*?</p>',
            new_guide,
            html,
            count=1,
            flags=re.S,
        )

    # Hors-A2L subsection → short note
    hors_pat = re.compile(
        r'<h3 class="maps-block-h" id="hors-a2l">2\) Hors A2L — suite rail \+ limiteurs</h3>.*?'
        r'<p class="note"><b>Rôle \(colonne\) :</b>.*?</p>',
        re.S,
    )
    hors_new = (
        '<h3 class="maps-block-h" id="hors-a2l">Hors A2L / provisoire — pourquoi ce badge ?</h3>\n'
        '  <p class="note maps-block-lead">Ces 16 maps sont <b>déjà dans le tableau ci-dessus</b> '
        "(filtre chip <b>Hors A2L / provisoire</b>). "
        "On leur a donné un <b>nom provisoire</b> pour les lister avec les autres ; "
        "le vrai nom OEM viendra avec un A2L complet. "
        "Adresses : banques <code>1EA168</code>…<code>1EBB68</code> (14 × 512 o, 16×16, facteur 0.0610359 bar) "
        "+ limiteurs <code>1EBDD8</code> / <code>1EBE58</code> (courbes ~55 valeurs). "
        "Même bump Stage1 1600→1656 / 1450→1500.7 — <b>pas</b> un delete FAP.</p>"
    )
    html2, n = hors_pat.subn(hors_new, html, count=1)
    if n != 1 and 'id="hors-a2l"' in html and "nom provisoire" not in html.split('id="hors-a2l"')[1][:500]:
        raise SystemExit("hors-a2l subsection replace failed")
    html = html2 if n == 1 else html

    # prio note
    html = html.replace(
        "Il y a <b>139 maps A2L</b> touchées (+ zones hors A2L en bas de page).",
        "Il y a <b>139 maps A2L</b> touchées + <b>16 provisoires</b> (hors A2L) dans Toutes maps.",
        1,
    )

    return html


def patch_css(css: str) -> str:
    if ".src-badge" in css:
        return css
    block = """
.src-badge {
  display: inline-block;
  font-family: var(--display);
  font-size: 0.68em;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-radius: 2px;
  padding: 2px 7px;
  font-weight: 700;
  white-space: nowrap;
}
.src-badge.src-a2l {
  background: rgba(62, 207, 122, 0.12);
  color: var(--ok);
  border: 1px solid rgba(62, 207, 122, 0.35);
}
.src-badge.src-prov {
  background: rgba(245, 197, 66, 0.14);
  color: var(--accent2);
  border: 1px solid rgba(245, 197, 66, 0.4);
}
.src-badge.src-dtc {
  background: var(--soft);
  color: var(--accent-hot);
  border: 1px solid var(--line-hot);
}
"""
    return css.rstrip() + "\n" + block


def main() -> None:
    ori = ORI_PATH.read_bytes()
    ace = ACE_PATH.read_bytes()
    v1 = V1_PATH.read_bytes()
    g1, r1 = bank_entries(ori, ace, v1)
    g2, r2 = lim_entries(ori, ace, v1)
    new_grids = g1 + g2
    new_rows = r1 + r2
    html = INDEX.read_text(encoding="utf-8")
    html = patch_html(html, new_grids, new_rows)
    INDEX.write_text(html, encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    CSS.write_text(patch_css(css), encoding="utf-8")
    print(f"OK: +{len(new_grids)} MAP_GRIDS, +{len(new_rows)} table rows")
    for g in new_grids:
        print(f"  {g['id']:40s} {g['addr']}-{g['end']} max {g['oriMax']} -> {g['aceMax']}")


if __name__ == "__main__":
    main()
