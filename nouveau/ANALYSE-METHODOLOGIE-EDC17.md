# Analyse Méthodologie EDC17 — Récapitulatif

**Date :** 27 octobre 2026  
**Contexte :** Comparaison méthodologie EDC17CP14 vs PCR2.1 + intégration méthodologie "shorts" (Facebook)

---

## 📁 Fichiers Créés

### 1. Récapitulatif Complet
**`METHODOLOGIE-EDC17-RECAP.md`** (racine repository)
- ✅ Méthodologie actuelle EDC17CP14 complète
- ✅ Comparaison détaillée avec PCR2.1 (Caddy)
- ✅ Lacunes identifiées (A2L, smoke, rail, accped)
- ✅ Recommandations fichiers à créer
- ✅ Protocole logs à compléter

**Points clés :**
- EDC17 : 3 versions (V1 → V1.1 → V1.5)
- Caddy : 8+ versions (V2 → V5g)
- **Nouvelle map EDC17 :** Injection Time @ 0x1D1496 (absente Caddy)
- Blocages : G83, EGT S3, FAP 55g

### 2. Template Méthodologie Shorts
**`METHODOLOGIE-SHORTS-TEMPLATE.md`** (racine repository)
- ✅ Template vierge pour shorts (30-60 sec)
- ✅ Exemples Caddy (AccPed, Rail, Smoke)
- ✅ Checklist récupération lien Facebook
- ✅ Matrice shorts par calculateur
- ✅ Format vidéo recommandations
- ✅ Structure fichiers `shorts/` à créer

**Points clés :**
- Lien Facebook : ⏳ timeout (récupération manuelle)
- Format : vertical 9:16 ou 16:9, 1080p, 30 fps
- Structure : intro → localisation → avant → modif → après → vérif

### 3. Script Analyse Détaillée
**`map-finder/ecu/edc17cp14/516657/analyze_v15_detailed.py`**
- ✅ Extraction banques smoke, rail, accped, injection
- ✅ Génération rapport JSON + Markdown
- ✅ Comparaison ORI vs V1.5 octets par octets
- ✅ Outputs : `v15_detailed_analysis.json` + `FICHE-EDC17-CHANGEMENTS-ORI-V15.md`

**Utilisation :**
```bash
cd /workspace/map-finder/ecu/edc17cp14/516657
python analyze_v15_detailed.py
```

**Outputs attendus :**
- Top 10 régions modifiées (adresses + octets)
- Injection Time : 90 cellules, +1.7% médiane
- AccPed : 8 banques candidates (grilles 8×16)
- Smoke : 5 banques candidates
- Rail : 10+ banques candidates

---

## 🔍 Résultats Analyse Comparative

### Similitudes EDC17 ↔ PCR2.1
✅ Scripts Python automatiques  
✅ Manifests JSON  
✅ Fiches détaillées  
✅ Viewer HTML  
✅ Logs VCDS  
✅ DTC off DaVinci  

### Différences Majeures

| Aspect | EDC17 (A5) | PCR2.1 (Caddy) |
|--------|------------|----------------|
| **A2L exact** | ❌ Similar 0005 | ✅ 9979 exact |
| **Maps nommées** | ⚠️ Partiel | ✅ 100% |
| **Launch control** | ❌ 0AW (pas de launch) | ✅ 2700 rpm |
| **Injection Time** | ✅ @ 0x1D1496 ✨ **NOUVEAU** | ❌ Absent |
| **Versions** | 3 (V1→V1.5) | 8+ (V2→V5g) |
| **Objectif couple** | ~400 Nm (conserv.) | ~360 Nm (perfo) |

### 🆕 Nouveautés EDC17 (absentes Caddy)

1. **Injection Time (us)** @ `0x1D1496`
   - 90 cellules modifiées
   - +1.7% médiane, cap +3%
   - Source : cells Stage1 ami
   - **Potentiel :** à tester sur PCR2.1 ?

2. **IQ Cruise Restore**
   - IQ #2/3/4 → ORI (721 cellules)
   - IQ #1 : +2% (maps principales)
   - Logique : Stage1 = cruise ORI, puissance = IQ #1

3. **Contraintes Spécifiques**
   - G83 (P102A / P2185)
   - EGT S3
   - FAP 55g régénération
   - **Bloquant flash** jusqu'à résolution

---

## ⚠️ Lacunes Identifiées

### Documentation Manquante EDC17

- [ ] `FICHE-EDC17-CHANGEMENTS-ORI-V1.5.md` (modèle Caddy)
- [ ] `FICHE-EDC17-SMOKE.md` (détail banques)
- [ ] `FICHE-EDC17-RAIL.md` (famille rail)
- [ ] `FICHE-EDC17-ACCPED.md` (8 banques ?)
- [ ] `LOG-PROCEDURES-EDC17.md` (ROUTE_RAIL, ROUTE_TURBO)
- [ ] `VERIFY-V1.5-DETAILED.txt` (checklist)

### Scripts à Créer

- [ ] `compare_ori_v15_detailed.py` (comme Caddy `compare_v5d_v6_*.py`)
- [ ] `extract_smoke_banks.py`
- [ ] `extract_rail_family.py`
- [ ] `validate_injtime_vs_pcr21.py` (transfert EDC17 → Caddy ?)

### Protocole Logs Incomplet

**Caddy (complet) :**
- ROUTE_RAIL, ROUTE_TURBO, VILLE, HARCUT, DEPART, ROUTE_INJ

**EDC17 (partiel) :**
- ROUTE_INJ ✅
- VILLE ✅
- HARCUT ✅
- ROUTE_RAIL ⏳ **manquant**
- ROUTE_TURBO ⏳ **manquant**
- DEPART ❌ N/A (0AW)

---

## 🔗 Méthodologie "Shorts" (Facebook)

### Statut Actuel
⏳ **Lien inaccessible** (timeout)  
📎 https://www.facebook.com/share/1Dnarw2JDw/?mibextid=wwXIfr

### Actions de Récupération

#### Méthode 1 : Manuelle
- [ ] Ouvrir lien dans navigateur
- [ ] Screenshots chaque étape
- [ ] Transcription texte
- [ ] Compléter `METHODOLOGIE-SHORTS-TEMPLATE.md`

#### Méthode 2 : Download
- [ ] `yt-dlp` ou équivalent Facebook
- [ ] Convertir MP4 local
- [ ] Extraire frames clés
- [ ] Transcrire audio

#### Méthode 3 : Archive
- [ ] Wayback Machine
- [ ] Google Cache

#### Méthode 4 : Contact
- [ ] Message privé auteur
- [ ] Export texte/PDF

### Format Attendu

**Hypothèses :**
- Vidéos courtes (<1 min)
- Focus : EDC17 spécificités
- Mention probable : Injection Time
- Format : TikTok/Instagram Reels/YouTube Shorts
- Audience : tuners débutants/intermédiaires

### Structure Template Créée

```
Short #N : [TITRE]
├── Durée : X sec
├── Calculateur : EDC17CP14
├── Étapes (1-7)
├── Erreurs courantes
├── Vérification rapide
└── Vidéo/screenshots
```

**Exemples Caddy créés :**
- Short #1 : AccPed WOT 350 Nm
- Short #2 : Rail Family Blend 35.7%
- Short #3 : Smoke Cap 360

---

## 📊 Matrice Shorts (prévisionnel)

| Short | PCR2.1 | EDC17 | MEVD | Priorité |
|---|:-:|:-:|:-:|:-:|
| AccPed WOT cap | ✅ | ⏳ | ⏳ | 🔴 Haute |
| **Injection Time** | ❌ | ✅ | ⏳ | 🔴 **NOUVEAU** |
| IQ cruise | ⏳ | ✅ | ⏳ | 🟡 Moyenne |
| Rail blend | ✅ | ⏳ | ⏳ | 🔴 Haute |
| Smoke cap | ✅ | ⏳ | ⏳ | 🔴 Haute |
| Hardcut | ✅ | ⏳ | ⏳ | 🟡 Moyenne |
| Launch | ✅ | ❌ | ⏳ | 🟢 Basse |
| DPF/EGR off | ✅ | ✅ | ⏳ | 🔴 Haute |
| Checksum | ✅ | ✅ | ⏳ | 🔴 Haute |
| Logs VCDS | ✅ | ⚠️ | ⏳ | 🟡 Moyenne |

---

## 🎯 Prochaines Actions

### Immédiat (priorité 1)
1. **Récupérer lien Facebook** (méthodologie shorts)
2. **Exécuter `analyze_v15_detailed.py`** → générer fiche détaillée
3. **Créer `FICHE-EDC17-CHANGEMENTS-ORI-V1.5.md`** (modèle Caddy)
4. **Compléter protocole logs** (ROUTE_RAIL, ROUTE_TURBO)

### Court terme (priorité 2)
5. **Extraire banques smoke/rail/accped** (scripts dédiés)
6. **Créer dossier `shorts/`** pour EDC17
7. **Valider Injection Time sur PCR2.1** (transfert possible ?)
8. **Page HTML unifiée** (intégrer EDC17 dans `index.html`)

### Moyen terme (priorité 3)
9. **Recherche A2L 0008 exact** (Damos-Big-Archive retry)
10. **Logs post-flash V1.5** (ROUTE_INJ, ROUTE_RAIL, VILLE, HARCUT)
11. **Comparaison logs A5 vs Caddy** (patterns couple/rail/smoke)
12. **Shorts vidéo Caddy baseline** (modèle EDC17)

---

## 📂 Structure Fichiers Proposée

```
workspace/
├── METHODOLOGIE-EDC17-RECAP.md           ← ✅ Créé (racine)
├── METHODOLOGIE-SHORTS-TEMPLATE.md       ← ✅ Créé (racine)
├── nouveau/
│   └── ANALYSE-METHODOLOGIE-EDC17.md     ← ✅ Ce fichier
│
└── map-finder/ecu/edc17cp14/516657/
    ├── analyze_v15_detailed.py            ← ✅ Créé
    ├── v15_detailed_analysis.json         ← ⏳ À générer
    ├── FICHE-EDC17-CHANGEMENTS-ORI-V15.md ← ⏳ À générer
    │
    ├── shorts/                             ← ⏳ À créer
    │   ├── README.md
    │   ├── 01-accped-wot-cap.md
    │   ├── 02-injection-time-soft.md      ← NOUVEAU EDC17
    │   ├── 03-iq-cruise-restore.md        ← NOUVEAU EDC17
    │   ├── 04-smoke-lambda.md
    │   ├── 05-dpf-egr-davinci.md
    │   └── 06-checksum-kess.md
    │
    └── shorts-videos/                      ← ⏳ À créer (si perms)
        ├── 01-accped.mp4
        ├── 02-injtime.mp4
        └── ...
```

---

## 🔄 Transferts Possibles EDC17 → PCR2.1

### 1. Injection Time (us)
**EDC17 :** @ `0x1D1496`, +1.7% médiane, cap +3%  
**PCR2.1 :** ❓ Adresse inconnue, à investiguer  
**Action :** `validate_injtime_vs_pcr21.py`

### 2. IQ Cruise Restore
**EDC17 :** IQ #2/3/4 → ORI (cruise soft), IQ #1 +2% (puissance)  
**PCR2.1 :** IQ maps à vérifier (probablement modifiées uniformément)  
**Action :** Comparer logs VCDS cruise A5 vs Caddy

### 3. Fill sous 400 Nm
**EDC17 :** Plafonds couple ORI (conservateur 0AW)  
**PCR2.1:** WOT 350 Nm (embrayage stock)  
**Transfert :** Logique identique (ceilings stock)

---

## 📈 Métriques Comparatives

| Métrique | EDC17 (V1.5) | PCR2.1 (V5g) |
|----------|--------------|--------------|
| **Octets modifiés** | 6,238 | ~25,718 |
| **% fichier** | ~0.3% | ~1.2% |
| **Versions** | 3 | 8+ |
| **Maps identifiées** | ~15 | ~40+ |
| **A2L exact** | ❌ | ✅ |
| **Logs VCDS types** | 3 | 6 |
| **Maturité** | 🟡 Moyen | 🟢 Haute |

---

## 💡 Insights Clés

1. **EDC17 moins mature** que PCR2.1 (3 vs 8+ versions)
2. **Injection Time = innovation EDC17** (absente Caddy)
3. **Contraintes physiques A5** (G83, EGT, FAP) retardent flash
4. **0AW Multitronic** limite performance (pas de launch, cap 400 Nm)
5. **A2L similar 0005** = risque offset drift
6. **Logs incomplets** EDC17 (manque ROUTE_RAIL, ROUTE_TURBO)
7. **Méthodologie shorts** probablement EDC17-centric (contenu Facebook)

---

## ✅ Résumé Exécutif

### Ce qui existe (EDC17)
✅ Build scripts Python automatiques  
✅ Manifests JSON versionnés  
✅ README projet détaillé  
✅ Viewer HTML dédié  
✅ 3 versions livrables (V1, V1.1, V1.5)  
✅ Protocole flash K-TAG/KESS documenté  

### Ce qui manque (EDC17)
❌ A2L exact 0008/B3UX  
❌ Fiche changements détaillée (modèle Caddy)  
❌ Documentation banques smoke/rail/accped  
❌ Protocole logs complet (6 types)  
❌ Méthodologie shorts (lien Facebook inaccessible)  
❌ Scripts extraction banques  

### Prochaine Étape Critique
🔴 **Récupérer méthodologie shorts** (Facebook) → débloquer documentation complète

---

**Auteur :** Cloud Agent Cursor (SavageSear repository)  
**Date :** 27 octobre 2026, 12:15 UTC-3  
**Statut :** Documentation partielle — attente récupération lien Facebook
