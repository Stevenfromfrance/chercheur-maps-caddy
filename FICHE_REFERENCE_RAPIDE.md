# 📋 FICHE DE RÉFÉRENCE RAPIDE - WDJ 1500W 72V

**⚠️ À IMPRIMER ET GARDER AVEC VOUS PENDANT L'INSTALLATION ⚠️**

---

## 🔴 POLARITÉ FARDRIVER

```
┌────────────────────────────────────────┐
│  Terminal ROUGE (B+)  =  +72V Positif │
│  Terminal NOIR  (B−)  =  GND Négatif  │
└────────────────────────────────────────┘
```

---

## ⚡ CONNEXIONS PRINCIPALES

### Alimentation Batterie
```
Batterie +72V (ROUGE) → [FUSIBLE 200A] → Terminal ROUGE B+
Batterie GND (NOIR)   → Terminal NOIR B−
```

### Moteur (3 fils)
```
Moteur BLEU   → Terminal BLEU (W)
Moteur JAUNE  → Terminal JAUNE (U)
Moteur VERT   → Terminal VERT (V)
```

### Accélérateur (3 fils)
```
Rouge/Orange → +5V
Noir         → GND
Vert/Jaune   → Signal (0.8V → 4.5V)
```

### Freins (2 fils chacun)
```
2 fils → Avant
2 fils → Arrière
Type: Interrupteur ON/OFF
```

---

## 🧪 TENSIONS DE RÉFÉRENCE

| Point de mesure | Tension |
|----------------|---------|
| Batterie pleine | 84V |
| Batterie vide | 60V |
| +5V capteurs | 5.0V |
| +12V accessoires | 12V |
| Throttle repos | 0.8-1.2V |
| Throttle max | 4.0-4.5V |

---

## 🔌 IDENTIFICATION CONNECTEURS

| Fils | Fonction probable |
|------|-------------------|
| 2 fils | Frein ou interrupteur |
| 3 fils | Accélérateur |
| 5-6 fils | Capteurs Hall ou écran |
| 8+ fils | Écran LCD complet |

---

## 📊 COULEURS STANDARDS

| Couleur | Usage typique |
|---------|---------------|
| Rouge épais | +72V DANGER |
| Noir épais | Masse batterie |
| Rouge fin | +5V ou +12V |
| Orange | +5V capteurs |
| Jaune | Signal/Hall A |
| Vert | Signal/Hall B |
| Bleu | Frein/Hall C |
| Violet | Frein/Accessoire |
| Blanc | Data/Communication |

---

## ✅ ORDRE DE CONNEXION

1. ❌ Batterie DÉBRANCHÉE
2. Connecter moteur (3 fils)
3. Connecter Hall si présent (5 fils)
4. Connecter accélérateur (3 fils)
5. Connecter freins (2x2 fils)
6. Connecter écran LCD
7. Connecter accessoires
8. Vérifier toutes les connexions
9. ✅ Brancher la batterie
10. Tests de sécurité

---

## 🧪 TESTS OBLIGATOIRES

### Test 1: Alimentation
```
□ Écran s'allume
□ Pas de fumée
□ Pas d'odeur
□ Tension affichée: ~72V
```

### Test 2: Freins (CRITIQUE!)
```
□ Frein avant actionné → Moteur bloqué
□ Frein arrière actionné → Moteur bloqué
□ SI LES FREINS NE COUPENT PAS: NE PAS ROULER!
```

### Test 3: Accélérateur
```
□ Roue surélevée
□ Tourner doucement l'accélérateur
□ Moteur tourne progressivement
□ Sens correct (avant, pas arrière)
```

---

## 🚨 CODES ERREUR

| Code | Problème | Action |
|------|----------|--------|
| E01 | Surtension | Batterie trop chargée |
| E02 | Sous-tension | Recharger batterie |
| E03 | Surintensité | Vérifier moteur/phases |
| E04 | Erreur Hall | Vérifier connecteur Hall |
| E05 | Frein bloqué | Vérifier interrupteurs |
| E06 | Throttle | Vérifier accélérateur |
| E07 | Surchauffe | Laisser refroidir |

---

## 🔧 DIAGNOSTIC RAPIDE

### Moteur ne tourne pas:
```
1. Écran allumé? → NON = Alimentation
2. Freins relâchés? → NON = Relâcher
3. Code erreur? → OUI = Voir tableau
4. Throttle varie? → NON = Accélérateur
```

### Moteur saccade:
```
1. Vérifier 3 fils moteur
2. Vérifier capteurs Hall (5 fils)
3. Essayer inverser 2 fils moteur
```

### Moteur sens inverse:
```
Solution: Échanger 2 fils du moteur
Exemple: Inverser BLEU ↔ JAUNE
```

---

## ⚠️ NE JAMAIS FAIRE

```
❌ Brancher/débrancher sous tension
❌ Toucher les bornes 72V à mains nues
❌ Rouler sans tester les freins
❌ Inverser + et - de la batterie
❌ Utiliser sans fusible 200A
❌ Court-circuiter les fils
❌ Dépasser 25 km/h en test
❌ Rouler avec code d'erreur
```

---

## 🛠️ OUTILS NÉCESSAIRES

```
✓ Multimètre (OBLIGATOIRE!)
✓ Tournevis cruciformes
✓ Clés Allen
✓ Pince à dénuder
✓ Ruban isolant
✓ Gaines thermorétractables
✓ Carnet + stylo
```

---

## 📱 NOTES PERSONNELLES

**Connecteur 1:**
- Nombre de fils: _____
- Couleurs: _________________
- Tension mesurée: _____V
- Fonction: _________________

**Connecteur 2:**
- Nombre de fils: _____
- Couleurs: _________________
- Tension mesurée: _____V
- Fonction: _________________

**Connecteur 3:**
- Nombre de fils: _____
- Couleurs: _________________
- Tension mesurée: _____V
- Fonction: _________________

**Connecteur 4:**
- Nombre de fils: _____
- Couleurs: _________________
- Tension mesurée: _____V
- Fonction: _________________

**Connecteur 5:**
- Nombre de fils: _____
- Couleurs: _________________
- Tension mesurée: _____V
- Fonction: _________________

---

## ✅ CHECKLIST AVANT DÉMARRAGE

```
[ ] Fusible 200A installé
[ ] Toutes connexions serrées
[ ] Pas de fils dénudés
[ ] Isolation correcte
[ ] Roue arrière surélevée
[ ] Batterie chargée (>70V)
[ ] Multimètre à portée
[ ] Équipement sécurité (casque, gants)
[ ] Interrupteur urgence accessible
```

---

## 📞 AIDE RAPIDE

**Si problème électrique:**
1. DÉBRANCHER BATTERIE immédiatement
2. Vérifier les connexions
3. Mesurer les tensions
4. Comparer avec les valeurs de référence
5. Corriger le problème
6. Retester

**Si fumée ou odeur:**
1. ⚠️ DÉBRANCHER BATTERIE IMMÉDIATEMENT
2. Laisser refroidir 30 minutes
3. Inspecter visuellement tous les composants
4. Vérifier absence de court-circuit
5. NE PAS rebrancher avant diagnostic complet

---

**📸 CONSEIL:** Prenez des photos de chaque connexion AVANT et APRÈS!

**⏱️ PRENEZ VOTRE TEMPS:** Une installation correcte = Sécurité garantie

**🔋 BATTERIE:** Commencez avec batterie à 70-80% (pas 100%) pour les premiers tests

---

**Date d'installation:** ____________________

**Notes finales:**
_____________________________________________
_____________________________________________
_____________________________________________
_____________________________________________
_____________________________________________

---

## 🎯 VERSION IMPRIMABLE

**Pour imprimer cette fiche:**
1. Ctrl+P ou Commande+P
2. Format: A4 ou Lettre
3. Marges: Normales
4. Couleur ou Noir & Blanc
5. Recto-verso si possible
6. Plastifier pour protection (recommandé)

**À garder:**
- Dans votre boîte à outils
- Sur l'établi pendant l'installation
- Dans le scooter pour dépannage

---

**Bonne installation! 🔧⚡🛴**

*Consultez les guides détaillés (GUIDE_CABLAGE_WDJ_1500W_72V.md, IDENTIFICATION_CONNECTEURS.md, SCHEMA_CABLAGE_SIMPLIFIE.md) pour plus d'informations.*
