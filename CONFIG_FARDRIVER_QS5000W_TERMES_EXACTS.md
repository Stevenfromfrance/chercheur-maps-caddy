# ⚡ Configuration Fardriver App - QS Motor 5000W
## TERMES EXACTS ANGLAIS de l'App

---

## 🎯 PARAMÈTRES ESSENTIELS (à régler maintenant)

### 📱 Dans l'app Fardriver, aller dans **"Parameters"**

---

## 1️⃣ MOTOR SETTINGS (Paramètres Moteur)

### **ProductCode/SN/ModelType**
```
Product : (Ne pas toucher - lecture seule)
Model Type : ND72450_14_A_H386
Model/Type/Power : 72V/5000W
```

### **Motor Type** (Type de moteur)
```
Sélectionner : BLDC
(Brushless DC Motor)
```

### **Throttle-Response-eLine** (Réponse accélérateur)
```
Valeur recommandée : MaxLineCurrt:200A
```

### **MaxSpeed:21200RPM** (Vitesse max moteur)
```
Laisser : 21200 RPM
(Ne pas modifier)
```

---

## 2️⃣ HALL SENSOR SETTINGS (Capteurs Hall)

### **No Exchange** (Échange des phases)
```
Sélectionner : No Exchange
(Pas d'échange de phase pour commencer)

⚠️ Si moteur vibre/ne démarre pas :
   Essayer : Phase-Exchange
```

### **WeakResponse:0** (Réponse faible)
```
Laisser : 0
```

### **Weak Character-O-Fast** (Caractéristique faible)
```
Sélectionner : Weak Character-O-Fast
```

---

## 3️⃣ BATTERY SETTINGS (Paramètres Batterie)

### **RatedVoltage:72V** (Tension nominale)
```
Régler : 72V
```

### **Motor Direction:010** (Direction moteur)
```
Sélectionner : 010
(Direction normale)

⚠️ Si moteur tourne à l'envers :
   Essayer : 001
```

### **PresSet:0;0;0** (Préréglages)
```
Laisser : 0;0;0
```

### **AngDirect:0**
```
Laisser : 0
```

---

## 4️⃣ SPEED & POWER RATIOS (Vitesses et puissance)

### **Ratios in Speed** (Ratios de vitesse)
```
MiSpeedLineRatio : 50%

Laisser tous les RPM à 0% pour commencer :
- 1000RPM : 100%
- 1600RPM : 80%
- 2000RPM : 80%
- 3000RPM : 60%
- 4000RPM : 53%
- 4500RPM : 48%
- 5000RPM : 44%
- 6500RPM : 35%
- 7000RPM : 1%
- 8000RPM : 0%
- 9000RPM : 0%
- 9500RPM : 0%
- LD-928

LimitSpeed:1350RPM
```

### **Ratios in Gear** (Ratios en vitesse)
```
Laisser comme configuration par défaut
```

---

## 5️⃣ REGENERATIVE BRAKING (Freinage régénératif)

### **Energy/Regenerate**
```
MiSpeedLineRatio : 50%
LotVSpeed:450RPM

Commencer bas :
- 9500RPM : 0%
- 8500RPM : 0%
- 7500RPM : 0%
- 6500RPM : 0%
- 5500RPM : 0%
- 4500RPM : 0%
- 3500RPM : 0%
- 2500RPM : 0%
- 1500RPM : 0%
- 500RPM : 0%
```

**Plus tard, augmenter progressivement à 10-20%**

---

## 6️⃣ FUNCTIONS & PROTECTIONS (Fonctions et protections)

### **Brake-On-SmoothvsGround**
```
Sélectionner selon type de frein :
- Si frein électronique : On
- Si frein mécanique : Ground
```

### **FollowOI-FD-Disabled**
```
Sélectionner : FD-Disabled
(Désactivé pour commencer)
```

### **Cruise-Pim-8-4NT7**
```
Laisser : défaut
(Régulateur de vitesse)
```

### **SpdStart-Pim** (Démarrage vitesse)
```
Laisser : défaut
```

### **Phase-Pim-O-NC** (Phase)
```
Sélectionner : O-NC
```

### **Backward-Pim-O-PN8**
```
Laisser : défaut
(Marche arrière)
```

### **Lowspeed-Pim-i--PN2**
```
Laisser : défaut
```

### **Forward-Pim-3-Invalid**
```
Laisser : défaut
```

### **H-Speed-Pim-2-PIN3** (Haute vitesse)
```
Laisser : défaut
```

---

## 7️⃣ PROTECTION SETTINGS (Paramètres de protection)

### **Charge-Pim-13-Invalid**
```
Laisser : Invalid
(Charge désactivée)
```

### **Switch-Invalid** (Interrupteur)
```
Laisser : Invalid
```

### **Shut-Pim-9-Invalid**
```
Laisser : Invalid
```

### **BoostTime: 4S** (Temps boost)
```
Laisser : 4S
```

### **HighNoSpeed:**
```
Laisser : défaut
```

### **THuntSpeed:**
```
Laisser : défaut
```

### **Emundum : 0**
```
Laisser : 0
```

---

## 8️⃣ DETECTION & START (Détection et démarrage)

### **Gear-Default : 0**
```
Laisser : 0
```

### **Brake-On-SmoothvsGround**
```
Selon installation :
- Smooth : Freinage doux
- Ground : Freinage normal
```

### **PN2-Disabled**
```
Laisser : Disabled
```

---

## 🔧 HALL SENSOR AUTO-LEARN (IMPORTANT!)

### Après avoir réglé tous les paramètres ci-dessus :

```
1. Chercher fonction "Hall Learn" ou "Motor Learn"
   (Peut être dans menu "Functions" ou "Settings")

2. ⚠️ ROUE EN L'AIR obligatoire

3. Cliquer "Start Learning"

4. Moteur va tourner lentement 10-30 secondes

5. Attendre "Learning Complete"

6. Redémarrer système
```

---

## 💾 SAUVEGARDER LES PARAMÈTRES

### **TRÈS IMPORTANT !**

```
1. Après avoir modifié les paramètres :
   Cliquer bouton "Save" ou "Write Parameters"

2. Attendre confirmation (bip ou message)

3. Éteindre système (OFF)

4. Débrancher batterie 30 secondes

5. Rebrancher batterie

6. Allumer système (ON)

7. Tester
```

---

## ✅ CHECKLIST RAPIDE

Cochez au fur et à mesure dans l'app :

### Paramètres de base
- [ ] **Motor Type** : BLDC
- [ ] **RatedVoltage** : 72V
- [ ] **MaxLineCurrt** : 200A
- [ ] **MaxSpeed** : 21200RPM
- [ ] **Motor Direction** : 010

### Hall & Phase
- [ ] **No Exchange** ou **Phase-Exchange** (selon test)
- [ ] **WeakResponse** : 0
- [ ] **Weak Character-O-Fast** sélectionné

### Vitesse
- [ ] **MiSpeedLineRatio** : 50%
- [ ] **LimitSpeed** : 1350RPM
- [ ] Tous les ratios configurés

### Protections
- [ ] **Brake-On-Smooth** ou **Ground** sélectionné
- [ ] **FollowOI-FD** : Disabled
- [ ] Autres fonctions laissées par défaut

### Final
- [ ] **Hall Auto-Learn** effectué
- [ ] Paramètres sauvegardés ("Save")
- [ ] Système redémarré (OFF/ON)
- [ ] Test roue en l'air OK

---

## 🚨 SI ÇA NE MARCHE PAS

### Erreur 7 persiste ?

**1. Vérifier Hall Sensor (connecteur 5 fils)**
```
- Débrancher
- Nettoyer
- Rebrancher fermement (CLIC)
```

**2. Essayer Phase Exchange**
```
Dans app :
No Exchange → Changer pour → Phase-Exchange
Sauvegarder et tester
```

**3. Essayer Motor Direction différent**
```
Dans app :
Motor Direction : 010 → Changer pour → 001
Sauvegarder et tester
```

**4. Inverser 2 des 3 phases moteur (gros câbles)**
```
⚠️ Débrancher batterie d'abord !
Échanger U et V (ou V et W)
Rebrancher batterie
Tester
```

---

## 📊 VALEURS PAR DÉFAUT RECOMMANDÉES

### Pour QS Motor 5000W 72V

```
┌─────────────────────────────────────┐
│ PARAMÈTRE         │ VALEUR          │
├─────────────────────────────────────┤
│ Motor Type        │ BLDC            │
│ RatedVoltage      │ 72V             │
│ MaxLineCurrt      │ 200A            │
│ MaxSpeed          │ 21200RPM        │
│ Motor Direction   │ 010             │
│ No Exchange       │ Oui (défaut)    │
│ WeakResponse      │ 0               │
│ MiSpeedLineRatio  │ 50%             │
│ LimitSpeed        │ 1350RPM         │
│ Brake             │ Smooth/Ground   │
│ FollowOI-FD       │ Disabled        │
└─────────────────────────────────────┘
```

---

## 🎯 ORDRE DE CONFIGURATION

**Suivez cet ordre exactement :**

```
1. Motor Type → BLDC
2. RatedVoltage → 72V
3. MaxLineCurrt → 200A
4. Motor Direction → 010
5. No Exchange → Oui
6. WeakResponse → 0
7. MiSpeedLineRatio → 50%
8. LimitSpeed → 1350RPM
9. Brake-On-Smooth → Selon installation
10. FollowOI-FD → Disabled
11. SAUVEGARDER ("Save")
12. HALL AUTO-LEARN
13. SAUVEGARDER encore
14. Redémarrer (OFF/ON)
15. TESTER roue en l'air
```

---

## 📱 NAVIGATION DANS L'APP

### Menu principal
```
Restore → Ne pas toucher
Save → CLIQUER après chaque modification
Return Simple Mode → Pour revenir
```

### Sections importantes
```
Parameters → Tous les réglages
Functions → Hall Learn, protections
Ratios in Speed → Vitesses et puissance
Ratios in Gear → Rapports de vitesse
Energy/Regenerate → Freinage régénératif
```

---

## ⚡ TEST FINAL

### Après configuration complète

```
1. Roue en l'air
2. Batterie branchée
3. Système ON
4. Tourner throttle doucement
5. ✅ Moteur tourne en douceur = OK !
6. ❌ Vibrations/bruits = Voir dépannage
```

---

## 💪 C'EST PARTI !

**Utilisez exactement ces termes anglais** pour ne pas vous perdre dans l'app !

**Temps estimé configuration : 15-20 minutes**

---

**Questions ? Problème ?**
- Prendre photo de l'écran problématique
- Me montrer quelle valeur ne fonctionne pas
- Je vous aide en temps réel !

🎉 **Bonne configuration !**
