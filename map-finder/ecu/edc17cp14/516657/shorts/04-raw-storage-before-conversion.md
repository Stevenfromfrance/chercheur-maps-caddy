# Short #4 : Raw Storage — Ce que l'ECU stocke vraiment

**Durée :** ~40 sec | **ECU :** EDC17CP14 | **SW :** 516657 | **⚠️ SYNTHÈSE #1+#2+#3**

## 🎯 Objectif

Voir une map **telle qu'elle est en flash** (nombres bruts), puis comprendre pourquoi les 3 conversions sont obligatoires.

## 🔍 Phrase Clé

> **Your ECU doesn't store Nm.**  
> It stores raw numbers: **8192 = 100 % pedal**, **4032 = 403.2 Nm**.

## 🖼️ Exemple (Driver's wish brut)

| Raw | Signifie | Conversion |
|---|---|---|
| **8192** (axe) | 100 % pédale | Short #2 → % |
| **4032** (cellule) | 403.2 Nm | Short #3 → ×0.1 |
| **10000** (axe) | 5000 rpm | Short #1 → ×0.5 |

Highlight orange du short : colonne 8192 × ligne 1000 → **4032**.

## 🔧 Workflow (ordre)

1. ✅ Regarder la map **raw** (ne rien toucher)
2. ✅ Axe RPM → factor **0.5**
3. ✅ Axe pédale → bouton **%**
4. ✅ Valeurs → factor **0.1** + precision **1** + unit **Nm**
5. ✅ Vérifier : WOT ~350–400 Nm, pas 3500–4000

## ⚠️ Erreurs Courantes

- ❌ Croire 4032 = 4032 Nm  
- ❌ Capper à « 350 » en raw → réel **35 Nm**  
- ❌ Comparer raw A5 vs Nm Caddy sans convertir  

## ✅ Vérification Rapide

Après les 3 conversions :
- [ ] WOT max ~**400 Nm** (pas 4000)
- [ ] Pédale max **100 %** (pas 8192)
- [ ] Redline ~**5000 rpm** (pas 10000)

## 🔗 Source

https://www.facebook.com/share/r/1M2ppwKwZW/?mibextid=wwXIfr

**Image :** `../../../../../fiche-assets/edc17-short-04-facebook.jpg`

## 📎 Shorts Liés

- `01-rpm-factor-x2.md`
- `02-pedal-axis-8192.md`
- `03-torque-factor-01.md`
- `../../../../../EDC17-RAW-STORAGE-CRITICAL.md`

---

**⚠️ JAMAIS MODIFIER EN RAW — CONVERTIR D'ABORD (#1+#2+#3).**

---

**Status :** ✅ Synthèse validée
