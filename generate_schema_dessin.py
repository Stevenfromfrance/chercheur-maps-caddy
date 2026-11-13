#!/usr/bin/env python3
"""
Schéma dessiné FarDriver :
- Page 1 : vue d'ensemble 30 broches → toutes les photos (fils colorés)
- Pages 2–10 : 1 photo = le 30-pin avec SEULEMENT les fils de cette photo dessinés
"""

from pathlib import Path
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

ROOT = Path(__file__).parent
OUT = ROOT / "SCHEMA_30PIN_FILS_COLORS.pdf"
ART = Path("/opt/cursor/artifacts/SCHEMA_30PIN_FILS_COLORS.pdf")
PHOTOS = ROOT / "photos_faisceau_web"

PINS = {
    1:  ("HALLA", "Jaune", "#F9A825"),
    2:  ("FW2", "Bleu/Blanc", "#4FC3F7"),
    3:  ("FW", "Jaune/Blanc", "#FFF176"),
    4:  ("HALL+", "Rouge", "#E53935"),
    5:  ("CANL", "Brun/Jaune", "#FBC02D"),
    6:  ("GND", "Noir", "#212121"),
    7:  ("GND", "Noir", "#212121"),
    8:  ("RE", "Brun/Blanc", "#BCAAA4"),
    9:  ("SPA", "Violet", "#7E57C2"),
    10: ("KEY", "Orange", "#FB8C00"),
    11: ("BH", "Gris", "#9E9E9E"),
    12: ("HALLB", "Vert", "#43A047"),
    13: ("RXD", "Rouge/Noir", "#C62828"),
    14: ("FD", "Noir/Blanc", "#78909C"),
    15: ("CANH", "Rouge/Jaune", "#FFEE58"),
    16: ("GND", "Noir", "#212121"),
    17: ("P", "Bleu/Rouge", "#EF5350"),
    18: ("ALARM", "Marron", "#8D6E63"),
    19: ("W", "Brun/Rouge", "#BF360C"),
    20: ("KEY", "Orange", "#FB8C00"),
    21: ("BL", "Jaune/Vert", "#C0CA33"),
    22: ("HALLC", "Bleu", "#1E88E5"),
    23: ("TXD", "Brun/Bleu", "#5D4037"),
    24: ("TEMP", "Blanc", "#ECEFF1"),
    25: ("—", "—", "#BDBDBD"),
    26: ("GND", "Noir", "#212121"),
    27: ("SV", "Vert/Blanc", "#81C784"),
    28: ("ACC+", "Rouge/Blanc", "#EF9A9A"),
    29: ("BW5V", "Brun/Vert", "#66BB6A"),
    30: ("60VC", "Rose", "#EC407A"),
}

GROUPS = [
    {
        "photo": 3,
        "file": "01a1bb62-d8e5-7ccf-8fe8-c683edaadd24.jpg",
        "title": "PHOTO 3 — HALL MOTEUR",
        "subtitle": "Label KS-NS-HALL → branche sur le moteur",
        "pins": [4, 24, 6, 22, 12, 1],
        "labels": ["Rouge = HALL+ alim", "Blanc = TEMP (option)", "Noir = GND", "Bleu = HALL C", "Vert = HALL B", "Jaune = HALL A"],
        "side": "L",
        "must": True,
    },
    {
        "photo": 8,
        "file": "01a1bb62-ddd3-741b-839b-5d435c48b8a3.jpg",
        "title": "PHOTO 8 — ACCÉLÉRATEUR",
        "subtitle": "Poignée de gaz 3 fils",
        "pins": [28, 27, 26],
        "labels": ["Rose = ACC+ (+5V)", "Vert/Blanc = SV signal gaz", "Noir = GND"],
        "side": "L",
        "must": True,
    },
    {
        "photo": 2,
        "file": "01a1bb62-d7cd-7099-93e1-b88e9b2e726c.jpg",
        "title": "PHOTO 2 — CONTACT KEY",
        "subtitle": "Fil orange seul = allumage",
        "pins": [10],
        "labels": ["Orange = KEY (+ batterie via clé)"],
        "side": "L",
        "must": True,
    },
    {
        "photo": 9,
        "file": "01a1bb62-deab-7e6a-8ebf-50ae01813956.jpg",
        "title": "PHOTO 9 — FREIN BASSE",
        "subtitle": "Vert/Jaune + Noir dénudés",
        "pins": [21, 26],
        "labels": ["Vert/Jaune = BL frein basse", "Noir = GND frein"],
        "side": "L",
        "must": True,
    },
    {
        "photo": 1,
        "file": "01a1bb62-d6b9-712b-bfcd-7e7fd39a54dd.jpg",
        "title": "PHOTO 1 — MODES VITESSE",
        "subtitle": "Bleu/Blanc + Jaune/Blanc + Noir + boucle",
        "pins": [2, 3, 7],
        "labels": ["Bleu/Blanc = FW2 vitesse basse", "Jaune/Blanc = FW vitesse haute", "Noir = GND (boucle = haute défaut)"],
        "side": "R",
        "must": False,
    },
    {
        "photo": 5,
        "file": "01a1bb62-db0b-706e-8102-999835e1d010.jpg",
        "title": "PHOTO 5 — FREIN HAUTE + COMPTEUR",
        "subtitle": "Gris + Violet + Bleu cosses",
        "pins": [11, 9],
        "labels": ["Gris = BH frein haute (+12V)", "Violet = SPA compteur vitesse"],
        "side": "R",
        "must": False,
    },
    {
        "photo": 4,
        "file": "01a1bb62-d9dd-769d-b9f9-ca90edeb854e.jpg",
        "title": "PHOTO 4 — ALARME ANTIVOL",
        "subtitle": "Connecteurs rouge/blanc alarme",
        "pins": [30, 7, 14, 19, 20],
        "labels": ["Rose = 60VC (+ batterie alarme)", "Noir = GND alarme", "Noir/Blanc = FD antivol", "Brun/Rouge = W lock", "Orange = KEY alarme"],
        "side": "R",
        "must": False,
    },
    {
        "photo": 7,
        "file": "01a1bb62-dce4-77b5-8d2a-9d53733d3bb6.jpg",
        "title": "PHOTO 7 — CRUISE / BOOST",
        "subtitle": "Bleu + Marron",
        "pins": [17, 18],
        "labels": ["Bleu/Rouge = P cruise", "Marron = ALARM / BOOST"],
        "side": "R",
        "must": False,
    },
    {
        "photo": 6,
        "file": "01a1bb62-dc1c-7703-a0ed-091d8d93ce51.jpg",
        "title": "PHOTO 6 — PRISE 6 FILS + MASSE",
        "subtitle": "Bluetooth / série / CAN",
        "pins": [29, 13, 23, 16, 15, 5],
        "labels": ["Brun/Vert = BW5V Bluetooth", "Rouge/Noir = RXD", "Brun/Bleu = TXD", "Noir = GND", "Rouge/Jaune = CANH", "Brun/Jaune = CANL"],
        "side": "R",
        "must": False,
    },
]


def hx(s):
    return HexColor(s.split("|")[0] if "|" in s else s)


def wire_color(pin):
    name = PINS[pin][1]
    dual = {
        "Bleu/Blanc": "#1E88E5",
        "Jaune/Blanc": "#FBC02D",
        "Brun/Jaune": "#F9A825",
        "Brun/Blanc": "#A1887F",
        "Rouge/Noir": "#E53935",
        "Noir/Blanc": "#546E7A",
        "Rouge/Jaune": "#FF7043",
        "Bleu/Rouge": "#5C6BC0",
        "Brun/Rouge": "#D84315",
        "Jaune/Vert": "#AFB42B",
        "Brun/Bleu": "#5D4037",
        "Vert/Blanc": "#66BB6A",
        "Rouge/Blanc": "#EF5350",
        "Brun/Vert": "#558B2F",
    }
    return dual.get(name, PINS[pin][2])


def draw_connector(c, x, y, cell_w, cell_h, highlight=None, dim_others=True):
    """Draw 3x10 grid. highlight=set of pins to emphasize."""
    highlight = set(highlight or [])
    plate_w = 10 * cell_w + 4 * mm
    plate_h = 3 * cell_h + 6 * mm
    c.setFillColor(hx("#263238"))
    c.roundRect(x - 2 * mm, y - plate_h + cell_h + 2 * mm, plate_w, plate_h, 2 * mm, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + plate_w / 2 - 2 * mm, y + 4.5 * mm, "CONNECTEUR 30 BROCHES")
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + plate_w / 2 - 2 * mm, y + 1.2 * mm, "Haut 21→30 · Milieu 11→20 · Bas 1→10")

    centers = {}
    rows = [list(range(21, 31)), list(range(11, 21)), list(range(1, 11))]
    for r, pins in enumerate(rows):
        for col, pin in enumerate(pins):
            code, name, color = PINS[pin]
            px = x + col * cell_w
            py = y - r * cell_h
            active = (not highlight) or (pin in highlight)
            if active:
                c.setFillColor(hx(color))
                c.setStrokeColor(hx("#000000"))
                c.setLineWidth(1.2 if highlight else 0.5)
            else:
                c.setFillColor(hx("#546E7A"))
                c.setStrokeColor(hx("#37474F"))
                c.setLineWidth(0.3)
            c.roundRect(px + 0.3 * mm, py - cell_h + 1.0 * mm, cell_w - 0.6 * mm, cell_h - 1.4 * mm, 1 * mm, fill=1, stroke=1)

            light = color.upper() in {
                "#FFF176", "#FFEE58", "#ECEFF1", "#81C784", "#EF9A9A",
                "#4FC3F7", "#BCAAA4", "#BDBDBD", "#F9A825", "#FBC02D",
                "#C0CA33", "#66BB6A",
            }
            if active:
                c.setFillColor(black if light else white)
            else:
                c.setFillColor(hx("#90A4AE"))
            c.setFont("Helvetica-Bold", 7 if cell_w > 15 * mm else 6)
            c.drawCentredString(px + cell_w / 2, py - 3.8 * mm, str(pin))
            c.setFont("Helvetica-Bold", 5)
            c.drawCentredString(px + cell_w / 2, py - 7.2 * mm, code)
            c.setFont("Helvetica", 4)
            c.drawCentredString(px + cell_w / 2, py - 10.2 * mm, name[:10])
            centers[pin] = (px + cell_w / 2, py - cell_h / 2)
    return centers


def draw_wire(c, x1, y1, x2, y2, color, width=2.4):
    c.setStrokeColor(hx(color))
    c.setLineWidth(width)
    c.setLineCap(1)
    c.line(x1, y1, x2, y2)


def draw_group_box(c, box_x, box_y, box_w, box_h, group):
    border = "#C62828" if group["must"] else "#1565C0"
    fill = "#FFEBEE" if group["must"] else "#E3F2FD"
    c.setFillColor(hx(fill))
    c.setStrokeColor(hx(border))
    c.setLineWidth(1.8)
    c.roundRect(box_x, box_y, box_w, box_h, 2 * mm, fill=1, stroke=1)

    c.setFillColor(hx(border))
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(box_x + 2 * mm, box_y + box_h - 5 * mm, group["title"])
    c.setFillColor(hx("#455A64"))
    c.setFont("Helvetica", 6)
    c.drawString(box_x + 2 * mm, box_y + box_h - 9 * mm, group["subtitle"][:48])

    cy = box_y + box_h - 15 * mm
    points = []
    for i, (pin, lab) in enumerate(zip(group["pins"], group["labels"])):
        col = wire_color(pin)
        c.setFillColor(hx(col))
        c.circle(box_x + 5 * mm, cy - i * 5.0 * mm, 2.0 * mm, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(box_x + 9 * mm, cy - i * 5.0 * mm - 1.1 * mm, f"broche #{pin}")
        c.setFont("Helvetica", 5.8)
        c.setFillColor(hx("#212121"))
        c.drawString(box_x + 26 * mm, cy - i * 5.0 * mm - 1.1 * mm, lab[:34])
        py = cy - i * 5.0 * mm
        if group["side"] == "L":
            points.append((box_x + box_w, py, pin))
        else:
            points.append((box_x, py, pin))

    c.setFillColor(hx(border))
    c.setFont("Helvetica-Bold", 6)
    c.drawRightString(box_x + box_w - 2 * mm, box_y + 2.2 * mm, "OBLIGATOIRE" if group["must"] else "OPTION")
    return points


def route(c, centers, points, side, cell_w, width=2.2):
    for bx, by, pin in points:
        if pin not in centers:
            continue
        px, py = centers[pin]
        col = wire_color(pin)
        if side == "L":
            mid = (px + bx) / 2
            draw_wire(c, px - cell_w / 2, py, mid, py, col, width)
            draw_wire(c, mid, py, mid, by, col, width)
            draw_wire(c, mid, by, bx, by, col, width)
        else:
            mid = (px + bx) / 2
            draw_wire(c, px + cell_w / 2, py, mid, py, col, width)
            draw_wire(c, mid, py, mid, by, col, width)
            draw_wire(c, mid, by, bx, by, col, width)
        c.setFillColor(hx(col))
        c.circle(px, py, 1.4 * mm, fill=1, stroke=0)


def page_overview(c):
    W, H = landscape(A3)
    c.setPageSize(landscape(A3))

    c.setFillColor(hx("#0D47A1"))
    c.rect(0, H - 18 * mm, W, 18 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(10 * mm, H - 7 * mm, "VUE D'ENSEMBLE — 30 BROCHES → FILS COLORÉS → TES PHOTOS")
    c.setFont("Helvetica", 8)
    c.drawString(10 * mm, H - 13 * mm, "FarDriver ND72450 · Chaque ligne colorée = 1 fil du faisceau · Suis la ligne de la broche jusqu'à la photo")

    cell_w, cell_h = 17 * mm, 12.5 * mm
    conn_w = 10 * cell_w
    conn_x = (W - conn_w) / 2
    conn_y = H - 48 * mm
    centers = draw_connector(c, conn_x, conn_y, cell_w, cell_h)

    box_w = 70 * mm
    left_x, right_x = 6 * mm, W - 6 * mm - box_w
    left = [g for g in GROUPS if g["side"] == "L"]
    right = [g for g in GROUPS if g["side"] == "R"]

    def stack(groups, x):
        top = H - 24 * mm
        placed = []
        by = top
        for g in groups:
            box_h = 13 * mm + len(g["pins"]) * 5.0 * mm
            by = by - box_h
            pts = draw_group_box(c, x, by, box_w, box_h, g)
            placed.append((pts, g))
            by -= 3.5 * mm
        return placed

    for pts, g in stack(left, left_x):
        route(c, centers, pts, "L", cell_w)
    for pts, g in stack(right, right_x):
        route(c, centers, pts, "R", cell_w)

    c.setFillColor(hx("#212121"))
    c.roundRect(6 * mm, 5 * mm, W - 12 * mm, 14 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 7.5)
    c.drawString(10 * mm, 12 * mm, "Pages suivantes = ZOOM photo par photo : ta photo à gauche, et à droite SEULEMENT les fils de cette photo dessinés sur le 30-pin.")
    c.drawString(10 * mm, 7 * mm, "Rouge = obligatoire · Bleu = option · Broche #25 vide · Bornes puissance B+/B−/U/V/W sont HORS de ce connecteur (vis).")
    c.showPage()


def page_detail(c, group, index, total):
    W, H = landscape(A4)
    c.setPageSize(landscape(A4))

    border = "#C62828" if group["must"] else "#1565C0"
    c.setFillColor(hx(border))
    c.rect(0, H - 16 * mm, W, 16 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(10 * mm, H - 7 * mm, group["title"])
    c.setFont("Helvetica", 8)
    c.drawString(10 * mm, H - 12.5 * mm, f"Page détail {index}/{total} · {group['subtitle']}")
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(W - 10 * mm, H - 7 * mm, "OBLIGATOIRE" if group["must"] else "OPTION")

    # LEFT: photo
    img_path = PHOTOS / group["file"]
    max_w, max_h = 95 * mm, H - 50 * mm
    im = Image.open(img_path)
    iw, ih = im.size
    scale = min(max_w / iw, max_h / ih)
    dw, dh = iw * scale, ih * scale
    ix, iy = 10 * mm, H - 22 * mm - dh
    c.setStrokeColor(hx("#90A4AE"))
    c.rect(ix - 1 * mm, iy - 1 * mm, dw + 2 * mm, dh + 2 * mm, fill=0, stroke=1)
    c.drawImage(ImageReader(str(img_path)), ix, iy, width=dw, height=dh, preserveAspectRatio=True, mask="auto")

    c.setFillColor(hx("#37474F"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(10 * mm, iy - 6 * mm, "← TA PHOTO")

    # RIGHT: connector with only these pins highlighted + wires to a label column
    cell_w, cell_h = 14 * mm, 11 * mm
    conn_x = 115 * mm
    conn_y = H - 35 * mm
    centers = draw_connector(c, conn_x, conn_y, cell_w, cell_h, highlight=group["pins"])

    # target column on far right
    tx = W - 8 * mm
    ty0 = H - 40 * mm
    for i, (pin, lab) in enumerate(zip(group["pins"], group["labels"])):
        ty = ty0 - i * 12 * mm
        col = wire_color(pin)
        # label pill
        c.setFillColor(hx("#FAFAFA"))
        c.setStrokeColor(hx(col))
        c.setLineWidth(2)
        c.roundRect(tx - 68 * mm, ty - 4 * mm, 66 * mm, 10 * mm, 1.5 * mm, fill=1, stroke=1)
        c.setFillColor(hx(col))
        c.circle(tx - 63 * mm, ty + 1 * mm, 2.3 * mm, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(tx - 58 * mm, ty - 0.5 * mm, f"#{pin}")
        c.setFont("Helvetica", 7)
        c.drawString(tx - 48 * mm, ty - 0.5 * mm, lab[:28])

        # wire from pin to label
        px, py = centers[pin]
        mid = (px + (tx - 68 * mm)) / 2 + 8 * mm
        draw_wire(c, px + cell_w / 2, py, mid, py, col, 3.0)
        draw_wire(c, mid, py, mid, ty + 1 * mm, col, 3.0)
        draw_wire(c, mid, ty + 1 * mm, tx - 68 * mm, ty + 1 * mm, col, 3.0)
        c.setFillColor(hx(col))
        c.circle(px, py, 1.6 * mm, fill=1, stroke=0)

    # bottom instruction
    c.setFillColor(hx("#212121"))
    c.roundRect(10 * mm, 6 * mm, W - 20 * mm, 16 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(14 * mm, 16 * mm, "LIS COMME ÇA :")
    c.setFont("Helvetica", 7.5)
    pins_txt = " + ".join(f"#{p}" for p in group["pins"])
    c.drawString(14 * mm, 10 * mm, f"Sur ta photo tu vois ce connecteur. Sur le FarDriver ça part des broches {pins_txt}. Suis chaque LIGNE COLORÉE = 1 fil.")
    c.showPage()


def build():
    c = canvas.Canvas(str(OUT), pagesize=landscape(A3))
    page_overview(c)
    # detail pages ordered by photo number
    ordered = sorted(GROUPS, key=lambda g: g["photo"])
    for i, g in enumerate(ordered, 1):
        page_detail(c, g, i, len(ordered))
    c.save()
    ART.write_bytes(OUT.read_bytes())
    print(f"PDF: {OUT} ({OUT.stat().st_size} bytes)")
    print(f"Artifact: {ART}")


if __name__ == "__main__":
    build()
