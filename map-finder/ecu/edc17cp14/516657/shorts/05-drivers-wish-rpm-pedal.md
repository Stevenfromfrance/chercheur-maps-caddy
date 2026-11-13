# Short #5 : Driver's Wish — Lire RPM + Pédale

**Durée :** ~45 sec | **ECU :** EDC17CP14 | **Prérequis :** Shorts #1–#4

## 🎯 Objectif

Lire correctement AccPed / Driver's wish : **chaque cellule = RPM × % pédale → Nm**.

## 🔍 Phrase Clé

> **Full torque demand doesn't always need 100 % pedal.**  
> From **500–1500 rpm**, full **403 Nm** already at **70 % pedal**.

## 📐 Lecture

| Axe | Après conversion | Short |
|---|---|---|
| Y = RPM | 500–5000 | #1 |
| X = pédale | 0–100 % | #2 |
| Cells = couple | Nm (×0.1) | #3 |

Highlight : **1500 rpm × 70 % → 403 Nm** (= déjà full, comme 100 %).

## 🔑 Zones Typiques (exemple stock)

| Zone | Pédale | Comportement |
|---|---|---|
| Dead | 0–10 % | **0 Nm** |
| Tip-in | 13–30 % | soft 5–120 Nm |
| Mid | 50 % | ~150–260 Nm |
| **Saturé bas** | **≥70 % @500–1500** | **403 Nm** (= WOT) |
| Haut régime | 100 % | roll-off 403→304 @5000 |

## ⚠️ Erreurs Courantes

- ❌ Stage1 seulement colonne 100 % (ignorer saturation à 70 %)
- ❌ Cap tip-in (0–30 %) comme WOT
- ❌ Lire une seule ligne RPM sans croiser pédale

## ✅ Vérification Rapide

- [ ] Conversions #1+#2+#3 OK
- [ ] Plateau 70 % = 100 % en bas régime ?
- [ ] Tip-in 0–10 % = 0 Nm ?
- [ ] Roll-off haut régime visible ?

## 🔗 vs PCR2.1

Même logique croisée RPM×pédale.  
Différence : EDC17 exemple sature dès **70 %** bas régime ; Caddy WOT souvent **≥85 %**.

## 🔗 Source

https://www.facebook.com/share/r/14tgFQF5D9C/?mibextid=wwXIfr

**Image :** `../../../../../fiche-assets/edc17-short-05-facebook.jpg`

**Détail :** `../../../../../EDC17-DRIVERS-WISH-READ-CRITICAL.md`

---

**⚠️ TOUJOURS CROISER RPM + PÉDALE. FULL ≠ TOUJOURS 100 %.**
