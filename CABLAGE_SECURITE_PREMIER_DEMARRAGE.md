# ⚡ Guide Câblage & Sécurité - Premier Démarrage

## 🔴 SÉCURITÉ AVANT TOUT

### ⚠️ DANGERS
```
72V × 200A = 14,400 Watts de puissance
→ MORTEL si mal branché
→ Risque d'incendie si court-circuit
→ Brûlures graves possibles
```

### 🛡️ ÉQUIPEMENT DE SÉCURITÉ OBLIGATOIRE
- [ ] Gants isolants (1000V rated)
- [ ] Lunettes de protection
- [ ] Extincteur (ABC ou CO₂) à portée de main
- [ ] Multimètre pour tests
- [ ] Espace bien ventilé
- [ ] Sol non-conducteur (pas de métal)
- [ ] Pas d'eau/humidité dans la zone

---

## 🔌 SCHÉMA DE CONNEXION COMPLET

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTÈME COMPLET 72V                          │
└─────────────────────────────────────────────────────────────────┘

BATTERIE 72V 200Ah
    │
    │ (Câble 10AWG/6mm² rouge)
    │
    ├─────[FUSIBLE 250A]───────┐
    │                          │
    │                     [INTERRUPTEUR]
    │                     Principal ON/OFF
    │                          │
    │                          │
    ▼                          ▼
┌────────────────────────────────────────┐
│    CONTRÔLEUR FARDRIVER NS24           │
│                                        │
│  [+] ←── Rouge (Batterie +)           │
│  [-] ←── Noir (Batterie -)            │
│                                        │
│  Connecteurs :                         │
│  • 3 fils gros (U,V,W) → MOTEUR       │
│  • 1 petit connecteur → HALL SENSOR    │
│  • 1 connecteur → THROTTLE (Accél.)    │
│  • 1 connecteur → BRAKE (Frein)        │
│  • 1 connecteur → DISPLAY (Écran)      │
│  • 1 antenne → BLUETOOTH               │
└────────────────────────────────────────┘
           │  │  │           │
           U  V  W        5 fils Hall
           │  │  │           │
           ▼  ▼  ▼           ▼
        ┌─────────────────────────┐
        │   MOTEUR QS 5000W       │
        │   • 3 gros fils phase   │
        │   • 5 fils Hall sensor  │
        └─────────────────────────┘

ACCESSOIRES :
┌──────────────┐
│  THROTTLE    │ ──→ Contrôleur (3 fils : 5V, Signal, GND)
│ (Accélérateur)│
└──────────────┘

┌──────────────┐
│ BRAKE SENSOR │ ──→ Contrôleur (2-3 fils)
│ (Frein)      │
└──────────────┘

┌──────────────┐
│   DISPLAY    │ ──→ Contrôleur (Communication série)
│  (Écran)     │
└──────────────┘
```

---

## 🔧 ORDRE DE CONNEXION (IMPORTANT !)

### ⚠️ RÈGLE D'OR : BATTERIE EN DERNIER !

```
ORDRE CORRECT (à respecter absolument) :

1. Moteur → Contrôleur ✅
   ├─ 3 fils de phase (U, V, W)
   └─ Capteurs Hall (5 fils)

2. Throttle → Contrôleur ✅
   (Accélérateur)

3. Brake → Contrôleur ✅
   (Capteur de frein, si présent)

4. Display → Contrôleur ✅
   (Écran, optionnel)

5. Vérifications visuelles ✅
   (Tous les connecteurs bien enfoncés)

6. FUSIBLE installé ✅
   (250A entre batterie et contrôleur)

7. Interrupteur sur OFF ✅

8. BATTERIE → Contrôleur ✅ EN DERNIER
   (+ rouge, - noir)

9. Vérifier tensions avec multimètre ✅

10. Interrupteur sur ON ✅
```

---

## 📋 CONNEXIONS DÉTAILLÉES

### 1️⃣ CONNEXION MOTEUR ⚡

#### A. Fils de phase (3 gros fils)
```
CONTRÔLEUR          MOTEUR
┌────────┐         ┌────────┐
│   U    │────────→│   U    │  Jaune/Bleu
│   V    │────────→│   V    │  Vert/Vert
│   W    │────────→│   W    │  Blanc/Noir
└────────┘         └────────┘

⚠️ Couleurs peuvent varier !
→ Repérer avec étiquettes U, V, W

Connecteurs : Généralement bullet 5.5mm ou 6.0mm

ATTENTION :
→ Bien isoler chaque connecteur
→ NE JAMAIS toucher pendant fonctionnement
→ Courant phase = jusqu'à 450A !
```

#### B. Capteurs Hall (5 fils fins)
```
CONTRÔLEUR          MOTEUR
┌────────────┐     ┌────────────┐
│ 🔴 Rouge   │────→│ 🔴 5V+     │  Alimentation
│ ⚫ Noir     │────→│ ⚫ GND      │  Masse
│ 🟡 Jaune   │────→│ 🟡 Hall A  │  Signal A
│ 🟢 Vert    │────→│ 🟢 Hall B  │  Signal B
│ 🔵 Bleu    │────→│ 🔵 Hall C  │  Signal C
└────────────┘     └────────────┘

Type connecteur : JST ou similaire (5 pins)

⚠️ TRÈS IMPORTANT :
→ Ce connecteur DOIT être bien enfoncé (clic)
→ 90% des erreurs 7 viennent de là !
→ Vérifier aucun fil coupé
→ Protéger de l'eau/poussière
```

### 2️⃣ CONNEXION THROTTLE (Accélérateur) 🎮

```
THROTTLE            CONTRÔLEUR
┌────────────┐     ┌────────────┐
│ 🔴 Rouge   │────→│ 🔴 5V+     │  Alimentation
│ ⚫ Noir     │────→│ ⚫ GND      │  Masse
│ 🟢 Vert    │────→│ 🟢 Signal  │  0.8V-4.2V
└────────────┘     └────────────┘

Type : Hall Effect Throttle (généralement)

Voltages normaux :
• Position repos : 0.8-1.2V
• Position max : 3.8-4.2V

Test avec multimètre :
→ Entre signal et GND
→ Tourner throttle → voltage augmente
```

### 3️⃣ CONNEXION BRAKE (Frein) 🛑

```
BRAKE SENSOR        CONTRÔLEUR
┌────────────┐     ┌────────────┐
│ 🔴 Rouge   │────→│ 🔴 5V+     │  (si alimenté)
│ ⚫ Noir     │────→│ ⚫ GND      │
│ 🟡 Signal  │────→│ 🟡 Brake   │  High = frein actif
└────────────┘     └────────────┘

Types :
• Mechanical switch (simple contact)
• Hall sensor (sans contact)

Fonction :
→ Coupe le moteur quand frein activé
→ Active freinage régénératif (optionnel)
```

### 4️⃣ CONNEXION BATTERIE 🔋

#### ⚠️ ORDRE CRITIQUE
```
1. Installer FUSIBLE 250A sur fil rouge (+)
   ├─ Entre batterie et contrôleur
   └─ Le plus proche possible de la batterie

2. Installer INTERRUPTEUR (optionnel mais recommandé)
   ├─ Sur fil rouge (+) après le fusible
   └─ Position OFF avant première connexion

3. Connecter fil NOIR (-) en premier
   ├─ Batterie (-) → Contrôleur (-)
   └─ Serrer fermement (couple 10-15 Nm)

4. Connecter fil ROUGE (+) en dernier
   ├─ Batterie (+) → Fusible → Interrupteur → Contrôleur (+)
   └─ S'attendre à une étincelle (normal)
   
⚠️ Étincelle normale au branchement !
   C'est le contrôleur qui charge ses condensateurs
   Si grosse étincelle/fumée → DÉBRANCHER IMMÉDIATEMENT
```

#### Câblage batterie
```
Section câble minimum :
• 10 AWG (6mm²) pour 200A
• 8 AWG (10mm²) recommandé (marge sécurité)
• 6 AWG (16mm²) idéal (moins de perte)

Longueur maximale :
• < 1 mètre : 10 AWG OK
• 1-2 mètres : 8 AWG minimum
• > 2 mètres : 6 AWG obligatoire

Connecteurs :
• Anderson SB175 : jusqu'à 175A (limite basse !)
• Anderson SB350 : jusqu'à 350A ✅ Recommandé
• XT90 : NON (max 90A, insuffisant)
```

---

## 🔍 VÉRIFICATIONS AVANT MISE SOUS TENSION

### Checklist complète

#### ✅ Connexions physiques
- [ ] Tous les connecteurs enfoncés à fond (entendu "clic")
- [ ] Aucun fil dénudé visible (risque court-circuit)
- [ ] Isolation électrique correcte partout
- [ ] Pas de fils tendus (risque déconnexion vibrations)
- [ ] Serre-câbles utilisés (organisation)
- [ ] Connecteurs Hall bien protégés eau/poussière

#### ✅ Contrôleur
- [ ] Bien fixé (dissipateur thermique accessible)
- [ ] Orientation correcte (refroidissement)
- [ ] Pas sur surface conductrice (isoler)
- [ ] Ventilation possible autour
- [ ] Pas d'objets métalliques près des bornes

#### ✅ Batterie
- [ ] Voltage vérifié avec multimètre (devrait être ~72-84V)
- [ ] Polarité correcte (+ rouge, - noir)
- [ ] BMS fonctionnel (LED si présente)
- [ ] Fusible 250A installé
- [ ] Interrupteur sur OFF
- [ ] Connecteurs serrés (10-15 Nm de couple)

#### ✅ Moteur
- [ ] Bien fixé (pas de jeu)
- [ ] Roue libre de tourner
- [ ] Pas d'obstacles (rien ne touche la roue)
- [ ] Phases U,V,W bien connectées
- [ ] Hall sensor bien branché

#### ✅ Sécurité
- [ ] Extincteur à portée
- [ ] Gants isolants prêts
- [ ] Espace dégagé
- [ ] Personne informée présente
- [ ] Portable chargé (appel urgence si besoin)

---

## 🚀 PROCÉDURE DE PREMIER DÉMARRAGE

### Phase 1 : Mise sous tension

```
1. DERNIER CHECK VISUEL
   → Tour complet de toutes les connexions
   
2. POSITION SÉCURISÉE
   → Roue en l'air (ne touche pas le sol)
   → Véhicule stable (béquille, support)
   
3. THROTTLE EN POSITION REPOS
   → Accélérateur complètement relâché
   → Vérifier qu'il revient bien au repos
   
4. BRANCHER BATTERIE
   ├─ Connecter - (noir) en premier
   └─ Connecter + (rouge) en dernier
       → Petite étincelle = NORMAL
       → Grosse étincelle = PROBLÈME → débrancher
   
5. ALLUMER INTERRUPTEUR
   → Passer de OFF à ON
   
6. OBSERVER
   ├─ LED contrôleur : doit s'allumer (vert généralement)
   ├─ Display : doit afficher tension batterie
   ├─ Bips : 1-2 bips normaux de démarrage
   └─ ⚠️ Bips répétés = CODE ERREUR
```

### Phase 2 : Si Code Erreur 7 🔴

```
ARRÊT IMMÉDIAT :
1. Relâcher throttle
2. Éteindre interrupteur
3. Débrancher batterie (+ rouge en premier cette fois)

VÉRIFICATION :
1. Reconnecter capteurs Hall
2. Vérifier configuration app Fardriver
3. Voir guide "DEPANNAGE_RAPIDE_ERREUR_7.md"
4. Réessayer après corrections
```

### Phase 3 : Premier test moteur ✅

```
Si PAS d'erreur :

1. PRÉPARER
   ├─ Roue toujours en l'air
   ├─ Main prête sur interrupteur (coupure urgence)
   └─ Observer le moteur
   
2. TOURNER THROTTLE DOUCEMENT
   ├─ Commencer par 10% seulement
   ├─ Moteur doit démarrer en douceur
   └─ Augmenter progressivement à 30%
   
3. OBSERVER
   ✅ BON :
      • Rotation fluide et silencieuse
      • Pas de vibrations
      • Vitesse proportionnelle au throttle
      • Température normale
      
   ❌ MAUVAIS :
      • Vibrations / à-coups
      • Bruits métalliques
      • Moteur qui cale
      • Surchauffe
      → ARRÊTER → Voir dépannage
   
4. TEST COMPLET
   ├─ Throttle 0% → 100% progressivement
   ├─ Vérifier toute la plage
   └─ Écouter sons anormaux
   
5. TEST FREIN
   ├─ Moteur en rotation (30%)
   ├─ Actionner frein
   └─ Moteur doit s'arrêter immédiatement
```

### Phase 4 : Test au sol (Prudence !) 🚗

```
⚠️ Seulement si test roue-en-l'air = parfait

1. PRÉPARATION
   ├─ Zone dégagée (parking vide)
   ├─ Surface plane
   ├─ Pas de circulation
   └─ Météo sèche
   
2. LIMITES DE SÉCURITÉ
   Dans l'app Fardriver, AVANT test au sol :
   ├─ Limite courant : 50% (100A)
   ├─ Vitesse max : 20 km/h
   └─ Accélération : Douce
   
3. PREMIER ROULAGE
   ├─ Démarrage très lent
   ├─ Accélération progressive
   ├─ Distance : 10-20 mètres seulement
   ├─ Tester frein régénératif
   └─ ARRÊT
   
4. INSPECTION
   Après 1er roulage, arrêt et vérification :
   ├─ Température contrôleur (main proche)
   ├─ Température moteur (chaud = normal, brûlant = problème)
   ├─ Toutes connexions encore bien branchées
   ├─ Pas d'odeur de brûlé
   ├─ Pas de fumée
   └─ Tensions batterie (app ou multimètre)
   
5. TEST PROGRESSIF
   Si inspection OK :
   ├─ Test 2 : 50 mètres
   ├─ Test 3 : 100 mètres
   ├─ Test 4 : 500 mètres
   └─ Inspection entre chaque test
   
6. AUGMENTATION PUISSANCE
   Après 2-3 km sans problème :
   ├─ Augmenter limite courant : 60% → 70% → 80% → 100%
   ├─ Tester sur plusieurs km entre chaque
   ├─ Surveiller températures
   └─ Ajuster selon comportement
```

---

## 🌡️ SURVEILLANCE TEMPÉRATURES

### Températures normales de fonctionnement

```
CONTRÔLEUR FARDRIVER NS24 :
┌────────────────────────────────────┐
│ Repos/faible charge  : 30-40°C ✅  │
│ Usage normal         : 40-60°C ✅  │
│ Usage intense        : 60-80°C ⚠️  │
│ Limite sécurité      : 85°C 🔴    │
│ Protection thermique : 90°C 🚨    │
└────────────────────────────────────┘

MOTEUR QS 5000W :
┌────────────────────────────────────┐
│ Repos                : 30-40°C ✅  │
│ Usage normal         : 50-70°C ✅  │
│ Usage intense        : 70-90°C ⚠️  │
│ Limite sécurité      : 100°C 🔴   │
│ Température max      : 120°C 🚨   │
└────────────────────────────────────┘

BATTERIE LiFePO4 :
┌────────────────────────────────────┐
│ Température idéale   : 20-30°C ✅  │
│ Charge/Décharge OK   : 0-45°C ✅   │
│ Limite haute         : 50°C ⚠️    │
│ Limite critique      : 60°C 🔴    │
└────────────────────────────────────┘
```

### Comment mesurer
```
Contrôleur : 
• App Fardriver (température en temps réel)
• Ou thermomètre infrarouge (radiateur)

Moteur :
• Thermomètre infrarouge (carter moteur)
• App Fardriver (si capteur intégré)

Batterie :
• BMS app Bluetooth (si équipé)
• Thermomètre infrarouge sur boîtier
```

### Que faire si surchauffe

```
CONTRÔLEUR > 85°C :
1. Réduire puissance immédiatement (50%)
2. Rouler doucement jusqu'à < 70°C
3. Vérifier ventilation
4. Ajouter ventilateur si nécessaire

MOTEUR > 100°C :
1. ARRÊT COMPLET
2. Laisser refroidir 15-30 min
3. Vérifier pas de court-circuit phases
4. Réduire courant dans paramètres

BATTERIE > 50°C :
1. Réduire courant (mode eco)
2. Éviter charges rapides
3. Améliorer refroidissement batterie
4. Si > 60°C : ARRÊT et laisser refroidir
```

---

## 🔊 CODES BIPS CONTRÔLEUR

### Signification bips Fardriver

```
DÉMARRAGE NORMAL :
• 1 bip long : Contrôleur OK ✅
• 2 bips courts : Initialisation réussie ✅

CODES ERREUR (bips répétés) :
┌──────────────────────────────────────┐
│ Code │ Bips     │ Signification       │
├──────────────────────────────────────┤
│  1   │ • ••••   │ Sous-tension batterie│
│  2   │ •• •••   │ Sur-tension batterie │
│  3   │ ••• ••   │ Surintensité moteur  │
│  4   │ •••• •   │ Surchauffe contrôleur│
│  5   │ ••••• -  │ Throttle mal calibré │
│  6   │ ••••• •  │ Problème BMS/batterie│
│  7   │ ••••• •• │ Capteurs Hall moteur 🔴│
│  8   │ ••••• •••│ MOSFET endommagé     │
│  9   │ ••••• ••••│ Autre erreur matériel│
└──────────────────────────────────────┘

• = bip court (0.1 sec)
••••• = 5 bips rapides
Puis pause 2 sec, puis répétition
```

### Actions selon code

```
Code 1 (Sous-tension) :
→ Batterie déchargée, recharger

Code 2 (Sur-tension) :
→ Chargeur mal réglé ou BMS défaillant

Code 3 (Surintensité) :
→ Moteur bloqué ou court-circuit
→ Vérifier phases, réduire courant max

Code 4 (Surchauffe) :
→ Améliorer refroidissement contrôleur
→ Réduire courant

Code 5 (Throttle) :
→ Recalibrer dans app Fardriver

Code 6 (BMS) :
→ Vérifier connexions batterie
→ Tester BMS

Code 7 (Hall) 🔴 ← VOTRE PROBLÈME
→ Voir guide dépannage erreur 7

Code 8 (MOSFET) :
→ Composant grillé, réparation nécessaire

Code 9 (Autre) :
→ Contacter support Fardriver
```

---

## ⚠️ SITUATIONS D'URGENCE

### 🚨 ARRÊT D'URGENCE

```
RAISONS D'ARRÊT IMMÉDIAT :
• Fumée visible
• Odeur de brûlé
• Étincelles
• Bruits métalliques forts
• Moteur bloqué
• Vibrations extrêmes
• Surchauffe visible
• Court-circuit

PROCÉDURE :
1. Couper throttle immédiatement
2. Appuyer frein (si accessible)
3. Couper interrupteur principal
4. Si pas d'interrupteur : débrancher batterie
   ├─ Gants isolants
   └─ Débrancher + (rouge) en premier
5. S'éloigner du véhicule
6. Avoir extincteur prêt
7. NE PAS REBRANCHER avant diagnostic complet
```

### 🔥 FEU ÉLECTRIQUE

```
Si feu visible :
1. NE PAS utiliser eau (électrocution + aggrave feu lithium)
2. Utiliser extincteur ABC ou CO₂
3. Si feu batterie lithium :
   ├─ Extincteur peut ne pas suffire
   ├─ Arroser ABONDAMMENT avec sable/terre
   └─ Appeler pompiers
4. Évacuer zone (fumées toxiques)
5. Ne pas approcher avant refroidissement complet (1-2h)
```

### ⚡ ÉLECTROCUTION

```
Si personne touchée par courant :
1. NE PAS toucher la personne directement
2. Couper alimentation en premier
3. Si impossible : utiliser objet isolant (bois sec)
   pour écarter la personne
4. Appeler urgences immédiatement
5. RCP si nécessaire (après coupure courant)
```

---

## 📊 TABLEAU DE DIAGNOSTIC RAPIDE

```
┌──────────────────────────────────────────────────────┐
│ SYMPTÔME          │ CAUSE PROBABLE   │ SOLUTION      │
├──────────────────────────────────────────────────────┤
│ Rien ne s'allume  │ Batterie morte   │ Recharger     │
│                   │ Fusible grillé   │ Remplacer     │
│                   │ Mauvais contact  │ Vérifier      │
├──────────────────────────────────────────────────────┤
│ Code erreur 7     │ Capteur Hall     │ Rebrancher    │
│                   │ Config moteur    │ Régler app    │
├──────────────────────────────────────────────────────┤
│ Moteur vibre      │ Phases inversées │ Inverser 2    │
│                   │ Hall mal réglé   │ Auto-learn    │
├──────────────────────────────────────────────────────┤
│ Moteur surchauffe │ Courant trop fort│ Réduire I max │
│                   │ Court-circuit    │ Vérifier phases│
├──────────────────────────────────────────────────────┤
│ Contrôleur chaud  │ Ventilation      │ Ajouter ventilo│
│                   │ Courant élevé    │ Réduire puis ↑│
├──────────────────────────────────────────────────────┤
│ Perte puissance   │ Batterie faible  │ Recharger     │
│                   │ BMS limitant     │ Check app BMS │
│                   │ Température      │ Refroidir     │
└──────────────────────────────────────────────────────┘
```

---

## ✅ RÉGLAGES POST-INSTALLATION

### Une fois que tout fonctionne

#### 1. Optimisation App Fardriver
```
Mode de conduite :
• Économique : 50% puissance, courbe douce
• Normal : 75% puissance, courbe linéaire
• Sport : 100% puissance, courbe agressive

Freinage régénératif :
• Début : 10% (habituation)
• Optimal : 20-30%
• Maximum : 50% (freinage fort)

Protections :
• Sur-température contrôleur : 85°C
• Sur-température moteur : 100°C
• Sous-tension batterie : 60V (LiFePO4) ou 60V (Li-ion)
• Surintensité : 200A
```

#### 2. Entretien régulier
```
CHAQUE SORTIE :
• Vérifier serrage connecteurs (vibrations)
• Check température après utilisation
• Vérifier voltage batterie

CHAQUE SEMAINE :
• Nettoyer poussière contrôleur
• Vérifier câbles (usure, coupures)
• Graisser connecteurs (si corrosion)

CHAQUE MOIS :
• Équilibrage batterie (laisser sur chargeur 2-3h après pleine charge)
• Vérifier isolation électrique
• Mise à jour firmware contrôleur (si dispo)

CHAQUE 6 MOIS :
• Remplacer connecteurs usés
• Vérifier résistance interne batterie
• Test complet système
```

---

## 📞 SUPPORT & RESSOURCES

### Documentation officielle
- **Fardriver Manual** : fardriver.net/download
- **QS Motor Manual** : Demander au vendeur

### Forums recommandés
- **Endless-Sphere** : Section "Controllers" (anglais)
- **Forums EV locaux** : Selon votre pays

### Vidéos tutoriels
- "Fardriver controller first setup"
- "BLDC motor hall sensor wiring"
- "High power ebike troubleshooting"

---

## 🎯 RÉSUMÉ : CHECKLIST PRÉ-DÉMARRAGE

```
┌─────────────────────────────────────────────────────┐
│ AVANT DE METTRE SOUS TENSION                        │
├─────────────────────────────────────────────────────┤
│ [ ] Toutes connexions vérifiées                     │
│ [ ] Isolation électrique OK                         │
│ [ ] Fusible 250A installé                           │
│ [ ] Interrupteur sur OFF                            │
│ [ ] Roue en l'air (premier test)                    │
│ [ ] Throttle en position repos                      │
│ [ ] Extincteur accessible                           │
│ [ ] Gants isolants prêts                            │
│ [ ] App Fardriver configurée (voir guide config)    │
│ [ ] Multimètre disponible                           │
│ [ ] Zone sécurisée                                  │
│ [ ] Personne informée présente                      │
│                                                     │
│ ✅ TOUT OK → Procéder mise sous tension            │
└─────────────────────────────────────────────────────┘
```

---

**🚀 Bonne chance pour votre premier démarrage !**

*En cas de problème, référez-vous aux guides détaillés :*
- *DEPANNAGE_RAPIDE_ERREUR_7.md*
- *CONFIGURATION_FARDRIVER_NS24.md*
- *GUIDE_BATTERIE_72V_200AH.md*
