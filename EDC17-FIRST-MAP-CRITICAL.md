# ⚠️ EDC17 FIRST MAP — DRIVER'S WISH (CRITIQUE #7)

## 🎯 Découverte (Facebook Post)

**Source :** https://www.facebook.com/share/r/1JDZ4dqzvv/?mibextid=wwXIfr

### Phrase clé

> **"The first map of the whole system: Driver's wish. It turns your pedal position into a torque demand. RPM on one axis, pedal on the other."**

Titre image : **THE FIRST MAP OF THE SYSTEM — Driver's wish • from pedal to torque**

## 📐 Rôle dans la Chaîne Couple

```
Pédale conducteur
       ↓
┌─────────────────────┐
│  DRIVER'S WISH      │  ← PREMIÈRE map du système
│  RPM × % pédale     │
│  → Nm demandés      │
└─────────────────────┘
       ↓
  Limiteurs (tqlim, smoke, rail, EGT…)
       ↓
  Injection / turbo / couple réel
```

**Sans Driver's wish correctement lu/modifié, toute la suite (smoke, rail, IQ…) est hors sujet.**

## 🔑 Ce que la Map Fait

| Entrée | Sortie |
|---|---|
| Axe Y = **RPM** | — |
| Axe X = **% pédale** | — |
| Cellules = **Nm** | **Torque demand** (wish) |

- **Ne produit pas** le couple mécanique directement
- **Demande** un couple → les autres maps **autorisent / limitent / convertissent**

## 📊 Caractéristiques Stock (même map #5/#6)

- Dead zone **0–10 %** → 0 Nm
- Tip-in soft dès **13 %**
- Plateau **403 Nm** bas régime (dès 70 % @500–1500)
- Roll-off haut régime @100 % : 403 → ~304 @5000

→ Détail lecture : Shorts #5 et #6  
→ Conversions axes/valeurs : Shorts #1–#4

## 🔗 Chaîne Complète (ordre logique EDC17)

| Ordre | Map / couche | Rôle |
|---:|---|---|
| **1** | **Driver's wish** | Pédale → Nm demandés |
| 2 | Torque limiters | Plafond wish |
| 3 | Smoke / IQ | Limite fumée / carburant |
| 4 | Rail / durée inj | Pression / temps injection |
| 5 | Turbo / VGT | Air pour soutenir le wish |
| 6 | Pollution (DPF/EGR) | Contraintes / deletes |

**Règle Stage1 :** wish ≤ tqlim ≤ smoke (comme Caddy : wish 360 < tqlim 370 ≤ smoke 375).

## 🔄 Comparaison PCR2.1 (Caddy)

| Aspect | PCR2.1 | EDC17 |
|--------|--------|-------|
| Première map | **AccPed** (mêmes banques) | **Driver's wish** |
| Fonction | pédale → Nm | **identique** |
| Place dans méthode | retouchée V1/V5g en premier levier | **« first map of the system »** |
| Nom A2L | AccPed banques | Driver's wish / driver's demand |

**Transfert :** AccPed Caddy = Driver's wish EDC17. Même place dans la philo Stage1.

## ⚠️ Erreurs Courantes

### Erreur #1 : Commencer par smoke/rail
```
❌ Monter smoke/rail avant de fixer le wish
→ Couple demandé trop bas → gain invisible
✅ D'abord Driver's wish (puis limiteurs)
```

### Erreur #2 : Confondre wish et couple réel
```
❌ "J'ai mis 450 Nm dans Driver's wish = 450 Nm roue"
→ Wish ≠ couple transmis (tqlim, smoke, boîte, grip…)
```

### Erreur #3 : Ignorer les conversions
```
Sans #1–#4 la « first map » est illisible
```

## ✅ Checklist Avant Stage1 EDC17

1. [ ] Identifier Driver's wish (première map)
2. [ ] Appliquer conversions #1–#3
3. [ ] Lire 2D (#5) + sweep lignes (#6)
4. [ ] Noter max wish stock (ici **403 Nm**)
5. [ ] Définir cible Stage1 ≤ tqlim ≤ smoke
6. [ ] Soft tip-in, plateau WOT, roll-off haut régime

## 🎯 Application A5 Bertin

- Stock ~**400 Nm** / wish exemple **403 Nm** → cohérent
- V1.5 : fill sous 400, plafonds ORI — wish reste le point de départ
- 0AW : pas de launch ; wish + limiteurs suffisent pour Stage1 conservateur

## 📎 Image Source

`fiche-assets/edc17-short-07-facebook.jpg`

## 🔗 Fichiers Liés

- Shorts #1–#6
- `shorts/07-first-map-drivers-wish.md`
- `METHODOLOGIE-EDC17-RECAP.md`
- PCR2.1 : AccPed dans `FICHE-CHANGEMENTS-ORI-V1.md` / `FICHE-V5G-360.md`

---

**⚠️ DRIVER'S WISH = PREMIÈRE MAP. PÉDALE → TORQUE DEMAND. TOUT LE RESTE SUIT.**

---

**Dernière mise à jour :** 27 oct 2026 12:40 UTC-3  
**Status :** ✅ Fondement chaîne couple
