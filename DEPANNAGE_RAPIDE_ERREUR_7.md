# 🚨 DÉPANNAGE RAPIDE - Code Erreur 7 Fardriver

## ⚡ SOLUTION RAPIDE (5 minutes)

### Étape 1 : Débrancher la batterie ✅
**TOUJOURS commencer par débrancher la batterie pour sécurité**

### Étape 2 : Vérifier connecteur Hall 🔌
Le petit connecteur avec 5 fils (Hall sensor) :
```
📍 Position : Entre le moteur et le contrôleur
🔴 Rouge  = 5V+
⚫ Noir   = GND (masse)
🟡 Jaune = Hall A
🟢 Vert  = Hall B
🔵 Bleu  = Hall C
```

**Actions** :
1. Débrancher le connecteur Hall
2. Vérifier qu'aucun fil n'est coupé
3. Vérifier qu'il n'y a pas d'eau ou corrosion
4. **Rebrancher fermement** en entendant le "clic"

### Étape 3 : Rebrancher et tester 🔋
1. Rebrancher la batterie
2. Mettre le contact
3. **Si encore erreur 7** → Passer à l'étape 4

### Étape 4 : Application Fardriver 📱

#### A. Télécharger l'app
- Android : "Fardriver" (Google Play)
- iOS : "Fardriver" (App Store)

#### B. Connecter en Bluetooth
1. Ouvrir l'app
2. Activer Bluetooth
3. Chercher "Fardriver-XXXX"
4. Connecter (mot de passe par défaut : 1234 ou 0000)

#### C. Configuration moteur QS 5000W
```
┌─────────────────────────────────────┐
│ PARAMÈTRES ESSENTIELS               │
├─────────────────────────────────────┤
│ Type moteur  : BLDC (Brushless DC)  │
│ Pôles moteur : 46 poles             │
│ Hall sensors : Enabled (Activé)     │
│ Hall angle   : 120° (ou Auto)       │
│                                      │
│ Voltage      : 72V                  │
│ Max current  : 200A                 │
│ Power        : 5000W                │
└─────────────────────────────────────┘
```

#### D. Sauvegarder
- Cliquer "Write Parameters" ou "Save"
- **Redémarrer** : Débrancher/rebrancher batterie

### Étape 5 : Auto-Learn Hall (Si disponible) 🤖
```
Dans l'app Fardriver :
1. Chercher "Hall Learn" ou "Motor Learn"
2. ⚠️ ROUE EN L'AIR (moteur ne touche pas le sol)
3. Appuyer "Start Learning"
4. Le moteur tourne lentement 10-30 sec
5. Attendre "Learning Complete"
6. Redémarrer système
```

### Étape 6 : Test final 🎯
1. Roue en l'air
2. Tourner l'accélérateur doucement
3. ✅ Moteur tourne = RÉSOLU !
4. ❌ Vibrations/bruits = Passer à solution avancée

---

## 🔧 SOLUTIONS AVANCÉES (si erreur persiste)

### Solution A : Inverser les phases moteur
```
Les 3 GROS fils qui vont au moteur (U, V, W) :

┌─────────────────────────────┐
│ AVANT          │  APRÈS     │
├─────────────────────────────┤
│ Contrôleur → Moteur         │
│   U → U        │   U → V    │ ← ÉCHANGER
│   V → V        │   V → U    │ ← ÉCHANGER  
│   W → W        │   W → W    │ ← LAISSER
└─────────────────────────────┘
```

**Procédure** :
1. Débrancher batterie
2. Échanger 2 des 3 connecteurs de phase
3. Rebrancher batterie
4. Tester

### Solution B : Tester angle Hall différent
Dans l'app, essayer dans cet ordre :
1. **120° électrique** (standard pour QS Motor)
2. 60° électrique
3. Auto-détection

Entre chaque test : sauvegarder et redémarrer

### Solution C : Vérifier tension Hall avec multimètre ⚡
```
Multimètre en mode tension DC (Volt) :

Test fil rouge (5V+) :
  Positif multimètre → Fil rouge Hall
  Négatif multimètre → Fil noir Hall (GND)
  Résultat attendu : 5V ± 0.2V
  
Test signaux Hall :
  En tournant le moteur à la main :
  Chaque fil Hall (Jaune, Vert, Bleu) doit alterner entre 0V et 5V
  
❌ Si un signal ne bouge pas → Capteur Hall défectueux dans le moteur
```

### Solution D : Séquence Hall
Dans l'app Fardriver, aller dans "Hall Status" ou "Motor Status" :
- Tourner le moteur à la main lentement
- Observer les 3 capteurs (A, B, C)
- Ils doivent changer d'état en séquence : 
  ```
  Hall A: HIGH → LOW → HIGH
  Hall B: HIGH → LOW → HIGH  
  Hall C: HIGH → LOW → HIGH
  (pas en même temps, en décalé)
  ```

❌ Si séquence incorrecte → Problème câblage ou capteurs

---

## 📋 CHECKLIST COMPLÈTE

Cochez au fur et à mesure :

### Connexions physiques
- [ ] Connecteur Hall bien branché (entendu le "clic")
- [ ] Les 3 fils de phase bien connectés
- [ ] Pas de fils endommagés ou coupés
- [ ] Batterie 72V bien chargée (tension > 70V)
- [ ] Tous les connecteurs propres (pas d'eau/corrosion)

### Configuration App
- [ ] App Fardriver installée
- [ ] Connecté en Bluetooth au contrôleur  
- [ ] Type moteur : BLDC
- [ ] Pôles : 46
- [ ] Hall activés
- [ ] Angle Hall : 120° (ou testé 60° et Auto)
- [ ] Paramètres sauvegardés ("Write Parameters")
- [ ] Système redémarré après sauvegarde

### Tests
- [ ] Hall Auto-Learn effectué (si disponible)
- [ ] Test roue en l'air réussi
- [ ] Pas de vibrations ni bruits anormaux
- [ ] Inversion phases testée (si nécessaire)
- [ ] Températures contrôleur/moteur normales

---

## ❓ TOUJOURS ERREUR 7 ?

### Causes possibles restantes :

1. **Capteur Hall défectueux dans le moteur**
   - Solution : Remplacer la carte Hall du moteur
   - Ou : Passer en mode "Sensorless" (sans capteurs)
   
2. **Contrôleur pas compatible avec ce moteur**
   - Vérifier compatibilité Fardriver NS24 avec QS 5000W
   - Contacter support Fardriver

3. **Problème matériel contrôleur**
   - Tester avec un autre moteur (si possible)
   - Si même erreur → Contrôleur défectueux
   
4. **Câblage personnalisé incorrect**
   - Vérifier schéma de câblage original
   - Comparer avec manuel Fardriver

---

## 📞 AIDE SUPPLÉMENTAIRE

### Forums utiles (en anglais)
- **Endless-Sphere** : endless-sphere.com/forums
  Section "E-bike Technical"
  Beaucoup d'experts Fardriver et QS Motor

- **ElectricBike.com Forum**
  Section "Controllers and Electronics"

### Recherches YouTube
- "Fardriver error 7 fix"
- "Hall sensor testing ebike motor"  
- "QS Motor setup Fardriver"
- "BLDC motor hall sensor troubleshooting"

### Contact Fardriver
- Site web : fardriver.net
- Email support (check leur site)
- WeChat : Si vous avez accès (support en chinois/anglais)

---

## ✅ SUCCÈS ?

Une fois que ça marche :

### Réglages fins recommandés
1. **Limite courant démarrage** : 50-70% (démarrage doux)
2. **Freinage régénératif** : Commencer à 10-20%
3. **Vitesse max** : Limiter à 80% pour premiers tests
4. **Courbe accélération** : Linéaire pour commencer

### Surveillance
- Température contrôleur (ne doit pas dépasser 80°C)
- Température moteur (< 100°C)
- Tensions batterie
- Courant consommé

### Ajustements progressifs
- Augmenter limites progressivement
- Tester sur terrain plat d'abord
- Puis pentes et charge

---

**🎉 Bonne chance ! Le code erreur 7 est résolu dans 90% des cas avec ces étapes.**
