# Short #2 : Pedal Axis 8192 = 100% — EDC17

**Durée :** ~30 sec | **ECU :** EDC17CP14 | **SW :** 516657 | **⚠️ CRITIQUE**

## 🎯 Objectif

Convertir l'axe pédale EDC17 (0-8192 raw) en pourcentage (0-100%) pour identifier clairement tip-in, partiels, et WOT.

## 🔍 Le Piège

```
WinOLS affiche : 0, 819, 2048, 4096, 6144, 7168, 8192
Signification   : 0%, 10%, 25%, 50%, 75%, 87.5%, 100%
```

**EDC17 stocke la pédale en valeur brute 0-8192.**

**8192 = 100% pédale (WOT)**

## 🔧 Conversion WinOLS (Méthode Rapide)

1. ✅ Ouvrir map AccPed (ou autre avec axe pédale)
2. ✅ **Double-clic** sur l'axe pédale (axe X typiquement)
3. ✅ Cliquer bouton **%** (pourcentage)
4. ✅ L'axe entier converti automatiquement : 0-8192 → 0-100%

**C'est tout ! Conversion instantanée.**

## 📊 Avant / Après

### Avant Conversion
```
Axe pédale (raw) : 80, 328, 819, 1885, 4096, 6144, 6963, 8183
                   [Illisible : où est le WOT ?]
```

### Après Conversion
```
Axe pédale (%)   : 0.98%, 4.00%, 10.00%, 23.02%, 50.00%, 75.00%, 85.00%, 99.90%
                   [Clair : WOT = dernières 2-3 cellules ≥85%]
```

## 🎯 Identifier les Zones

Après conversion % :

| Zone | % Pédale | Signification |
|---|---|---|
| **Tip-in** | 0-23% | Confort, douceur, démarrage |
| **Partiels** | 23-75% | Charge normale, conduite courante |
| **WOT** | ≥85% | Plein gaz, performance, Stage1 |

## ⚠️ Erreurs Courantes

### ❌ Erreur #1 : Modifier mauvaise zone
```
Sans conversion % :
"Je veux Stage1 WOT, je modifie cellule 4096"
→ 4096 = 50% pédale (partiels, pas WOT !)
```

### ❌ Erreur #2 : Cap toute la map
```
Sans identifier tip-in (0-23%) :
"Je cap toute la map à 350 Nm"
→ Tip-in aussi cappé = inconfort
```

### ❌ Erreur #3 : Oublier RPM factor 0.5
```
✅ Axe pédale converti en %
❌ Axe RPM encore ×2 (voir Short #1)
→ Un axe correct, un axe faux
```

## ✅ Vérification Rapide

Après conversion :

- [ ] Axe pédale : **0-100%** (pas 0-8192)
- [ ] WOT identifié : cellules **≥85%**
- [ ] Tip-in identifié : cellules **0-23%**
- [ ] Axe RPM aussi converti : **factor 0.5** (Short #1)

## 🔗 Combinaison Short #1 + Short #2

**AccPed EDC17 nécessite DEUX conversions :**

1. **Short #1** : Axe RPM ×2 → **factor 0.5**
2. **Short #2** : Axe pédale 8192 → **bouton %**

**Exemple complet :**

```
Map AccPed brute :
├── Axe X (pédale) : 0, 819, 2048, 4096, 6144, 6963, 8192
├── Axe Y (RPM)    : 0, 798, 1218, 1800, 2016, 2982, 3990, 4998, 6006, 7980...
└── Valeurs (Nm)   : grille 8×16

Après conversions :
├── Axe X (pédale) : 0%, 10%, 25%, 50%, 75%, 85%, 100%     ← Short #2
├── Axe Y (RPM)    : 0, 399, 609, 900, 1008, 1491, 1995... ← Short #1
└── Valeurs (Nm)   : grille 8×16 (inchangée)
```

**Maintenant lisible :**
- Tip-in : 0-23% pédale, tous RPM
- WOT : ≥85% pédale, 1500-4800 rpm

## 📐 Formule (si conversion manuelle)

```
% pédale = (valeur_raw / 8192) × 100

Exemples :
8192 / 8192 × 100 = 100.00% (WOT)
6963 / 8192 × 100 = 85.00%  (début WOT)
4096 / 8192 × 100 = 50.00%  (partiels)
819  / 8192 × 100 = 10.00%  (tip-in)
```

## 🔗 Source

**Facebook post :** https://www.facebook.com/share/r/1HqguUpZe5/?mibextid=wwXIfr

> "On this pedal axis, 8192 means 100 %. Double-click it, press the % button — and the whole axis is in percent."

## 📊 Différence PCR2.1 vs EDC17

| Aspect | PCR2.1 (Caddy) | EDC17 (A5) |
|--------|----------------|------------|
| **Pédale 100%** | 100 | **8192** |
| **Conversion** | Aucune (déjà %) | **Double-clic + %** |
| **WOT seuil** | ≥85% (~85) | **≥6963** (avant) / ≥85% (après) |

## 📎 Fichiers Liés

- `01-rpm-factor-x2.md` (Short #1, obligatoire avant)
- `../../../../../EDC17-PEDAL-AXIS-CRITICAL.md` (détail complet)
- `../../../../../EDC17-RPM-FACTOR-CRITICAL.md` (Short #1 détail)

## ✅ Checklist AccPed Complète

Workflow AccPed EDC17 complet :

1. [ ] Localiser AccPed banque (0x1CF9C0...)
2. [ ] **Convertir axe pédale** : double-clic + % ← **CE SHORT**
3. [ ] **Convertir axe RPM** : factor 0.5 ← Short #1
4. [ ] Identifier tip-in (0-23%)
5. [ ] Identifier WOT (≥85%)
6. [ ] Appliquer stratégie (tip-in soft, WOT cap 350)
7. [ ] Hardcut ligne ≥4800 rpm → 0 Nm

---

**⚠️ TOUJOURS CONVERTIR PÉDALE EN % AVANT MODIFICATION !**

Sans cela, **impossible d'identifier WOT** → modifications au mauvais endroit.

---

**Dernière mise à jour :** 27 oct 2026  
**Auteur :** SavageSear (via Facebook post recovery)  
**Status :** ✅ Validé — information critique #2
