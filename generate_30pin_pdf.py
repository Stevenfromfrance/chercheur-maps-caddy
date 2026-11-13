#!/usr/bin/env python3
"""PDF pinout exact connecteur 30 broches FarDriver ND72450 / NS24 (Hall V1.5)."""

from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas

OUT = Path(__file__).parent / "FARDRIVER_30PIN_PINOUT.pdf"

# Official Hall first-line 30PIN definition (SiAECOSYS / FarDriver manual V1.5)
# Layout as in manual (3 rows x 10):
# 21..30
# 11..20
#  1..10

PINS = {
    1:  ("HALLA", "Jaune", "#FDD835", "Signal Hall moteur A", "Obligatoire"),
    2:  ("FW2", "Bleu/Blanc", "#81D4FA", "Vitesse basse (masse = actif)", "Option"),
    3:  ("FW", "Jaune/Blanc", "#FFF59D", "Vitesse haute (masse = actif)", "Option"),
    4:  ("HALL+", "Rouge", "#E53935", "Alim Hall moteur (~5–14V)", "Obligatoire"),
    5:  ("CANL", "Brun/Jaune", "#F9A825", "Bus CAN Low", "Option"),
    6:  ("GND", "Noir", "#212121", "Masse (Hall)", "Obligatoire"),
    7:  ("GND", "Noir", "#212121", "Masse (alarme / modes)", "Obligatoire"),
    8:  ("RE", "Brun/Blanc", "#D7CCC8", "Marche arrière (masse = actif)", "Option"),
    9:  ("SPA", "Violet", "#7E57C2", "Sortie compteur vitesse analogique", "Option"),
    10: ("KEY", "Orange", "#FB8C00", "Contact / serrure électrique (+ batterie)", "Obligatoire"),
    11: ("BH", "Gris", "#9E9E9E", "Frein haute (+12V / +batterie)", "Selon frein"),
    12: ("HALLB", "Vert", "#43A047", "Signal Hall moteur B", "Obligatoire"),
    13: ("485A/RXD", "Rouge/Noir", "#C62828", "Série RX / pulse vitesse (SPD)", "Bluetooth / écran"),
    14: ("FD", "Noir/Blanc", "#ECEFF1", "Signal antivol / lock", "Alarme"),
    15: ("CANH", "Rouge/Jaune", "#FFEE58", "Bus CAN High", "Option"),
    16: ("GND", "Noir", "#212121", "Masse (reverse / Bluetooth)", "Obligatoire"),
    17: ("P", "Bleu/Rouge", "#EF9A9A", "Cruise / parking", "Option"),
    18: ("ALARM", "Marron", "#8D6E63", "BOOST / alarme (selon config)", "Option"),
    19: ("W", "Brun/Rouge", "#BF360C", "Phase lock antivol", "Alarme"),
    20: ("KEY", "Orange", "#FB8C00", "2e KEY (sortie alarme → contact)", "Alarme / contact"),
    21: ("BL", "Jaune/Vert", "#AFB42B", "Frein basse (masse = frein)", "Selon frein"),
    22: ("HALLC", "Bleu", "#1E88E5", "Signal Hall moteur C", "Obligatoire"),
    23: ("485B/TXD", "Brun/Bleu", "#5D4037", "Série TX (Bluetooth / PC)", "Bluetooth / écran"),
    24: ("TEMP", "Blanc", "#FAFAFA", "Capteur température moteur", "Option"),
    25: ("—", "—", "#BDBDBD", "Non utilisé", "—"),
    26: ("GND", "Noir", "#212121", "Masse (throttle / frein basse)", "Obligatoire"),
    27: ("SV", "Vert/Blanc", "#A5D6A7", "Signal accélérateur 0.5–4.3V", "Obligatoire"),
    28: ("ACC+", "Rouge/Blanc", "#EF9A9A", "+5V accélérateur", "Obligatoire"),
    29: ("BW5V", "Brun/Vert", "#81C784", "+5V module Bluetooth", "Bluetooth"),
    30: ("60VC", "Rose", "#EC407A", "+ batterie pour alarme (sortie)", "Alarme"),
}

# Breakout connectors from manual
BREAKOUTS = [
    ("Hall moteur (6 fils)", [
        ("4", "Rouge", "HALL+"),
        ("24", "Blanc", "TEMP"),
        ("6", "Noir", "GND"),
        ("22", "Bleu", "HALLC"),
        ("12", "Vert", "HALLB"),
        ("1", "Jaune", "HALLA"),
    ]),
    ("Accélérateur (3 fils)", [
        ("28", "Rouge/Blanc", "ACC+ +5V"),
        ("27", "Vert/Blanc", "SV signal"),
        ("26", "Noir", "GND"),
    ]),
    ("Contact KEY", [
        ("10", "Orange", "KEY contact"),
    ]),
    ("Frein basse", [
        ("21", "Jaune/Vert", "BL"),
        ("26", "Noir", "GND"),
    ]),
    ("Frein haute", [
        ("11", "Gris", "BH"),
    ]),
    ("Alarme signal", [
        ("14", "Noir/Blanc", "FD antivol"),
        ("19", "Brun/Rouge", "W phase lock"),
        ("20", "Orange", "KEY"),
    ]),
    ("Alarme alim", [
        ("30", "Rose", "60VC +"),
        ("7", "Noir", "GND −"),
    ]),
    ("Modes vitesse", [
        ("3", "Jaune/Blanc", "FW haute"),
        ("7", "Noir", "GND"),
        ("2", "Bleu/Blanc", "FW2 basse"),
    ]),
    ("Marche arrière", [
        ("8", "Brun/Blanc", "RE"),
        ("16", "Noir", "GND"),
    ]),
    ("Bluetooth / upgrade", [
        ("29", "Brun/Vert", "BW5V"),
        ("13", "Rouge/Noir", "RXD"),
        ("23", "Brun/Bleu", "TXD"),
        ("16", "Noir", "GND"),
    ]),
]


def draw_header(c, W, H, page):
    c.setFillColor(HexColor("#0D47A1"))
    c.rect(0, H - 22 * mm, W, 22 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(10 * mm, H - 10 * mm, "FARDRIVER ND72450 / NS24 — CONNECTEUR 30 BROCHES")
    c.setFont("Helvetica", 9)
    c.drawString(10 * mm, H - 16 * mm, "Pinout officiel Hall V1.5 · Couleur de chaque fil · Fonction exacte")
    c.drawRightString(W - 10 * mm, H - 10 * mm, f"Page {page}/2")
    c.drawRightString(W - 10 * mm, H - 16 * mm, "WDJ 1500W 72V")


def pin_fill(hex_color):
    try:
        return HexColor(hex_color)
    except Exception:
        return HexColor("#9E9E9E")


def text_on(hex_color):
    # dark text on light colors
    light = {"#FDD835", "#FFF59D", "#FAFAFA", "#ECEFF1", "#FFEE58", "#A5D6A7", "#EF9A9A", "#81D4FA", "#D7CCC8", "#BDBDBD", "#81C784"}
    return black if hex_color.upper() in {c.upper() for c in light} or hex_color.lower() in {c.lower() for c in light} else white


def draw_connector_face(c, x, y, cell_w, cell_h):
    """Draw 3x10 pin grid matching manual orientation."""
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#1565C0"))
    c.drawString(x, y + 8 * mm, "VUE DU CONNECTEUR 30 BROCHES (comme dans le manuel FarDriver)")
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#455A64"))
    c.drawString(x, y + 3.5 * mm, "Rangée du haut = broches 21→30 · milieu 11→20 · bas 1→10")

    rows = [
        list(range(21, 31)),
        list(range(11, 21)),
        list(range(1, 11)),
    ]

    # background plate
    plate_w = 10 * cell_w + 4 * mm
    plate_h = 3 * cell_h + 4 * mm
    c.setFillColor(HexColor("#37474F"))
    c.roundRect(x - 2 * mm, y - plate_h + cell_h + 2 * mm, plate_w, plate_h, 2 * mm, fill=1, stroke=0)

    for r, pins in enumerate(rows):
        for col, pin in enumerate(pins):
            code, color_name, hexc, func, prio = PINS[pin]
            px = x + col * cell_w
            py = y - r * cell_h
            c.setFillColor(pin_fill(hexc))
            c.setStrokeColor(HexColor("#212121"))
            c.setLineWidth(0.6)
            c.roundRect(px, py - cell_h + 1.5 * mm, cell_w - 1.2 * mm, cell_h - 1.8 * mm, 1.2 * mm, fill=1, stroke=1)

            c.setFillColor(text_on(hexc))
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(px + (cell_w - 1.2 * mm) / 2, py - 4.2 * mm, str(pin))
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(px + (cell_w - 1.2 * mm) / 2, py - 7.8 * mm, code)
            c.setFont("Helvetica", 5)
            # truncate color name
            c.drawCentredString(px + (cell_w - 1.2 * mm) / 2, py - 11 * mm, color_name[:11])

    # legend note under grid
    note_y = y - 3 * cell_h - 2 * mm
    c.setFillColor(HexColor("#E65100"))
    c.setFont("Helvetica-Bold", 7)
    c.drawString(x, note_y, "Chaque case = N° broche + CODE + couleur du fil du faisceau FarDriver")
    return note_y - 4 * mm


def draw_full_table(c, x, y, width):
    c.setFillColor(HexColor("#0D47A1"))
    c.roundRect(x, y - 1 * mm, width, 7 * mm, 1.2 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 2 * mm, y + 1 * mm, "TABLE COMPLÈTE DES 30 BROCHES")
    y -= 8 * mm

    # headers
    headers = [("N°", 10 * mm), ("CODE", 24 * mm), ("COULEUR", 28 * mm), ("FONCTION EXACTE", 78 * mm), ("PRIORITÉ", 28 * mm)]
    c.setFillColor(HexColor("#CFD8DC"))
    c.rect(x, y - 1.2 * mm, width, 6 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#263238"))
    c.setFont("Helvetica-Bold", 7)
    hx = x + 2 * mm
    for label, w in headers:
        c.drawString(hx, y, label)
        hx += w
    y -= 6.2 * mm

    # two columns of 15 pins
    col_w = width / 2 - 2 * mm
    left_pins = list(range(1, 16))
    right_pins = list(range(16, 31))

    def draw_pin_rows(pins, ox, oy):
        yy = oy
        for i, pin in enumerate(pins):
            code, color_name, hexc, func, prio = PINS[pin]
            if i % 2 == 0:
                c.setFillColor(HexColor("#ECEFF1"))
                c.rect(ox, yy - 1.2 * mm, col_w, 5.8 * mm, fill=1, stroke=0)
            # color chip
            c.setFillColor(pin_fill(hexc))
            c.setStrokeColor(HexColor("#424242"))
            c.circle(ox + 5 * mm, yy + 1.2 * mm, 2.1 * mm, fill=1, stroke=1)
            c.setFillColor(black)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(ox + 9 * mm, yy, f"{pin}")
            c.setFillColor(HexColor("#0D47A1"))
            c.setFont("Helvetica-Bold", 6.5)
            c.drawString(ox + 16 * mm, yy, code)
            c.setFillColor(HexColor("#37474F"))
            c.setFont("Helvetica", 6.5)
            c.drawString(ox + 40 * mm, yy, color_name)
            c.setFillColor(HexColor("#212121"))
            c.drawString(ox + 68 * mm, yy, func[:42])
            # priority color
            if prio == "Obligatoire":
                c.setFillColor(HexColor("#C62828"))
            elif prio.startswith("Selon") or prio.startswith("Alarme") or "Bluetooth" in prio:
                c.setFillColor(HexColor("#EF6C00"))
            else:
                c.setFillColor(HexColor("#546E7A"))
            c.setFont("Helvetica-Bold", 6)
            c.drawRightString(ox + col_w - 2 * mm, yy, prio)
            yy -= 5.8 * mm
        return yy

    draw_pin_rows(left_pins, x, y)
    draw_pin_rows(right_pins, x + width / 2 + 2 * mm, y)
    return y - 15 * 5.8 * mm - 2 * mm


def draw_breakouts(c, x, y, width):
    c.setFillColor(HexColor("#2E7D32"))
    c.roundRect(x, y - 1 * mm, width, 7 * mm, 1.2 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 2 * mm, y + 1 * mm, "CONNECTEURS DU FAISCEAU (sortie des 30 broches)")
    y -= 10 * mm

    # 5 columns x 2 rows — height fits up to 6 wire lines
    box_w = (width - 8 * mm) / 5
    box_h = 52 * mm
    for i, (title, wires) in enumerate(BREAKOUTS):
        col = i % 5
        row = i // 5
        bx = x + col * (box_w + 2 * mm)
        by = y - row * (box_h + 3 * mm)

        c.setFillColor(HexColor("#E8F5E9") if row == 0 else HexColor("#E3F2FD"))
        c.setStrokeColor(HexColor("#2E7D32") if row == 0 else HexColor("#1565C0"))
        c.setLineWidth(1)
        c.roundRect(bx, by - box_h, box_w, box_h, 1.5 * mm, fill=1, stroke=1)

        c.setFillColor(HexColor("#1B5E20") if row == 0 else HexColor("#0D47A1"))
        c.setFont("Helvetica-Bold", 6.5)
        c.drawString(bx + 1.5 * mm, by - 5 * mm, title[:28])

        ty = by - 10 * mm
        for pin, color, name in wires:
            c.setFillColor(black)
            c.setFont("Helvetica-Bold", 6)
            c.drawString(bx + 1.5 * mm, ty, f"#{pin}")
            c.setFillColor(HexColor("#1565C0"))
            c.setFont("Helvetica", 6)
            c.drawString(bx + 8 * mm, ty, f"{color}")
            c.setFillColor(HexColor("#333333"))
            c.drawString(bx + 1.5 * mm, ty - 3.2 * mm, name)
            ty -= 6.8 * mm

    return y - 2 * (box_h + 3 * mm) - 2 * mm


def draw_howto(c, x, y, width):
    c.setFillColor(HexColor("#BF360C"))
    c.roundRect(x, y - 32 * mm, width, 34 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 3 * mm, y - 5 * mm, "COMMENT LIRE ÇA SUR TON FAISCEAU")
    c.setFont("Helvetica", 7.5)
    lines = [
        "1. Le gros connecteur noir/orange se branche sur ces 30 broches du FarDriver.",
        "2. De l’autre côté du faisceau, les fils sont regroupés en petits connecteurs (Hall, accélérateur, frein, KEY…).",
        "3. Pour identifier un fil : suis sa couleur → trouve le N° de broche dans le tableau → lis la FONCTION.",
        "4. Minimum pour rouler : #1 #4 #6 #10 #12 #21ou11 #22 #26 #27 #28 + bornes B+/B−/U/V/W.",
        "5. Si un fil a 2 couleurs (ex: Vert/Blanc) = fil bicolore rayé. Vérifie toujours au multimètre en cas de doute.",
    ]
    ty = y - 11 * mm
    for line in lines:
        c.drawString(x + 3 * mm, ty, line)
        ty -= 4 * mm


def build():
    W, H = landscape(A4)
    c = canvas.Canvas(str(OUT), pagesize=landscape(A4))

    # PAGE 1 — connector face + full table
    draw_header(c, W, H, 1)
    y = H - 28 * mm
    cell_w = 27.5 * mm
    cell_h = 14 * mm
    y = draw_connector_face(c, 8 * mm, y, cell_w, cell_h)

    # quick priority legend
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(HexColor("#C62828"))
    c.drawString(8 * mm, y, "● Obligatoire")
    c.setFillColor(HexColor("#EF6C00"))
    c.drawString(40 * mm, y, "● Frein / Alarme / BT")
    c.setFillColor(HexColor("#546E7A"))
    c.drawString(85 * mm, y, "● Option")
    y -= 6 * mm

    draw_full_table(c, 8 * mm, y, W - 16 * mm)

    c.setFillColor(HexColor("#546E7A"))
    c.setFont("Helvetica", 6.5)
    c.drawString(8 * mm, 5 * mm, "Source: FarDriver / SiAECOSYS Manual Hall V1.5 §6.1 — 30PIN recommended color definition")
    c.showPage()

    # PAGE 2 — breakouts + howto + electrical notes
    draw_header(c, W, H, 2)
    y = H - 28 * mm
    y = draw_breakouts(c, 8 * mm, y, W - 16 * mm)

    howto_top = y - 1 * mm
    draw_howto(c, 8 * mm, howto_top, W - 16 * mm)

    notes_top = howto_top - 36 * mm
    notes_bottom = 9 * mm
    c.setFillColor(HexColor("#263238"))
    c.roundRect(8 * mm, notes_bottom, W - 16 * mm, notes_top - notes_bottom, 2 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(11 * mm, notes_top - 5 * mm, "RAPPELS ÉLECTRIQUES (manuel FarDriver)")
    c.setFont("Helvetica", 7.5)
    notes = [
        "• HALL+ : ~14V à vide / ~8V sous charge — ne pas confondre avec ACC+ (+5.1V accélérateur)",
        "• Accélérateur SV : 0.5V → 4.3V (réglable 1.1V → 3.9V dans l’app)",
        "• KEY (orange #10 / #20) : + batterie pour allumer le contrôleur — SANS CE FIL RIEN NE MARCHE",
        "• Frein BL (#21) : actif à la masse · Frein BH (#11) : actif au +12V/+batterie — brancher le bon type",
        "• Modes FW/FW2 et reverse RE : actifs en reliant le fil à GND",
        "• 60VC (#30 rose) : sortie +batterie pour alimenter l’alarme — ne pas court-circuiter à la masse",
        "• Bornes puissance séparées (pas dans les 30 broches) : B+ rouge, B− noir, U jaune, V vert, W bleu",
    ]
    ty = notes_top - 11 * mm
    for n in notes:
        c.drawString(11 * mm, ty, n)
        ty -= 3.8 * mm

    c.setFillColor(HexColor("#546E7A"))
    c.setFont("Helvetica", 6.5)
    c.drawString(8 * mm, 4 * mm, "À imprimer et garder avec le scooter · Vérifier les couleurs au multimètre si le faisceau a été modifié")
    c.save()
    print(f"PDF créé: {OUT}")


if __name__ == "__main__":
    build()
