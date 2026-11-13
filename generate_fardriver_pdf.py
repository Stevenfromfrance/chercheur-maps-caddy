#!/usr/bin/env python3
"""Generate FarDriver ND72450 harness color PDF diagram."""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pathlib import Path

OUT = Path(__file__).parent / "FAISCEAU_FARDRIVER_ND72450.pdf"

# Wire groups: (title, items[(color_hex, label, function, note)])
GROUPS = [
    (
        "1. PUISSANCE (bornes à vis)",
        [
            ("#E53935", "ROUGE", "B+", "Batterie +72V (via fusible 200A)"),
            ("#212121", "NOIR", "B−", "Batterie masse / GND"),
            ("#FDD835", "JAUNE", "U", "Phase moteur U"),
            ("#43A047", "VERT", "V", "Phase moteur V"),
            ("#1E88E5", "BLEU", "W", "Phase moteur W"),
        ],
    ),
    (
        "2. CAPTEURS HALL MOTEUR (label NS霍尔 / HALL)",
        [
            ("#E53935", "ROUGE", "HALL+", "Alimentation Hall (~5–12V)"),
            ("#212121", "NOIR", "GND", "Masse Hall"),
            ("#FDD835", "JAUNE", "HALL A", "Signal Hall A"),
            ("#43A047", "VERT", "HALL B", "Signal Hall B"),
            ("#1E88E5", "BLEU", "HALL C", "Signal Hall C"),
            ("#FAFAFA", "BLANC", "TEMP", "Température moteur (optionnel)"),
        ],
    ),
    (
        "3. ACCÉLÉRATEUR / THROTTLE (connecteur 3 broches)",
        [
            ("#EF9A9A", "ROUGE/BLANC", "ACC+", "+5V accélérateur"),
            ("#212121", "NOIR", "GND", "Masse accélérateur"),
            ("#A5D6A7", "VERT/BLANC", "SV", "Signal 0.8V → 4.5V"),
        ],
    ),
    (
        "4. CONTACT / SERRURE ÉLECTRIQUE",
        [
            ("#FB8C00", "ORANGE", "KEY", "Contact ON = + batterie (obligatoire)"),
        ],
    ),
    (
        "5. FREINS",
        [
            ("#AFB42B", "JAUNE/VERT", "BL", "Frein basse (masse) — leviers classiques"),
            ("#9E9E9E", "GRIS", "BH", "Frein haute (+12V) — si frein envoie du +"),
            ("#212121", "NOIR", "GND", "Masse frein basse"),
        ],
    ),
    (
        "6. ALARME / ANTIVOL",
        [
            ("#EC407A", "ROSE / ROSE-ROUGE", "60VC", "Alim + alarme (depuis contrôleur)"),
            ("#212121", "NOIR", "GND", "Masse alarme"),
            ("#FB8C00", "ORANGE", "KEY", "Sortie contact alarme → KEY"),
            ("#8D6E63", "MARRON", "ALARM / U", "Signal antivol / phase lock"),
            ("#FAFAFA", "BLANC / BLANC-NOIR", "FW / FD", "Signal antivol / lock"),
            ("#5E35B1", "VIOLET / ROSE / BLEU", "Divers", "Start distant / klaxon / lock"),
        ],
    ),
    (
        "7. OPTIONS (pas obligatoires pour rouler)",
        [
            ("#7E57C2", "VIOLET", "SPA", "Sortie compteur vitesse analogique"),
            ("#FFF59D", "JAUNE/BLANC", "FW / SDH", "Vitesse haute / mode"),
            ("#81D4FA", "BLEU/BLANC", "FW2 / SDL", "Vitesse basse / mode"),
            ("#D7CCC8", "MARRON/BLANC", "RE", "Marche arrière"),
            ("#EF9A9A", "BLEU/ROUGE", "P / XH", "Cruise / parking"),
            ("#A1887F", "MARRON", "BOOST / One-Lin", "Boost ou compteur one-line"),
            ("#C62828", "ROUGE/NOIR", "485A / RXD", "Com série / écran"),
            ("#5D4037", "MARRON/BLEU", "485B / TXD", "Com série / écran"),
            ("#FFEE58", "ROUGE/JAUNE", "CAN H", "Bus CAN (option)"),
            ("#F9A825", "BRUN/JAUNE", "CAN L", "Bus CAN (option)"),
            ("#81C784", "BRUN/VERT", "BW5V", "+5V module Bluetooth"),
        ],
    ),
]


def draw_header(c, W, H):
    c.setFillColor(HexColor("#0D47A1"))
    c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(12 * mm, H - 12 * mm, "FAISCEAU FARDRIVER ND72450 / NS24")
    c.setFont("Helvetica", 10)
    c.drawString(12 * mm, H - 19 * mm, "72V · 200A / 450A · Couleurs des câbles et fonctions")
    c.setFont("Helvetica", 8)
    c.drawRightString(W - 12 * mm, H - 12 * mm, "WDJ 1500W 72V")
    c.drawRightString(W - 12 * mm, H - 19 * mm, "Réf. DN72450_14_A_HA86")


def draw_wire_row(c, x, y, color_hex, color_name, code, function, col_w):
    # color swatch
    try:
        col = HexColor(color_hex)
    except Exception:
        col = HexColor("#888888")
    c.setFillColor(col)
    c.setStrokeColor(HexColor("#333333"))
    c.roundRect(x, y - 1.2 * mm, 8 * mm, 5.5 * mm, 1.2 * mm, fill=1, stroke=1)

    # stripe hint for dual colors (draw thin white/black line)
    if "/" in color_name:
        c.setStrokeColor(white if color_hex.lower() not in ("#fafafa", "#fff59d") else HexColor("#333333"))
        c.setLineWidth(1.2)
        c.line(x + 1 * mm, y + 1.5 * mm, x + 7 * mm, y + 1.5 * mm)
        c.setLineWidth(1)

    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 10 * mm, y + 0.5 * mm, color_name)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#0D47A1"))
    c.drawString(x + col_w[0], y + 0.5 * mm, code)
    c.setFillColor(HexColor("#222222"))
    c.setFont("Helvetica", 8)
    c.drawString(x + col_w[1], y + 0.5 * mm, function)


def draw_group(c, x, y, title, items, width):
    # group header bar
    c.setFillColor(HexColor("#1565C0"))
    c.roundRect(x, y - 1 * mm, width, 7 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 3 * mm, y + 1 * mm, title)
    y -= 8 * mm

    # column headers
    c.setFillColor(HexColor("#ECEFF1"))
    c.rect(x, y - 1.5 * mm, width, 6 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#455A64"))
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x + 3 * mm, y, "COULEUR")
    c.drawString(x + 45 * mm, y, "CODE")
    c.drawString(x + 75 * mm, y, "FONCTION")
    y -= 7 * mm

    col_w = (45 * mm, 75 * mm)
    for i, (hexc, name, code, func) in enumerate(items):
        if i % 2 == 0:
            c.setFillColor(HexColor("#F5F7FA"))
            c.rect(x, y - 1.5 * mm, width, 6.5 * mm, fill=1, stroke=0)
        draw_wire_row(c, x + 2 * mm, y, hexc, name, code, func, col_w)
        y -= 6.8 * mm

    return y - 3 * mm


def draw_legend_box(c, x, y, w, h):
    c.setStrokeColor(HexColor("#FF6F00"))
    c.setFillColor(HexColor("#FFF8E1"))
    c.setLineWidth(1.5)
    c.roundRect(x, y - h, w, h, 3 * mm, fill=1, stroke=1)
    c.setFillColor(HexColor("#E65100"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 3 * mm, y - 6 * mm, "MINIMUM POUR ROULER")
    c.setFillColor(HexColor("#333333"))
    c.setFont("Helvetica", 8)
    lines = [
        "1. Batterie B+ / B−  (+ fusible 200A)",
        "2. Phases moteur U / V / W",
        "3. Hall moteur (R N J V B)",
        "4. Contact ORANGE (KEY)",
        "5. Accélérateur 3 fils",
        "6. Au moins 1 frein",
        "",
        "Le reste = options (alarme, modes,",
        "compteur, Bluetooth…)",
    ]
    ty = y - 12 * mm
    for line in lines:
        c.drawString(x + 3 * mm, ty, line)
        ty -= 4.2 * mm


def draw_controller_sketch(c, x, y):
    """Simple FarDriver box with terminals."""
    c.setFillColor(HexColor("#263238"))
    c.roundRect(x, y - 42 * mm, 70 * mm, 42 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#90A4AE"))
    c.rect(x, y - 42 * mm, 70 * mm, 8 * mm, fill=1, stroke=0)  # heatsink look
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + 35 * mm, y - 6 * mm, "FARDRIVER NS24")
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + 35 * mm, y - 10 * mm, "ND72450 · 72V")

    # terminals
    terms = [
        ("#E53935", "B+"),
        ("#212121", "B−"),
        ("#FDD835", "U"),
        ("#43A047", "V"),
        ("#1E88E5", "W"),
    ]
    tx = x + 6 * mm
    for hexc, lab in terms:
        c.setFillColor(HexColor(hexc))
        c.circle(tx, y - 22 * mm, 3.2 * mm, fill=1, stroke=0)
        c.setFillColor(white if hexc != "#FDD835" else black)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(tx, y - 23.5 * mm, lab)
        tx += 12 * mm

    # 30-pin connector hint
    c.setFillColor(HexColor("#FF9800"))
    c.roundRect(x + 12 * mm, y - 36 * mm, 46 * mm, 7 * mm, 1 * mm, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(x + 35 * mm, y - 33.5 * mm, "Connecteur 30 broches (faisceau)")


def build():
    W, H = landscape(A4)
    c = canvas.Canvas(str(OUT), pagesize=landscape(A4))

    # ========== PAGE 1 ==========
    draw_header(c, W, H)
    y = H - 34 * mm
    left_w = 115 * mm
    right_x = 128 * mm
    right_w = W - right_x - 10 * mm

    # left column groups 1-4
    for group in GROUPS[:4]:
        y = draw_group(c, 10 * mm, y, group[0], group[1], left_w)

    # right side: controller sketch + legend + freins
    draw_controller_sketch(c, right_x + 10 * mm, H - 38 * mm)
    draw_legend_box(c, right_x, H - 88 * mm, right_w, 48 * mm)

    y2 = H - 142 * mm
    for group in GROUPS[4:6]:
        y2 = draw_group(c, right_x, y2, group[0], group[1], right_w)

    c.setFillColor(HexColor("#546E7A"))
    c.setFont("Helvetica", 7)
    c.drawString(10 * mm, 6 * mm, "Page 1/2 · FarDriver ND72450 — Schéma couleurs faisceau · À imprimer et garder près du scooter")
    c.showPage()

    # ========== PAGE 2 ==========
    draw_header(c, W, H)
    y = H - 34 * mm
    y = draw_group(c, 10 * mm, y, GROUPS[6][0], GROUPS[6][1], W - 20 * mm)

    # Mapping table scooter -> fardriver
    y -= 2 * mm
    c.setFillColor(HexColor("#2E7D32"))
    c.roundRect(10 * mm, y - 1 * mm, W - 20 * mm, 7 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(13 * mm, y + 1 * mm, "8. BRANCHEMENT SCOOTER → FARDRIVER (résumé)")
    y -= 10 * mm

    rows = [
        ("Gros ROUGE batterie", "B+ rouge", "Alim +72V"),
        ("Gros NOIR batterie", "B− noir", "Masse"),
        ("Gros JAUNE moteur", "U jaune", "Phase"),
        ("Gros VERT moteur", "V vert", "Phase"),
        ("Gros BLEU moteur", "W bleu", "Phase"),
        ("Hall R/N/J/V/B moteur", "Hall R/N/J/V/B", "Capteurs position"),
        ("Fil contact / clé", "ORANGE KEY", "Allumage contrôleur"),
        ("Accélérateur 3 fils", "R/blanc + N + V/blanc", "Gaz"),
        ("Levier frein", "JAUNE/VERT (BL) ou GRIS (BH)", "Coupe moteur"),
        ("Alarme (option)", "Module rose/orange/noir", "Antivol / start"),
    ]

    # header
    c.setFillColor(HexColor("#E8F5E9"))
    c.rect(10 * mm, y - 1.5 * mm, W - 20 * mm, 6.5 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#1B5E20"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(12 * mm, y, "CÔTÉ SCOOTER")
    c.drawString(95 * mm, y, "CÔTÉ FARDRIVER")
    c.drawString(175 * mm, y, "RÔLE")
    y -= 7 * mm

    for i, (scoot, far, role) in enumerate(rows):
        if i % 2 == 0:
            c.setFillColor(HexColor("#F1F8E9"))
            c.rect(10 * mm, y - 1.5 * mm, W - 20 * mm, 6.5 * mm, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica", 8)
        c.drawString(12 * mm, y, scoot)
        c.setFillColor(HexColor("#0D47A1"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(95 * mm, y, far)
        c.setFillColor(HexColor("#333333"))
        c.setFont("Helvetica", 8)
        c.drawString(175 * mm, y, role)
        y -= 6.8 * mm

    # warnings
    y -= 4 * mm
    c.setFillColor(HexColor("#B71C1C"))
    c.roundRect(10 * mm, y - 28 * mm, W - 20 * mm, 30 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(14 * mm, y - 5 * mm, "⚠ SÉCURITÉ")
    c.setFont("Helvetica", 8)
    warns = [
        "• Batterie DÉBRANCHÉE pendant tout le câblage",
        "• Ne jamais inverser B+ et B− (grille le FarDriver)",
        "• Tester les freins AVANT de rouler (doivent couper le moteur)",
        "• Premier essai = roue arrière SURÉLEVÉE",
        "• Fusible 200A obligatoire sur le +72V",
    ]
    ty = y - 11 * mm
    for wline in warns:
        c.drawString(14 * mm, ty, wline)
        ty -= 3.8 * mm

    c.setFillColor(HexColor("#546E7A"))
    c.setFont("Helvetica", 7)
    c.drawString(
        10 * mm,
        6 * mm,
        "Page 2/2 · Sources: manuel FarDriver ND72450 / NS24 · Couleurs standard faisceau (vérifier au multimètre si doute)",
    )
    c.save()
    print(f"PDF créé: {OUT}")


if __name__ == "__main__":
    build()
