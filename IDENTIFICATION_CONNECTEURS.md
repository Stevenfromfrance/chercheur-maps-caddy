# Identification Visuelle des Connecteurs - Votre Faisceau

## 🔍 ANALYSE DES PHOTOS

Basé sur vos photos, voici l'identification précise de chaque connecteur visible:

---

## CONNECTEUR 1: Petit connecteur blanc à 2 fils (Photo 3)

**Couleurs visibles:** Orange + Jaune-Vert (avec gaine noire)

### Identification probable: **CAPTEUR DE VITESSE** ou **INTERRUPTEUR DE FREIN**

| Fil | Couleur | Fonction |
|-----|---------|----------|
| 1 | Orange | Signal + ou +5V |
| 2 | Jaune-Vert (gaine noire) | Signal - ou Masse |

**Test à faire:**
```
1. Multimètre en mode Ohm (Ω)
2. Mesurer la résistance entre les 2 fils
3. Si résistance infinie → C'est un interrupteur (frein)
4. Si résistance variable → C'est un capteur
```

---

## CONNECTEUR 2: Connecteur blanc à 2 fils (Photo 5)

**Couleurs visibles:** Violet + Bleu

### Identification probable: **FREIN AVANT ou ARRIÈRE**

| Fil | Couleur | Fonction |
|-----|---------|----------|
| 1 | Violet | Signal frein |
| 2 | Bleu | Masse ou +5V |

**Connexion:** Se branche sur le levier de frein

**Test:**
- Connecter temporairement ces 2 fils ensemble
- Si le moteur refuse de tourner → C'est bien le frein
- Si rien ne change → Ce n'est pas un capteur de frein critique

---

## CONNECTEUR 3: Grand connecteur blanc (Photo 6)

**Type:** Connecteur large rectangulaire (6-9 broches)

**Couleurs visibles dans le faisceau:**
- Rose
- Cyan (turquoise)
- Noir
- Rouge
- Orange
- Autres fils

### Identification: **TABLEAU DE BORD / ÉCRAN LCD**

**Brochage typique:**

| Broche | Couleur | Fonction |
|--------|---------|----------|
| 1 | Rouge | +12V ou +5V |
| 2 | Noir | Masse (GND) |
| 3 | Vert/Cyan | RX (Réception) |
| 4 | Blanc/Orange | TX (Transmission) |
| 5 | Jaune | Bouton + |
| 6 | Bleu | Bouton - |
| 7 | Rose | Bouton Set/Mode |
| 8 | Violet | Rétroéclairage |

**Ce connecteur se branche sur l'écran/compteur du scooter**

---

## CONNECTEUR 4: Connecteur blanc rectangulaire moyen (Photo 7)

**Visible:** Connecteur avec plusieurs fils dont noir et bleu

### Identification: **ACCÉLÉRATEUR (THROTTLE)** ou **CAPTEURS HALL**

**Si 3 fils:**

| Fil | Fonction |
|-----|----------|
| Rouge | +5V |
| Noir | Masse |
| Vert/Jaune | Signal 0-5V |

**Si 5-6 fils:**

| Fil | Fonction |
|-----|----------|
| Rouge | +5V |
| Noir | Masse |
| Jaune | Hall A |
| Vert | Hall B |
| Bleu | Hall C |

**Test de l'accélérateur:**
1. Brancher le multimètre sur le fil de signal
2. Tourner la poignée d'accélération
3. La tension doit varier de ~1V à ~4.5V

---

## CONNECTEUR 5: Connecteur rouge (Photo 4)

**Visible:** Connecteur rouge/rose avec plusieurs fils

### Identification: **ALIMENTATION ACCESSOIRES 12V**

**Fils typiques:**
- Rouge épais = +12V
- Noir épais = Masse
- Autres fils = Commandes diverses

**Peut alimenter:**
- Phare avant
- Feu arrière
- Klaxon
- Clignotants
- Feu de freinage

---

## CONNECTEUR 6: Connecteur avec GPS/tracker (Photo 4)

**Visible:** Petit boîtier noir avec connecteur

### Identification: **TRACKER GPS ou MODULE ANTI-VOL**

**Ne pas débrancher si présent!**

Ce module peut:
- Tracer la position du scooter
- Verrouiller le moteur à distance
- Enregistrer les trajets

---

## CONNECTEUR 7: Fils libres Orange, Jaune-Vert, Noir (Photo 3)

**Visibles:** 3 fils sortant du faisceau

### Identification probable: **ACCÉLÉRATEUR (THROTTLE)**

| Fil | Couleur | Fonction |
|-----|---------|----------|
| 1 | Orange | +5V alimentation |
| 2 | Noir | Masse (GND) |
| 3 | Jaune-Vert | Signal variable |

**À connecter:** Poignée d'accélération (throttle grip)

**IMPORTANT:** Ce sont les fils les plus critiques!
- Sans eux, le scooter ne peut pas avancer
- La tension sur le fil jaune-vert doit varier de 0.8V à 4.5V

---

## 🔌 CONNECTEUR PRINCIPAL (Grand connecteur noir du contrôleur)

**Type:** Connecteur rectangulaire à ~30-40 broches

**Ce connecteur contient TOUT:**
- Alimentation 72V
- Signaux de contrôle
- Capteurs
- Freins
- Accélérateur
- Communication

**Tous les petits connecteurs que vous voyez se relient finalement à ce grand connecteur**

---

## 📊 TABLEAU RÉCAPITULATIF DES COULEURS STANDARDS

| Couleur | Fonction habituelle |
|---------|---------------------|
| **Rouge épais** | +72V batterie (DANGER!) |
| **Noir épais** | Masse batterie (GND) |
| **Rouge fin** | +12V ou +5V |
| **Noir fin** | Masse signal |
| **Orange** | +5V capteurs ou signal |
| **Jaune** | Signal accélérateur ou Hall A |
| **Vert** | Signal ou Hall B |
| **Bleu** | Signal frein ou Hall C |
| **Blanc** | Communication/Data |
| **Gris** | Contact/démarrage |
| **Violet** | Frein ou accessoire |
| **Rose** | Éclairage ou bouton |
| **Cyan** | Communication série |

⚠️ **ATTENTION:** Ces couleurs sont des standards, mais peuvent varier selon les fabricants!

---

## 🧪 PROCÉDURE DE TEST AVEC MULTIMÈTRE

### Matériel nécessaire:
- Multimètre numérique
- Batterie 72V chargée
- Câbles de test avec pinces crocodile
- Ruban isolant
- Carnet pour noter les mesures

### Test 1: Identifier les fils d'alimentation

1. **Régler le multimètre en DC Volts 200V**
2. Connecter le fil noir du multimètre sur le châssis (masse)
3. Connecter la batterie
4. Toucher chaque fil avec le fil rouge du multimètre
5. Noter les tensions:
   - **~72V** = Positif batterie (DANGER!)
   - **~12V** = Sortie DC-DC converter
   - **~5V** = Alimentation capteurs
   - **0V** = Masse
   - **Variable** = Signaux

### Test 2: Identifier l'accélérateur

1. **Régler le multimètre en DC Volts 20V**
2. Trouver le connecteur à 3 fils
3. Identifier +5V, masse, et signal
4. Brancher sur le signal
5. Tourner la poignée:
   - Repos: 0.8-1.2V
   - Plein gaz: 4.0-4.5V
   - Si OK → C'est l'accélérateur!

### Test 3: Identifier les freins

1. **Régler le multimètre en mode Continuité (⚡ ou )))))**
2. Toucher les 2 fils du connecteur
3. Actionner le levier de frein:
   - Frein relâché: Pas de continuité (beep OFF)
   - Frein serré: Continuité (beep ON)
   - Si OK → C'est un capteur de frein!

### Test 4: Identifier les capteurs Hall

1. **Régler le multimètre en DC Volts 20V**
2. Brancher le moteur
3. Tourner la roue à la main
4. Mesurer sur les fils jaune/vert/bleu
5. La tension doit osciller entre 0V et 5V
6. Si OK → Ce sont les capteurs Hall!

---

## 🎯 PLAN D'ACTION POUR VOTRE ADAPTATION

### Phase 1: Inventaire (30 minutes)

1. ✅ Étalez tous les connecteurs sur une table
2. ✅ Prenez une photo de chaque connecteur
3. ✅ Comptez le nombre de fils par connecteur
4. ✅ Notez les couleurs dans un tableau

### Phase 2: Tests électriques (1 heure)

1. ✅ Testez les tensions avec multimètre
2. ✅ Identifiez +5V, +12V, +72V, masses
3. ✅ Testez la continuité des freins
4. ✅ Testez la variation de l'accélérateur
5. ✅ Notez tout dans un carnet

### Phase 3: Mapping (30 minutes)

1. ✅ Créez un tableau avec:
   - Nom du connecteur
   - Nombre de broches
   - Couleurs des fils
   - Fonction identifiée
   - Tensions mesurées

### Phase 4: Adaptation (2-3 heures)

1. ✅ Comparez les connecteurs du contrôleur NS24 avec ceux du WDJ
2. ✅ Identifiez les connecteurs compatibles (branchement direct)
3. ✅ Identifiez les connecteurs à adapter (changement de prise)
4. ✅ Pour chaque connecteur incompatible:
   - Couper l'ancien connecteur
   - Dénuder les fils (5mm)
   - Souder sur le nouveau connecteur
   - Isoler avec gaine thermorétractable
   - Tester la continuité

### Phase 5: Tests de sécurité (1 heure)

1. ⚠️ Roue arrière surélevée
2. ⚠️ Batterie déconnectée au début
3. ⚠️ Vérifier toutes les connexions
4. ⚠️ Reconnecter la batterie
5. ⚠️ Tester le contact
6. ⚠️ Tester les freins (moteur doit se couper)
7. ⚠️ Tester l'accélérateur doucement
8. ⚠️ Vérifier l'écran LCD
9. ⚠️ Faire un essai à basse vitesse

---

## 🆘 QUESTIONS À SE POSER

Pour chaque connecteur inconnu:

1. **Combien de fils?**
   - 2 fils → Frein, interrupteur, ou alimentation simple
   - 3 fils → Accélérateur ou capteur analogique
   - 5-6 fils → Capteurs Hall ou écran
   - 8+ fils → Écran LCD complexe

2. **Quelles couleurs?**
   - Rouge + Noir → Alimentation
   - 3 couleurs vives → Accélérateur
   - 5 couleurs → Capteurs Hall

3. **Quelle tension?**
   - 72V → Alimentation principale (DANGER!)
   - 12V → Accessoires
   - 5V → Capteurs et contrôle
   - 0-5V variable → Signaux

4. **Continuité ou variable?**
   - ON/OFF → Interrupteur (frein)
   - Variable → Capteur (accélérateur, Hall)

---

## 📝 TEMPLATE DE TABLEAU À REMPLIR

```
┌─────────────┬────────┬──────────────┬──────────────┬─────────┐
│ Connecteur  │ Broches│ Couleurs     │ Tension      │ Fonction│
├─────────────┼────────┼──────────────┼──────────────┼─────────┤
│ Connecteur 1│   2    │ Orange/Noir  │ 5V / 0V      │ Throttle│
│ Connecteur 2│   2    │ Violet/Bleu  │ ON/OFF       │ Frein   │
│ Connecteur 3│   8    │ Multicolore  │ 12V/5V/GND   │ Écran   │
│ Connecteur 4│   3    │ R/N/Y        │ 5V/0V/0-5V   │ Throttle│
│ Connecteur 5│   5    │ R/N/J/V/B    │ 5V Hall      │ Hall    │
│ Connecteur 6│   2    │ Rouge/Noir   │ 12V          │ Lumière │
└─────────────┴────────┴──────────────┴──────────────┴─────────┘
```

**Remplissez ce tableau pour votre faisceau!**

---

## ✅ CHECKLIST FINALE AVANT PREMIER DÉMARRAGE

- [ ] Batterie chargée à 100%
- [ ] Toutes les connexions bien serrées
- [ ] Pas de court-circuit visible
- [ ] Isolation correcte des fils nus
- [ ] Fusible 200A installé sur le +72V
- [ ] Roue arrière surélevée
- [ ] Freins testés (coupent le moteur)
- [ ] Accélérateur testé (tension varie)
- [ ] Écran s'allume
- [ ] Pas de fumée ni d'odeur de brûlé
- [ ] Interrupteur d'urgence accessible
- [ ] Équipement de sécurité (gants, lunettes)

---

**Si vous avez besoin d'aide pour identifier un connecteur spécifique, envoyez-moi:**
1. Photo claire du connecteur
2. Nombre de fils et leurs couleurs
3. Tensions mesurées avec le multimètre
4. D'où vient ce connecteur sur le scooter

Bonne chance avec votre installation! 🛴⚡
