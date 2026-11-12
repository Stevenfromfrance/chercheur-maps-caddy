# ⚡ SOLUTION RAPIDE - Erreur 7 (Français)

## 🔴 Votre problème : Contrôleur Fardriver bipe code erreur 7

### Qu'est-ce que l'erreur 7 ?
**Erreur 7 = Problème capteurs Hall du moteur**

Les capteurs Hall sont 5 petits fils qui vont du moteur au contrôleur.

---

## ✅ SOLUTION EN 5 ÉTAPES (15 MINUTES)

### Étape 1 : SÉCURITÉ ⚠️
```
1. Débrancher la batterie (câble rouge + en premier)
2. Attendre 30 secondes
3. Mettre gants isolants
```

### Étape 2 : VÉRIFIER CONNECTEUR HALL 🔌

**Trouver le connecteur Hall :**
- Petit connecteur avec **5 fils fins**
- Entre le moteur et le contrôleur
- Couleurs typiques : Rouge, Noir, Jaune, Vert, Bleu

**Action :**
```
1. Débrancher le connecteur (tirer doucement)
2. Regarder s'il y a :
   • Eau / humidité → Sécher avec air comprimé
   • Corrosion → Nettoyer avec alcool
   • Fils coupés → Réparer/souder
3. Rebrancher fermement (doit faire "CLIC")
4. S'assurer qu'il est BIEN enfoncé
```

**⚠️ 80% des erreurs 7 sont résolues à cette étape !**

### Étape 3 : REBRANCHER BATTERIE 🔋
```
1. Brancher câble noir (-) en premier
2. Brancher câble rouge (+) en second
3. Petite étincelle = NORMAL
4. Allumer système
```

**✅ Si ça marche → TERMINÉ !**  
**❌ Si erreur 7 persiste → Passer étape 4**

---

### Étape 4 : CONFIGURATION APP FARDRIVER 📱

**A. Télécharger l'application**

**Android :**
1. Ouvrir Google Play Store
2. Chercher "Fardriver"
3. Installer

**iPhone :**
1. Ouvrir App Store
2. Chercher "Fardriver"  
3. Installer

**B. Se connecter au contrôleur**
```
1. Activer Bluetooth sur téléphone
2. Ouvrir app Fardriver
3. Cliquer "Scan" ou icône Bluetooth
4. Chercher "Fardriver-XXXX"
5. Cliquer pour connecter
6. Mot de passe (si demandé) : 1234 ou 0000
```

**C. Configuration moteur QS 5000W**

Aller dans **"Parameters"** ou **"Paramètres"** :

```
┌─────────────────────────────────────┐
│ PARAMÈTRES À RÉGLER                 │
├─────────────────────────────────────┤
│ Motor Type (Type moteur)            │
│ → Sélectionner : BLDC               │
│                                     │
│ Motor Poles (Pôles moteur)          │
│ → Entrer : 46                       │
│                                     │
│ Hall Sensors (Capteurs Hall)        │
│ → Activer : ON / Enabled            │
│                                     │
│ Hall Angle (Angle Hall)             │
│ → Sélectionner : 120° électrique    │
│   (ou "Auto" si disponible)         │
│                                     │
│ Rated Voltage (Tension)             │
│ → 72V                               │
│                                     │
│ Max Current (Courant max)           │
│ → 200A                              │
└─────────────────────────────────────┘
```

**D. IMPORTANT - Sauvegarder**
```
1. Cliquer "Write Parameters" ou "Sauvegarder"
2. Attendre confirmation (bip ou message)
3. Éteindre système (interrupteur OFF)
4. Débrancher batterie 30 secondes
5. Rebrancher batterie
6. Rallumer système
```

---

### Étape 5 : AUTO-APPRENTISSAGE HALL (Si disponible) 🤖

**Dans l'app Fardriver, chercher :**
- "Hall Learn" ou "Hall Learning"
- "Motor Learn"
- "Self-Learn"

**Si trouvé :**
```
1. ⚠️ IMPORTANT : Roue en l'air (ne touche pas le sol)
2. Véhicule bien stable
3. Dans l'app : Cliquer "Start Learning" ou "Démarrer"
4. Le moteur va tourner lentement 10-30 secondes
5. Attendre message "Learning Complete" ou "Terminé"
6. Redémarrer système (OFF/ON)
```

**Test final :**
```
1. Roue toujours en l'air
2. Tourner accélérateur doucement
3. ✅ Moteur tourne en douceur = RÉSOLU !
4. ❌ Vibrations/bruits = Voir solutions avancées
```

---

## 🔧 SOLUTIONS AVANCÉES (Si erreur persiste)

### Solution A : Inverser les phases moteur

**Les 3 GROS fils du moteur (U, V, W) :**
```
1. Débrancher batterie
2. Repérer les 3 connecteurs de phase (gros fils)
3. Échanger 2 des 3 connecteurs
   Exemple : 
   • Avant : U→U, V→V, W→W
   • Après : U→V, V→U, W→W (échanger U et V)
4. Rebrancher batterie
5. Tester
```

### Solution B : Essayer angle Hall différent

**Dans l'app Fardriver :**
```
Essayer dans cet ordre :
1. Hall Angle : 120° ✅ (essayer d'abord)
2. Hall Angle : 60°
3. Hall Angle : Auto-détection

Entre chaque :
• Sauvegarder ("Write Parameters")
• Redémarrer système
• Tester
```

### Solution C : Vérifier avec multimètre

**Si vous avez un multimètre :**
```
Test alimentation Hall :
1. Mode DC Voltage (tension continue)
2. Positif (rouge) → Fil rouge Hall
3. Négatif (noir) → Fil noir Hall
4. Résultat attendu : 5V ± 0.2V
   ❌ Si 0V → Problème alimentation contrôleur

Test signaux Hall :
1. Même configuration
2. Tester fils Jaune, Vert, Bleu (un par un vs noir)
3. Tourner moteur à la main lentement
4. Chaque fil doit alterner : 0V → 5V → 0V → 5V
   ❌ Si un fil ne bouge pas → Capteur Hall moteur défectueux
```

---

## 📞 TOUJOURS BLOQUÉ ?

### Causes possibles restantes :

**1. Capteur Hall dans le moteur est cassé**
- Solution : Ouvrir moteur et remplacer carte Hall
- Ou : Utiliser mode "Sensorless" (sans capteurs)
- Coût réparation : 50-100 USD

**2. Câblage personnalisé incorrect**
- Vérifier ordre fils Hall (rouge, noir, jaune, vert, bleu)
- Comparer avec manuel moteur

**3. Contrôleur pas compatible**
- Vérifier compatibilité Fardriver NS24 avec QS Motor
- Contacter vendeur contrôleur

**4. Problème matériel contrôleur**
- Rare mais possible
- Tester avec autre moteur (si disponible)
- Garantie contrôleur ?

---

## 📋 RÉCAPITULATIF - ORDRE D'ACTION

```
✅ 1. Débrancher batterie
✅ 2. Vérifier connecteur Hall (5 fils)
✅ 3. Rebrancher fermement
✅ 4. Rebrancher batterie
✅ 5. Tester → Si erreur persiste :
✅ 6. Installer app Fardriver
✅ 7. Configurer moteur (BLDC, 46 pôles, Hall 120°)
✅ 8. Sauvegarder et redémarrer
✅ 9. Hall Auto-Learn (si dispo)
✅ 10. Tester roue en l'air → Si erreur persiste :
✅ 11. Inverser 2 phases moteur
✅ 12. Tester angle Hall différents
✅ 13. Vérifier avec multimètre
```

---

## 🎯 AIDE SUPPLÉMENTAIRE

### Documents détaillés (français/anglais) :

1. **DEPANNAGE_RAPIDE_ERREUR_7.md** (plus détaillé)
2. **CONFIGURATION_FARDRIVER_NS24.md** (tous paramètres)
3. **CABLAGE_SECURITE_PREMIER_DEMARRAGE.md** (câblage complet)
4. **README_SYSTEME_72V.md** (vue d'ensemble système)

### Forums en ligne :
- **Endless-Sphere.com** : Forum anglais, très actif
  Rechercher : "Fardriver error 7"
  
- **Groupes Facebook** : Chercher groupes véhicules électriques locaux

### YouTube :
- Rechercher : "Fardriver error 7 fix"
- Rechercher : "Hall sensor troubleshooting ebike"

---

## ⚡ RÉSULTAT ATTENDU

Une fois résolu, vous devriez avoir :
```
✅ Plus de bips d'erreur
✅ Moteur démarre en douceur
✅ Pas de vibrations
✅ Accélération proportionnelle
✅ Températures normales
```

---

## 🚨 SÉCURITÉ RAPPEL

```
⚠️ 72V peut être MORTEL
• Toujours débrancher batterie avant manipulation
• Porter gants isolants
• Ne jamais toucher bornes avec mains humides
• Avoir extincteur à portée
• Premiers tests : roue en l'air
```

---

## 💪 BON COURAGE !

**L'erreur 7 se résout dans 90% des cas avec ces étapes.**

La plupart du temps, c'est juste le connecteur Hall qui est mal branché ou sale.

**Ne pas se décourager !**

---

**Questions ? Besoin d'aide ?**
- Consulter les guides détaillés dans ce dossier
- Poster sur forums avec photos
- Contacter support Fardriver

**🎉 Bonne réparation !**
