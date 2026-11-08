#!/usr/bin/env python3
"""Guide simple : 1 photo = 1 page. Faisceau FarDriver expliqué clairement."""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

ROOT = Path(__file__).parent
PHOTOS = ROOT / "photos_faisceau_web"
OUT = ROOT / "GUIDE_PHOTO_PAR_PHOTO.pdf"

# Chaque page : fichier, titre, role, fils[(couleur, role)], action, note
PAGES = [
    {
        "file": "01a1bb62-d6b9-712b-bfcd-7e7fd39a54dd.jpg",
        "num": 1,
        "titre": "MODES VITESSE (haute / basse)",
        "quoi": "Sélecteur de vitesse du FarDriver",
        "fils": [
            ("Bleu / Blanc", "Vitesse BASSE (FW2)"),
            ("Jaune / Blanc", "Vitesse HAUTE (FW)"),
            ("Noir", "Masse (GND)"),
            ("Boucle noire", "Cavalier = mode haute par défaut"),
        ],
        "action": "Pas obligatoire pour rouler. Tu peux laisser tel quel.",
        "prio": "OPTION",
        "prio_color": "#546E7A",
    },
    {
        "file": "01a1bb62-d7cd-7099-93e1-b88e9b2e726c.jpg",
        "num": 2,
        "titre": "CONTACT / CLÉ (KEY)",
        "quoi": "Fil qui ALLUME le FarDriver",
        "fils": [
            ("Orange", "KEY = + batterie via la clé / alarme"),
        ],
        "action": "À brancher sur le contact du scooter (ou sortie contact de l’alarme). SANS CE FIL = RIEN NE MARCHE.",
        "prio": "OBLIGATOIRE",
        "prio_color": "#C62828",
    },
    {
        "file": "01a1bb62-d8e5-7ccf-8fe8-c683edaadd24.jpg",
        "num": 3,
        "titre": "HALL MOTEUR",
        "quoi": "Capteurs de position du moteur (label KS-NS-HALL)",
        "fils": [
            ("Rouge", "HALL+ = alim des capteurs"),
            ("Noir", "GND = masse"),
            ("Jaune", "Hall A"),
            ("Vert", "Hall B"),
            ("Bleu", "Hall C"),
        ],
        "action": "Brancher sur le connecteur Hall du MOTEUR (mêmes couleurs).",
        "prio": "OBLIGATOIRE",
        "prio_color": "#C62828",
    },
    {
        "file": "01a1bb62-d9dd-769d-b9f9-ca90edeb854e.jpg",
        "num": 4,
        "titre": "ALARME / ANTIVOL",
        "quoi": "Prises de l’alarme FarDriver (label NS… ligne standard)",
        "fils": [
            ("Orange / Gris / Marron", "Signaux alarme (contact + antivol)"),
            ("Rose / Noir", "Alimentation alarme (+ batterie / masse)"),
            ("Bleu / Violet", "Côté module alarme"),
        ],
        "action": "Déjà câblé pour l’alarme fournie. Si tu gardes l’alarme du scooter, tu peux ignorer ce module.",
        "prio": "OPTION (alarme)",
        "prio_color": "#EF6C00",
    },
    {
        "file": "01a1bb62-db0b-706e-8102-999835e1d010.jpg",
        "num": 5,
        "titre": "FREIN HAUTE + COMPTEUR + DIVERS",
        "quoi": "Plusieurs petits signaux séparés",
        "fils": [
            ("Gris (connecteur blanc)", "Frein HAUTE BH (+12V)"),
            ("Noir + Blanc", "Signal antivol / data"),
            ("Violet (cosse)", "Compteur vitesse SPA"),
            ("Bleu (cosse)", "Pulse vitesse / one-line"),
            ("Marron (nu)", "Boost / alarme"),
        ],
        "action": "Pour démarrer : brancher seulement le GRIS si tes freins sont en +12V. Le reste = plus tard.",
        "prio": "FREIN = utile · reste = option",
        "prio_color": "#EF6C00",
    },
    {
        "file": "01a1bb62-dc1c-7703-a0ed-091d8d93ce51.jpg",
        "num": 6,
        "titre": "PRISE 6 FILS + MASSE CHÂSSIS",
        "quoi": "Connecteur multi-signaux + cosse de masse",
        "fils": [
            ("Rouge / Blanc / Noir", "Alim / data / masse"),
            ("Jaune-Rouge / Vert / Bleu-Blanc", "Signaux annexes (CAN / modes / com)"),
            ("Vert/Jaune + cosse", "Masse châssis OU frein basse"),
        ],
        "action": "Pas besoin pour le 1er essai. La cosse Vert/Jaune peut aller sur une vis du cadre (masse).",
        "prio": "OPTION",
        "prio_color": "#546E7A",
    },
    {
        "file": "01a1bb62-dce4-77b5-8d2a-9d53733d3bb6.jpg",
        "num": 7,
        "titre": "CRUISE / BOOST",
        "quoi": "Fonctions confort (pas la propulsion)",
        "fils": [
            ("Bleu", "Cruise / parking (P)"),
            ("Marron", "Boost / alarme"),
        ],
        "action": "Tu peux laisser débranché. Aucun impact pour démarrer et rouler.",
        "prio": "OPTION",
        "prio_color": "#546E7A",
    },
    {
        "file": "01a1bb62-ddd3-741b-839b-5d435c48b8a3.jpg",
        "num": 8,
        "titre": "ACCÉLÉRATEUR (THROTTLE)",
        "quoi": "Poignée de gaz — 3 fils",
        "fils": [
            ("Rose / Rouge clair", "ACC+ = +5V"),
            ("Vert / Blanc", "SV = signal gaz (0.5 → 4.3V)"),
            ("Noir", "GND = masse"),
        ],
        "action": "Brancher sur la poignée d’accélérateur du scooter (3 fils).",
        "prio": "OBLIGATOIRE",
        "prio_color": "#C62828",
    },
    {
        "file": "01a1bb62-deab-7e6a-8ebf-50ae01813956.jpg",
        "num": 9,
        "titre": "FREIN BASSE + FILS NUS",
        "quoi": "Frein classique (masse) + câble coupé",
        "fils": [
            ("Vert / Jaune (dénudé)", "Frein BASSE BL"),
            ("Noir (dénudé)", "Masse GND frein"),
            ("Rouge + Jaune + Noir (fins)", "Petit câble 3 fils (souvent spare / capteur)"),
        ],
        "action": "Si tes leviers de frein ferment à la masse → brancher Vert/Jaune + Noir sur les freins du scooter.",
        "prio": "OBLIGATOIRE (sécurité)",
        "prio_color": "#C62828",
    },
]


def fit_image(path, max_w, max_h):
    im = Image.open(path)
    w, h = im.size
    scale = min(max_w / w, max_h / h)
    return w * scale, h * scale


def draw_page(c, page, W, H):
    # header
    c.setFillColor(HexColor("#0D47A1"))
    c.rect(0, H - 24 * mm, W, 24 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(12 * mm, H - 10 * mm, f"PHOTO {page['num']} / 9")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(12 * mm, H - 18 * mm, page["titre"])

    # priority badge
    c.setFillColor(HexColor(page["prio_color"]))
    c.roundRect(W - 62 * mm, H - 18 * mm, 50 * mm, 10 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W - 37 * mm, H - 14.5 * mm, page["prio"])

    # photo
    img_path = PHOTOS / page["file"]
    max_w, max_h = W - 24 * mm, 105 * mm
    iw, ih = fit_image(img_path, max_w, max_h)
    ix = (W - iw) / 2
    iy = H - 30 * mm - ih
    c.setStrokeColor(HexColor("#90A4AE"))
    c.setLineWidth(1)
    c.rect(ix - 1 * mm, iy - 1 * mm, iw + 2 * mm, ih + 2 * mm, fill=0, stroke=1)
    c.drawImage(ImageReader(str(img_path)), ix, iy, width=iw, height=ih, preserveAspectRatio=True, mask="auto")

    y = iy - 8 * mm

    # what is it
    c.setFillColor(HexColor("#E3F2FD"))
    c.roundRect(12 * mm, y - 14 * mm, W - 24 * mm, 16 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(HexColor("#0D47A1"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(16 * mm, y - 5 * mm, "C’EST QUOI ?")
    c.setFillColor(HexColor("#212121"))
    c.setFont("Helvetica", 11)
    c.drawString(16 * mm, y - 11 * mm, page["quoi"])
    y -= 22 * mm

    # wires
    c.setFillColor(HexColor("#1565C0"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(12 * mm, y, "CHAQUE FIL :")
    y -= 3 * mm

    for color, role in page["fils"]:
        y -= 9 * mm
        c.setFillColor(HexColor("#FFF8E1"))
        c.roundRect(12 * mm, y - 2 * mm, W - 24 * mm, 9 * mm, 1.5 * mm, fill=1, stroke=0)
        c.setFillColor(HexColor("#E65100"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(16 * mm, y + 1 * mm, color)
        c.setFillColor(HexColor("#212121"))
        c.setFont("Helvetica", 10)
        c.drawString(70 * mm, y + 1 * mm, "→  " + role)

    y -= 14 * mm

    # action
    c.setFillColor(HexColor("#E8F5E9"))
    c.setStrokeColor(HexColor("#2E7D32"))
    c.setLineWidth(1.5)
    box_h = 28 * mm
    c.roundRect(12 * mm, y - box_h, W - 24 * mm, box_h, 2 * mm, fill=1, stroke=1)
    c.setFillColor(HexColor("#1B5E20"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(16 * mm, y - 7 * mm, "QUE FAIRE ?")
    c.setFillColor(HexColor("#212121"))
    c.setFont("Helvetica", 10)
    # wrap action text
    text = page["action"]
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, "Helvetica", 10) < W - 40 * mm:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    ty = y - 14 * mm
    for line in lines[:3]:
        c.drawString(16 * mm, ty, line)
        ty -= 5 * mm

    # footer
    c.setFillColor(HexColor("#78909C"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, 8 * mm, f"Guide FarDriver — Photo {page['num']}/9 — Une photo = une explication")


def draw_sommaire(c, W, H):
    c.setFillColor(HexColor("#0D47A1"))
    c.rect(0, H - 28 * mm, W, 28 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(12 * mm, H - 12 * mm, "TON FAISCEAU FARDRIVER")
    c.setFont("Helvetica", 11)
    c.drawString(12 * mm, H - 20 * mm, "Guide simple · 1 photo = 1 explication · Pas de mélange")

    y = H - 40 * mm
    c.setFillColor(HexColor("#212121"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(12 * mm, y, "Sommaire")
    y -= 8 * mm

    for p in PAGES:
        c.setFillColor(HexColor(p["prio_color"]))
        c.roundRect(12 * mm, y - 2 * mm, 8 * mm, 8 * mm, 1 * mm, fill=1, stroke=0)
        c.setFillColor(HexColor("#212121"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(24 * mm, y, f"Photo {p['num']}")
        c.setFont("Helvetica", 10)
        c.drawString(48 * mm, y, p["titre"])
        c.setFillColor(HexColor("#607D8B"))
        c.setFont("Helvetica", 8)
        c.drawRightString(W - 12 * mm, y, p["prio"])
        y -= 10 * mm

    y -= 6 * mm
    c.setFillColor(HexColor("#C62828"))
    c.roundRect(12 * mm, y - 42 * mm, W - 24 * mm, 44 * mm, 2 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(16 * mm, y - 8 * mm, "POUR ROULER, TU AS BESOIN DE :")
    c.setFont("Helvetica", 10)
    needs = [
        "1. Photo 2 — Contact orange (KEY)",
        "2. Photo 3 — Hall moteur",
        "3. Photo 8 — Accélérateur",
        "4. Photo 9 — Frein (Vert/Jaune + Noir)  OU  Photo 5 Gris",
        "5. + Batterie B+/B− et phases moteur U/V/W (bornes à vis)",
    ]
    ty = y - 16 * mm
    for n in needs:
        c.drawString(16 * mm, ty, n)
        ty -= 5 * mm

    c.setFillColor(HexColor("#78909C"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, 8 * mm, "Le reste (alarme, modes, cruise, compteur) = après le premier essai")


def build():
    W, H = A4
    c = canvas.Canvas(str(OUT), pagesize=A4)
    draw_sommaire(c, W, H)
    c.showPage()
    for page in PAGES:
        draw_page(c, page, W, H)
        c.showPage()
    c.save()
    print(f"PDF créé: {OUT}")


if __name__ == "__main__":
    build()
