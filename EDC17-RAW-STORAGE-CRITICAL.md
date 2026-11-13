# ⚠️ EDC17 RAW STORAGE — INFORMATION CRITIQUE #4 (SYNTHÈSE)

## 🎯 Découverte (Facebook Post)

**Source :** https://www.facebook.com/share/r/1M2ppwKwZW/?mibextid=wwXIfr

### Ce que l'ECU stocke vraiment

> **"Your ECU doesn't store Nm. It stores raw numbers: 8192 is 100 % pedal, 4032 is 403.2 Nm. Here's what a map looks like straight from the ECU — before conversion."**

Titre image : **WHAT THE ECU REALLY STORES — Raw values before conversion • WinOLS**

## 📐 Exemple Concret (Driver's wish brut)

| Élément | Valeur affichée (raw) | Signification réelle | Conversion |
|---|---|---|---|
| Cellule orange | **4032** | **403.2 Nm** | ×0.1 (Short #3) |
| Axe X dernière col. | **8192** | **100 % pédale** | bouton % (Short #2) |
| Axe Y dernière ligne | **10000** | **5000 rpm** | ×0.5 (Short #1) |
| Axe X col. 2 | **819** | **~10 % pédale** | /8192 ×100 |
| Axe X col. 6 | **4096** | **50 % pédale** | /8192 ×100 |

**Formule unique à retenir :**
```
ECU = nombres entiers bruts
WinOLS factors/axes = traduction humaine
```

## 🖼️ Map Brute (ce qu'on voit sans conversion)

```
Axe Y (rpm raw ×2) : 1000, 1500, 2000, …, 9000, 10000
Axe X (pédale raw) : 0, 819, 1065, 1638, 2458, 4096, 5734, 8192
Cells (couple raw) : 0 … 4032 (WOT bas régime)

Highlight : 1000 rpm × 8192 → 4032
→ réel : 500 rpm? Non — si axe encore ×2 : 1000 raw = 500 rpm réel
→ Wait: dans le short pédagogique, l'axe est ÉTIQUETÉ "rpm" mais valeurs 1000–10000
   = stockage ×2 non converti → 10000 raw = 5000 rpm réel
```

**Interprétation correcte de la cellule orange :**
- Position : colonne **8192** (100 % pédale) × ligne **1000** (raw RPM = **500 rpm réel** si factor 0.5, OU 1000 rpm si déjà partiellement converti)
- Valeur **4032** → avec factor 0.1 = **403.2 Nm**

> Note : sur l'image source, l'axe RPM montre encore 1000–10000 (= raw ×2). C'est volontaire : le short montre l'état **avant** conversion.

## 🔗 Synthèse des 3 Critiques

Ce short **prouve** les trois conversions précédentes sur une seule map :

| Raw ECU | Conversion | Réel | Short |
|---|---|---|---|
| 8192 (axe) | % | 100 % pédale | #2 |
| 4032 (cellule) | ×0.1 | 403.2 Nm | #3 |
| 10000 (axe) | ×0.5 | 5000 rpm | #1 |

**Phrase clé du post :** *"ECU doesn't store Nm"* — seulement des entiers. Les Nm / % / rpm sont une **couche WinOLS**.

## ⚠️ Différence vs PCR2.1

| Aspect | PCR2.1 | EDC17 |
|--------|--------|-------|
| Stockage | raw aussi, mais factors A2L différents | raw + **trio 0.5 / % / 0.1** |
| Affichage immédiat | souvent déjà correct via A2L exact | **illisible** sans 3 conversions |
| Exemple WOT max | ~350 Nm affiché | raw **~3500–4032** |

## ❌ Erreurs Courantes

### Erreur #1 : Croire que 4032 = 4032 Nm
```
❌ "Le couple max est 4032 Nm"
✅ "4032 raw × 0.1 = 403.2 Nm"
```

### Erreur #2 : Croire que 8192 = 8192 % pédale
```
❌ Insensé
✅ 8192 = 100 % pédale
```

### Erreur #3 : Modifier en raw sans factors
```
❌ Capper à "350" dans une grille encore raw
→ Stocke 350 = 35.0 Nm réel
✅ Afficher en Nm (factor 0.1) puis saisir 350.0
   → Stocke 3500 raw
```

### Erreur #4 : Comparer A5 raw vs Caddy converti
```
❌ "A5 a 4032, Caddy a 350 — A5 trop fort"
✅ Convertir A5 d'abord : 403.2 Nm ≈ Caddy Stage1
```

## ✅ Workflow Obligatoire Avant Toute Modif

1. [ ] Ouvrir map (Driver's wish / AccPed / tqlim)
2. [ ] Axe RPM → factor **0.5** (Short #1)
3. [ ] Axe pédale → bouton **%** (Short #2)
4. [ ] Valeurs → factor **0.1**, precision **1**, unit **Nm** (Short #3)
5. [ ] Relire : tip-in ~10–50 Nm, WOT ~350–400 Nm, idle RPM ~800–1000
6. [ ] **Ensuite seulement** modifier

## 📊 Avant / Après (même map)

### Avant (raw — image Facebook)
```
rpm: 1000 … 10000
ped: 0, 819, …, 8192
WOT@1000: 4032
```

### Après (3 conversions)
```
rpm: 500 … 5000
ped: 0%, ~10%, …, 100%
WOT@500rpm: 403.2 Nm
```

## 📎 Image Source

`fiche-assets/edc17-short-04-facebook.jpg`

## 🔗 Fichiers Liés

- `EDC17-RPM-FACTOR-CRITICAL.md` (#1)
- `EDC17-PEDAL-AXIS-CRITICAL.md` (#2)
- `EDC17-TORQUE-FACTOR-CRITICAL.md` (#3)
- `shorts/04-raw-storage-before-conversion.md`

---

**⚠️ RÈGLE D'OR EDC17 : JAMAIS MODIFIER EN RAW SANS LES 3 CONVERSIONS.**

L'ECU ne stocke pas des Nm — seulement des entiers. WinOLS traduit.

---

**Dernière mise à jour :** 27 oct 2026 12:34 UTC-3  
**Status :** ✅ Synthèse critiques #1+#2+#3
