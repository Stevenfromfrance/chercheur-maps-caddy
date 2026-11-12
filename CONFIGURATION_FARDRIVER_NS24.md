# Configuration Fardriver NS24 - Premier Démarrage

## Matériel
- **Contrôleur** : Fardriver NS24 (JYD72450_14_A_HA86)
- **Moteur** : QS Motor 872V 5000W
- **Batterie** : 72V 200Ah (recommandée)

## 🔴 Code Erreur 7 - RÉSOLU

### Cause principale
Le code erreur 7 = **Problème capteur Hall moteur**

### Solutions étape par étape

#### ✅ ÉTAPE 1 : Vérifications physiques
1. **Déconnecter la batterie** (sécurité)
2. Vérifier le connecteur Hall (petit connecteur 5 fils) :
   - Rouge = 5V+
   - Noir = GND
   - Jaune, Vert, Bleu = Signaux Hall A, B, C
3. Rebrancher fermement tous les connecteurs
4. Vérifier les 3 gros fils de phase (U, V, W)

#### ✅ ÉTAPE 2 : Configuration Application Fardriver

### Installation App
- **Android** : "Fardriver" sur Google Play
- **iOS** : "Fardriver" sur App Store
- Connecter via Bluetooth au contrôleur

### Paramètres OBLIGATOIRES pour QS Motor 5000W

```
========================================
PARAMÈTRES MOTEUR (Motor Parameters)
========================================
Type de moteur : Brushless DC Motor (BLDC)
Nombre de pôles : 46 pôles (pour QS 5000W)
Capteurs Hall : Activés (60° ou 120° selon moteur)

Puissance nominale : 5000W
Tension nominale : 72V
Courant maximal : 200A (phase : 450A)

========================================
PARAMÈTRES BATTERIE (Battery Parameters)
========================================
Type batterie : Lithium (LiFePO4 ou Li-ion)
Tension nominale : 72V
Tension max charge : 84V (pour 20S Li-ion)
Tension min décharge : 60V (protection décharge)
Courant max batterie : 200A

========================================
PARAMÈTRES THROTTLE (Accélérateur)
========================================
Type : Hall Throttle (accélérateur à effet Hall)
Tension min : 0.8V - 1.2V (position repos)
Tension max : 3.8V - 4.2V (position pleine accélération)

Courbe accélération : Linéaire (pour commencer)
Vitesse max : 100% (ajuster selon besoin)

========================================
PARAMÈTRES PROTECTION
========================================
Protection surchauffe contrôleur : 85°C
Protection surchauffe moteur : 100°C
Protection sous-tension : 60V
Protection surintensité : 200A

Limite courant de démarrage : 50-70% (pour démarrage doux)

========================================
PARAMÈTRES AVANCÉS (Advanced)
========================================
Angle phasage Hall : Auto-détection
  OU essayer : 120° ou 60° selon moteur
  
FOC/Sinusoidal : Désactivé pour premier test
Mode : Speed Mode (mode vitesse)

Freinage régénératif : 10-20% (commencer bas)
```

## 📋 PROCÉDURE DE PREMIER DÉMARRAGE

### 1️⃣ Avant de brancher
- [ ] Tous les connecteurs bien enfoncés
- [ ] Vérifier polarité batterie (+ et -)
- [ ] Contrôleur bien fixé (dissipation chaleur)
- [ ] Moteur bien monté

### 2️⃣ Connexion initiale
1. Brancher les capteurs Hall
2. Brancher les 3 phases moteur (U, V, W)
3. Brancher l'accélérateur (throttle)
4. Brancher le frein (si présent)
5. **EN DERNIER** : Brancher la batterie

### 3️⃣ Configuration App
1. Ouvrir l'app Fardriver
2. Connecter en Bluetooth
3. Aller dans "Parameters"
4. Entrer les valeurs ci-dessus
5. **IMPORTANT** : "Write Parameters" (sauvegarder)
6. Redémarrer le système (débrancher/rebrancher batterie)

### 4️⃣ Test Auto-Learn (Apprentissage Hall)
Certains contrôleurs Fardriver ont une fonction "Hall Auto-Learn" :
1. Dans l'app, chercher "Hall Learn" ou "Motor Learn"
2. Roue en l'air (moteur ne doit pas toucher le sol)
3. Lancer l'apprentissage
4. Le moteur va tourner lentement pour détecter les capteurs
5. Attendre la fin (10-30 secondes)

### 5️⃣ Premier test
1. Roue en l'air
2. Tourner doucement l'accélérateur
3. Le moteur doit tourner en douceur
4. Si vibrations ou bruits bizarres → inverser 2 phases

## 🔧 DÉPANNAGE CODE ERREUR 7

Si l'erreur persiste après configuration :

### Test 1 : Inverser les phases
- Débrancher batterie
- Échanger 2 des 3 fils de phase (exemple : inverser U et V)
- Rebrancher batterie
- Tester

### Test 2 : Changer angle Hall
Dans l'app, essayer les configurations :
- 120° électrique
- 60° électrique
- Auto-détection

### Test 3 : Vérifier tension Hall
Avec un multimètre :
- Fil rouge Hall : devrait avoir 5V
- Fils de signal : 0-5V qui changent quand on tourne le moteur à la main

### Test 4 : Séquence Hall
Dans l'app, vérifier que les 3 capteurs Hall changent d'état quand on tourne le moteur manuellement. Si un capteur ne bouge pas → capteur défectueux.

## 🔋 BATTERIE RECOMMANDÉE 72V 200Ah

### Spécifications requises
- **Tension nominale** : 72V (20S pour Li-ion, 24S pour LiFePO4)
- **Capacité** : 200Ah minimum
- **Décharge continue** : 200A minimum (pour votre contrôleur)
- **BMS requis** : 200A continu minimum
- **Connecteur** : Anderson SB175 ou équivalent (gros courant)

### Options de batterie

#### Option 1 : LiFePO4 (Lithium Fer Phosphate) ⭐ RECOMMANDÉ
```
Configuration : 24S (24 cellules en série)
Tension : 72V nominal (76.8V chargé, 60V déchargé)
Chimie : LiFePO4 3.2V/cellule
Avantages : 
  - Très sûr
  - Longue durée de vie (3000-5000 cycles)
  - Stable en température
Poids : ~100-120 kg pour 200Ah
```

#### Option 2 : Li-ion NMC/NCM
```
Configuration : 20S (20 cellules en série)
Tension : 72V nominal (84V chargé, 60V déchargé)
Chimie : Li-ion 3.6V/cellule
Avantages :
  - Plus léger que LiFePO4
  - Densité énergétique supérieure
Poids : ~70-90 kg pour 200Ah
Attention : Plus sensible aux surcharges
```

### Fournisseurs recommandés (selon localisation)
- **Aliexpress** : Rechercher "72V 200Ah battery pack"
- **QS Motor Store** : Batteries compatibles avec leurs moteurs
- **Fabrication locale** : Assembleur de batteries locales (plus sûr pour garantie)

### Calcul autonomie
```
Énergie batterie = 72V × 200Ah = 14,400 Wh (14.4 kWh)
Consommation moteur 5000W à pleine puissance
Autonomie théorique = 14,400 / 5,000 = 2.88 heures

En usage réel (pas toujours pleine puissance) :
- Usage modéré : 4-6 heures
- Usage léger : 6-10 heures
```

## ⚠️ SÉCURITÉ

### IMPORTANT
1. **Toujours débrancher batterie** avant manipulation
2. **Fusible principal** : 250A minimum entre batterie et contrôleur
3. **Interrupteur d'urgence** : Fortement recommandé
4. **Ventilation** : Contrôleur doit être ventilé (peut chauffer)
5. **Câblage** : Utiliser câbles 10 AWG minimum (6mm²) pour 200A

### Premiers tests
- Commencer avec limite courant à 50%
- Tester roue en l'air d'abord
- Augmenter progressivement la puissance
- Surveiller température contrôleur et moteur

## 📞 SUPPORT

### Ressources Fardriver
- Manuel : Chercher "Fardriver NS24 manual" en ligne
- Forum : Endless-sphere.com (section EV controllers)
- Support : Contact Fardriver via leur site officiel

### Vidéos YouTube utiles
- "Fardriver controller setup"
- "QS Motor installation"
- "E-bike controller hall sensor testing"

---

**Version** : 1.0
**Date** : Novembre 2024
**Pour** : Fardriver NS24 + QS Motor 5000W 72V
