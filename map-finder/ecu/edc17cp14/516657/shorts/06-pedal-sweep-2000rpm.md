# Short #6 : Pedal Sweep @ 2000 rpm

**Durée :** ~30 sec | **ECU :** EDC17CP14 | **Prérequis :** Shorts #1–#5

## 🎯 Objectif

Lire **une ligne RPM fixe** en balayant la pédale 0→100 % — c'est ainsi que l'ECU interprète la demande conducteur.

## 🔍 Phrase Clé

> **2000 rpm, pedal down slowly:**  
> **0 → 12 → 40 → 88 → … → 403 Nm**  
> That's how the ECU reads what the driver wants.

## 📊 Sweep @ 2000 rpm

| Pédale % | Nm |
|---:|---:|
| 0–10 | **0** |
| 13 | **12** |
| 20 | **40** |
| 30 | **88** |
| 50 | **218** |
| 70 | **381** |
| 100 | **403** ★ |

★ Highlight : **2000 × 100 % → 403 Nm**

## 🔑 vs Short #5

| | Short #5 | Short #6 |
|---|---|---|
| Vue | grille 2D | **1 ligne RPM** |
| Focus | saturation 70 % bas régime | **courbe sensation pédale** |
| @2000 / 70 % | — | **381** (plus saturé à 403) |

## ⚠️ Erreurs Courantes

- ❌ Ne toucher que la case WOT 100 %
- ❌ Tip-in en falaise (12 → 200 d'un coup)
- ❌ Forcer 70 %=100 % à tous les régimes

## ✅ Vérification Rapide

Choisir 1500 / 2000 / 3000 rpm → lire chaque ligne 0→100 % :
- [ ] Dead 0–10 % = 0
- [ ] Tip-in progressif
- [ ] WOT = cible Stage1

## 🔗 vs PCR2.1

Même check « soft tip-in + WOT cap » en lisant des **lignes AccPed** régime par régime.

## 🔗 Source

https://www.facebook.com/share/r/1MVKdHekmK/?mibextid=wwXIfr

**Image :** `../../../../../fiche-assets/edc17-short-06-facebook.jpg`  
**Détail :** `../../../../../EDC17-PEDAL-SWEEP-CRITICAL.md`

---

**⚠️ FIXER RPM → BALAYER PÉDALE = LIRE LE DRIVER WISH.**
