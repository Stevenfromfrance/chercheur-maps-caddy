"""
Échelle fiable pour un scan HP en A4 (éventuellement croppé).

Méthode Onshape que tu utilisais
--------------------------------
1. Scan A4 entier (idéalement 300 DPI).
2. Tu crop la zone utile.
3. Tu importes le crop dans Onshape comme image de référence.
4. Tu donnes au crop sa **largeur / hauteur réelle en mm**, calculée
   comme une fraction de la feuille A4 :

   A4 = 210 mm (large) × 297 mm (haut)

   Si le scan complet faisait Aw × Ah pixels, et que ton crop fait
   Cw × Ch pixels (même résolution, sans redimensionner) :

       largeur_mm = 210 * (Cw / Aw)
       hauteur_mm = 297 * (Ch / Ah)

Astuce plus simple si le fichier garde le DPI (HP le met souvent)
-----------------------------------------------------------------
   mm = pixels * 25.4 / DPI

   Exemple 300 DPI : 1 px = 0.08467 mm
   → un trou de 30 px fait 30 * 0.08467 ≈ 2,54 mm

Usage
-----
  python scan_scale.py chemin/image.png
  python scan_scale.py chemin/crop.png --a4-full 2480x3508
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

A4_W_MM = 210.0
A4_H_MM = 297.0
# A4 @ 300 DPI (standard HP)
A4_300_PX = (2480, 3508)


def dpi_of(img: Image.Image) -> float | None:
    dpi = img.info.get("dpi")
    if not dpi:
        return None
    if isinstance(dpi, tuple):
        return float(dpi[0])
    return float(dpi)


def scale_from_dpi(px_w: int, px_h: int, dpi: float) -> tuple[float, float, float]:
    mpp = 25.4 / dpi
    return mpp, px_w * mpp, px_h * mpp


def scale_from_a4_fraction(
    crop_w: int, crop_h: int, full_w: int, full_h: int
) -> tuple[float, float]:
    """Retourne (largeur_mm, hauteur_mm) du crop."""
    return A4_W_MM * crop_w / full_w, A4_H_MM * crop_h / full_h


def main():
    p = argparse.ArgumentParser(description="Calcule l'échelle mm d'un scan/crop A4")
    p.add_argument("image", type=Path)
    p.add_argument(
        "--a4-full",
        default=None,
        help="Taille px du A4 complet avant crop, ex: 2480x3508 (300 DPI). "
        "Si omis, on utilise le DPI du fichier s'il existe.",
    )
    p.add_argument(
        "--part-bbox",
        default=None,
        help="Bbox de la pièce en px dans l'image: x0,y0,x1,y1 (optionnel)",
    )
    args = p.parse_args()

    img = Image.open(args.image)
    w, h = img.size
    dpi = dpi_of(img)
    print(f"Image : {args.image}")
    print(f"Pixels : {w} × {h}")
    print(f"DPI métadonnée : {dpi}")

    if args.a4_full:
        fw, fh = map(int, args.a4_full.lower().split("x"))
        mm_w, mm_h = scale_from_a4_fraction(w, h, fw, fh)
        print(f"\nMéthode fraction A4 (plein page {fw}×{fh} px) :")
        print(f"  Crop = {mm_w:.3f} × {mm_h:.3f} mm")
        print(f"  mm/px = ({mm_w/w:.6f}, {mm_h/h:.6f})")
        mpp = mm_w / w
    elif dpi:
        mpp, mm_w, mm_h = scale_from_dpi(w, h, dpi)
        print(f"\nMéthode DPI ({dpi:.1f}) :")
        print(f"  Crop = {mm_w:.3f} × {mm_h:.3f} mm")
        print(f"  mm/px = {mpp:.6f}")
    else:
        print(
            "\nPas de DPI ni de --a4-full. Relance avec par ex. :\n"
            "  python scan_scale.py crop.png --a4-full 2480x3508"
        )
        return

    if args.part_bbox:
        x0, y0, x1, y1 = map(int, args.part_bbox.split(","))
        pw, ph = x1 - x0, y1 - y0
        print(f"\nPièce bbox {pw}×{ph} px → {pw*mpp:.3f} × {ph*mpp:.3f} mm")

    print(
        "\nDans Onshape : importe l'image et règle sa largeur à "
        f"{mm_w:.3f} mm (hauteur {mm_h:.3f} mm)."
    )
    print(
        "Ensuite tu traces par-dessus : toutes les cotes seront justes."
    )


if __name__ == "__main__":
    main()
