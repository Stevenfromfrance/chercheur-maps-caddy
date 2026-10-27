# Short #3 : Torque Factor 0.1 — EDC17

**Durée :** ~30 sec | **ECU :** EDC17CP14 | **SW :** 516657 | **⚠️ CRITIQUE**

## 🎯 Objectif

Appliquer **factor 0.1** + **precision 1** sur les maps couple (Nm) pour afficher le dixième de Nm.

## 🔍 Pourquoi ?

```
EPROM raw : 153
× factor 0.1 → 15.3 Nm
```

**Un chiffre de précision en plus** vs factor 1.0 (qui donnerait seulement 15 Nm).

## 🔧 WinOLS (Properties)

1. ✅ Ouvrir map couple (ex. **Driver's wish**)
2. ✅ Properties / Factor, offset
3. ✅ **Factor = 0.1**
4. ✅ **Offset = 0**
5. ✅ **Unit = Nm**
6. ✅ **Precision = 1**
7. ✅ Formule : `Value = 0.1 * Eprom + 0`

## 📊 Exemple

| Raw | Affiché (factor 0.1) |
|---|---|
| 153 | **15.3 Nm** |
| 547 | **54.7 Nm** |
| 1188 | **118.8 Nm** |
| 3500 | **350.0 Nm** |
| 4000 | **400.0 Nm** |

## ⚠️ Erreurs Courantes

### ❌ Factor oublié (1.0)
```
Écrire "350" pour 350 Nm
→ Stocke 350 raw = 35.0 Nm réel
```

### ❌ Factor PCR2.1 (0.03125−1024)
```
Ne pas copier le factor Caddy sur EDC17
→ Nm absurdes
```

### ❌ Precision 0
```
Factor 0.1 + Precision 0
→ Perd le 0.3 de 15.3 Nm
```

## ✅ Vérification Rapide

- [ ] WOT stock ~**400 Nm** (pas 4000)
- [ ] Tip-in bas ~**15–50 Nm** (pas 150–500)
- [ ] Cap Stage1 ~**350 Nm** affiché
- [ ] Hardcut = **0.0 Nm**

## 🔗 Triple Conversion AccPed

| Élément | Action | Short |
|---|---|---|
| Axe RPM | factor **0.5** | #1 |
| Axe pédale | bouton **%** | #2 |
| **Valeurs Nm** | factor **0.1** | **#3** |

Les **trois** sont obligatoires pour lire AccPed / Driver's wish correctement.

## 🔗 Source

**Facebook :** https://www.facebook.com/share/r/19EQXUuYcA/?mibextid=wwXIfr

> "WHY TORQUE HAS FACTOR 0.1 — One extra digit of precision"

**Image :** `../../../../../fiche-assets/edc17-short-03-facebook.jpg`

## 📎 Fichiers Liés

- `01-rpm-factor-x2.md`
- `02-pedal-axis-8192.md`
- `../../../../../EDC17-TORQUE-FACTOR-CRITICAL.md`

---

**⚠️ FACTOR 0.1 + PRECISION 1 SUR TOUT COUPLE EDC17 (Nm) !**

---

**Dernière mise à jour :** 27 oct 2026  
**Status :** ✅ Validé — critique #3
