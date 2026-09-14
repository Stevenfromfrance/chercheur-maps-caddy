# FICHE V5d — EGT lim ORI + launch hold 110 (fichier unique)

**Fichier :** `Caddy_CAYE_03L906023TB_9979_MOD_V5d_tegtORI_launch110.NOCS`  
**Base :** `..._V5b_tqlim370.NOCS`

## Contenu vs voiture (Italie + launch + hardcut = V2)

| Couche | Voiture V2 | **V5d** |
|---|---|---|
| AccPed / smoke / tqlim | Italie / ~350 | **V5 fill + smoke 375 + tqlim 370** |
| Launch hold | **0 Nm** @2501 | **110 / 85 Nm** @2700–3000 |
| Hardcut | 4800 | **4800 inchangé** |
| `tqlim_tegt_temp` | ACE souple (~350) | **ORI stock** (max ~290) |
| Turbo / rail / SOI | Italie | Italie (héritage, pas retouché ici) |

Octets ≠ V5b : **398** (tegt 386 + launch 12)

## 1) EGT lim → ORI

- Map `tqlim_tegt_temp` @`1D35A8` (512 B)
- Max Nm : 350 (ACE/V5b) → **290** (ORI)
- Effet : coupe couple plus tôt si EGT haute — plus safe, pas de gain puissance à froid

## 2) Launch hold 110 / 85

| RPM | V2 | V5b | **V5d** |
|---|---|---|---|
| 2700/2800/3000 col0 | 0 | 90 | **110** |
| 2700/2800/3000 col1 | — | 70 | **85** |
| 4800/4801 | hardcut | hardcut | **hardcut** |

## Flash

1. KESS **CHK**
2. Clear DTC
3. Logs : `DEPART` (launch) puis `ROUTE_RAIL` / `VILLE` si besoin Stage1
4. Fichier log launch : `CADDY_9979_V5d_DEPART_LAUNCH_YYYYMMDD.csv`

## Log DEPART (après flash)

**Type :** `DEPART`

### IDE (noms exacts VCDS ADVMB)

- IDE00021 — Engine RPM
- IDE00075 — Vehicle speed
- IDE00086 — Accelerator pedal position
- IDE00100 — Engine torque-TQI_SP
- IDE00188 — Fuel high-pressure: actual value-FUP_FIL
- IDE00201 — High fuel pressure: specified value-FUP_SP_KPA
- IDE00190 — Charge air pressure: specified value-MAP_SP_MMV
- IDE00191 — Charge air pressure: actual value-MAP_MMV
- IDE00347 — Air mass: actual value:

### Conditions

ASR **OFF** · 1ʳᵉ · frein à main · embrayé · hold **~2800** (pas 2500)

### Séquence

Start → plein gaz 2–3 s @~2800 → départ contrôlé → Stop → `CADDY_9979_V5d_DEPART_LAUNCH_YYYYMMDD.csv`

### À prouver

1. Hold : TQI_SP ~100–120 Nm (plus 0) · MAP monte
2. Départ : speed > 0 sans patinage long

### Interdits

Hardcut dans le même CSV · ASR ON · hold à 2500

Voir `log-aide.html` run DEPART.

## Note naming

- **V5c** (launch seul) = obsolète / intermédiaire — préférer **V5d**
- V5d = intention « un seul fichier » (EGT ORI + launch + stack V5b)
