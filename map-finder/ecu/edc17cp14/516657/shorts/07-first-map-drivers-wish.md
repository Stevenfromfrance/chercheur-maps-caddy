# Short #7 : The First Map — Driver's Wish

**Durée :** ~30 sec | **ECU :** EDC17CP14 | **Prérequis :** Shorts #1–#4 (conversions)

## 🎯 Objectif

Comprendre que **Driver's wish** est la **première map du système** : elle transforme la pédale en **demande de couple (Nm)**.

## 🔍 Phrase Clé

> **The first map of the whole system: Driver's wish.**  
> It turns your pedal position into a torque demand.  
> **RPM on one axis, pedal on the other.**

## 📐 Structure

```
Pédale %  ×  RPM  →  Nm (wish)
         ↓
   Limiteurs / smoke / rail / turbo
```

| Axe | Contenu | Short |
|---|---|---|
| Y | RPM | #1 |
| X | % pédale | #2 |
| Cells | Nm demandés | #3 |

## 🔑 Place dans la Méthode

1. **Driver's wish** ← tu es ici
2. Torque limiters
3. Smoke / IQ
4. Rail / Injection Time
5. Turbo
6. DPF/EGR deletes

**Règle :** wish ≤ tqlim ≤ smoke

## 🔄 vs PCR2.1

**AccPed Caddy = Driver's wish EDC17** — même rôle (premier levier Stage1).

## ⚠️ Erreurs Courantes

- ❌ Commencer par smoke/rail avant le wish
- ❌ Croire wish = couple roue réel
- ❌ Modifier sans conversions #1–#3

## ✅ Vérification Rapide

- [ ] Map identifiée comme Driver's wish / AccPed
- [ ] Axes convertis (RPM 0.5, pédale %, Nm 0.1)
- [ ] Max stock noté (~403 Nm exemple)
- [ ] Tip-in soft + WOT + roll-off lus (#5/#6)

## 🔗 Source

https://www.facebook.com/share/r/1JDZ4dqzvv/?mibextid=wwXIfr

**Image :** `../../../../../fiche-assets/edc17-short-07-facebook.jpg`  
**Détail :** `../../../../../EDC17-FIRST-MAP-CRITICAL.md`

---

**⚠️ FIRST MAP = DRIVER'S WISH. TOUT PART DE LÀ.**
