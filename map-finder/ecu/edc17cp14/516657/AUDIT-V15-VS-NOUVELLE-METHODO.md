# Audit A5 Bertin V1.5 × Nouvelle méthodologie EDC17

**Verdict mis à jour :** V1.5 avait encore des **erreurs PCR2.1** (wish/gear fill + redline +8 %).  
→ **Corrigé dans V1.6 SAFE** (`build_v16_0aw_safe.py`) — fichier de confiance **sans logs**.

Date audit : 27 oct 2026 · Soft **516657**  
Flash : `A5_516657_V1.6_0AW_SAFE_noPCR_wish_noRPMup_injtime_turbo_DPF_EGR_noCHK.fls`

---

## 1. Scorecard rapide

| Critère méthodologie | V1.5 | Note |
|---|:-:|---|
| Factors WinOLS (RPM 0.5 / pédale % / Nm 0.1) | 📄 | Process lecture — à formaliser atelier |
| Driver's wish = first map | ✅ | Torque Request maps touchées |
| wish ≤ limiteurs (turbo lim monté avec turbo) | ✅ | Turbo +3.98 % **et** limiteur turbo +3.97 % |
| InjTime +1–13 % | ✅ | **+1.71 %** méd, cap +3 % |
| SOI advance avec fuel | ✅ | Timing ~+5 % |
| Smoke / lambda marge | ✅ | Higher Lambda ~+5 % |
| Turbo +4–8 % | ⚠️ | **~+4.0 %** (bas de fourchette) |
| EGR/DPF = 0 | ✅ | Pack **DaVinci** (mieux que switches manuels YT) |
| Clear limiters before requests | ⚠️ | Plafonds couple **ORI** (choix 0AW) |
| VGT playbook 95/5 | ❌ | Maps VGT présentes KP, **non touchées** V1.5 |
| Hot Start / Idle FIX | ❌ | Absent (vidéo YT + Lesson 21 cranking) |
| Limp / Error TQ raise | ❌ | Non documenté — **prudence 0AW** |
| Pas de launch | ✅ | Correct Multitronic |
| Checksum avant flash | ✅ | noCHK → CHK obligatoire |
| Logs complets | ⚠️ | VILLE / ROUTE_INJ / HARCUT seulement |

**Score :** ~**12/16 OK** · 3 gaps secondaires · 1 zone à surveiller (Gear TQ)

---

## 2. Ce qui est déjà correct (ne pas casser)

### Deletes
DaVinci DPF+EGR+FLAPS > chasse switches A6 505999. Garder.

### Pulse (Lesson 21 §4)
| Map | Δ méd V1.5 | Playbook |
|---|---:|---|
| Injection Time (us) `1D1496` | +1.71 % | +1–13 % ✅ |
| SOI Main (deg BTDC) | ~+5 % | more fuel → more advance ✅ |
| IQ #1 | +2 % | soft ✅ |
| IQ #2/#3/#4 | **ORI** | cruise soft ✅ |

### Air
| Map | Δ | Playbook |
|---|---:|---|
| Turbo Pressure ×7 | +3.98 % | +4–8 % → **seuil bas OK** |
| Limiter Turbo f(APS) | +3.97 % | **monté avec la consigne** ✅ (erreur YT évitée) |
| Rail / lim rail | +3 % | prudent ✅ |

### 0AW
- Pas de launch ✅  
- Fill sous 400 + plafonds ORI ✅ (philosophie conservatrice)  
- Blocages G83 / EGT / FAP physiques ✅

---

## 3. Points à revoir / corriger

### 🔴 P1 — Torque Request Gear 1–5 (+36 à +51 % méd)

Maps `Torque Request - Gear N` fortement touchées.  
Lesson 21 : **Gearbox protection** = cap R/1re pour protéger la boîte.

**Risque 0AW Multitronic :** wish trop haut en 1–2 peut stresser la CVT même si « plafond ORI » ailleurs.

**Action :**
1. WinOLS : factors 0.1 + axes RPM 0.5 — lire **max Nm** par rapport (pas seulement %)
2. Vérifier que max ≤ ~400 Nm et que **1re / bas régime** n’est pas plus agressif que stock WOT
3. Si max Gear1/2 > stock WOT → **reculer** en V1.6 (priorité sécurité 0AW)

### 🟠 P2 — Driver's Wish lecture (shorts #5–#6)

Formaliser checklist atelier :
- Tip-in 0–10 % = soft / 0 Nm ?
- Saturation WOT dès quel % pédale ?
- Sweep @ 1500 / 2000 / 3000 progressif ?

**Action :** session WinOLS 30 min + capturer grilles ORI vs V1.5 (comme fiche Caddy AccPed).

### 🟠 P3 — Chaîne wish ≤ tqlim ≤ smoke

Expliciter dans une fiche :
- Max Driver wish / Torque Request  
- Max `Limiter of Maximum Torque`  
- Max Smoke Higher Lambda (équivalent marge fumée)

**Action :** extraire 3 max depuis KP/WinOLS → tableau dans `FICHE-EDC17-CHAIN.md`.

### 🟡 P4 — VGT non touché

Maps `Variable Geometry (VGT)…` @ `1D3796`… existent, **0 cellule** dans compare V1.5.  
Playbook : après +fuel/+turbo, VGT peut aider bas régime — **pas obligatoire** Stage1 soft.

**Action V1.6 optionnelle :** seulement si logs ROUTE_TURBO montrent lag ; sinon laisser.

### 🟡 P5 — Hot Start / Idle

Absent V1.5. YouTube + Lesson 21 cranking.  
**Action :** seulement si hard start / ralenti instable **après** flash + deletes. Chercher équivalents via A2L 0005 (noms Hot start / Start torque / LLK).

### 🟡 P6 — Turbo +4 % pile bas de fourchette

Légèrement sous « +4–8 % ». OK pour 0AW.  
**Ne pas monter** sans logs MAP + EGT.

### 🟢 P7 — Doc / process (pas binaire)

| Manque | Livrable |
|---|---|
| Factors WinOLS | Checklist short #1–#3 dans README A5 ✅ partiel |
| Logs incomplets | Ajouter ROUTE_RAIL, ROUTE_TURBO, ROUTE_HOT |
| Fiche changements type Caddy | Générer via `analyze_v15_detailed.py` |
| Limp Error TQ | Noter « ne pas raise 550 sur 0AW » |

---

## 4. Plan d’amélioration recommandé

### Phase A — Sans reflash (immédiat)
1. ✅ Audit écrit (ce fichier)
2. Checklist WinOLS lecture V1.5 (factors + sweep pédale + max Gear TQ)
3. Compléter `LOG-PROCEDURES` A5 (rail/turbo/hot)
4. Mettre `pack_later` à jour dans `project.json`

### Phase B — Après G83 + 1er flash V1.5
1. Logs VILLE + ROUTE_INJ + ROUTE_TURBO + HARCUT  
2. Décider V1.6 seulement si :
   - fumée / EGT / rail décroche, **ou**
   - hard start, **ou**
   - Gear TQ trop agressif mesuré

### Phase C — V1.6 possible (si logs le demandent)
| Levier | Direction |
|---|---|
| Gear 1–2 TQ | Soft vers ORI si 0AW souffre |
| InjTime | Garder ≤ +3 % sauf ROUTE_INJ OK pour +5–8 % |
| Turbo/VGT | +1–2 % seulement si MAP lag + limiteur suivi |
| Hot start / Idle | Patch dédié si symptôme |
| Limp 550 | **Non** par défaut sur 0AW |

---

## 5. Réponse directe

> Est-ce que le travail A5 peut être corrigé / revu / amélioré ?

**Oui — surtout revue + doc + validations.**  
Le binaire V1.5 n’est **pas** « faux » au regard de la nouvelle méthodo : InjTime, SOI, lambda, turbo+limiteur, DaVinci, 0AW sans launch = **conforme playbook**.

Les vrais chantiers :
1. **Sécurité 0AW** : auditer Torque Request Gear (P1)  
2. **Méthode lecture** : factors + sweeps (P2–P3)  
3. **Après logs** : Hot start / VGT / turbo seulement si besoin (P4–P5)

**Ne pas** remplacer DaVinci par les adresses YouTube A6 505999.  
**Ne pas** appliquer limp 550 Nm Lesson 21 aveuglément.

---

## 6. Fichiers liés

- `LIVRAISON-V1.5-0AW.txt` · `A5_516657_V1.5_0AW_manifest.json` · `v15_kp_compare.json`  
- `../../../../EDC17-LESSON21-TUNING-GUIDE.md`  
- `../../../../EDC17-YOUTUBE-DPF-EGR-HOTSTART.md`  
- Shorts `#1–#18`
