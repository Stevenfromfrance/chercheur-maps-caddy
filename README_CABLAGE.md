# 📚 Documentation Complète - Câblage WDJ 1500W 72V

**Contrôleur:** Jiangsu Pardriver NS24 (DN72450_14_A_HA86)  
**Moteur:** WDJ 1500W 72V BLDC  
**Date:** 8 novembre 2026

---

## 📖 TABLE DES MATIÈRES

Cette documentation complète comprend **4 guides** pour vous aider à câbler correctement votre scooter électrique:

### 🔵 Guide 1: [GUIDE_CABLAGE_WDJ_1500W_72V.md](GUIDE_CABLAGE_WDJ_1500W_72V.md)
**📘 Guide de câblage complet et détaillé**

**Contenu:**
- Spécifications du contrôleur NS24
- Description complète de toutes les connexions
- Identification des bornes et connecteurs
- Procédure d'installation étape par étape
- Tests de sécurité obligatoires
- Dépannage des problèmes courants
- Précautions de sécurité détaillées

**À lire en premier** pour comprendre le système dans son ensemble.

---

### 🔵 Guide 2: [IDENTIFICATION_CONNECTEURS.md](IDENTIFICATION_CONNECTEURS.md)
**📘 Identification visuelle des connecteurs**

**Contenu:**
- Analyse détaillée de chaque connecteur visible sur vos photos
- Tableaux d'identification par nombre de fils et couleurs
- Procédures de test avec multimètre
- Template de tableau à remplir pour votre faisceau spécifique
- Plan d'action en 5 phases
- Questions à se poser pour chaque connecteur

**À utiliser pendant l'inventaire** de votre faisceau pour identifier chaque connecteur.

---

### 🔵 Guide 3: [SCHEMA_CABLAGE_SIMPLIFIE.md](SCHEMA_CABLAGE_SIMPLIFIE.md)
**📘 Schémas de câblage en format texte**

**Contenu:**
- Schémas ASCII art pour chaque connexion
- Ordre de connexion recommandé
- Procédures de test étape par étape
- Codes d'erreur et leur signification
- Valeurs électriques de référence
- Diagnostic rapide des problèmes
- Checklist quotidienne

**À consulter pendant l'installation** pour visualiser rapidement les connexions.

---

### 🔵 Guide 4: [FICHE_REFERENCE_RAPIDE.md](FICHE_REFERENCE_RAPIDE.md)
**📘 Fiche de référence rapide (à imprimer!)**

**Contenu:**
- Toutes les informations essentielles sur 1-2 pages
- Format optimisé pour impression A4
- Tableaux de référence rapide
- Checklist de sécurité
- Zone de notes personnelles
- À plastifier et garder dans votre boîte à outils

**À imprimer et garder à portée de main** pendant toute l'installation.

---

## 🎯 COMMENT UTILISER CETTE DOCUMENTATION

### Phase 1: PRÉPARATION (1 heure)

1. **Lire le Guide 1** en entier pour comprendre le système
2. **Imprimer la Fiche de référence rapide** (Guide 4)
3. **Préparer les outils:**
   - Multimètre numérique ✅
   - Tournevis et clés Allen ✅
   - Pinces et fer à souder ✅
   - Ruban isolant et gaines ✅
   - Carnet et stylo ✅

### Phase 2: INVENTAIRE (30-60 minutes)

1. **Ouvrir le Guide 2** (Identification connecteurs)
2. **Déballer tous les connecteurs** de votre faisceau
3. **Prendre des photos** de chaque connecteur
4. **Remplir le tableau** dans le Guide 2 avec:
   - Nombre de fils
   - Couleurs de fils
   - Type de connecteur
5. **Comparer avec les descriptions** du Guide 2

### Phase 3: TESTS ÉLECTRIQUES (1 heure)

1. **Utiliser le multimètre** (procédures dans Guide 2)
2. **Mesurer les tensions** sur chaque connecteur
3. **Noter les valeurs** dans votre carnet et sur la fiche
4. **Comparer avec les valeurs de référence** (Guide 3)
5. **Identifier la fonction** de chaque connecteur

### Phase 4: INSTALLATION (2-3 heures)

1. **Suivre l'ordre de connexion** du Guide 3
2. **Consulter les schémas** du Guide 3 pour chaque branchement
3. **Vérifier avec la Fiche rapide** (Guide 4) les points critiques
4. **⚠️ ATTENTION:** Batterie DÉBRANCHÉE pendant toute cette phase
5. **Prendre des photos** de chaque connexion effectuée

### Phase 5: TESTS DE SÉCURITÉ (1-2 heures)

1. **Suivre les procédures de test** du Guide 3
2. **Cocher la checklist** de la Fiche rapide (Guide 4)
3. **Tester OBLIGATOIREMENT les freins** en premier
4. **Tests progressifs:**
   - Alimentation
   - Freins
   - Accélérateur (roue surélevée)
   - Essai au sol à basse vitesse
5. **Documenter les résultats** dans votre carnet

---

## ⚠️ POINTS CRITIQUES DE SÉCURITÉ

### 🔴 DANGER N°1: Polarité batterie

```
╔══════════════════════════════════════════════╗
║  Terminal ROUGE (B+)  =  +72V POSITIF       ║
║  Terminal NOIR  (B−)  =  GND NÉGATIF        ║
║                                              ║
║  Inverser B+/B− = FarDriver grillé          ║
╚══════════════════════════════════════════════╝
```

**Où trouver cette info:**
- Guide 1: Section "Connexions principales"
- Guide 3: Section "Connexions alimentation"
- Guide 4: Encadré en haut
- **MAPPING_SCOOT_VERS_FARDRIVER.md** (mapping scooter → FarDriver)

### 🔴 DANGER N°2: Test des freins obligatoire

**Les freins DOIVENT couper le moteur complètement!**

Si les freins ne coupent pas le moteur → **NE PAS ROULER!**

**Procédure de test:**
1. Roue arrière surélevée
2. Actionner le frein avant
3. Essayer de tourner l'accélérateur
4. Le moteur ne doit PAS tourner
5. Répéter avec le frein arrière

**Où trouver cette info:**
- Guide 1: Section "Tests de sécurité"
- Guide 3: Section "Test 3"
- Guide 4: Checklist "Tests obligatoires"

### 🔴 DANGER N°3: Fusible 200A obligatoire

**Un fusible de 200A DOIT être installé sur le fil +72V!**

Position: Entre la batterie (+) et le terminal NOIR du contrôleur

**Sans fusible = Risque d'incendie en cas de court-circuit!**

**Où trouver cette info:**
- Guide 1: Section "Procédure de connexion - Étape 1"
- Guide 3: Section "Connexions alimentation"
- Guide 4: Checklist avant démarrage

---

## 🔧 OUTILS OBLIGATOIRES

| Outil | Priorité | Où trouver la liste |
|-------|----------|---------------------|
| **Multimètre numérique** | ⚠️ OBLIGATOIRE | Tous les guides |
| Tournevis cruciformes | Nécessaire | Guide 1, 3 |
| Clés Allen | Nécessaire | Guide 1, 3 |
| Pince à dénuder | Utile | Guide 1, 3 |
| Fer à souder | Si modification | Guide 2 |
| Ruban isolant | OBLIGATOIRE | Tous les guides |
| Gaines thermorétractables | Recommandé | Guide 1, 2 |

---

## 📊 RÉFÉRENCES RAPIDES

### Tensions normales (batterie connectée, contact ON):

| Point | Tension | Guide |
|-------|---------|-------|
| Batterie pleine | 84V | 3, 4 |
| Batterie vide | 60V | 3, 4 |
| +5V capteurs | 5.0V ±0.2V | 1, 3, 4 |
| +12V accessoires | 12V ±0.5V | 1, 3, 4 |
| Throttle repos | 0.8-1.2V | 1, 2, 3, 4 |
| Throttle max | 4.0-4.5V | 1, 2, 3, 4 |

### Identification par nombre de fils:

| Nombre de fils | Fonction probable | Guide |
|----------------|-------------------|-------|
| 2 fils | Frein ou interrupteur | 1, 2, 4 |
| 3 fils | Accélérateur | 1, 2, 3, 4 |
| 5-6 fils | Capteurs Hall ou écran | 1, 2, 3 |
| 8+ fils | Écran LCD complet | 1, 2, 3 |

### Codes d'erreur courants:

| Code | Signification | Action | Guide |
|------|---------------|--------|-------|
| E01 | Surtension | Batterie trop chargée | 3, 4 |
| E02 | Sous-tension | Recharger batterie | 3, 4 |
| E03 | Surintensité | Vérifier moteur | 3, 4 |
| E04 | Erreur Hall | Vérifier connecteur Hall | 3, 4 |
| E05 | Frein bloqué | Vérifier interrupteurs | 3, 4 |
| E06 | Throttle défectueux | Vérifier accélérateur | 3, 4 |
| E07 | Surchauffe | Laisser refroidir | 3, 4 |

---

## 📸 VOS PHOTOS DE RÉFÉRENCE

Les photos que vous avez fournies montrent:

1. **Contrôleur Jiangsu Pardriver NS24**
   - Bornes de puissance colorées (Bleu, Vert, Jaune, Noir, Rouge)
   - Connecteur principal rectangulaire
   - Étiquette avec spécifications

2. **Connecteurs du faisceau**
   - Connecteur blanc 2 fils (orange + jaune-vert)
   - Connecteur blanc 2 fils (violet + bleu)
   - Grand connecteur blanc multi-fils
   - Connecteur rouge multi-fils
   - Module GPS/tracker noir
   - Fils libres de différentes couleurs

**Analysées en détail dans:** Guide 2 (IDENTIFICATION_CONNECTEURS.md)

---

## 🆘 AIDE ET SUPPORT

### En cas de problème:

1. **Consultez d'abord le Guide correspondant:**
   - Problème de compréhension → Guide 1
   - Connecteur non identifié → Guide 2
   - Erreur de câblage → Guide 3
   - Référence rapide → Guide 4

2. **Utilisez les sections de diagnostic:**
   - Guide 1: "Problèmes courants"
   - Guide 3: "Diagnostic rapide"
   - Guide 4: "Aide rapide"

3. **Vérifiez les valeurs de référence:**
   - Tensions dans Guide 3 et 4
   - Codes d'erreur dans Guide 3 et 4

4. **Si le problème persiste:**
   - Prenez des photos claires du problème
   - Notez les tensions mesurées
   - Notez tout code d'erreur affiché
   - Décrivez précisément le symptôme
   - Consultez les forums spécialisés ou un professionnel

---

## 📋 CHECKLIST GÉNÉRALE DU PROJET

### Avant de commencer:
- [ ] Lire le Guide 1 en entier
- [ ] Imprimer le Guide 4
- [ ] Rassembler tous les outils
- [ ] Préparer le multimètre (piles neuves)
- [ ] Charger la batterie à 70-80%
- [ ] Prévoir 5-8 heures au total

### Pendant l'installation:
- [ ] Suivre l'ordre des guides (1→2→3→4)
- [ ] Prendre des photos de chaque étape
- [ ] Noter toutes les mesures dans un carnet
- [ ] Faire des pauses régulières
- [ ] Ne jamais travailler sous tension
- [ ] Vérifier deux fois, brancher une fois

### Après l'installation:
- [ ] Tous les tests de sécurité passés
- [ ] Aucun code d'erreur
- [ ] Freins fonctionnels (moteur coupé)
- [ ] Accélérateur répond correctement
- [ ] Premier essai à basse vitesse OK
- [ ] Documentation complétée et archivée

---

## 📞 CONTACTS UTILES

### Support technique:
- **Jiangsu Pardriver** (fabricant du contrôleur NS24)
- **Revendeur WDJ** (pour schémas du scooter)
- **Forums:** ElectricBike.com, EndlessSphere
- **Groupes Facebook:** Scooters électriques DIY

### En cas d'urgence:
- **Électricien spécialisé** véhicules électriques
- **Réparateur agréé** scooters électriques
- **Service d'incendie** (si fumée ou feu)

---

## 📝 VERSIONS DES DOCUMENTS

| Document | Version | Date | Pages |
|----------|---------|------|-------|
| README_CABLAGE.md | 1.0 | 08/11/2026 | Ce document |
| GUIDE_CABLAGE_WDJ_1500W_72V.md | 1.0 | 08/11/2026 | 15+ pages |
| IDENTIFICATION_CONNECTEURS.md | 1.0 | 08/11/2026 | 12+ pages |
| SCHEMA_CABLAGE_SIMPLIFIE.md | 1.0 | 08/11/2026 | 10+ pages |
| FICHE_REFERENCE_RAPIDE.md | 1.0 | 08/11/2026 | 4 pages |

---

## 🎓 RÉSUMÉ POUR DÉMARRER RAPIDEMENT

### Si vous êtes pressé (⚠️ non recommandé!):

**Lecture minimale:**
1. Guide 1 → Sections "Connexions principales" et "Procédure de connexion"
2. Guide 3 → Sections "Connexions" et "Tests"
3. Guide 4 → Tout (2 pages seulement)

**Actions minimales:**
1. Identifier +72V, GND, et les 3 fils moteur
2. Identifier l'accélérateur (3 fils)
3. Identifier les freins (2x2 fils)
4. Brancher dans l'ordre du Guide 3
5. Faire TOUS les tests de sécurité du Guide 4

**⚠️ Mais il est FORTEMENT RECOMMANDÉ de tout lire!**

---

## ✅ VALIDATION FINALE

Avant de considérer l'installation terminée, vérifier:

- [ ] Tous les 4 guides ont été consultés
- [ ] Toutes les connexions sont identifiées et documentées
- [ ] Tous les tests de sécurité sont passés avec succès
- [ ] Aucun code d'erreur n'est affiché
- [ ] Les freins coupent bien le moteur
- [ ] Premier essai au sol réussi (basse vitesse)
- [ ] Photos prises et archivées
- [ ] Carnet de notes complété
- [ ] Fiche de référence remplie et plastifiée
- [ ] Vous vous sentez en confiance pour utiliser le scooter

**Si tout est ✅ → Installation réussie! Félicitations! 🎉**

**Si certains points sont ⚠️ → Revenir aux guides et corriger avant utilisation**

---

## 🔐 GARANTIE ET RESPONSABILITÉ

⚠️ **IMPORTANT:**
- Cette documentation est fournie à titre informatif
- L'installation doit être faite par une personne compétente
- Tout travail sur un système 72V présente des risques
- En cas de doute, consultez un professionnel
- L'auteur décline toute responsabilité en cas d'accident

**Respect des normes:**
- Norme électrique locale
- Réglementation sur les véhicules électriques
- Code de la route applicable
- Assurance appropriée

---

## 📚 FICHIERS DE CETTE DOCUMENTATION

```
chercheur-maps-caddy/
│
├── README_CABLAGE.md                    ← Vous êtes ici!
├── GUIDE_CABLAGE_WDJ_1500W_72V.md      ← Guide complet
├── IDENTIFICATION_CONNECTEURS.md        ← Identification visuelle
├── SCHEMA_CABLAGE_SIMPLIFIE.md         ← Schémas de câblage
├── FICHE_REFERENCE_RAPIDE.md           ← À imprimer
│
└── assets/                              ← Vos photos
    ├── 0B305350-C42E-4B41-80A9-E95817541EBE_L0_001.jpg
    ├── 477CBD67-0CFE-41AF-A171-62201D9BB885_L0_001.jpg
    ├── A7A250B7-9F5C-4E02-9BB2-F45CEC47DD16_L0_001.jpg
    ├── E60B6789-86E2-4672-A560-16EC3D8BF789_L0_001.jpg
    ├── ... (et autres photos)
```

---

## 🎯 PROCHAINES ÉTAPES

1. **Lire cette page README** pour avoir une vue d'ensemble ✅
2. **Commencer par le Guide 1** pour comprendre le système
3. **Suivre l'ordre des phases** décrit dans "Comment utiliser cette documentation"
4. **Imprimer le Guide 4** et le garder avec vous
5. **Prendre votre temps** - Une installation correcte vaut mieux qu'une installation rapide
6. **Documenter votre travail** - Photos et notes vous seront utiles plus tard

---

**Bon courage pour votre installation! 🔧⚡🛴**

**N'oubliez pas: La sécurité avant tout!**

---

*Documentation créée le 8 novembre 2026*  
*Pour: Adaptation contrôleur Jiangsu Pardriver NS24 sur WDJ 1500W 72V*  
*Version: 1.0*
