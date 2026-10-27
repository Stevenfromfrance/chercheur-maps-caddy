# Checklist WinOLS — Revue V1.5 (avant flash)

À faire en atelier (~30–45 min). Factors obligatoires shorts #1–#3.

## 0. Ouvrir
- [ ] `ORI_FLS.fls` + V1.5 côte à côte (ou projet + compare)
- [ ] Import A2L similar 0005 si besoin noms
- [ ] Checksum : fichier reste **noCHK** jusqu’à calc final

## 1. Factors (chaque map Nm / RPM / pédale)
- [ ] Axes RPM → factor **0.5**
- [ ] Axes pédale → bouton **%** (8192=100%)
- [ ] Valeurs couple → factor **0.1**, precision **1**, unit Nm

## 2. Chaîne wish ≤ lim ≤ smoke
Noter max affichés (Nm ou équivalent) :

| Couche | Map | max ORI | max V1.5 |
|---|---|---:|---:|
| Wish / TQ req | Torque Request Standard | | |
| Wish gears | Gear 1 … Gear 5 | | |
| Limiteur | Limiter of Maximum Torque | | |
| Smoke | Higher Lambda (noter marge) | | |

- [ ] V1.5 wish max ≲ 400 Nm (stock A5)
- [ ] Limiteur ≥ wish (pas de coupe silencieuse)
- [ ] Smoke / lambda laisse de la marge

## 3. Gear TQ — priorité 0AW (P1 audit)
Pour **Gear 1** et **Gear 2** :
- [ ] Sweep pédale @ 1500 et 2000 rpm (short #6)
- [ ] Max Nm ≤ stock WOT (~400)
- [ ] Pas de falaise tip-in
- [ ] Si trop agressif → noter cellules pour V1.6 soft

## 4. Pulse
- [ ] Injection Time `1D1496` : ~+1.7 %, aucune cellule > +3 %
- [ ] SOI ~+5 % cohérent
- [ ] IQ #2/#3/#4 = ORI ; IQ #1 ~+2 %

## 5. Air
- [ ] Turbo Pressure ~+4 % **et** Limiter Turbo ~+4 % (les deux)
- [ ] VGT : laisser ORI sauf lag logs plus tard
- [ ] Rail ~+3 %

## 6. Deletes
- [ ] DaVinci DPF/EGR/FLAPS présent (ne pas recopier adresses YT 505999)
- [ ] Pas de TVA / lambda DaVinci full si hors scope V1.5

## 7. Avant flash
- [ ] G83 / coolant OK
- [ ] EGT / FAP physiques OK
- [ ] KESS OBD read IDs 516657 + 2 Mo
- [ ] **Checksum CHK** WinOLS/KESS
- [ ] Plan logs : VILLE, ROUTE_INJ, ROUTE_TURBO, ROUTE_RAIL, HARCUT

---

Réf : `AUDIT-V15-VS-NOUVELLE-METHODO.md`
