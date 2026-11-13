# Guide de Câblage - Contrôleur Jiangsu Pardriver NS24 pour WDJ 1500W 72V

## Informations du Contrôleur

**Modèle:** Jiangsu Pardriver NS24  
**Référence:** DN72450_14_A_HA86  
**Tension nominale:** 72V  
**Courant ligne/phase:** 200A/450A  
**Type:** Contrôleur de moteur brushless (BLDC)  

---

## 🔴 CONNEXIONS PRINCIPALES SUR LE CONTRÔLEUR

### Bornes à vis colorées (Alimentation et Moteur)

| Couleur | Étiquette | Fonction | Câble à connecter |
|---------|-----------|----------|-------------------|
| **🔵 BLEU** | W | Phase W du moteur | Fil bleu du moteur |
| **🟢 VERT** | V | Phase V du moteur | Fil vert du moteur |
| **🟡 JAUNE** | U | Phase U du moteur | Fil jaune du moteur |
| **⚫ NOIR** | B− | Négatif batterie (GND) | Câble noir épais de la batterie |
| **🔴 ROUGE** | B+ | Positif batterie (72V+) | Câble rouge épais de la batterie |

⚠️ **Polarité FarDriver standard:**
- Terminal **ROUGE (B+)** = +72V
- Terminal **NOIR (B−)** = Masse/GND

---

## 🔌 CONNECTEURS DU FAISCEAU

### 1. **CONNECTEUR PRINCIPAL (Grand connecteur noir rectangulaire)**

Ce connecteur se branche sur le port principal du contrôleur. Il contient tous les signaux de contrôle.

**Fonctions typiques (à vérifier avec multimètre):**

| Couleur du fil | Fonction probable |
|----------------|-------------------|
| Rouge épais | +72V alimentation |
| Noir épais | Masse (GND) |
| Rouge fin | +5V ou +12V accessoires |
| Noir fin | Masse signal |
| Vert | Signal accélérateur (Throttle) |
| Bleu | Signal frein avant |
| Jaune | Signal frein arrière |
| Blanc | Vitesse/Hall sensor |
| Orange | Communication/Data |
| Rose/Violet | Éclairage/Feu arrière |
| Gris | Interrupteur contact/démarrage |

---

### 2. **CONNECTEUR À 2 FILS (Blanc, avec fils Bleu et Rouge)**

**Fonction:** Capteur de frein (Brake switch)

| Fil | Fonction |
|-----|----------|
| Bleu | Signal frein |
| Rouge | +5V ou masse |

**Connexion:** Interrupteur de frein (avant ou arrière)
- Quand le frein est actionné, le circuit se ferme
- Coupe l'alimentation du moteur pour la sécurité

---

### 3. **CONNECTEUR À 3 FILS (Blanc, avec fils Jaune, Noir, Orange)**

**Fonction:** Accélérateur (Throttle) ou capteur Hall

**Option A - Si c'est l'accélérateur:**

| Fil | Fonction |
|-----|----------|
| Rouge/Orange | +5V alimentation |
| Noir | Masse (GND) |
| Jaune | Signal variable (0-5V) |

**Option B - Si c'est un capteur Hall moteur:**

| Fil | Fonction |
|-----|----------|
| Rouge/Orange | +5V alimentation |
| Noir | Masse (GND) |
| Jaune | Signal Hall |

---

### 4. **CONNECTEUR À 2 FILS (Petit blanc, fils Violet et Bleu)**

**Fonction:** Deuxième capteur de frein ou interrupteur

| Fil | Fonction |
|-----|----------|
| Violet | Signal |
| Bleu | Masse ou +5V |

---

### 5. **CONNECTEUR LARGE BLANC (6-9 broches)**

**Fonction:** Écran LCD / Tableau de bord

| Position | Fonction probable |
|----------|-------------------|
| 1 | +12V ou +5V |
| 2 | Masse (GND) |
| 3 | RX (Réception données) |
| 4 | TX (Transmission données) |
| 5 | Bouton + |
| 6 | Bouton - |
| 7 | Bouton mode |
| 8 | Rétroéclairage |

---

### 6. **CONNECTEUR ROUGE (2-3 broches)**

**Fonction:** Feux / Accessoires 12V

| Fil | Fonction |
|-----|----------|
| Rouge | +12V accessoires |
| Noir | Masse |

**Peut alimenter:**
- Phare avant
- Feu arrière
- Klaxon
- Clignotants

---

### 7. **CONNECTEUR GRIS (2-4 broches)**

**Fonction:** Interrupteur de contact (contacteur à clé)

| Fil | Fonction |
|-----|----------|
| Noir | Masse |
| Rouge | +12V contact |
| Cyan/Bleu | Signal ON/OFF |
| Rose | Verrouillage moteur |

---

## 📋 PROCÉDURE DE CONNEXION POUR VOTRE WDJ 1500W 72V

### Étape 1: Connexions de puissance (FAIRE EN DERNIER!)

1. ⚠️ **DÉBRANCHER LA BATTERIE D'ABORD**
2. Connecter le fil épais de la batterie **+72V (ROUGE)** au terminal **NOIR (+B)** du contrôleur
3. Connecter le fil épais de la batterie **GND (NOIR)** au terminal **ROUGE (-)** du contrôleur
4. Serrer fermement les vis (couple de serrage élevé)
5. Isoler les connexions avec du ruban isolant haute tension

### Étape 2: Connexions moteur

1. Brancher les 3 fils du moteur sur les bornes colorées:
   - **BLEU** du moteur → Terminal **BLEU (B)**
   - **JAUNE** du moteur → Terminal **JAUNE (U)**
   - **VERT** du moteur → Terminal **VERT (V)**

⚠️ Si le moteur tourne dans le mauvais sens, inverser 2 fils parmi les 3.

### Étape 3: Connecteur principal

1. Brancher le grand connecteur rectangulaire noir sur le contrôleur

### Étape 4: Capteurs Hall du moteur

Si votre moteur a des capteurs Hall (petits fils sortant du moteur):
1. Identifier le connecteur à 5-6 fils (typiquement: Rouge, Noir, Jaune, Vert, Bleu)
2. Le brancher sur le connecteur Hall correspondant du contrôleur

### Étape 5: Accélérateur (Throttle)

1. Connecteur à 3 fils de l'accélérateur:
   - **Rouge** = +5V
   - **Noir** = Masse
   - **Vert/Jaune** = Signal

### Étape 6: Freins

1. Brancher les 2 connecteurs de frein:
   - Un pour le frein avant
   - Un pour le frein arrière

### Étape 7: Écran / Tableau de bord

1. Brancher le connecteur large blanc à l'écran LCD
2. Vérifier l'affichage au démarrage

### Étape 8: Tests de sécurité

1. Vérifier toutes les connexions
2. Rebrancher la batterie
3. Mettre le contact
4. Vérifier l'écran LCD
5. Tester les freins (le moteur doit se couper)
6. Tester l'accélérateur doucement

---

## 🔧 IDENTIFICATION DES FILS AVEC MULTIMÈTRE

### Pour identifier les fils inconnus:

**Position du multimètre:** Mode voltmètre DC

1. **Masse/GND:** Toujours à 0V par rapport à la batterie négative
2. **+5V:** 5 volts par rapport à la masse (pour capteurs)
3. **+12V:** 12 volts par rapport à la masse (pour accessoires)
4. **+72V:** Tension de la batterie (DANGER!)
5. **Signaux:** Varient entre 0-5V selon l'action

### Test de l'accélérateur:

1. Mesurer la tension sur le fil de signal (généralement vert ou jaune)
2. Au repos: 0.8-1V
3. Plein gaz: 4-4.5V
4. Si ces valeurs correspondent, c'est bien l'accélérateur

### Test des freins:

1. Mesurer la continuité entre les 2 fils
2. Frein relâché: Circuit ouvert (∞ Ω)
3. Frein serré: Circuit fermé (0 Ω)

---

## ⚠️ PRÉCAUTIONS DE SÉCURITÉ

### AVANT DE BRANCHER LA BATTERIE:

- ✅ Vérifier toutes les connexions
- ✅ S'assurer qu'aucun fil ne touche le châssis métallique
- ✅ Isoler les connexions haute tension
- ✅ Vérifier la polarité (+/- ATTENTION À L'INVERSION!)
- ✅ Mettre un fusible 200A sur le fil positif de la batterie

### PENDANT LES TESTS:

- ⚠️ Surélever la roue arrière (aucun contact avec le sol)
- ⚠️ Porter des gants isolants
- ⚠️ Ne pas toucher les bornes de puissance sous tension
- ⚠️ Avoir un interrupteur d'urgence accessible
- ⚠️ Commencer avec des tests à basse vitesse

### PROBLÈMES COURANTS:

| Problème | Cause probable | Solution |
|----------|----------------|----------|
| Moteur ne tourne pas | Pas de signal accélérateur | Vérifier le connecteur throttle |
| Moteur saccade | Sens des phases incorrect | Inverser 2 fils moteur |
| Moteur tourne dans le mauvais sens | Phases inversées | Échanger 2 fils parmi les 3 |
| Écran ne s'allume pas | Pas d'alimentation | Vérifier le connecteur d'écran |
| Frein ne coupe pas le moteur | Frein mal branché | Vérifier les connecteurs de frein |
| Erreur "Hall sensor" | Capteurs Hall défectueux | Vérifier le connecteur à 5 fils |

---

## 📸 PHOTOS DE RÉFÉRENCE

Voir les photos fournies pour identifier visuellement:
- Le contrôleur et ses bornes
- Les différents connecteurs
- Les couleurs de fils
- Les positions de branchement

---

## 🛠️ PROCHAINES ÉTAPES

1. **Identifier chaque connecteur** en comparant avec ce guide
2. **Prendre des photos** de votre faisceau WDJ actuel
3. **Noter les couleurs** et positions de chaque fil
4. **Tester avec multimètre** avant de brancher
5. **Adapter les connecteurs** si nécessaire (soudure + gaine thermo)
6. **Tester progressivement** chaque fonction

---

## 📞 BESOIN D'AIDE?

Si vous avez besoin d'identifier un connecteur spécifique:
1. Prenez une photo claire du connecteur
2. Comptez le nombre de fils et notez leurs couleurs
3. Mesurez les tensions avec un multimètre
4. Comparez avec ce guide

---

**Date de création:** 8 novembre 2026  
**Version:** 1.0  
**Compatible avec:** WDJ 1500W 72V + Contrôleur Jiangsu Pardriver NS24
