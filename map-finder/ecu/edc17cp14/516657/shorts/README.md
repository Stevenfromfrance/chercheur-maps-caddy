# EDC17CP14 — Shorts Méthodologie

Collection de guides courts (30-60 sec) pour la reprogrammation EDC17CP14.

## ⚠️ PRÉREQUIS CRITIQUE

**Lire en priorité :** `01-rpm-factor-x2.md`

EDC17 stocke RPM ×2 → factor 0.5 WinOLS **obligatoire** sur tous axes RPM !

## 📋 Index Shorts

### Fondamentaux (à lire en ordre)
1. **[01-rpm-factor-x2.md](01-rpm-factor-x2.md)** ⚠️ **CRITIQUE**
   - RPM storage ×2
   - Factor WinOLS 0.5
   - Hardcut / Launch conversion

2. **[02-pedal-axis-8192.md](02-pedal-axis-8192.md)** ⚠️ **CRITIQUE**
   - Pédale 8192 = 100%
   - Conversion WinOLS (double-clic + %)
   - Identifier tip-in / WOT

3. **[03-torque-factor-01.md](03-torque-factor-01.md)** ⚠️ **CRITIQUE**
   - Couple Nm : factor **0.1** + precision **1**
   - Un chiffre décimal de plus
   - Driver's wish / tqlim / hardcut

4. **[04-raw-storage-before-conversion.md](04-raw-storage-before-conversion.md)** ⚠️ **SYNTHÈSE**
   - ECU ne stocke pas des Nm — que des raw
   - 8192 = 100 % · 4032 = 403.2 Nm · 10000 = 5000 rpm
   - Preuve visuelle #1+#2+#3 sur une map

5. **[05-drivers-wish-rpm-pedal.md](05-drivers-wish-rpm-pedal.md)** ⚠️ **LECTURE**
   - Lire AccPed = RPM × % pédale → Nm
   - Full torque dès **70 %** @500–1500 (pas besoin 100 %)
   - Tip-in / saturation / roll-off

6. ⏳ **06-a2l-similar-0005.md** (à créer)
   - Import A2L similar
   - Offset 0005 → 0008
   - Vérification noms maps

7. ⏳ **07-injection-time-soft.md** (à créer)
   - Map @ 0x1D1496
   - +1.7% médiane
   - Cap +3% vs ORI

### Maps Principales
4. ⏳ **04-iq-cruise-restore.md** (à créer)
   - IQ #2/3/4 → ORI
   - IQ #1 +2%
   - Logique Stage1 cruise

5. ⏳ **05-accped-wot-cap.md** (à créer)
   - Banques AccPed (si applicable)
   - Cap conservateur
   - 0AW Multitronic limits

6. ⏳ **06-smoke-lambda.md** (à créer)
   - Smoke limiters
   - Lambda +5%
   - Fill sous 400 Nm

7. ⏳ **07-rail-pressure.md** (à créer)
   - Rail family (si modifié V1.5)
   - Plafonds bar
   - Cohérence banques

### Pollution / DTC
8. ⏳ **08-dpf-egr-davinci.md** (à créer)
   - DaVinci packs
   - Masques DTC
   - Zone 0x19E000-0x1A4000

9. ⏳ **09-dtc-verification.md** (à créer)
   - Liste DTCs off
   - Vérification complète
   - Diff ORI vs MOD

### Flash / Logs
10. ⏳ **10-checksum-kess.md** (à créer)
    - WinOLS checksum
    - KESS V2 OBD
    - noCHK → CHK

11. ⏳ **11-logs-vcds-edc17.md** (à créer)
    - IDE VCDS A5
    - ROUTE_INJ priorité
    - VILLE, HARCUT

12. ⏳ **12-blocages-flash.md** (à créer)
    - G83 / P102A
    - EGT S3
    - FAP 55g régénération

## 🎯 Différences vs PCR2.1

| Short | PCR2.1 | EDC17 | Notes |
|---|:-:|:-:|---|
| **RPM ×2 factor** | ❌ | ✅ | **NOUVEAU** — critique #1 |
| **Pédale 8192** | ❌ | ✅ | **NOUVEAU** — critique #2 |
| **Couple factor 0.1** | ❌ (autre formule) | ✅ | **NOUVEAU** — critique #3 |
| **Raw storage view** | ⏳ | ✅ | **SYNTHÈSE** #1+#2+#3 |
| A2L similar | ❌ | ✅ | 0005 → 0008 |
| Injection Time | ❌ | ✅ | **NOUVEAU** @ 0x1D1496 |
| IQ cruise | ⏳ | ✅ | Logique différente |
| AccPed WOT | ✅ | ⏳ | Similaire |
| Smoke cap | ✅ | ⏳ | Similaire |
| Rail blend | ✅ | ⏳ | À documenter |
| Launch | ✅ | ❌ | N/A (0AW) |
| DPF/EGR | ✅ | ✅ | Méthode différente |
| Checksum | ✅ | ✅ | Similaire |

## 🔗 Références

- **Repository root :** `../../../../../`
- **Méthodologie complète :** `../../../../../METHODOLOGIE-EDC17-RECAP.md`
- **RPM factor détail :** `../../../../../EDC17-RPM-FACTOR-CRITICAL.md`
- **Template shorts :** `../../../../../METHODOLOGIE-SHORTS-TEMPLATE.md`

## 📝 Contribuer

Pour ajouter un short :

1. Copier template : `../../../../../METHODOLOGIE-SHORTS-TEMPLATE.md`
2. Créer `NN-nom-court.md` (NN = numéro séquence)
3. Suivre structure :
   - Durée + ECU + SW
   - Objectif (1 ligne)
   - Localisation (adresse + taille)
   - Étapes numérotées
   - Erreurs courantes
   - Vérification rapide
4. Ajouter dans ce README index

## 🎥 Vidéos

Si vidéos disponibles, les placer dans :
```
shorts-videos/
├── 01-rpm-factor.mp4
├── 02-a2l-similar.mp4
└── ...
```

---

**Dernière mise à jour :** 27 oct 2026  
**Statut :** 4/12 shorts créés (#1–#3 critiques + #4 synthèse raw)  
**Priorité :** Compléter #5-#12 selon ordre logique
