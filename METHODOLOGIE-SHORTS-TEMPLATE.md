# MÉTHODOLOGIE SHORTS — Template à Compléter

## 📌 Source

**Lien Facebook :** https://www.facebook.com/share/1Dnarw2JDw/?mibextid=wwXIfr  
**Status :** ⏳ Non accessible (timeout) — à récupérer manuellement

---

## 🎯 Objectif

Documenter la méthodologie "shorts" (courte, visuelle, étape par étape) pour :
- EDC17CP14 (Audi A5 Sportback CGKA)
- PCR2.1 (Caddy CAYE)
- MEVD17.2.5 (BMW)
- Autres calculateurs

---

## 📝 Format Short (exemple Caddy V5g)

### Short #1 : AccPed WOT 350 Nm
**Durée :** ~45 sec  
**Calculateur :** PCR2.1 SW 9979

**Étapes :**
1. ✅ Ouvrir WinOLS : `Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin`
2. ✅ Importer A2L (si disponible)
3. ✅ Localiser banque AccPed : `0x1CF9C0` (8×16 grilles, 8 banques)
4. ✅ Identifier WOT (ligne pédale ≥85%)
5. ✅ Cap à **350 Nm** (plafond sécurité stock)
6. ✅ Blend partiels : soft vers ORI (tip-in doux)
7. ✅ Hardcut : ligne ≥4800 rpm → **0 Nm**
8. ✅ Checksum : save `_noCHK` puis WinOLS → calc CHK

**Erreurs courantes :**
- ❌ Modifier tip-in 0–23% pédale (reste stock)
- ❌ Oublier hardcut 4800 (danger over-rev)
- ❌ Cap >380 Nm (embrayage stock limité)

**Vérif rapide :**
- Max AccPed banque 1-6 : **350.0 Nm**
- Max banque 7 : **334.8 Nm** (différente)
- Ligne 4800+ : **0.0 Nm** (hardcut)

---

### Short #2 : Rail Family Blend 35.7%
**Durée :** ~1 min  
**Calculateur :** PCR2.1 SW 9979

**Étapes :**
1. ✅ Base : ACE Stage1 rail ~1656 bar (trop agressif)
2. ✅ Localiser 21 banques rail : 7 A2L (`0x1E9368`...) + 14 hors A2L + 2 lim
3. ✅ Règle : `V1 = ORI + 0.357×(ACE−ORI)` si ACE ≠ ORI
4. ✅ Cap : **1620 bar** (ne pas dépasser 1656 → 1620)
5. ✅ Appliquer sur **toutes** les banques (cohérence famille)
6. ✅ Vérif : max V1 ~1620 bar (pas ~1677)

**Erreurs courantes :**
- ❌ Oublier banques hors A2L (14+2)
- ❌ Dépasser 1620 bar (pompe HP limite)
- ❌ Blend différent par banque (incohérence)

**Vérif rapide :**
- 7 banques A2L max : **1620.0 bar**
- 14 banques hors A2L : **1620.0 bar** (V1b fix)
- 2 limiteurs : **1620.0 bar**

---

### Short #3 : Smoke Cap 360
**Durée :** ~30 sec  
**Calculateur :** PCR2.1 SW 9979

**Étapes :**
1. ✅ Base : ACE Stage1 smoke ~400 mg/stroke
2. ✅ Règle : `min(ORI × 1.20, 360)` si ACE ≠ ORI
3. ✅ Localiser 5 banques smoke : `0x1D1D18`...
4. ✅ Appliquer cap 360 (fumée acceptable + marge)
5. ✅ Ordre final : **wish 360 < tqlim 370 ≤ smoke 375**

**Erreurs courantes :**
- ❌ Cap trop haut (fumée noire excessive)
- ❌ Cap trop bas (perte couple / EGT)
- ❌ Smoke < wish (incohérence chaîne couple)

**Vérif rapide :**
- Max smoke banques 1-3 : **360.0**
- Max smoke banque 4 : **348.0**
- Max smoke banque 5 : **336.0**

---

## 📋 Template Short Vierge

### Short #N : [TITRE]
**Durée :** ~X sec  
**Calculateur :** [ECU] SW [VERSION]

**Étapes :**
1. ✅ [Étape 1]
2. ✅ [Étape 2]
3. ✅ [Étape 3]
...

**Erreurs courantes :**
- ❌ [Erreur 1]
- ❌ [Erreur 2]

**Vérif rapide :**
- [Check 1]
- [Check 2]

---

## 🔗 Shorts EDC17 à Créer (liste)

### À extraire du lien Facebook
- [ ] Short #1 : AccPed EDC17 (si applicable)
- [ ] Short #2 : Injection Time EDC17 @ 0x1D1496 ✨ **NOUVEAU**
- [ ] Short #3 : IQ cruise restore ORI
- [ ] Short #4 : Smoke / lambda EDC17
- [ ] Short #5 : Rail EDC17 (si modifié)
- [ ] Short #6 : DPF/EGR/FLAPS DaVinci
- [ ] Short #7 : DTC masques
- [ ] Short #8 : Checksum KESS V2
- [ ] Short #9 : Logs VCDS post-flash
- [ ] Short #10 : Vérif G83/EGT/FAP avant flash

### Spécificités EDC17 vs PCR2.1
- [ ] A2L similar 0005 → 0008 (offset recal)
- [ ] WinOLS import similar (procédure)
- [ ] K-TAG BOOT backup vs KESS OBD flash
- [ ] 0AW Multitronic : pas de launch control
- [ ] Injection Time : nouvelle map absente PCR2.1

---

## 📊 Matrice Shorts par Calculateur

| Short | PCR2.1 Caddy | EDC17 A5 | MEVD BMW | Notes |
|---|:-:|:-:|:-:|---|
| AccPed WOT cap | ✅ 350 Nm | ⏳ TBD | ⏳ TBD | Caddy 8 banques |
| Rail blend | ✅ 1620 bar | ⏳ TBD | ⏳ TBD | Caddy 21 banques |
| Smoke cap | ✅ 360 mg | ⏳ TBD | ⏳ TBD | Caddy 5 banques |
| Hardcut | ✅ 4800 rpm | ⏳ TBD | ⏳ TBD | Ligne rpm |
| Launch | ✅ 2700 rpm | ❌ N/A | ⏳ TBD | EDC17 = 0AW |
| **Injection Time** | ❌ N/A | ✅ @ 0x1D1496 | ⏳ TBD | **NOUVEAU EDC17** |
| IQ cruise | ⏳ TBD | ✅ #2/3/4 ORI | ⏳ TBD | EDC17 V1.5 |
| DPF/EGR off | ✅ via ACE | ✅ DaVinci | ⏳ TBD | Méthodes différentes |
| Checksum | ✅ KESS CHK | ✅ WinOLS→KESS | ⏳ TBD | EDC17 noCHK→CHK |

---

## 🎬 Format Vidéo Short (recommandations)

### Specs techniques
- **Durée :** 30–60 sec max
- **Ratio :** 9:16 (vertical) ou 16:9 (horizontal)
- **Résolution :** 1080p min
- **Framerate :** 30 fps
- **Audio :** voix off claire OU texte sur écran
- **Screen capture :** WinOLS / hex editor

### Structure type
1. **Intro** (3 sec) : titre + calculateur
2. **Localisation** (5 sec) : adresse + nom map
3. **Avant** (5 sec) : valeurs ORI
4. **Modification** (25 sec) : étapes + règles
5. **Après** (5 sec) : valeurs MOD
6. **Vérif** (5 sec) : checkpoints rapides
7. **Outro** (2 sec) : logo / next short

---

## 📝 Checklist Récupération Lien Facebook

### Méthode 1 : Copie manuelle
- [ ] Ouvrir lien dans navigateur
- [ ] Screenshots de chaque étape (PNG)
- [ ] Transcription texte dans ce fichier
- [ ] Notes voix off (si vidéo)

### Méthode 2 : Download vidéo
- [ ] Outil : `yt-dlp` ou équivalent Facebook
- [ ] Convertir en MP4 local
- [ ] Extraire frames clés (screenshots)
- [ ] Transcrire audio (si applicable)

### Méthode 3 : Archive Web
- [ ] Wayback Machine (archive.org)
- [ ] Cached Google (si public)

### Méthode 4 : Contact auteur
- [ ] Message privé Facebook
- [ ] Demander export texte/PDF
- [ ] Autorisation reproduction

---

## 🔄 Intégration dans Repository

### Fichiers à créer
```
map-finder/ecu/edc17cp14/516657/
├── shorts/
│   ├── 01-accped-wot-cap.md
│   ├── 02-injection-time-soft.md        ← NOUVEAU EDC17
│   ├── 03-iq-cruise-restore.md           ← NOUVEAU EDC17
│   ├── 04-smoke-lambda.md
│   ├── 05-dpf-egr-davinci.md
│   ├── 06-checksum-kess.md
│   └── README.md                         # Index shorts EDC17
│
└── shorts-videos/                         # Vidéos sources (si perms)
    ├── 01-accped.mp4
    ├── 02-injtime.mp4
    └── ...
```

### Format Markdown short
```markdown
# Short #N : [TITRE]

**Durée :** X sec | **ECU :** EDC17CP14 | **SW :** 516657

## 🎯 Objectif
[Description 1 ligne]

## 📍 Localisation
- **Adresse :** 0x______
- **Taille :** XXX octets
- **Nom map :** [si A2L]

## 🔧 Étapes
1. [Étape]
2. [Étape]

## ⚠️ Erreurs courantes
- ❌ [Erreur]

## ✅ Vérification
- [Check]

## 🎥 Vidéo
[lien ou `../shorts-videos/0N-xxx.mp4`]
```

---

## 📌 Actions Prioritaires

1. **⏳ URGENCE** : Récupérer contenu lien Facebook (timeout actuel)
2. **⏳** : Compléter template avec méthodologie shorts réelle
3. **⏳** : Créer dossier `shorts/` pour EDC17
4. **⏳** : Comparer avec méthodologie Caddy existante
5. **⏳** : Identifier transferts PCR2.1 ← EDC17 (Injection Time ?)
6. **⏳** : Générer shorts manquants Caddy (baseline)
7. **⏳** : Valider avec logs VCDS

---

**Dernière mise à jour :** 27 oct 2026  
**Statut lien Facebook :** ⏳ Fetch timeout — récupération manuelle nécessaire  
**Auteur :** SavageSear (via cloud agent template)

---

## 💡 Notes pour Récupération

Quand le lien Facebook sera accessible :
1. Copier cette structure de template
2. Remplacer `[TITRE]`, `[Étape]`, etc. par contenu réel
3. Ajouter screenshots dans `fiche-assets/shorts/`
4. Créer index dans `METHODOLOGIE-EDC17-RECAP.md`
5. Cross-référencer avec Caddy (transferts possibles)

**Hypothèses sur contenu attendu :**
- Vidéos courtes (<1 min)
- Focus : EDC17 spécificités
- Mention probable : Injection Time (absent Caddy)
- Format : TikTok/Instagram Reels/YouTube Shorts
- Audience : tuners débutants/intermédiaires
