# MÉTHODOLOGIE EDC17CP14 — Récapitulatif et Comparaison

## ⚠️ INFORMATIONS CRITIQUES EDC17

### 🔴 Critique #1 : RPM ×2 Factor

**EDC17 stocke RPM ×2 !**

- L'axe WinOLS affiche 10,000 → valeur réelle moteur = **5000 rpm**
- **Facteur WinOLS obligatoire : 0.5**
- Hardcut 4800 rpm → saisir **9600** dans WinOLS
- Launch 2700 rpm → saisir **5400** dans WinOLS
- **Tous les axes RPM** de toutes les maps sont doublés

📄 **Détail :** `EDC17-RPM-FACTOR-CRITICAL.md` | **Short :** `shorts/01-rpm-factor-x2.md`

### 🔴 Critique #2 : Pédale 8192 = 100%

**EDC17 stocke pédale en valeur brute 0-8192 !**

- L'axe pédale affiche 8192 → valeur réelle = **100%**
- **Conversion WinOLS : double-clic axe + bouton %**
- Sans conversion : impossible d'identifier tip-in (0-23%) vs WOT (≥85%)
- S'applique à **toutes les maps** avec axe pédale (AccPed, torque request...)

📄 **Détail :** `EDC17-PEDAL-AXIS-CRITICAL.md` | **Short :** `shorts/02-pedal-axis-8192.md`

### 🔴 Critique #3 : Couple Factor 0.1

**EDC17 stocke le couple en dixièmes de Nm !**

- Raw 153 → **15.3 Nm** (factor **0.1**, precision **1**)
- Formule : `Value = 0.1 × Eprom + 0`
- Objectif : **un chiffre de précision** de plus vs factor 1.0
- Driver's wish, tqlim, hardcut… — **pas** le factor PCR2.1 (0.03125−1024)

📄 **Détail :** `EDC17-TORQUE-FACTOR-CRITICAL.md` | **Short :** `shorts/03-torque-factor-01.md`

**AccPed EDC17 = 3 conversions :** RPM ×0.5 + pédale % + couple ×0.1

### 🔴 Critique #4 : Vue RAW (synthèse)

**L'ECU ne stocke pas des Nm — uniquement des entiers bruts.**

- Exemple post FB : **8192 = 100 % pédale**, **4032 = 403.2 Nm**
- Axe RPM raw 10000 = **5000 rpm** (×2)
- Preuve visuelle des 3 conversions sur une seule map Driver's wish

📄 **Détail :** `EDC17-RAW-STORAGE-CRITICAL.md` | **Short :** `shorts/04-raw-storage-before-conversion.md`

### 🔴 Critique #5 : Lecture Driver's Wish (RPM + pédale)

**Full torque ≠ toujours 100 % pédale.**

- Exemple : **500–1500 rpm** → déjà **403 Nm** dès **70 %** pédale
- Toujours croiser **RPM × % pédale** (jamais une seule colonne)
- Tip-in : 0–10 % = 0 Nm ; roll-off haut régime sur 70 % et 100 %
- **vs Caddy :** même logique croisée ; seuil WOT Caddy souvent ≥85 %, ici saturation dès 70 % bas régime

📄 **Détail :** `EDC17-DRIVERS-WISH-READ-CRITICAL.md` | **Short :** `shorts/05-drivers-wish-rpm-pedal.md`

### 🔴 Critique #6 : Pedal Sweep (ligne RPM fixe)

**Fixer le régime, balayer la pédale = lire le driver wish.**

- Exemple @ **2000 rpm** : **0 → 12 → 40 → 88 → … → 403 Nm**
- C'est la courbe « sensation » tip-in → mid → WOT
- À 2000 rpm, 70 % = 381 Nm (plus saturé comme @500–1500)
- **vs Caddy :** même check progressivité ligne par ligne AccPed

📄 **Détail :** `EDC17-PEDAL-SWEEP-CRITICAL.md` | **Short :** `shorts/06-pedal-sweep-2000rpm.md`

### 🔴 Critique #7 : First Map = Driver's Wish

**Première map du système entier.**

- Transforme **% pédale × RPM → Nm demandés**
- Wish ≠ couple roue : les limiteurs / smoke / rail suivent
- **vs Caddy :** AccPed = même rôle (premier levier Stage1)
- Ordre : wish → tqlim → smoke → rail/inj → turbo → deletes

📄 **Détail :** `EDC17-FIRST-MAP-CRITICAL.md` | **Short :** `shorts/07-first-map-drivers-wish.md`

### 🔴 Critiques #8–#10 : WinOLS Hex Basics

**Socle hexdump (démo BMW EDC17 390655, applicable A5).**

| # | Règle |
|---|---|
| 8 | Adresses **toujours hex** |
| 9 | Lignes 16 octets : début `…0`, fin `…F` (start from zero) |
| 10 | Colonne **gauche** = adresse |

📄 **Détail :** `EDC17-WINOLS-HEX-BASICS.md` | **Shorts :** `08` · `09` · `10`

### 🔴 Lesson 21 — Guide Tuning Complet (EDC16 & EDC17)

**Source Facebook screenshots** → `EDC17-LESSON21-TUNING-GUIDE.md` + shorts **#11–#17**

Chaîne : Wish → Translation → **Limiters** → Fuel (µs/°) → Air (mbar/VGT)  
Playbook : turbo +4–8 % · InjTime +1–13 % · EGR=0 · limp raise · λ 1.2–1.3 · 14.55:1  
EDC16≈EDC17 (même math, fichier plus gros)

**Scorecard A5 V1.5 :** InjTime +1.7 % ✅ · EGR off ✅ · turbo ~+6 % ✅ · limp/0AW ⏳ prudence

### 🔴 YouTube EDC17CP14 — DPF / EGR / Hot Start / Idle

**https://youtu.be/dKaJ-WJMwcc** (Dragiša Trimunović) — démo Audi A6 SW **505999**

- Switches DPF `1EE34A` 0100→0000 + EGR + **Hot start** `1F84FA` + Idle FIX  
- **≠ adresses A5 516657** — logique OK, offsets non  
- A5 : deletes déjà via **DaVinci** ; **trou** = Hot Start / Idle si hard start post-flash  

📄 `EDC17-YOUTUBE-DPF-EGR-HOTSTART.md` | Short `#18`

---

## 📋 Contexte

Ce document récapitule la méthodologie appliquée au calculateur **EDC17CP14** (Audi A5 Sportback CGKA) et la compare avec les méthodologies utilisées pour le **PCR2.1** (Caddy) déjà documentées dans ce repository.

**Projet :** Client Bertin — Audi A5 Sportback 2.7 TDI (190 ch / 400 Nm)  
**ECU :** Bosch EDC17CP14 TC1796  
**Software :** 8K1907401K ver 0008 / Bosch 516657  
**Objectif :** Stage 1 conservateur + DPF/EGR/FLAPS off

---

## 🔍 Méthodologie Actuelle EDC17CP14

### 1. Architecture de Fichiers

```
map-finder/ecu/edc17cp14/516657/
├── ORI_FLS.fls                    # Flash origine (2 Mo)
├── BACKUP_MICRO.mpc                # Sauvegarde IROM TC1796
├── BACKUP_EEPROM.epr               # EEPROM 128 ko
├── identity.json                   # IDs + offsets
├── README.md                       # Documentation projet
├── damos-similar-0005/             # A2L similar (pas 0008 exact)
├── ref-a4-516657-stage2/           # Référence Stage2 même SW
└── build_v1.py, build_v11.py       # Scripts de construction
```

### 2. Méthodologie de Construction Carto

#### **Philosophie de base**
```python
# build_v1.py — Règles V1 conservateur
CAP = 1.12          # +12% max vs ORI (0AW Multitronic, 256k km)
CAL_LO = 0x180000   # Zone calibration
CAL_HI = 0x1F0000
FLAG_LO = 0x185000  # Zone flags à éviter
FLAG_HI = 0x186200
```

#### **Processus de build** (cf. `build_v1.py`)

1. **Base ORI** : fichier flash origine 2 Mo
2. **Couche DaVinci** : DPF/EGR/FLAPS off (masques DTC inclus)
3. **Couche Stage 1** :
   - Scan des runs de calibration (groupements de cellules modifiées)
   - Application sélective : only raise cells already used (`ori > 0`)
   - Cap +12% max (protection boîte 0AW)
   - Exclusions :
     - Cellules ORI = 0 (pas de fill)
     - Ratio > 1.20 (trop agressif)
     - Ratio < 1.02 (trop faible, bruit)
     - Zone flags et zones protégées
4. **Vérification** :
   - IDs intacts (516657, B3UX, CGKA...)
   - DaVinci fully applied
   - Pas de TVA / lambda
   - Checksum marqué `noCHK` (manuel avant flash)

#### **Versions successives**

| Version | Fichier | Focus |
|---------|---------|-------|
| V1 | `A5_516657_V1_S1cons_DPF_EGR_noCHK.fls` | Stage1 aveugle +12% |
| V1.1 | `A5_516657_V1.1_S1named_DPF_EGR_noCHK.fls` | Stage1 **named** (mappack ami) |
| **V1.5** | `A5_516657_V1.5_0AW_injtime_cruiseIQ_vmaxoff_nosmoke_fill400_DPF_EGR_HC_SOI_noCHK.fls` | **InjTime soft + cruise IQ + no-smoke + fill@400** |

### 3. Maps Modifiées (V1.5)

#### **Injection Time (Durée)**
- **Adresse :** `0x1D1496`
- **Cellules :** 90 (axes RPM intacts)
- **Variation :** +1.7% médiane, cap +3% vs ORI
- **Source :** cells Stage1 ami (référence validée)

#### **IQ (Quantité Injectée)**
- **IQ #1 :** +2% (maps principales)
- **IQ #2/3/4 :** **restaurées ORI** (maps cruise)
- **Cellules :** 721 remises stock

#### **Couple / Smoke / Rail**
- **Fill :** sous 400 Nm
- **Smoke lambda :** +5%
- **Plafonds couple :** ORI (conservateur 0AW)
- **Rail :** inchangé vs V1.4

#### **Pollution / Hardcut / SOI**
- **DPF/EGR/FLAPS :** off (DaVinci)
- **Hardcut :** maintenu
- **SOI :** maintenu
- **Vmax :** 350 km/h (désactivé)

### 4. Blocages et Contraintes

**⚠️ Pas de flash avant :**
1. **G83** (sonde température liquide) réparé (P102A / P2185 à 123°C)
2. **EGT S3** (sonde température échappement) OK
3. **FAP** 55g régénération traitée
4. Lecture **KESS V2 OBD** confirmée (IDs 516657 + taille 2 Mo)

**🔧 Lecture :** K-TAG plugin 151 BOOT (MICRO + EEPROM)  
**✍️ Flash :** KESS V2 OBD CHK (checksum WinOLS obligatoire)  
**♻️ Restore :** K-TAG 151 BOOT (EEPROM off pour Stage 1)

### 5. Protocole de Logs

**Page interactive :** `a5-winols.html` (viewer WinOLS)

**Logs prioritaires post-flash :**

```
A5_516657_V15_ROUTE_INJ_YYYYMMDD.csv   # Priorité 1 : injection + fumée
A5_516657_V15_VILLE_YYYYMMDD.csv       # Confort
A5_516657_V15_HARCUT_YYYYMMDD.csv      # Hardcut validation
```

**IDE VCDS attendus :**
- Engine RPM, Vehicle speed, Accelerator pedal
- Engine torque TQI
- Rail pressure (SP / ACT)
- MAP (SP / ACT)
- Air mass, Injection quantity

---

## 📊 Comparaison avec PCR2.1 (Caddy)

### Similitudes

| Aspect | EDC17CP14 | PCR2.1 (Caddy) | Statut |
|--------|-----------|----------------|--------|
| **Scripts Python automatiques** | ✅ `build_v1.py`, `build_v11.py` | ✅ `build_caddy_v5*.py` | ✅ Identique |
| **Manifests JSON** | ✅ `A5_516657_V1.5_0AW_manifest.json` | ✅ `caddy-9979-v5g-manifest.json` | ✅ Identique |
| **Fiches détaillées** | ✅ `README.md`, `LIVRAISON-V1.5-0AW.txt` | ✅ `FICHE-V5G-360.md` | ✅ Identique |
| **Viewer HTML** | ✅ `a5-cgka-edc17cp14.html` | ✅ `index.html` (multi-ECU) | ✅ Identique |
| **Logs VCDS** | ✅ Procédure documentée | ✅ `LOG-PROCEDURES.md` | ✅ Identique |
| **DTC off DaVinci** | ✅ `diff_davinci_packs.py` | ✅ Appliqué via ACE | ✅ Identique |

### Différences Clés

| Aspect | EDC17CP14 (A5) | PCR2.1 (Caddy) | Raison |
|--------|----------------|----------------|--------|
| **RPM storage** | ⚠️ **×2 (factor 0.5 WinOLS)** | ×1 (normal) | **CRITIQUE : axes RPM doublés** |
| **Pédale storage** | ⚠️ **0–8192 (conv %)** | 0–100% direct | **CRITIQUE : 8192 = 100%** |
| **Couple factor** | ⚠️ **0.1 (dixièmes Nm)** | souvent 0.03125−1024 | **CRITIQUE : ne pas copier PCR** |
| **A2L exact** | ❌ Similar 0005 seulement | ✅ A2L 9979 exact | Limitation DAMOS-Big-Archive |
| **Maps nommées** | ⚠️ Partiel (via A2L similar) | ✅ 100% nommées | Pas d'A2L 0008/B3UX exact |
| **Référence Stage2** | ✅ A4 même SW 516657 | ❌ Pas de ref directe | Bonne pratique A5 |
| **Launch control** | ❌ 0AW Multitronic (pas de launch) | ✅ V2/V3 launch 2500-2700 | Type boîte |
| **Évolution versions** | V1 → V1.1 → **V1.5** (3 itérations) | V2 → V5d/e/f → **V5g** (8+ itérations) | Caddy plus mature |
| **Objectif couple** | ~400 Nm (conservateur 0AW) | **~360 Nm** (V5g last stock) | Usage véhicule |
| **Philosophie** | **Conservateur** (256k km, client) | **Performance** (380→360 final) | Contexte projet |

### Points d'Attention EDC17

#### ⚠️ **Lacunes identifiées**

1. **Pas d'A2L exact 0008/B3UX**
   - Similar 0005 utilisé (P714/C714B3UN)
   - Noms maps OK, offsets 0005→0008 à recaler manuellement
   - Risque : offset drift non détecté

2. **Smoke maps non détaillées**
   - `nosmoke_lambda` mentionné mais pas de fiche dédiée
   - Pas de banques smoke listées (contrairement à Caddy FICHE-CHANGEMENTS-ORI-V1.md)

3. **Rail maps non documentées**
   - Caddy : 21 banques rail (7 A2L + 14 hors A2L + 2 lim)
   - EDC17 : "Rail inchangé" mais pas de détail

4. **AccPed maps non listées**
   - Caddy : 8 banques AccPed détaillées avec adresses
   - EDC17 : pas de maps AccPed explicites

5. **InjTime nouvelle map**
   - Injection Time (us) @ `0x1D1496` ajoutée V1.5
   - Pas d'équivalent Caddy documenté
   - ✅ **Potentiel : reproduire sur PCR2.1 ?**

6. **Protocole logs moins mature**
   - Caddy : 6 types logs (ROUTE_RAIL, TURBO, VILLE, HARCUT, DEPART, INJ)
   - EDC17 : 3 types seulement (ROUTE_INJ, VILLE, HARCUT)
   - Pas de log rail / turbo dédié

---

## 🎯 Méthodologie "Shorts" (source externe non accessible)

**⚠️ Lien Facebook non accessible** (timeout)

### Actions proposées

1. **Récupération manuelle** : Copier/coller le contenu texte si accessible
2. **Screenshots** : Capturer les étapes de la méthodologie
3. **Transcription** : Documenter les points clés dans ce fichier

### Éléments attendus d'une méthodologie "shorts"

- **Durée par étape** : rapide, visuel, étapes numérotées
- **Focus :** une map / une action par short
- **Format :** vidéo courte (<1 min) ou image annotée
- **Exemple Caddy :** FICHE-V5G-360.md déjà proche (sections courtes, tableaux visuels)

### Points à extraire du contenu Facebook

- [ ] Ordre de modification des maps
- [ ] Règles de cap / blend par map
- [ ] Protocole de vérification court
- [ ] Erreurs courantes à éviter
- [ ] Durée typique par étape

---

## 📝 Recommandations pour Compléter l'EDC17

### 1. Documentation manquante

```bash
# À créer sur le modèle PCR2.1
map-finder/ecu/edc17cp14/516657/
├── FICHE-EDC17-CHANGEMENTS-ORI-V1.5.md  # Comme FICHE-CHANGEMENTS-ORI-V1.md
├── FICHE-EDC17-SMOKE.md                  # Détail banques smoke
├── FICHE-EDC17-RAIL.md                   # Famille rail complète
├── FICHE-EDC17-ACCPED.md                 # AccPed 8 banques ?
├── LOG-PROCEDURES-EDC17.md               # Adaptation protocole logs A5
└── VERIFY-V1.5-DETAILED.txt              # Checklist détaillée
```

### 2. Scripts à ajouter

```python
# Analyse comparative fine
map-finder/ecu/edc17cp14/516657/
├── compare_ori_v15_detailed.py           # Comme compare_v5d_v6_*.py
├── extract_smoke_banks.py                # Extraction banques smoke
├── extract_rail_family.py                # Extraction famille rail
└── validate_injtime_vs_pcr21.py          # Injection Time applicable PCR2.1 ?
```

### 3. Logs post-flash

Compléter avec les 3 logs manquants :

```
A5_516657_V15_ROUTE_RAIL_YYYYMMDD.csv     # ✅ À ajouter
A5_516657_V15_ROUTE_TURBO_YYYYMMDD.csv    # ✅ À ajouter
A5_516657_V15_DEPART_YYYYMMDD.csv         # ❌ N/A (0AW, pas de launch)
```

### 4. Page HTML unifiée

Intégrer EDC17 dans `index.html` (sélecteur multi-ECU) au lieu de page dédiée `a5-cgka-edc17cp14.html`.

---

## 🔗 Fichiers Clés Référence

### EDC17CP14
- `map-finder/ecu/edc17cp14/516657/README.md`
- `map-finder/ecu/edc17cp14/516657/LIVRAISON-V1.5-0AW.txt`
- `data/edc17cp14-516657/project.json`
- `a5-cgka-edc17cp14.html`

### PCR2.1 (référence mature)
- `FICHE-CHANGEMENTS-ORI-V1.md` ← **Template à reproduire**
- `FICHE-V5G-360.md` ← Dernière version
- `LOG-PROCEDURES.md` ← Protocole logs complet
- `tools/build_caddy_v5g.py` ← Script de build documenté

---

## 📌 Prochaines Étapes

1. ✅ **Documenter méthodologie actuelle EDC17** (ce fichier)
2. ⏳ **Récupérer méthodologie "shorts"** (lien Facebook à ré-essayer)
3. ⏳ **Créer FICHE-EDC17-CHANGEMENTS-ORI-V1.5.md** (sur modèle Caddy)
4. ⏳ **Extraire et documenter banques smoke/rail/accped**
5. ⏳ **Compléter protocole logs EDC17** (ajouter ROUTE_RAIL, ROUTE_TURBO)
6. ⏳ **Valider applicabilité InjTime sur PCR2.1** (potentiel retour)

---

**Dernière mise à jour :** 27 oct 2026  
**Auteur :** SavageSear (via cloud agent analyse repository)
