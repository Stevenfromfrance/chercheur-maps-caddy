# ⚠️ EDC17 DRIVER'S WISH — LECTURE RPM + PÉDALE (CRITIQUE #5)

## 🎯 Découverte (Facebook Post)

**Source :** https://www.facebook.com/share/r/14tgFQF5D9C/?mibextid=wwXIfr

### Phrase clé

> **"Full torque demand doesn't always need 100 % pedal. In this map, from 500 to 1500 rpm the ECU already asks for the full 403 Nm at 70 % pedal."**

Titre image : **READ FROM TWO VALUES — RPM + pedal · ACCELERATOR PEDAL**

## 📐 Principe

Une cellule Driver's wish / AccPed = **f(RPM, % pédale) → Nm demandés**.

| Entrée | Rôle |
|---|---|
| **RPM** (axe Y) | régime moteur (après factor 0.5) |
| **% pédale** (axe X) | après conversion 8192→% |
| **Cellule** | couple demandé (après factor 0.1) |

**Ne jamais lire une seule ligne ou une seule colonne.** Toujours croiser les deux.

## 📊 Map Exemple (après #1+#2+#3)

Valeurs Nm (Driver's wish stock typique ~403 Nm) :

| RPM \\ Pedal % | 0 | 10 | 13 | 20 | 30 | 50 | **70** | **100** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **500** | 0 | 0 | 15 | 55 | 119 | 264 | **403** | **403** |
| **750** | 0 | 0 | 15 | 52 | 113 | 256 | **403** | **403** |
| **1000** | 0 | 0 | 14 | 50 | 107 | 248 | **403** | **403** |
| **1250** | 0 | 0 | 14 | 47 | 101 | 240 | **403** | **403** |
| **1500** | 0 | 0 | 13 | 45 | 96 | 232 | **403** ★ | **403** |
| **1750** | 0 | 0 | 12 | 43 | 92 | 225 | 394 | 403 |
| **2000** | 0 | 0 | 12 | 40 | 88 | 218 | 381 | 403 |
| **2500** | 0 | 0 | 10 | 37 | 82 | 204 | 355 | 403 |
| **3000** | 0 | 0 | 9 | 33 | 76 | 191 | 331 | 402 |
| **3500** | 0 | 0 | 8 | 30 | 70 | 179 | 309 | 379 |
| **4000** | 0 | 0 | 7 | 27 | 65 | 168 | 288 | 354 |
| **4500** | 0 | 0 | 6 | 25 | 60 | 157 | 268 | 329 |
| **5000** | 0 | 0 | 5 | 22 | 56 | 147 | 250 | 304 |

★ Cellule highlight short : **1500 rpm × 70 % → 403 Nm**

## 🔑 Insights Méthodologiques

### 1. Full torque ≠ toujours 100 % pédale
- **500–1500 rpm** : dès **70 %** pédale → déjà **403 Nm** (= WOT)
- Colonne 100 % = colonne 70 % dans cette zone (plateau saturé)
- Au-delà (~1750+) : 70 % **décroît**, 100 % reste plus haut plus longtemps

### 2. Tip-in très soft
- **0–10 %** : **0 Nm** (dead zone)
- **13 %** : démarre ~5–15 Nm
- **20–30 %** : montée progressive

### 3. Roll-off haut régime
- À **100 %** : 403 Nm jusqu'~3000, puis 379 @3500 → **304 @5000**
- À **70 %** : chute plus tôt (403 → 250 @5000)

## 🔄 Comparaison PCR2.1 (Caddy) vs EDC17

| Aspect | PCR2.1 Caddy (V5g) | EDC17 (short FB) |
|--------|--------------------|------------------|
| Lecture | RPM + pédale | **identique** |
| Tip-in soft | 0–~23 % vers ORI | 0–10 % = 0 Nm, 13 % soft |
| WOT seuil | souvent **≥85 %** | dès **70 %** bas régime |
| Plateau WOT | ~360 Nm mid | **403 Nm** (stock A5 ~400) |
| Roll-off | dès ~3800 | dès ~3000–3500 @100 % |
| Cap Stage1 | AccPed ~350–360 | A5 V1.5 : plafonds ORI / fill@400 |

**Transfert utile :** la logique « lire croisé RPM×pédale » est **identique** Caddy/A5.  
**Différence :** seuil saturation WOT (70 % EDC17 exemple vs ~85 % Caddy).

## ⚠️ Erreurs Courantes

### Erreur #1 : Ne regarder que la colonne 100 %
```
❌ "Je Stage1 seulement la colonne 100 %"
→ Ignorer que 70 % = déjà full à bas régime
→ Sensation on/off ou incohérence partiels hauts
```

### Erreur #2 : Monter 70 % et 100 % différemment bas régime
```
❌ 70 % = 403, 100 % = 450 entre 500–1500
→ Inutile : conducteur atteint déjà 403 à 70 %
→ Mieux : garder plateau cohérent 70–100 % bas régime
```

### Erreur #3 : Cap tip-in
```
❌ Cap global 350 Nm y compris 13–30 %
→ Conduite ville cassante
✅ Soft tip-in, cap seulement ≥50–70 %
```

### Erreur #4 : Oublier les conversions
```
Sans #1+#2+#3 la map est illisible
→ Faire Shorts #1–#4 AVANT cette lecture
```

## ✅ Checklist Lecture AccPed EDC17

1. [ ] Conversions #1+#2+#3 appliquées
2. [ ] Identifier dead zone 0–10 %
3. [ ] Identifier tip-in 13–30 %
4. [ ] Identifier saturation WOT (ici dès **70 %** @500–1500)
5. [ ] Identifier roll-off haut régime (100 % et 70 %)
6. [ ] Avant Stage1 : noter max stock (ici **403 Nm**)
7. [ ] Cap cible cohérent 70 % **et** 100 % bas régime

## 🎯 Application A5 Bertin (V1.5)

Contexte repo : A5 CGKA ~**400 Nm** stock, 0AW, V1.5 conservateur.

| Zone | Stock (short) | V1.5 logique repo |
|---|---|---|
| Tip-in | 0 Nm @0–10 % | rester soft / ORI |
| WOT bas | 403 @≥70 % | plafonds ORI / fill sous 400 |
| Haut régime | roll-off | hardcut + SOI (pas launch 0AW) |

**Ne pas copier un plateau Caddy 360 « à 85 % » aveuglément** : sur EDC17, vérifier d'abord à quel % le stock sature déjà.

## 📎 Image Source

`fiche-assets/edc17-short-05-facebook.jpg`

## 🔗 Fichiers Liés

- Shorts #1–#4 (conversions + raw)
- `shorts/05-drivers-wish-rpm-pedal.md`
- `METHODOLOGIE-EDC17-RECAP.md`
- PCR2.1 : `FICHE-CHANGEMENTS-ORI-V1.md`, `FICHE-V5G-360.md`

---

**⚠️ DRIVER'S WISH = TOUJOURS LIRE RPM × % PÉDALE. FULL TORQUE PEUT SATURER AVANT 100 %.**

---

**Dernière mise à jour :** 27 oct 2026 12:36 UTC-3  
**Status :** ✅ Méthodologie lecture AccPed
