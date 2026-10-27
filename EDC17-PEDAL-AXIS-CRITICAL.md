# ⚠️ EDC17 PEDAL AXIS — INFORMATION CRITIQUE #2

## 🎯 Découverte (Facebook Post)

**Source :** https://www.facebook.com/share/r/1HqguUpZe5/?mibextid=wwXIfr

### L'Axe Pédale EDC17

> **"On this pedal axis, 8192 means 100 %. Double-click it, press the % button — and the whole axis is in percent."**

## 📐 Conversion Pédale

**EDC17 stocke la position pédale en valeur brute 0-8192**

| Valeur Brute | % Pédale | Conversion |
|---|---|---|
| 8192 | 100% | /8192 ×100 |
| 4096 | 50% | /8192 ×100 |
| 2048 | 25% | /8192 ×100 |
| 819 | 10% | /8192 ×100 |
| 0 | 0% | - |

## 🔧 WinOLS : Conversion Automatique

### Méthode Rapide
1. ✅ Double-clic sur **l'axe pédale** (axe X typiquement)
2. ✅ Cliquer bouton **%** (pourcentage)
3. ✅ L'axe entier converti automatiquement en %

### Résultat
```
Avant : 0, 819, 2048, 4096, 6144, 7168, 8192
Après : 0%, 10%, 25%, 50%, 75%, 87.5%, 100%
```

## 📊 Maps Concernées

Toutes les maps EDC17 avec **axe position pédale** :

### AccPed (Accelerator Pedal) — Principal
- **AccPed banques** (8 banques typiquement)
  - Adresses : 0x1CF9C0, 0x1CFAC0, 0x1CFBC0, 0x1CFCC0...
  - Axe X (pédale) : 0-8192 → **convertir en %**
  - Axe Y (RPM) : ×2 → **factor 0.5** (voir Short #1)

### Autres Maps avec Pédale
- Torque request pedal maps
- Driver wish torque
- Electronic throttle maps (si applicable)
- Launch control pedal threshold (si applicable)

## ⚠️ Différence vs PCR2.1

| Aspect | PCR2.1 (Caddy) | EDC17 (A5) |
|--------|----------------|------------|
| **Pédale storage** | 0-100% (direct) | **0-8192 (raw)** |
| **Conversion WinOLS** | Aucune (déjà %) | **Double-clic + %** |
| **100% pédale** | 100 | **8192** |
| **WOT (plein gaz)** | ≥85% (~85) | **≥6963** (avant conv) |

## 🎯 Exemple Pratique : AccPed WOT

### Identifier WOT (Wide Open Throttle)

**Avant conversion :**
```
Axe pédale (raw) : 80, 328, 819, 1885, 4096, 6144, 6963, 8183
Quelle cellule = WOT ?
→ Dernières 2-3 cellules (≥6963 = ≥85%)
```

**Après conversion % :**
```
Axe pédale (%) : 0.98%, 4.00%, 10.00%, 23.02%, 50.00%, 75.00%, 85.00%, 99.90%
Quelle cellule = WOT ?
→ Dernières 2-3 cellules (≥85%)
```

### Modifier AccPed WOT

**Sans conversion % :**
```
❌ "Je modifie cellule 4096 (milieu tableau)"
→ C'est 50% pédale, pas WOT !
→ Erreur de ciblage
```

**Avec conversion % :**
```
✅ "Je modifie cellules ≥85% (6963-8192 raw)"
→ C'est bien WOT
→ Modification correcte
```

## 📋 Workflow AccPed EDC17 Complet

### 1. Localiser AccPed Bank
```
WinOLS → Search → Pattern 8×16 grilles
Adresses typiques : 0x1CF9C0, 0x1CFAC0...
```

### 2. Convertir Axe Pédale
```
Double-clic axe X (pédale)
→ Bouton %
→ Axe en 0-100%
```

### 3. Convertir Axe RPM
```
Axe Y (RPM) : valeurs >6000
→ Factor 0.5 (voir Short #1)
→ Axe en valeurs réelles (0-5500 rpm)
```

### 4. Identifier Zones
```
Tip-in  : 0-23% pédale (soft, confort)
Partiels: 23-75% pédale (charge normale)
WOT     : ≥85% pédale (plein gaz, performance)
```

### 5. Modifier Selon Stratégie
```
Tip-in  : Garder ORI ou softener (confort)
Partiels: Blend progressif ORI → Stage1
WOT     : Cap conservateur (350 Nm A5 0AW)
Hardcut : Ligne ≥4800 rpm → 0 Nm
```

## 🔍 Vérification Rapide

Après conversion, vérifier cohérence :

- [ ] **Axe pédale** : 0-100% (pas 0-8192)
- [ ] **Axe RPM** : 0-5500 rpm (pas 0-11000)
- [ ] **Tip-in** : 0-23% identifié clairement
- [ ] **WOT** : ≥85% identifié clairement
- [ ] **Valeurs Nm** : 0-400 Nm plausibles

Si axe pédale encore 0-8192 → **conversion % non appliquée**.

## ❌ Erreurs Courantes

### Erreur #1 : Modifier mauvaise zone pédale
```
Sans conversion % :
"Je veux Stage1 WOT, je modifie cellule 4096"
→ 4096 = 50% pédale (partiels, pas WOT !)
→ Stage1 appliqué au mauvais endroit
```

### Erreur #2 : Comparer A5 vs Caddy sans conversion
```
Caddy : AccPed axe 0, 4, 10, 23, 50, 75, 85, 100%
A5    : AccPed axe 80, 328, 819, 1885, 4096, 6144, 6963, 8183

"Les axes sont différents, incomparable ?"
→ Non ! Convertir A5 en % → axes identiques
```

### Erreur #3 : Oublier axe RPM factor 0.5
```
✅ Axe pédale converti en %
❌ Axe RPM encore ×2
→ Pédale OK mais RPM faux (voir Short #1)
```

### Erreur #4 : Cap WOT sur tip-in
```
Sans conversion % :
"Je cap toute la map à 350 Nm"
→ Tip-in 0-23% aussi cappé (inconfort)

Avec conversion % :
"Je cap seulement cellules ≥50% à 350 Nm"
→ Tip-in préservé, WOT cappé (correct)
```

## 🎓 Relation avec Short #1 (RPM ×2)

**EDC17 a DEUX conversions critiques :**

1. **Short #1 : RPM ×2** → factor 0.5 (axes régime)
2. **Short #2 : Pédale 8192** → bouton % (axes pédale)

**Les deux s'appliquent souvent à la même map (AccPed) :**
- Axe X (pédale) : **0-8192 → 0-100%** (ce short)
- Axe Y (RPM) : **×2 → ×1** (short #1)

**Sans ces deux conversions :**
- ❌ Impossible de lire correctement les maps AccPed
- ❌ Risque modifier mauvaises cellules
- ❌ Comparaison PCR2.1 vs EDC17 impossible

## 📐 Formule Conversion Manuelle

Si besoin de convertir manuellement (sans WinOLS) :

```
% pédale = (valeur_raw / 8192) × 100

Exemples :
8192 / 8192 × 100 = 100.00%
6963 / 8192 × 100 = 85.00%
4096 / 8192 × 100 = 50.00%
819  / 8192 × 100 = 10.00%
```

**Inverse (% → raw) :**
```
valeur_raw = (% / 100) × 8192

Exemples :
100% : (100/100) × 8192 = 8192
85%  : (85/100) × 8192 = 6963
50%  : (50/100) × 8192 = 4096
10%  : (10/100) × 8192 = 819
```

## 🔗 Source

**Facebook post :** https://www.facebook.com/share/r/1HqguUpZe5/?mibextid=wwXIfr

**Image :** https://scontent-atl3-1.xx.fbcdn.net/v/t15.5256-10/869832139_1445973910843485_6568671457941467589_n.jpg

**Full course :** Mentionné dans posts précédents (lien à récupérer)

## 📊 Tableau Récapitulatif EDC17 vs PCR2.1

| Map | Axe | PCR2.1 | EDC17 (raw) | EDC17 (converti) | Action WinOLS |
|---|---|---|---|---|---|
| AccPed | Pédale (X) | 0-100% | 0-8192 | 0-100% | Double-clic + % |
| AccPed | RPM (Y) | 0-5500 rpm | 0-11000 | 0-5500 rpm | Factor 0.5 |
| Smoke | RPM | 0-5500 rpm | 0-11000 | 0-5500 rpm | Factor 0.5 |
| Rail | RPM | 0-5500 rpm | 0-11000 | 0-5500 rpm | Factor 0.5 |
| Torque lim | RPM | 0-5500 rpm | 0-11000 | 0-5500 rpm | Factor 0.5 |

**Règle simple EDC17 :**
- Axe RPM (>6000) → **factor 0.5**
- Axe pédale (>100) → **bouton %**
- Autres axes → vérifier A2L

## 📎 Fichiers Liés

- `EDC17-RPM-FACTOR-CRITICAL.md` (short #1)
- `map-finder/ecu/edc17cp14/516657/shorts/01-rpm-factor-x2.md`
- `map-finder/ecu/edc17cp14/516657/shorts/02-pedal-axis-8192.md` (à créer)
- `METHODOLOGIE-EDC17-RECAP.md`

## ✅ TODO

- [ ] Créer `shorts/02-pedal-axis-8192.md` (ce short)
- [ ] Auditer `build_v1.py` : conversion pédale appliquée ?
- [ ] Vérifier AccPed banques A5 : axes en % ou raw ?
- [ ] Mettre à jour README A5 : mention axe pédale
- [ ] Ajouter exemple AccPed complet (avant/après)

---

**⚠️ TOUJOURS CONVERTIR AXES PÉDALE EDC17 EN % !**

Sans cela, **impossible d'identifier WOT vs tip-in** → modifications au mauvais endroit.

---

**Dernière mise à jour :** 27 oct 2026 12:28 UTC-3  
**Auteur :** Cloud Agent Cursor (via Facebook post recovery)  
**Status :** ✅ Information critique #2
