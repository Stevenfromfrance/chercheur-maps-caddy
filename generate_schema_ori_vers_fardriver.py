#!/usr/bin/env python3
"""
Schéma : faisceau ORIGINE scooter (connecteur blanc/orange)
→ branchement vers faisceau FARDRIVER.
"""

from pathlib import Path
from reportlab.lib.pagesizes import A3, A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

ROOT = Path(__file__).parent
OUT = ROOT / "SCHEMA_ORI_VERS_FARDRIVER.pdf"
ART = Path("/opt/cursor/artifacts/SCHEMA_ORI_VERS_FARDRIVER.pdf")
PHOTOS = [
    Path("/home/ubuntu/.cursor/projects/agent-repos-chercheur-maps-caddy/assets/BBB4F0FE-2773-4327-83F3-B5AC561DFA27_L0_001.jpg"),
    Path("/home/ubuntu/.cursor/projects/agent-repos-chercheur-maps-caddy/assets/95C1587C-94CC-4CAD-B025-6A0FEBA525D9_L0_001.jpg"),
]

# OEM 16-pin (2x8) — orientation: looking at ORANGE FACE, wires exit to the RIGHT.
# Columns numbered 1→8 from LEFT to RIGHT on the orange face.
# Colors cross-checked from face + back photos (confidence noted).
# Format: (col, row, color_name, hex, function_probable, fardriver_target, conf)
# row: 'H' = haute (loin du pouce / top in face photo), 'B' = basse
# Orientation: face ORANGE vers toi, faisceau de fils vers la DROITE de la photo.
# Colonnes 1→8 = GAUCHE → DROITE sur la face.
# Rangée H = haute (loin du pouce) · B = basse (près du pouce).
# Couleurs lues sur tes 2 photos (face + dos). Fonctions = standards scoot CN + matching FarDriver.
OEM_PINS = [
    # Rangée HAUTE L→R
    (1, "H", "Rouge", "#E53935", "Alim accessoire / +5V possible", "Tester tension → ACC+ #28 si ~5V", "med"),
    (2, "H", "Vert/Blanc", "#81C784", "Signal accélérateur (SV) probable", "FarDriver SV Vert/Blanc #27", "med"),
    (3, "H", "Bleu/Blanc", "#4FC3F7", "Mode vitesse / signal", "FW2 Bleu/Blanc #2 (option)", "low"),
    (4, "H", "Gris", "#9E9E9E", "Frein haute (+12V) probable", "FarDriver BH Gris #11", "med"),
    (5, "H", "Orange", "#FB8C00", "CONTACT KEY (allumage)", "FarDriver KEY Orange #10 — OBLIGATOIRE", "high"),
    (6, "H", "Jaune", "#F9A825", "Compteur / signal vitesse", "SPA Violet FarDriver #9 (option)", "med"),
    (7, "H", "Bleu", "#1E88E5", "Frein / accessoire / reverse", "Tester au levier frein", "med"),
    (8, "H", "Rouge/Blanc", "#EF9A9A", "+5V accélérateur probable", "FarDriver ACC+ Rouge/Blanc #28", "med"),
    # Rangée BASSE L→R
    (1, "B", "Vide", "#BDBDBD", "—", "—", "high"),
    (2, "B", "Violet foncé", "#6A1B9A", "Frein / mode / alarme", "Option — tester", "low"),
    (3, "B", "Vert", "#43A047", "Frein basse ou signal", "Si frein masse → BL #21", "med"),
    (4, "B", "Vide", "#BDBDBD", "—", "—", "high"),
    (5, "B", "Violet", "#8E24AA", "Accessoire / frein", "Option", "med"),
    (6, "B", "Gris", "#78909C", "Frein / signal", "Possible BH #11", "low"),
    (7, "B", "Blanc", "#ECEFF1", "Frein / data / GND signal", "Tester continuité frein", "med"),
    (8, "B", "Jaune", "#FBC02D", "Signal / vitesse", "SPA #9 ou tester", "med"),
]

# Cleaner mapping table for the "how to connect" page — function-first
MAP = [
    {
        "ori": "Gros ROUGE batterie",
        "ori_color": "#E53935",
        "far": "Borne B+ (rouge)",
        "far_color": "#E53935",
        "note": "Hors connecteur signal · fusible 200A",
        "must": True,
    },
    {
        "ori": "Gros NOIR batterie",
        "ori_color": "#212121",
        "far": "Borne B− (noir)",
        "far_color": "#212121",
        "note": "Hors connecteur signal",
        "must": True,
    },
    {
        "ori": "Gros JAUNE moteur",
        "ori_color": "#F9A825",
        "far": "Borne U (jaune)",
        "far_color": "#F9A825",
        "note": "Phase moteur",
        "must": True,
    },
    {
        "ori": "Gros VERT moteur",
        "ori_color": "#43A047",
        "far": "Borne V (verte)",
        "far_color": "#43A047",
        "note": "Phase moteur",
        "must": True,
    },
    {
        "ori": "Gros BLEU moteur",
        "ori_color": "#1E88E5",
        "far": "Borne W (bleue)",
        "far_color": "#1E88E5",
        "note": "Phase moteur",
        "must": True,
    },
    {
        "ori": "Hall moteur (prise à part 5 fils)",
        "ori_color": "#E53935",
        "far": "Photo 3 FarDriver HALL",
        "far_color": "#E53935",
        "note": "R N J V B → HALL+ GND A B C",
        "must": True,
    },
    {
        "ori": "Fil ORANGE du connecteur blanc",
        "ori_color": "#FB8C00",
        "far": "Photo 2 KEY orange #10",
        "far_color": "#FB8C00",
        "note": "Contact / allumage — OBLIGATOIRE",
        "must": True,
    },
    {
        "ori": "3 fils accélérateur (R/+5V, N, signal)",
        "ori_color": "#EF5350",
        "far": "Photo 8 throttle #28 #27 #26",
        "far_color": "#81C784",
        "note": "+5V / SV / GND — tester 0.8→4.5V",
        "must": True,
    },
    {
        "ori": "Frein (2 fils, continuité au levier)",
        "ori_color": "#AFB42B",
        "far": "Photo 9 BL #21+#26  OU  Photo 5 Gris #11",
        "far_color": "#AFB42B",
        "note": "Masse=BL · +12V=BH",
        "must": True,
    },
    {
        "ori": "Gris / Violet / Blanc / Bleu restants",
        "ori_color": "#7E57C2",
        "far": "Photos 1,5,6,7 FarDriver",
        "far_color": "#1565C0",
        "note": "Modes / compteur / alarme — APRÈS premier essai",
        "must": False,
    },
]


def hx(c):
    return HexColor(c)


def draw_oem_connector(c, x, y, cell_w, cell_h):
    """Draw 2x8 OEM connector face with colored wires."""
    # housing
    c.setFillColor(hx("#ECEFF1"))
    c.setStrokeColor(hx("#FB8C00"))
    c.setLineWidth(2.5)
    plate_w = 8 * cell_w + 6 * mm
    plate_h = 2 * cell_h + 10 * mm
    c.roundRect(x, y - plate_h, plate_w, plate_h, 3 * mm, fill=1, stroke=1)

    # orange face insert
    c.setFillColor(hx("#FF9800"))
    c.roundRect(x + 2 * mm, y - plate_h + 3 * mm, plate_w - 4 * mm, plate_h - 8 * mm, 2 * mm, fill=1, stroke=0)

    c.setFillColor(hx("#E65100"))
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + plate_w / 2, y - 4 * mm, "CONNECTEUR ORIGINE SCOOTER (face orange)")
    c.setFont("Helvetica", 6.5)
    c.setFillColor(hx("#5D4037"))
    c.drawCentredString(x + plate_w / 2, y - 7.5 * mm, "16 broches · 2 rangées × 8 · vue face (côté qui rentrait dans l’ancien contrôleur)")

    centers = {}
    for col, row, color_name, color_hex, func, target, conf in OEM_PINS:
        r = 0 if row == "H" else 1
        px = x + 3 * mm + (col - 1) * cell_w
        py = y - 12 * mm - r * cell_h
        # pin hole circle with wire color
        if color_name == "Vide":
            c.setFillColor(hx("#FFF3E0"))
            c.setStrokeColor(hx("#BF360C"))
            c.setLineWidth(0.8)
            c.circle(px + cell_w / 2, py - cell_h / 2, 3.2 * mm, fill=1, stroke=1)
            c.setFillColor(hx("#BF360C"))
            c.setFont("Helvetica", 5)
            c.drawCentredString(px + cell_w / 2, py - cell_h / 2 - 1.2 * mm, "vide")
        else:
            c.setFillColor(hx(color_hex))
            c.setStrokeColor(hx("#212121"))
            c.setLineWidth(1)
            c.circle(px + cell_w / 2, py - cell_h / 2, 3.5 * mm, fill=1, stroke=1)
            light = color_hex.upper() in {"#ECEFF1", "#EF9A9A", "#F9A825", "#FBC02D", "#4FC3F7", "#66BB6A", "#AFB42B", "#BDBDBD"}
            c.setFillColor(black if light else white)
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(px + cell_w / 2, py - cell_h / 2 + 0.8 * mm, f"{row}{col}")
            c.setFont("Helvetica", 4)
            c.drawCentredString(px + cell_w / 2, py - cell_h / 2 - 2.2 * mm, color_name[:8])
        centers[(col, row)] = (px + cell_w / 2, py - cell_h / 2)

        # column numbers under
        if row == "B":
            c.setFillColor(hx("#5D4037"))
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(px + cell_w / 2, y - plate_h + 1.5 * mm, str(col))

    return centers, plate_w, plate_h


def page_overview(c):
    W, H = landscape(A3)
    c.setPageSize(landscape(A3))

    # header
    c.setFillColor(hx("#BF360C"))
    c.rect(0, H - 18 * mm, W, 18 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(10 * mm, H - 7 * mm, "SCHÉMA : FAISCEAU ORIGINE SCOOTER  →  FAISCEAU FARDRIVER")
    c.setFont("Helvetica", 8)
    c.drawString(10 * mm, H - 13 * mm, "À gauche = connecteur blanc/orange d’origine · À droite = où brancher sur le FarDriver · Lignes = branchements")

    # LEFT OEM connector
    cell_w, cell_h = 18 * mm, 16 * mm
    centers, pw, ph = draw_oem_connector(c, 8 * mm, H - 28 * mm, cell_w, cell_h)

    # wire list under OEM
    y = H - 28 * mm - ph - 6 * mm
    c.setFillColor(hx("#E65100"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(8 * mm, y, "FILS DU CONNECTEUR ORIGINE (couleur → rôle probable)")
    y -= 5 * mm
    for col, row, color_name, color_hex, func, target, conf in OEM_PINS:
        if color_name == "Vide":
            continue
        c.setFillColor(hx(color_hex))
        c.circle(10 * mm, y + 1 * mm, 1.8 * mm, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(14 * mm, y, f"{row}{col}")
        c.setFillColor(hx("#E65100"))
        c.setFont("Helvetica-Bold", 6)
        c.drawString(22 * mm, y, color_name[:14])
        c.setFillColor(hx("#212121"))
        c.setFont("Helvetica", 6)
        c.drawString(48 * mm, y, func[:42])
        # conf
        conf_c = {"high": "#2E7D32", "med": "#EF6C00", "low": "#C62828"}[conf]
        c.setFillColor(hx(conf_c))
        c.setFont("Helvetica", 5)
        c.drawString(110 * mm, y, conf)
        y -= 4.2 * mm

    # RIGHT FarDriver targets
    box_x = 145 * mm
    box_w = W - box_x - 8 * mm
    by = H - 30 * mm
    c.setFillColor(hx("#0D47A1"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(box_x, by, "CÔTÉ FARDRIVER — OÙ BRANCHER")
    by -= 4 * mm

    for m in MAP:
        h = 14 * mm if m["must"] else 11 * mm
        by -= h + 2 * mm
        border = "#C62828" if m["must"] else "#1565C0"
        fill = "#FFEBEE" if m["must"] else "#E3F2FD"
        c.setFillColor(hx(fill))
        c.setStrokeColor(hx(border))
        c.setLineWidth(1.5)
        c.roundRect(box_x, by, box_w, h, 1.5 * mm, fill=1, stroke=1)

        c.setFillColor(hx(m["ori_color"]))
        c.circle(box_x + 4 * mm, by + h / 2, 2.2 * mm, fill=1, stroke=0)
        c.setFillColor(hx(m["far_color"]))
        c.circle(box_x + box_w / 2, by + h / 2, 2.2 * mm, fill=1, stroke=0)

        c.setStrokeColor(hx("#455A64"))
        c.setLineWidth(1)
        c.line(box_x + 7 * mm, by + h / 2, box_x + box_w / 2 - 3 * mm, by + h / 2)

        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(box_x + 8 * mm, by + h - 4.5 * mm, "ORI: " + m["ori"][:40])
        c.setFillColor(hx("#0D47A1"))
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(box_x + box_w / 2 + 4 * mm, by + h - 4.5 * mm, "→ " + m["far"][:36])
        c.setFillColor(hx("#455A64"))
        c.setFont("Helvetica", 5.5)
        c.drawString(box_x + 8 * mm, by + 2 * mm, m["note"][:70])

    # bottom note
    c.setFillColor(hx("#212121"))
    c.roundRect(8 * mm, 5 * mm, W - 16 * mm, 16 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(12 * mm, 15 * mm, "IMPORTANT")
    c.setFont("Helvetica", 7)
    c.drawString(12 * mm, 10 * mm, "Les couleurs du connecteur ORI sont lues sur tes photos. Confiance high/med/low. Avant de souder : vérifie KEY / accélérateur / frein au multimètre.")
    c.drawString(12 * mm, 6.5 * mm, "Hall moteur = connecteur SÉPARÉ (pas ce blanc/orange). Phases + batterie = bornes à vis, pas ce connecteur.")
    c.showPage()


def page_how_to_splice(c):
    W, H = landscape(A4)
    c.setPageSize(landscape(A4))

    c.setFillColor(hx("#0D47A1"))
    c.rect(0, H - 16 * mm, W, 16 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(10 * mm, H - 7 * mm, "COMMENT BRANCHER ORI → FARDRIVER (ordre + schéma)")
    c.setFont("Helvetica", 8)
    c.drawString(10 * mm, H - 12 * mm, "Coupe / soude / gaine · Batterie DÉBRANCHÉE · 1 fonction à la fois")

    steps = [
        ("1. PUISSANCE", [
            "ORI gros Rouge → FarDriver B+",
            "ORI gros Noir → FarDriver B−",
            "ORI Jaune/Vert/Bleu épais → U / V / W",
            "Mettre fusible 200A sur le +",
        ]),
        ("2. HALL MOTEUR", [
            "Prise Hall moteur (5 fils à part)",
            "→ Photo 3 FarDriver (label HALL)",
            "Rouge→HALL+ · Noir→GND",
            "Jaune/Vert/Bleu → A/B/C",
        ]),
        ("3. CONTACT", [
            "Trouver le fil ORANGE ORI",
            "(connecteur blanc/orange)",
            "→ Photo 2 FarDriver KEY #10",
            "Sans ça = FarDriver éteint",
        ]),
        ("4. ACCÉLÉRATEUR", [
            "3 fils gaz du guidon",
            "→ Photo 8 FarDriver",
            "#28 +5V · #27 signal · #26 GND",
            "Test : 0.8V → 4.5V au gaz",
        ]),
        ("5. FREINS", [
            "Levier frein : test continuité",
            "Si → masse : Photo 9 BL #21+#26",
            "Si → +12V : Photo 5 Gris #11",
            "Doit COUPER le moteur",
        ]),
        ("6. LE RESTE", [
            "Alarme, modes, compteur",
            "Photos FarDriver 1,4,5,6,7",
            "SEULEMENT après 1er essai OK",
            "Roue surélevée pour tester",
        ]),
    ]

    box_w = (W - 20 * mm) / 3 - 3 * mm
    for i, (title, lines) in enumerate(steps):
        col = i % 3
        row = i // 3
        bx = 10 * mm + col * (box_w + 4 * mm)
        by = H - 28 * mm - row * 72 * mm
        c.setFillColor(hx("#FFEBEE") if i < 5 else "#E3F2FD")
        c.setStrokeColor(hx("#C62828") if i < 5 else "#1565C0")
        c.setLineWidth(1.5)
        c.roundRect(bx, by - 62 * mm, box_w, 62 * mm, 2 * mm, fill=1, stroke=1)
        c.setFillColor(hx("#B71C1C") if i < 5 else "#0D47A1")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(bx + 3 * mm, by - 6 * mm, title)
        c.setFillColor(hx("#212121"))
        c.setFont("Helvetica", 7.5)
        ty = by - 14 * mm
        for line in lines:
            c.drawString(bx + 3 * mm, ty, "• " + line)
            ty -= 8 * mm

    c.setFillColor(hx("#212121"))
    c.roundRect(10 * mm, 6 * mm, W - 20 * mm, 18 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(14 * mm, 17 * mm, "MINI TEST APRÈS BRANCHEMENT")
    c.setFont("Helvetica", 7)
    c.drawString(14 * mm, 12 * mm, "1) Roue arrière en l’air  2) Batterie ON  3) Contact ON  4) Frein = moteur bloqué  5) Gaz doux = roue tourne  6) Sinon inverser 2 phases")
    c.drawString(14 * mm, 8 * mm, "Si doute sur un fil du connecteur blanc/orange : multimètre avant de souder. Ne jamais inverser B+ et B−.")
    c.showPage()


def page_photos(c):
    W, H = landscape(A4)
    c.setPageSize(landscape(A4))
    c.setFillColor(hx("#BF360C"))
    c.rect(0, H - 14 * mm, W, 14 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(10 * mm, H - 9 * mm, "TES PHOTOS — CONNECTEUR ORIGINE (référence visuelle)")

    for i, p in enumerate(PHOTOS):
        if not p.exists():
            continue
        im = Image.open(p).convert("RGB")
        im.thumbnail((1100, 900))
        tmp = Path(f"/tmp/ori_ref_{i}.jpg")
        im.save(tmp, quality=75)
        max_w = (W - 30 * mm) / 2
        max_h = H - 40 * mm
        iw, ih = im.size
        sc = min(max_w / iw, max_h / ih)
        dw, dh = iw * sc, ih * sc
        x = 10 * mm + i * (max_w + 10 * mm)
        y = H - 22 * mm - dh
        c.drawImage(ImageReader(str(tmp)), x, y, width=dw, height=dh, preserveAspectRatio=True, mask="auto")
        c.setFillColor(hx("#5D4037"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y - 5 * mm, "Face orange" if i == 0 else "Entrée des fils (dos)")
    c.showPage()


def page_pin_map_detail(c):
    """Big clear table ORI pin -> FarDriver."""
    W, H = landscape(A4)
    c.setPageSize(landscape(A4))
    c.setFillColor(hx("#BF360C"))
    c.rect(0, H - 14 * mm, W, 14 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(10 * mm, H - 9 * mm, "TABLEAU BROCHE PAR BROCHE — ORI → FARDRIVER")

    headers = ["Broche ORI", "Couleur ORI", "Rôle probable", "Brancher sur FarDriver", "Confiance"]
    widths = [28 * mm, 32 * mm, 70 * mm, 85 * mm, 25 * mm]
    x0, y = 10 * mm, H - 22 * mm
    c.setFillColor(hx("#FFCCBC"))
    c.rect(x0, y - 2 * mm, sum(widths), 7 * mm, fill=1, stroke=0)
    c.setFillColor(hx("#BF360C"))
    c.setFont("Helvetica-Bold", 7)
    x = x0 + 1 * mm
    for h, w in zip(headers, widths):
        c.drawString(x, y, h)
        x += w
    y -= 7 * mm

    for i, (col, row, color_name, color_hex, func, target, conf) in enumerate(OEM_PINS):
        if i % 2 == 0:
            c.setFillColor(hx("#FFF3E0"))
            c.rect(x0, y - 1.5 * mm, sum(widths), 6.5 * mm, fill=1, stroke=0)
        c.setFillColor(hx(color_hex))
        c.circle(x0 + 4 * mm, y + 1 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x0 + 8 * mm, y, f"{row}{col}")
        c.setFillColor(hx("#E65100"))
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(x0 + widths[0], y, color_name[:18])
        c.setFillColor(hx("#212121"))
        c.setFont("Helvetica", 6.5)
        c.drawString(x0 + widths[0] + widths[1], y, func[:48])
        c.setFillColor(hx("#0D47A1"))
        c.setFont("Helvetica", 6.5)
        c.drawString(x0 + widths[0] + widths[1] + widths[2], y, target[:52])
        conf_c = {"high": "#2E7D32", "med": "#EF6C00", "low": "#C62828"}[conf]
        c.setFillColor(hx(conf_c))
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(x0 + sum(widths[:4]), y, conf)
        y -= 6.5 * mm

    c.setFillColor(hx("#212121"))
    c.roundRect(10 * mm, 6 * mm, W - 20 * mm, 14 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 7)
    c.drawString(14 * mm, 12 * mm, "Confiance high = couleur claire sur photo · med = probable · low = à confirmer au multimètre avant soudure.")
    c.drawString(14 * mm, 8 * mm, "Numérotation H1…H8 / B1…B8 = rangée Haute/Basse, colonnes 1→8 de gauche à droite sur la FACE ORANGE.")
    c.showPage()


def build():
    c = canvas.Canvas(str(OUT), pagesize=landscape(A3))
    page_overview(c)
    page_how_to_splice(c)
    page_pin_map_detail(c)
    page_photos(c)
    c.save()
    ART.write_bytes(OUT.read_bytes())
    print(f"PDF: {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
