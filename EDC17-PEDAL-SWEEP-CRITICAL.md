# ⚠️ EDC17 PEDAL SWEEP — LECTURE LIGNE RPM FIXE (CRITIQUE #6)

## 🎯 Découverte (Facebook Post)

**Source :** https://www.facebook.com/share/r/1MVKdHekmK/?mibextid=wwXIfr

### Phrase clé

> **"2000 rpm, pedal down slowly: 0 → 12 → 40 → 88 → … → 403 Nm. That's how the ECU reads what the driver wants."**

Titre image : **PEDAL DOWN: 403 Nm — At 2000 rpm · Driver's wish map**

## 📐 Principe

Après Short #5 (lecture 2D RPM × pédale), Short #6 = **fixer le régime** et lire **une seule ligne** :

```
RPM fixé (ex. 2000)
Pédale 0 % → 100 % (lentement)
→ Suite de Nm = « ce que le conducteur demande »
```

C'est exactement le parcours ECU en conduite : régime stable, pédale progressive.

## 📊 Sweep @ 2000 rpm (même map que #5)

Colonnes pédale : 0 · 10 · 13 · 20 · 30 · 50 · 70 · 100 %

| Pédale % | Nm @ 2000 rpm | Note |
|---:|---:|---|
| 0 | **0** | dead |
| 10 | **0** | dead |
| 13 | **12** | début tip-in |
| 20 | **40** | soft |
| 30 | **88** | montée |
| 50 | **218** | mid |
| 70 | **381** | presque full |
| 100 | **403** ★ | full wish |

★ Highlight short : **2000 rpm × 100 % → 403 Nm**

Suite citée dans le post : **0 → 12 → 40 → 88 → … → 403 Nm**  
(= cellules 0/10 → 13 → 20 → 30 → … → 100 %, en sautant les 0 dead zone).

## 🔑 Insights Méthodologiques

### 1. La ligne RPM = courbe « sensation pédale »
- Soft bas : 13–30 % → 12–88 Nm (confort)
- Mid : 50 % → 218 Nm
- WOT : 100 % → 403 Nm (à 2000 : 70 % déjà 381, proche)

### 2. Différence vs bas régime (Short #5)
| RPM | @ 70 % | @ 100 % |
|---:|---:|---:|
| 500–1500 | **403** (= full) | **403** |
| **2000** | **381** | **403** |
| 3000 | 331 | 402 |
| 5000 | 250 | 304 |

À **2000 rpm**, 70 % n'est **plus** saturé à 403 — il faut aller vers 100 % pour le max.

### 3. Comment « lire ce que le conducteur veut »
1. Choisir un régime représentatif (ville ~1500, route ~2000, pull ~3000)
2. Lire la ligne de gauche à droite
3. Vérifier progressivité (pas de marche d'escalier brutale)
4. Stage1 : adoucir tip-in, relever mid/WOT **sans casser** la courbe

## 🔄 Comparaison PCR2.1 (Caddy)

| Aspect | PCR2.1 AccPed | EDC17 Driver's wish |
|--------|---------------|---------------------|
| Méthode lecture ligne | identique | **identique** |
| Tip-in soft | blend ORI bas pédale | 0–10 % = 0, puis 12→40→88 |
| WOT cible Stage1 | ~350–360 Nm | stock 403 ; A5 V1.5 plafonds ORI/~400 |
| Check progressivité | oui (V5g tip-in soft) | **même check sur 1 ligne** |

**Transfert :** le protocole Caddy « soft tip-in + WOT cap + roll-off » se valide en lisant **des lignes RPM** comme ce short.

## ⚠️ Erreurs Courantes

### Erreur #1 : Ne regarder que le coin WOT
```
❌ Modifier uniquement 2000×100% = 403
→ Ignorer 13–50 % (sensation ville/route)
```

### Erreur #2 : Marche trop raide tip-in
```
❌ 13% = 12 Nm → 20% = 200 Nm (saut)
→ On/off, plaintes client
✅ Garder montée type 12 → 40 → 88
```

### Erreur #3 : Copier plateau 70%=100% de bas régime partout
```
❌ Forcer 403 @70% aussi à 3000–5000
→ Peut être trop agressif / fumée / EGT
✅ Respecter le roll-off naturel haut régime
```

## ✅ Checklist Sweep Pédale

Pour chaque régime clé (1500 / 2000 / 3000) :

1. [ ] Lire ligne complète 0→100 %
2. [ ] Dead zone 0–10 % = 0 Nm ?
3. [ ] Tip-in progressif (pas de falaise) ?
4. [ ] Mid 50 % cohérent (~200 Nm stock @2000) ?
5. [ ] WOT 100 % = cible Stage1 ?
6. [ ] Comparer 70 % vs 100 % (saturé ou écart ?)

## 🎯 Application A5 Bertin

- Stock ~**403 Nm** wish (aligné 400 Nm fiche projet)
- V1.5 : fill sous 400, plafonds ORI — **ne pas casser** la suite 12→40→88 tip-in
- Logs VILLE : vérifier sensation = sweep 1500–2000 rpm

## 📎 Image Source

`fiche-assets/edc17-short-06-facebook.jpg`

## 🔗 Fichiers Liés

- `EDC17-DRIVERS-WISH-READ-CRITICAL.md` (#5, vue 2D)
- `shorts/06-pedal-sweep-2000rpm.md`
- Shorts #1–#4 (conversions)

---

**⚠️ FIXER LE RPM, BALAYER LA PÉDALE = LIRE LE « DRIVER WISH » RÉEL.**

---

**Dernière mise à jour :** 27 oct 2026 12:38 UTC-3  
**Status :** ✅ Méthodologie lecture ligne RPM
