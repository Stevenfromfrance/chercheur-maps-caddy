# Short #1 : RPM Factor ×2 — CRITIQUE EDC17

**Durée :** ~45 sec | **ECU :** EDC17CP14 | **SW :** 516657 | **⚠️ PRIORITÉ ABSOLUE**

## 🎯 Objectif

Comprendre que **EDC17 stocke RPM ×2** → factor **0.5** WinOLS obligatoire sur tous axes RPM.

## 🔍 Le Piège

```
WinOLS affiche : 10,000 rpm
Valeur réelle   : 5,000 rpm
```

**Tous les calculateurs EDC17** stockent les axes RPM doublés.

## 📐 Factor de Correction

**WinOLS → Map Properties → Axis → Factor : 0.5**

| Affiché WinOLS (raw) | ×0.5 | Valeur Réelle Moteur |
|---|---|---|
| 10,000 | → | **5,000 rpm** |
| 9,600 | → | **4,800 rpm** (hardcut) |
| 5,400 | → | **2,700 rpm** (launch) |
| 8,000 | → | **4,000 rpm** |

## 🔧 Étapes

1. ✅ Ouvrir map EDC17 dans WinOLS
2. ✅ Identifier axe RPM (typiquement axe Y ou X)
3. ✅ Vérifier plage : >6000 raw → probablement ×2
4. ✅ Clic droit axe → **Properties**
5. ✅ Onglet **Factor** → saisir **0.5**
6. ✅ Valider → axe maintenant en valeurs réelles
7. ✅ **Répéter pour TOUTES les maps EDC17**

## ⚠️ Erreurs Courantes

### ❌ Erreur #1 : Hardcut trop bas
```
Saisir 4800 dans WinOLS (sans factor)
→ Hardcut réel = 2400 rpm
→ Moteur cale en pleine charge !
```

### ❌ Erreur #2 : Launch trop haut
```
Saisir 2700 dans WinOLS (sans factor)
→ Launch réel = 1350 rpm
→ Pas assez de boost, départ mou
```

### ❌ Erreur #3 : Comparer A5 vs Caddy sans conversion
```
"Le Caddy PCR2.1 a hardcut 4800, je copie 4800 sur l'A5"
→ A5 hardcut réel = 2400 rpm (ERREUR !)
→ Correct : saisir 9600 sur A5 pour obtenir 4800 réel
```

### ❌ Erreur #4 : Oublier sur certaines maps
```
Factor 0.5 sur AccPed ✅
Mais oublier sur Smoke / Rail ❌
→ Incohérence axes, erreur d'interprétation
```

## ✅ Vérification Rapide

Après application factor 0.5, vérifier cohérence :

- [ ] **Idle** : ~800-900 rpm (pas ~1600-1800)
- [ ] **Redline** : ~5000-5500 rpm (pas ~10000-11000)
- [ ] **Hardcut** : ~4800 rpm (pas ~9600)
- [ ] **Launch** : ~2700 rpm (pas ~5400)
- [ ] **Plage utile** : ~1500-4500 rpm (pas ~3000-9000)

Si axes encore en valeurs doublées → **factor non appliqué ou appliqué ×2 par erreur**.

## 📋 Maps Concernées (liste non exhaustive)

**Toutes** les maps EDC17 avec axe RPM :

- AccPed banques (×8)
- Torque limiters (tqlim_base, tqlim_tegt, tqlim_speed...)
- Smoke limiters (×5+)
- Rail pressure (×20+)
- Injection Time / Duration
- IQ quantity maps
- SOI (Start of Injection)
- VGT turbo maps
- EGR maps
- ...et **toutes les autres** avec axe régime

**Règle absolue :** Dès qu'un axe représente RPM → **factor 0.5**.

## 🔗 Source

**Facebook post :** https://www.facebook.com/share/r/1JSyXmmAYL/?mibextid=wwXIfr

> "EDC17 stores RPM ×2. The axis says 10,000 — the real value is 5000. One factor in WinOLS fixes it: 0.5."

**Full course :** Lien dans commentaire Facebook (à récupérer)

## 📊 Comparaison PCR2.1 vs EDC17

| Aspect | PCR2.1 (Caddy) | EDC17 (A5) |
|--------|----------------|------------|
| **RPM storage** | ×1 (normal) | **×2 (doubled)** |
| **WinOLS factor** | 1.0 (aucun) | **0.5 (obligatoire)** |
| **Hardcut 4800** | Saisir 4800 | Saisir **9600** |
| **Launch 2700** | Saisir 2700 | Saisir **5400** |
| **Idle ~850** | Affiché ~850 | Affiché ~1700 (avant factor) |

## 💡 Astuce Rapide

**Doute sur un axe ?**

1. Regarder la plage de valeurs
2. Si >6000 → probablement RPM ×2 → factor 0.5
3. Si 0-100 → probablement % → factor 1.0
4. Si 0-500 → probablement Nm ou bar → factor dépend A2L

## 📎 Fichiers Liés

- `../../../../../EDC17-RPM-FACTOR-CRITICAL.md` (détail complet)
- `../../../../../METHODOLOGIE-EDC17-RECAP.md` (méthodologie)
- `../README.md` (warning en haut)
- `../build_v1.py` (à auditer : factor appliqué ?)

## ✅ Checklist Avant Toute Modif EDC17

- [ ] A2L similar 0005 importé WinOLS
- [ ] **Factor 0.5 appliqué sur TOUS axes RPM** ← **CE SHORT**
- [ ] Axes couple/pression vérifiés avec A2L
- [ ] Valeurs cohérentes (pas de hardcut 2400 rpm !)
- [ ] Comparaison vs PCR2.1 avec conversion ×2

---

**⚠️ NE JAMAIS OUBLIER LE FACTOR 0.5 SUR EDC17 !**

Sans cela, **toutes les valeurs RPM sont fausses** → risque casse moteur / embrayage / turbo.

---

**Dernière mise à jour :** 27 oct 2026  
**Auteur :** SavageSear (via Facebook post recovery)  
**Status :** ✅ Validé — information critique
