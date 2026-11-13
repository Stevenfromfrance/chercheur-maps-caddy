# Schéma de Câblage Simplifié - WDJ 1500W 72V + Contrôleur NS24

## 🔋 CONNEXIONS ALIMENTATION (FAIRE EN DERNIER!)

```
BATTERIE 72V
│
├─── [FUSIBLE 200A] ──── Fil ROUGE épais ──→ Terminal ROUGE (B+) du FarDriver ⚡
│
└─── Fil NOIR épais ──────────────────────→ Terminal NOIR (B−) du FarDriver  ⏚

Polarité FarDriver standard:
   Terminal ROUGE (B+) = +72V
   Terminal NOIR  (B−) = Masse
```

---

## 🔄 CONNEXIONS MOTEUR BRUSHLESS

```
MOTEUR 1500W
│
├─── Fil BLEU ────→ Terminal BLEU (W) du contrôleur
├─── Fil JAUNE ───→ Terminal JAUNE (U) du contrôleur
└─── Fil VERT ────→ Terminal VERT (V) du contrôleur

Si le moteur tourne à l'envers, inverser 2 fils parmi les 3
```

---

## 🎮 CONNEXION ACCÉLÉRATEUR (THROTTLE)

```
POIGNÉE D'ACCÉLÉRATION (3 fils)
│
├─── Rouge/Orange ──→ +5V (du contrôleur)
├─── Noir ──────────→ GND (masse)
└─── Vert/Jaune ────→ Signal (0.8V repos → 4.5V plein gaz)

Test: Tourner la poignée doit faire varier la tension de 1V à 4.5V
```

---

## 🛑 CONNEXIONS FREINS

```
FREIN AVANT (2 fils)           FREIN ARRIÈRE (2 fils)
├─── Signal 1 ──┐              ├─── Signal 1 ──┐
└─── Signal 2 ──┤              └─── Signal 2 ──┤
                │                              │
                └──────────────────────────────┴──→ Contrôleur

Type: Interrupteur normalement ouvert (NO)
Fonctionnement: Freinage = Circuit fermé = Moteur coupé
Test: Continuité ON quand frein actionné, OFF quand relâché
```

---

## 📊 CONNEXION ÉCRAN LCD / TABLEAU DE BORD

```
ÉCRAN LCD (6-9 fils typiquement)
│
├─── Rouge ────────→ +12V ou +5V
├─── Noir ─────────→ GND (masse)
├─── Vert/Cyan ────→ RX (Réception données)
├─── Orange/Blanc ─→ TX (Transmission données)
├─── Jaune ────────→ Bouton + (ou autre fonction)
├─── Bleu ─────────→ Bouton - (ou autre fonction)
├─── Rose/Violet ──→ Bouton Set/Mode
└─── (Autre) ──────→ Rétroéclairage LCD

L'écran affiche: Vitesse, Km parcourus, Niveau batterie, Mode de conduite
```

---

## 🌀 CAPTEURS HALL DU MOTEUR (Si présents)

```
CAPTEURS HALL (5-6 fils)
│
├─── Rouge ──→ +5V
├─── Noir ───→ GND
├─── Jaune ──→ Hall A (signal pulsé)
├─── Vert ───→ Hall B (signal pulsé)
└─── Bleu ───→ Hall C (signal pulsé)

Fonction: Détectent la position du rotor pour un contrôle précis
Sans eux: Le moteur peut démarrer mais sera moins efficace ou saccader
```

---

## 💡 ACCESSOIRES 12V (OPTIONNEL)

```
SORTIE 12V DU CONTRÔLEUR
│
├─── Rouge (+12V) ─┬─→ Phare avant
│                  ├─→ Feu arrière
│                  ├─→ Clignotants
│                  └─→ Klaxon
│
└─── Noir (GND) ───→ Masse commune

Puissance max: 2-3A (24-36W) - Ne pas surcharger!
```

---

## 🔌 ORDRE DE CONNEXION RECOMMANDÉ

```
Étape    Connexion                    ⚠️ Batterie
─────────────────────────────────────────────────────
  1      Moteur (3 fils)             DÉBRANCHÉE ❌
  2      Capteurs Hall (5 fils)      DÉBRANCHÉE ❌
  3      Accélérateur (3 fils)       DÉBRANCHÉE ❌
  4      Freins (2x2 fils)           DÉBRANCHÉE ❌
  5      Écran LCD                   DÉBRANCHÉE ❌
  6      Accessoires 12V             DÉBRANCHÉE ❌
  7      Connecteur principal        DÉBRANCHÉE ❌
  8      ✅ Vérification complète    DÉBRANCHÉE ❌
  9      ⚡ BATTERIE                 CONNECTÉE ✅
 10      🧪 Tests de sécurité        CONNECTÉE ✅
```

---

## 🧪 PROCÉDURE DE TEST ÉTAPE PAR ÉTAPE

### TEST 1: Vérification visuelle (Batterie DÉBRANCHÉE)

```
✓ Pas de fils dénudés touchant le châssis
✓ Toutes les connexions bien isolées
✓ Les bornes du contrôleur bien serrées
✓ Pas de court-circuit visible
✓ Fusible 200A installé
```

### TEST 2: Premier branchement (Roue SURÉLEVÉE)

```
1. Connecter la batterie
2. Mettre le contact
3. Vérifier l'écran LCD s'allume → ✓ OK / ✗ Problème alimentation
4. Vérifier aucune fumée / odeur    → ✓ OK / ✗ DÉBRANCHER IMMÉDIATEMENT
5. Vérifier tension affichée: ~72V  → ✓ OK / ✗ Problème batterie
```

### TEST 3: Test des freins (CRITIQUE!)

```
1. Actionner le frein avant
2. Essayer de tourner l'accélérateur
3. Le moteur ne doit PAS tourner → ✓ SÉCURISÉ / ✗ DANGER!

4. Relâcher le frein
5. Actionner le frein arrière
6. Essayer de tourner l'accélérateur
7. Le moteur ne doit PAS tourner → ✓ SÉCURISÉ / ✗ DANGER!

⚠️ Si les freins ne coupent pas le moteur, NE PAS ROULER!
```

### TEST 4: Test de l'accélérateur (Roue SURÉLEVÉE)

```
1. S'assurer que les freins sont relâchés
2. Tourner DOUCEMENT l'accélérateur
3. Le moteur doit tourner progressivement
4. Vérifier le sens de rotation:
   - ✓ AVANT (normal)
   - ✗ ARRIÈRE (inverser 2 fils moteur)
5. Relâcher l'accélérateur → moteur s'arrête
```

### TEST 5: Test de puissance (Roue SURÉLEVÉE)

```
1. Accélérer à fond progressivement
2. Écouter le bruit du moteur:
   - ✓ Bruit régulier = OK
   - ✗ Saccades / bruits bizarres = Problème phases ou Hall
3. Vérifier l'écran:
   - Vitesse affichée augmente
   - Pas de code d'erreur
   - Niveau de batterie stable
```

### TEST 6: Premier essai au sol (PRUDENCE!)

```
⚠️ ÉQUIPEMENT DE SÉCURITÉ:
- Casque
- Gants
- Chaussures fermées
- Vêtements appropriés

1. Poser le scooter au sol
2. Monter dessus avec prudence
3. Tester les freins à l'arrêt
4. Démarrer DOUCEMENT (10% d'accélération max)
5. Rouler 5 mètres et freiner
6. Vérifier:
   - Freinage efficace
   - Pas de vibrations anormales
   - Pas de surchauffe (toucher le contrôleur)
   - Écran affiche correctement

Si tout est OK → Augmenter progressivement la vitesse
Si problème → S'ARRÊTER et diagnostiquer
```

---

## 🚨 CODES D'ERREUR COURANTS

```
┌──────────┬─────────────────────────┬──────────────────────────┐
│ Code     │ Signification           │ Solution                 │
├──────────┼─────────────────────────┼──────────────────────────┤
│ E01      │ Surtension batterie     │ Batterie trop chargée    │
│ E02      │ Sous-tension batterie   │ Batterie déchargée       │
│ E03      │ Surintensité moteur     │ Moteur bloqué / Phases   │
│ E04      │ Erreur capteur Hall     │ Vérifier connecteur Hall │
│ E05      │ Frein bloqué activé     │ Vérifier interrupteurs   │
│ E06      │ Accélérateur défectueux │ Vérifier tension throttle│
│ E07      │ Surchauffe contrôleur   │ Laisser refroidir        │
│ E08      │ Communication perdue    │ Vérifier connecteur LCD  │
└──────────┴─────────────────────────┴──────────────────────────┘
```

---

## ⚡ VALEURS ÉLECTRIQUES DE RÉFÉRENCE

### Tensions normales (moteur à l'arrêt):

```
Point de mesure              Tension attendue
─────────────────────────────────────────────
Batterie pleine             84V (72V nominal)
Batterie vide               60V
Sortie +5V capteurs         5.0V ±0.2V
Sortie +12V accessoires     12V ±0.5V
Accélérateur au repos       0.8-1.2V
Accélérateur plein gaz      4.0-4.5V
Capteurs Hall au repos      0V ou 5V (alternent)
```

### Courants normaux:

```
Situation                    Courant typique
──────────────────────────────────────────────
Repos (contact ON)          0.1-0.5A
Roulage plat 25 km/h        8-15A
Accélération forte          30-50A
Montée de côte             50-100A
Pointe maximale            200A (limité par contrôleur)
⚠️ DANGER si >200A         Court-circuit! Fusible grille
```

---

## 🔧 OUTILS NÉCESSAIRES

### Pour l'installation:

```
✓ Multimètre numérique (obligatoire!)
✓ Jeu de tournevis cruciformes
✓ Clés Allen (hexagonales)
✓ Pince à dénuder
✓ Fer à souder + étain (si modification connecteurs)
✓ Gaines thermorétractables
✓ Briquet ou décapeur thermique
✓ Ruban isolant haute tension
✓ Serre-câbles (colliers)
✓ Carnet + stylo (pour noter!)
```

### Pour les tests:

```
✓ Multimètre
✓ Béquille ou support pour surélever la roue
✓ Batterie chargée 100%
✓ Équipement de sécurité (casque, gants)
✓ Extincteur (au cas où!)
```

---

## 📞 DIAGNOSTIC RAPIDE

### Problème: Le moteur ne tourne pas

```
1. Écran LCD allumé?
   NON → Problème alimentation ou connecteur écran
   OUI → Continuer

2. Freins relâchés?
   NON → Relâcher les freins
   OUI → Continuer

3. Code d'erreur affiché?
   OUI → Voir tableau codes d'erreur
   NON → Continuer

4. Tension accélérateur varie (1V → 4.5V)?
   NON → Problème accélérateur
   OUI → Problème contrôleur ou moteur
```

### Problème: Le moteur saccade / ne pousse pas

```
1. Vérifier les 3 fils du moteur bien connectés
2. Vérifier les capteurs Hall (5 fils)
3. Essayer d'inverser 2 fils moteur parmi les 3
4. Vérifier qu'il n'y a pas de code d'erreur E04
```

### Problème: Le moteur tourne en arrière

```
Solution simple:
1. Débrancher la batterie
2. Sur les 3 fils du moteur, échanger 2 fils
   Exemple: Échanger le BLEU et le JAUNE
3. Rebrancher et tester
```

### Problème: Surchauffe du contrôleur

```
Causes possibles:
- Surintensité (montées trop longues)
- Court-circuit partiel
- Mauvaise ventilation
- Contrôleur défectueux

Solution:
1. Laisser refroidir 30 minutes
2. Vérifier les connexions
3. Ajouter un ventilateur sur le contrôleur
4. Réduire le courant max dans les paramètres
```

---

## ⚠️ SÉCURITÉ - À NE JAMAIS FAIRE

```
❌ Brancher/débrancher avec la batterie connectée
❌ Toucher les bornes +72V à mains nues
❌ Court-circuiter les fils pour "tester"
❌ Rouler sans tester les freins avant
❌ Dépasser 25 km/h lors des premiers tests
❌ Rouler avec un code d'erreur affiché
❌ Forcer une connexion qui ne rentre pas
❌ Utiliser un fusible de valeur incorrecte
❌ Inverser le + et le - de la batterie
❌ Souder des fils sous tension
```

---

## ✅ CHECKLIST QUOTIDIENNE (Avant chaque sortie)

```
[ ] Batterie chargée (>60V)
[ ] Pas de code d'erreur à l'écran
[ ] Freins avant et arrière fonctionnels
[ ] Accélérateur répond normalement
[ ] Pas de fils dénudés visibles
[ ] Contrôleur bien fixé
[ ] Pas d'odeur de brûlé
[ ] Pression des pneus correcte
[ ] Éclairages fonctionnels (si nuit)
[ ] Équipement de sécurité (casque)
```

---

## 📚 RESSOURCES SUPPLÉMENTAIRES

### Pour aller plus loin:

1. **Manuel du contrôleur NS24** (si disponible)
2. **Schéma électrique du WDJ 1500W**
3. **Forums spécialisés** (Electricbike.com, EndlessSphere)
4. **Groupes Facebook** scooters électriques DIY
5. **Vidéos YouTube** sur le câblage de contrôleurs BLDC

### Contacts utiles:

- **Support Jiangsu Pardriver** (pour questions sur le contrôleur)
- **Revendeur WDJ** (pour schémas et pièces)
- **Électriciens spécialisés** véhicules électriques

---

## 🎓 RÉSUMÉ EN 10 POINTS

1. ⚡ **BORNES INVERSÉES:** Noir = +72V, Rouge = Masse
2. 🔌 **3 fils moteur:** Bleu, Jaune, Vert (inverser 2 si mauvais sens)
3. 🎮 **Accélérateur:** 3 fils (Rouge +5V, Noir GND, Vert signal)
4. 🛑 **Freins:** 2 connecteurs à 2 fils (interrupteurs)
5. 📊 **Écran LCD:** Connecteur multi-fils (alimentation + data)
6. 🌀 **Hall:** 5 fils optionnels (Rouge, Noir, Jaune, Vert, Bleu)
7. 🔋 **Fusible:** 200A obligatoire sur le fil +72V
8. 🧪 **Tests:** Toujours roue surélevée au début
9. 🛡️ **Sécurité:** Freins doivent couper le moteur
10. 📱 **Support:** Prendre des photos et noter les valeurs

---

**Bon courage pour votre installation! 🔧⚡**

*Si vous rencontrez un problème spécifique, référez-vous aux guides détaillés ou demandez de l'aide avec photos et valeurs mesurées.*
