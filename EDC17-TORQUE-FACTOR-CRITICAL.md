# ⚠️ EDC17 TORQUE FACTOR 0.1 — INFORMATION CRITIQUE #3

## 🎯 Découverte (Facebook Post)

**Source :** https://www.facebook.com/share/r/19EQXUuYcA/?mibextid=wwXIfr

### Pourquoi le couple a factor 0.1

> **"WHY TORQUE HAS FACTOR 0.1 — One extra digit of precision • WinOLS"**

## 📐 Conversion Couple (Nm)

**EDC17 stocke le couple en dixièmes de Nm.**

| Valeur EPROM (raw) | ×0.1 | Valeur Réelle |
|---|---|---|
| 153 | → | **15.3 Nm** |
| 547 | → | **54.7 Nm** |
| 1188 | → | **118.8 Nm** |
| 4000 | → | **400.0 Nm** |
| 3500 | → | **350.0 Nm** |

**Formule WinOLS :**
```
Value = 0.1 × Eprom + 0
Unit  = Nm
Precision = 1
```

## 🔧 Configuration WinOLS

### Properties of "Driver's wish" (exemple)

| Champ | Valeur |
|---|---|
| **Name** | Driver's wish |
| **Unit** | Nm |
| **Data organization** | 16 Bit (LoHi) |
| **Factor** | **0.1** |
| **Offset** | 0 |
| **Precision** | **1** |
| **Formula** | `Value = 0.1 * Eprom + 0` |

### Pourquoi Precision = 1 ?

Avec factor 0.1 + precision 1 :
- Affiche **15.3 Nm** (1 décimale)
- Sans factor 0.1 → seulement **15 Nm** (perd 0.3 Nm)
- **Un chiffre de précision en plus** vs factor 1.0

## 📊 Maps Concernées

Toutes les maps EDC17 en **Nm** (couple) :

### Principales
- **Driver's wish** (AccPed / wish torque) — exemple du short
- Torque limiters (`tqlim_base`, `tqlim_tegt`, `tqlim_speed`…)
- Torque request / internal torque
- Clutch / gear protection torque
- Hardcut torque (ligne → 0.0 Nm)

### Attention : PAS toutes les maps
| Map type | Factor typique | Unit |
|---|---|---|
| Couple (wish, tqlim) | **0.1** | Nm |
| Smoke / IQ | dépend A2L | mg/stroke |
| Rail | dépend A2L | bar |
| RPM (axe) | **0.5** | rpm |
| Pédale (axe) | **%** (8192=100%) | % |

## ⚠️ Différence vs PCR2.1

| Aspect | PCR2.1 (Caddy) | EDC17 (A5) |
|--------|----------------|------------|
| **Couple factor** | souvent `0.03125` + offset `-1024` | **0.1** (simple) |
| **Précision** | ~0.03 Nm | **0.1 Nm** |
| **Formule** | `raw×0.03125 − 1024` | `raw × 0.1` |
| **Exemple 400 Nm** | raw dépend offset | raw **4000** |

**Ne pas copier le factor PCR2.1 sur EDC17 !**

## 🎯 Exemple Pratique : Cap WOT 350 Nm

### Avec factor 0.1 correct
```
Objectif : 350.0 Nm
→ Écrire raw = 3500 dans EPROM
→ WinOLS affiche 350.0 Nm
```

### Sans factor (factor 1.0)
```
❌ Lire 3500 → croire "3500 Nm" (faux)
❌ Écrire 350 → réel 35.0 Nm (moteur mort)
```

### Avec factor PCR2.1 par erreur
```
❌ Appliquer 0.03125 −1024 sur EDC17
→ Valeurs Nm totalement fausses
```

## 🔗 Triple Conversion AccPed EDC17

**AccPed / Driver's wish nécessite MAINTENANT 3 conversions :**

| # | Élément | Conversion | Short |
|---|---|---|---|
| 1 | Axe RPM | ×2 → factor **0.5** | Short #1 |
| 2 | Axe pédale | 8192 → **%** | Short #2 |
| 3 | **Valeurs couple** | ×10 → factor **0.1** | **Short #3** |

### Avant (brut illisible)
```
Axe X : 0, 819, 1065, 1638, 2458, 4096, 6963, 8192
Axe Y : 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 8000, 10000
Cells : 153, 547, 1188, 2500, 3500, 4000...
```

### Après les 3 conversions
```
Axe X : 0%, 10%, 13%, 20%, 30%, 50%, 85%, 100%     ← Short #2
Axe Y : 500, 750, 1000, 1250, 1500, 2000, 2500, 3000, 4000, 5000 rpm  ← Short #1
Cells : 15.3, 54.7, 118.8, 250.0, 350.0, 400.0 Nm  ← Short #3
```

**Note image source :** l'axe RPM est déjà converti (500–5000), l'axe pédale encore raw (0, 819…), les cellules affichées avec factor 0.1.

## ❌ Erreurs Courantes

### Erreur #1 : Factor 1.0 (oubli)
```
Cap "350" avec factor 1.0
→ Stocke 350 raw = 35.0 Nm réel
→ Perte massive de couple
```

### Erreur #2 : Copier factor PCR2.1
```
Appliquer 0.03125 −1024 sur Driver's wish EDC17
→ Nm absurdes
```

### Erreur #3 : Precision 0
```
Factor 0.1 + Precision 0
→ Affiche 15 Nm au lieu de 15.3 Nm
→ Perd le chiffre décimal (intérêt du factor 0.1)
```

### Erreur #4 : Modifier raw sans savoir
```
Voir 4000 dans hex → "trop haut, je mets 350"
→ Réel 35 Nm si factor 0.1
```

## ✅ Vérification Rapide

Après factor 0.1 + precision 1 :

- [ ] Idle / tip-in bas : **~10–50 Nm** (pas 100–500)
- [ ] WOT stock A5 2.7 TDI : **~380–400 Nm** (pas 3800–4000)
- [ ] Cap Stage1 0AW : **~350–400 Nm** affichés
- [ ] Hardcut : **0.0 Nm** (pas 0)
- [ ] Unit = **Nm**, Precision = **1**

Si valeurs à 4 chiffres (ex. 3500) encore affichées comme couple → **factor non appliqué**.

## 📋 Checklist Properties WinOLS

Pour chaque map couple EDC17 :

1. [ ] Data organization : **16 Bit LoHi**
2. [ ] Unit : **Nm**
3. [ ] Factor : **0.1**
4. [ ] Offset : **0**
5. [ ] Precision : **1**
6. [ ] Axe RPM : factor **0.5** (Short #1)
7. [ ] Axe pédale : **%** si présent (Short #2)

## 📎 Image Source

Capture sauvegardée : `fiche-assets/edc17-short-03-facebook.jpg`

## 🔗 Fichiers Liés

- `EDC17-RPM-FACTOR-CRITICAL.md` (critique #1)
- `EDC17-PEDAL-AXIS-CRITICAL.md` (critique #2)
- `map-finder/ecu/edc17cp14/516657/shorts/03-torque-factor-01.md`
- `METHODOLOGIE-EDC17-RECAP.md`

---

**⚠️ TOUJOURS FACTOR 0.1 + PRECISION 1 SUR LES MAPS COUPLE EDC17 !**

Sans cela : lecture fausse (×10) ou écriture dangereuse (÷10).

---

**Dernière mise à jour :** 27 oct 2026 12:32 UTC-3  
**Auteur :** Cloud Agent Cursor (via Facebook post recovery)  
**Status :** ✅ Information critique #3
