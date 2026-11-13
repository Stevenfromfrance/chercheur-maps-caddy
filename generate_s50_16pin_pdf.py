#!/usr/bin/env python3
"""PDF clair : prise 16 broches S50 — à quoi sert chaque fil."""

from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).parent
OUT = ROOT / "S50_16PIN_FONCTIONS.pdf"
ART = Path("/opt/cursor/artifacts/S50_16PIN_FONCTIONS.pdf")
PHOTO = Path(
    "/home/ubuntu/.cursor/projects/agent-repos-chercheur-maps-caddy/assets/"
    "01a1bb84-345f-78fc-a2aa-8dd39eb80fa6.jpg"
)

FUNCS = [
    ("Orange", "#FB8C00", "CONTACT (KEY)", "+72V clé ON → allume le contrôleur", "FarDriver KEY #10", True),
    ("Rouge fin", "#E53935", "ACCÉLÉRATEUR +5V", "Alimente la poignée", "FarDriver ACC+ #28", True),
    ("Vert / Blanc", "#43A047", "ACCÉLÉRATEUR SIGNAL", "0.8V → 4.5V en tournant", "FarDriver SV #27", True),
    ("Noir", "#212121", "ACCÉLÉRATEUR MASSE", "Masse poignée / signaux", "FarDriver GND #26", True),
    ("Violet", "#8E24AA", "FREIN HAUTE", "Étiquette : High Level → +12V au frein", "FarDriver BH #11", True),
    ("Jaune / J-Vert", "#F9A825", "FREIN BASSE / E-ABS", "Si présent : masse au frein", "FarDriver BL #21", False),
    ("Rose / Gris", "#EC407A", "3 VITESSES", "2 fils → masse = haute / basse", "FW #3 / FW2 #2", False),
    ("Blanc / Brun", "#ECEFF1", "MARCHE ARRIÈRE", "Masse = reverse", "FarDriver RE #8", False),
    ("Bleu / Jaune", "#1E88E5", "COMPTEUR VITESSE", "Impulsion vers afficheur", "SPA #9 (option)", False),
]

NOT_HERE = [
    "Batterie + / − → gros Rouge / gros Noir (bornes)",
    "Phases moteur → gros Jaune / Vert / Bleu (bornes)",
    "Hall moteur → prise à part (souvent 10 pin ou 5 fils moteur)",
    "Alarme → ta prise 8 broches",
]


def page_cover(c, W, H):
    c.setFillColor(HexColor("#0D1B2A"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#FF6D00"))
    c.setFont("Helvetica-Bold", 28)
    c.drawString(20 * mm, H - 25 * mm, "S50 — Prise 16 broches")
    c.setFillColor(white)
    c.setFont("Helvetica", 14)
    c.drawString(20 * mm, H - 35 * mm, "TB-72/60-HS35 · TC-ZY-01 · 72V / 50A · Frein High Level")
    c.setFont("Helvetica", 11)
    c.drawString(
        20 * mm,
        H - 45 * mm,
        "Uniquement la 16 pin (la 8 pin = alarme). Voici à quoi sert chaque type de fil.",
    )

    # photo
    if PHOTO.exists():
        img = ImageReader(str(PHOTO))
        c.drawImage(img, 20 * mm, 25 * mm, width=110 * mm, height=82 * mm, preserveAspectRatio=True, mask="auto")
        c.setFillColor(HexColor("#90CAF9"))
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, 18 * mm, "Ta prise 16 pin (face orange) — photo scooter")

    # legend boxes
    x0, y0 = 140 * mm, H - 60 * mm
    for i, (col, hexc, title, role, far, must) in enumerate(FUNCS):
        y = y0 - i * 14 * mm
        c.setFillColor(HexColor(hexc))
        c.roundRect(x0, y, 8 * mm, 8 * mm, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        tag = "OBLIGATOIRE" if must else "option"
        c.drawString(x0 + 11 * mm, y + 4.5 * mm, f"{title}  [{tag}]")
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#B0BEC5"))
        c.drawString(x0 + 11 * mm, y + 0.5 * mm, f"{col} · {role}")


def page_table(c, W, H):
    c.setFillColor(HexColor("#F5F7FA"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#0D1B2A"))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(15 * mm, H - 18 * mm, "Tableau fil → fonction → FarDriver")

    headers = ["Couleur typique", "Fonction", "Ce que ça fait", "Branche FarDriver"]
    widths = [40 * mm, 45 * mm, 95 * mm, 70 * mm]
    x = 15 * mm
    y = H - 30 * mm
    c.setFillColor(HexColor("#1565C0"))
    c.rect(x, y - 2 * mm, sum(widths), 10 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    cx = x + 2 * mm
    for h, w in zip(headers, widths):
        c.drawString(cx, y + 1 * mm, h)
        cx += w

    y -= 12 * mm
    c.setFont("Helvetica", 8)
    for i, (col, hexc, title, role, far, must) in enumerate(FUNCS):
        bg = HexColor("#FFFFFF") if i % 2 == 0 else HexColor("#E3F2FD")
        if must:
            bg = HexColor("#FFF3E0") if i % 2 == 0 else HexColor("#FFE0B2")
        c.setFillColor(bg)
        c.rect(x, y - 3 * mm, sum(widths), 11 * mm, fill=1, stroke=0)
        c.setFillColor(HexColor(hexc))
        c.circle(x + 5 * mm, y + 2 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(black)
        vals = [col, title, role, far]
        cx = x + 2 * mm
        for j, (v, w) in enumerate(zip(vals, widths)):
            if j == 0:
                c.drawString(cx + 8 * mm, y, v)
            else:
                c.drawString(cx, y, v)
            cx += w
        y -= 12 * mm

    c.setFillColor(HexColor("#B71C1C"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(15 * mm, 35 * mm, "PAS dans la 16 pin :")
    c.setFillColor(HexColor("#37474F"))
    c.setFont("Helvetica", 10)
    for i, line in enumerate(NOT_HERE):
        c.drawString(15 * mm, 28 * mm - i * 6 * mm, "• " + line)


def page_tests(c, W, H):
    c.setFillColor(HexColor("#0D1B2A"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(HexColor("#FF6D00"))
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, H - 25 * mm, "Tests multimètre — zéro erreur")
    c.setFillColor(white)
    c.setFont("Helvetica", 12)
    c.drawString(20 * mm, H - 35 * mm, "Batterie ON · contact ON · noir du multi sur B− (gros noir)")

    steps = [
        ("~72V", "Fil CONTACT / KEY → FarDriver orange #10"),
        ("~5V stable", "Alim accélérateur → ACC+ #28"),
        ("1V → 4.5V en tournant", "Signal gaz → SV #27"),
        ("0 Ω vers B−", "Masse → GND #26"),
        ("~12V au frein", "Frein HAUTE (étiquette) → BH gris #11"),
        ("Continuité masse au frein", "Frein basse (si présent) → BL #21"),
        ("Continuité selon levier 3 vitesses", "Modes → FW / FW2"),
        ("Continuité bouton reverse", "Marche arrière → RE #8"),
    ]
    y = H - 55 * mm
    for a, b in steps:
        c.setFillColor(HexColor("#FF6D00"))
        c.roundRect(20 * mm, y - 2 * mm, 55 * mm, 10 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(22 * mm, y + 1.5 * mm, a)
        c.setFont("Helvetica", 11)
        c.drawString(80 * mm, y + 1.5 * mm, b)
        y -= 16 * mm

    c.setFillColor(HexColor("#69F0AE"))
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, 22 * mm, "Minimum pour rouler depuis la 16 pin : KEY + gaz 3 fils + frein violet (BH)")
    c.setFillColor(HexColor("#B0BEC5"))
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, 14 * mm, "Hall + batterie + phases = hors 16 pin. Alarme = 8 pin.")


def main():
    W, H = landscape(A4)
    c = canvas.Canvas(str(OUT), pagesize=landscape(A4))
    page_cover(c, W, H)
    c.showPage()
    page_table(c, W, H)
    c.showPage()
    page_tests(c, W, H)
    c.save()
    ART.parent.mkdir(parents=True, exist_ok=True)
    ART.write_bytes(OUT.read_bytes())
    print("Wrote", OUT, "and", ART)


if __name__ == "__main__":
    main()
