# Lesson 21 — EDC16 & EDC17 Tuning Guide (Facebook → Repo)

**Source :** Facebook « ECU Explain » — *[Study ECU Remapping] Lesson 21: EDC16 & EDC17 Tuning Guide Techniques and Best Practices* (11 juin)  
**Images :** `fiche-assets/edc17-lesson21-01.jpg` … `05.jpg`  
**Complète** les shorts #1–#10 (WinOLS factors + AccPed + hex)

---

## 1. Anatomie de la puissance — Chaîne complète

> **Never tune one step without adjusting the downstream reactions.**

| Étape | Nom | Variables |
|---|---|---|
| 1 | **The Wish** | Pedal % + RPM |
| 2 | **The Translation** | Torque request (Nm) |
| 3 | **The Gatekeepers** | FAPS, EGT, Gearbox… |
| 4 | **The Pulse** | Duration (µs) + Timing (° BTDC) |
| 5 | **The Lungs** | Boost (mbar) + VGT / wastegate |

```
Wish → Translation → Limiters → Fuel → Air
```

**vs repo :** Short #7 (Driver's wish = first map) + règle Caddy `wish ≤ tqlim ≤ smoke` = même logique.

---

## 2. Driver's Wish (Engine Torque map)

- Fondation diesel tuning : pied → demande mathématique Nm
- Exemple nodes (autre véhicule que A5) :
  - Cruise : **30 % @ 1500 rpm → 10.1 Nm**
  - WOT : **100 % @ 2000 rpm → 475.1 Nm**
- **Takeoff logic :** appui lent = maps standard ; appui brusque = maps « Takeoff » agressives ; relâchement → 0

**vs A5 shorts #5–#6 :** même AccPed/Driver's wish ; stock A5 ~**403 Nm** @ WOT (pas 475).  
**vs Caddy AccPed :** tip-in soft + WOT cap + roll-off — même philo.

---

## 3. Gatekeepers — Limiters

> Un conducteur peut demander 450 Nm ; si limiteur = 400 Nm → ECU impose **400**.  
> **Raise limiters proportionally.**

| Limiteur | Rôle | Règle tuner (Lesson 21) |
|---|---|---|
| **FAPS** (atm) | Cap altitude | Ignorer zones **&lt; 900 hPa** |
| **FEGT** (EGT) | Coupe fuel si trop chaud | Surveiller / ne pas delete aveugle |
| **Gearbox** | Cap R / 1re | Respecter boîte (A5 = **0AW**) |
| **Cranking** | Couple froid bas | Pro tip : modif peut aider hard start |
| **Error Torque / Limp** | Safe mode | Remonter (ex. **550 Nm**) pour ne pas limper le Stage1 |

**vs A5 V1.5 :** plafonds couple **ORI** (conservateur 0AW) ; pas de raise limp documenté.  
**vs Caddy V5g :** `tqlim_base` 370, `tqlim_tegt` ~360 mid — limiteurs montés **proportionnellement** au wish 360.

---

## 4. The Pulse — Fuel Duration & Advance

> **Torque = fuel (Torque-to-IQ Conversion).**  
> Plus de puissance = plus de volume **et** timing précis.

| Paramètre | Unité | Règle |
|---|---|---|
| **Duration** | µs | Selon rail (bar) + volume (mm³) — more duration = more fuel |
| **Timing** | ° BTDC | 0° = TDC ; positif = advance ; **more fuel → more advance** |
| Négatif | retard | après TDC |

**Playbook safe :** Injection Time **+1 % à +13 %** (atomisation, pas trop de fumée).

**vs A5 V1.5 :** Injection Time @ `0x1D1496` — **+1.7 % méd, cap +3 %** → **dans la fourchette Lesson 21 (1–13 %)**, côté très soft.  
**vs Caddy :** SOI hérité ACE ; pas d'InjTime soft dédié documenté (opportunité transfert A5→Caddy).

---

## 5. Golden Ratio — Stoichiometry Diesel

| Essence | Diesel optimal |
|---|---|
| ~14.7:1 | **14.55:1** |

**Lambda** = multiplicateur du ratio parfait  
Exemple : `1.2 × 14.55 ≈ 17.5 AFR`  
**Sweet spot turbo diesel : Lambda 1.2 – 1.3**

> Ne pas modifier lourdement « Small Limit Lower Lambda » — respecter le ratio.

**vs A5 V1.5 :** `nosmoke_lambda +5 %` (aligné « respecter lambda / fumée »).  
**vs Caddy :** smoke cap 360–375 — même idée marge air/fuel.

---

## 6. Turbo Pressure & VGT

More fuel → more air (mbar). Contrôle = **VGT / wastegate duty**.

| Valeur VGT | Effet |
|---|---|
| **~95 % (fermé)** | Lames ferment échappement → turbine rapide → boost bas régime |
| **~5 % (ouvert)** | Lames ouvertes → échappement libre → purge haut régime |

⚠️ **Si tu montes la consigne turbo, monte aussi le limiteur turbo absolu** — sinon ECU bloque.

**Playbook :** boost zones utiles **+4 % à +8 %** ; **ne pas toucher** zone **1000 rpm 0-boost**.

**vs A5 :** turbo +6 % en V1.1 named ; V1.5 pas de détail VGT explicite.  
**vs Caddy V5g :** turbo = héritage ACE (inchangé V5g) ; logs ROUTE_TURBO prioritaires.

---

## 7. Tuner's Playbook — Safe Increments

| Levier | Incrément Lesson 21 | A5 V1.5 | Caddy V5g |
|---|---|---|---|
| **Règle 30 %** | +30 % wish → ~**30–35 mm³** fuel | wish soft / fill@400 | wish 360 |
| **Turbo** | +4–8 % ; leave 1k 0-boost | ~+6 % (V1.1) | héritage ACE |
| **Fuel Duration** | +1–13 % µs | **+1.7 % / cap +3 %** ✅ | SOI ACE |
| **EGR** | activation → **0** | DaVinci EGR off ✅ | via ACE ✅ |
| **Limp / Error TQ** | raise (ex. 550 Nm) | non doc | tqlim montés |

> Power is proportional. Never blind-crank numbers.  
> Clear the path (**limiters**) **before** commanding power (**requests**).

---

## 8. EDC16 vs EDC17 — Evolution, Not Revolution

> EDC17 files are larger, but **core math is identical**. If you can map 16, you can map 17.

| Feature | EDC16 C35 (BMW 530d) | EDC17 C46 (Passat 2.0 TDI) |
|---|---|---|
| Architecture | Standard size | Larger, more overlapping maps |
| Torque limiters | Real caps (ex. 400 Nm) | Sometimes **3000 Nm** (= « unlimited » ceiling) |
| Core logic | Pedal → Limiter → Fuel → Air | **Identical** |
| Cranking map | Modifiable hot/cold | Often zeroes — inject values for hard start |

**vs A5 EDC17CP14 516657 :**
- Fichier 2 Mo, maps overlapping → A2L similar 0005 nécessaire
- Plafonds ORI ~400 Nm (pas 3000) — **limiteurs « réels »** comme EDC16 exemple
- Chaîne logique identique aux shorts #1–#7

---

## 9. Final Takeaways (Lesson 21)

1. **Every digital %** = physical µs fuel or mbar air  
2. **Respect stoichiometry** (14.55:1 diesel ; lambda ~1.2–1.3)  
3. **Always clear limiters before raising requests**

---

## 10. Comparaison Globale — Gap Analysis

| Sujet Lesson 21 | Documenté shorts FB #1–#10 | A5 Bertin V1.5 | Caddy V5g | Action |
|---|:-:|:-:|:-:|---|
| Factors WinOLS RPM/pedal/Nm | ✅ #1–#4 | partiel | N/A (autre ECU) | Auditer builds A5 |
| Driver's wish lecture | ✅ #5–#7 | implicite | AccPed ✅ | OK |
| Hexdump basics | ✅ #8–#10 | — | — | OK formation |
| Chaîne Wish→Air | ✅ Lesson 21 | partiel | ✅ wish≤tqlim≤smoke | Doc chaîne A5 |
| Limiters FAPS/FEGT/GBX/Limp | ✅ Lesson 21 | ORI ceilings | tqlim/tegt ✅ | Doc lim A5 |
| InjTime +1–13 % | ✅ | **+1.7 %** ✅ | ❌ | Option Caddy |
| Lambda 14.55 / 1.2–1.3 | ✅ | +5 % nosmoke | smoke 375 | Aligner vocab |
| Turbo +4–8 % / VGT 95–5 | ✅ | +6 % V1.1 | ACE héritage | Doc VGT A5 |
| EGR = 0 | ✅ | DaVinci ✅ | ACE ✅ | OK |
| EDC16≈EDC17 logic | ✅ | — | — | Short #11 |
| A2L similar 0005 | ❌ | used | A2L exact | Short restant |

---

## 11. Shorts dérivés Lesson 21

| Short | Sujet |
|---|---|
| `11-torque-chain-downstream.md` | Never tune one step without downstream |
| `12-gatekeepers-limiters.md` | FAPS / FEGT / GBX / Limp |
| `13-fuel-duration-advance.md` | µs + ° BTDC ; +1–13 % |
| `14-lambda-1455.md` | 14.55:1 ; sweet spot 1.2–1.3 |
| `15-turbo-vgt-playbook.md` | VGT 95/5 ; boost +4–8 % |
| `16-edc16-vs-edc17.md` | Evolution not revolution |
| `17-safe-increments-playbook.md` | 30 % rule + checklist |

---

## 12. Implications A5 Bertin (priorité)

1. **V1.5 InjTime +1.7 %** = conforme playbook (sous 13 %) ✅  
2. **EGR/DPF off** = conforme ✅  
3. **Manque doc :** limiteur erreur / limp, FAPS, VGT explicite, lambda 14.55 wording  
4. **0AW :** gearbox limiter = ne pas copier « raise to 550 » aveuglément — boîte CVT fragile  
5. **G83 / EGT physiques** restent bloquants flash (déjà dans project.json)

---

**Dernière mise à jour :** 27 oct 2026 12:44 UTC-3  
**Status :** Lesson 21 intégrée + comparée repo
