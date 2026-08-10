# FICHE CHANGEMENTS — Caddy CAYE PCR2.1 SW 9979

**Comparaison exacte : ORI (stock) → V1 actuelle** (fichier à flasher)

| Fichier | Rôle |
|---|---|
| `ORI/Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin` | Stock usine |
| `MOD/..._MOD_ACE_stage1_dpf_egr.NOCS` | Stage1 prépa + FAP/EGR off (base) |
| `MOD/..._MOD_V1_350wot_smooth.NOCS` | **Ta carto V1** (ACE adoucie + rail famille) |

Taille dump : **2 097 152** octets (identique ORI / ACE / V1).

## 1. Résumé global octets

| Paire | Octets différents |
|---|---:|
| ORI → ACE (Stage1 + deletes) | **25778** |
| ORI → V1 (ta carto complète) | **25718** |
| ACE → V1 (seulement tes adoucissements) | **6473** |
| Zone DTC `19E000–1A3FFF` ORI→V1 | **72** |
| Zone DTC ACE→V1 | **0** (inchangé vs ACE) |

## 2. Philosophie V1 vs ORI

La V1 part d’**ACE**, puis adoucit. Vs **ORI** tu as donc **deux couches** :

1. **Hérité d’ACE** : turbo, nm2iq, SOI, deletes DTC, limiteurs secondaires…
2. **Retouché V1** : AccPed, tqlim principal, smoke, **toute la famille rail** (7 A2L + 14 hors A2L + 2 limiteurs).

| Leviers | ORI (stock) | V1 (cible) |
|---|---|---|
| AccPed WOT | ~294–380 Nm selon banque | **plafond ~350 Nm** + partiels soft |
| Limiteur couple principal | ~239 Nm | **~348 Nm** |
| Rail consigne | 1600 / 1450 bar | **~1620 / ~1468 bar** |
| Smoke | ~280–310 | **ORI×1.20 plafonné 360** |
| Hardcut | soft / tire loin | **4800 rpm → 0 Nm** |
| FAP/EGR DTC | actifs | **off** (via ACE) |
| Turbo / SOI / nm2iq | stock | **= ACE** (pas retouché V1) |

## 3. AccPed — banques (ORI → V1)

Grilles 8×16 (256 octets / banque).

| Adresse | max ORI | max ACE | max V1 | octets ORI→V1 | octets ACE→V1 |
|---|---:|---:|---:|---:|---:|
| `1CF9C0` | 293.7 | 380.0 | 350.0 | 142 | 148 |
| `1CFAC0` | 293.7 | 380.0 | 350.0 | 142 | 148 |
| `1CFBC0` | 293.7 | 380.0 | 350.0 | 142 | 148 |
| `1CFCC0` | 293.7 | 380.0 | 350.0 | 142 | 148 |
| `1CFDC0` | 293.7 | 380.0 | 350.0 | 142 | 148 |
| `1CFEC0` | 293.7 | 380.0 | 350.0 | 142 | 148 |
| `1CFFC0` | 234.9 | 340.0 | 334.8 | 138 | 147 |
| `1D0640` | 380.0 | 380.0 | 350.0 | 36 | 35 |

**Logique :** partiels calmes (blend faible vers ACE), WOT blend fort puis **cap 350 Nm**, ligne **≥4800 rpm = 0 Nm**.

## 4. Limiteur couple `tqlim_base_pu_4A`

- Adresse `1D3190`–`1D332F` · 8×26 · Nm
- max ORI **239.0** → ACE **350.0** → V1 **347.6**
- cellules ORI→V1 : **176** / 208 · octets ORI→V1 **352** · ACE→V1 **240**
- Hardcut 4800 sur la ligne régime correspondante.

## 5. Smoke — banques

| Adresse | max ORI | max ACE | max V1 | octets ORI→V1 | octets ACE→V1 |
|---|---:|---:|---:|---:|---:|
| `1D1D18` | 310.0 | 400.0 | 360.0 | 133 | 125 |
| `1D1FC4` | 310.0 | 400.0 | 360.0 | 133 | 125 |
| `1D2270` | 310.0 | 400.0 | 360.0 | 676 | 641 |
| `1D251C` | 290.2 | 400.0 | 348.0 | 160 | 154 |
| `1D27C8` | 280.0 | 400.0 | 336.0 | 135 | 139 |

**Logique :** `min(ORI × 1.20, 360)` là où ACE ≠ ORI.

## 6. Rail — famille complète (correctif V1b)

Règle unique : si ACE ≠ ORI, `V1 = ORI + 0.357×(ACE−ORI)` plafonné à **1620 bar** (1656 → 1620).

### 6.1 Banques A2L `rail_base_int_trq2B` (7)

| Adresse | max ORI | max ACE | max V1 | octets ORI→V1 | octets ACE→V1 |
|---|---:|---:|---:|---:|---:|
| `1E9368` | 1600.0 | 1656.0 | 1620.0 | 179 | 181 |
| `1E9568` | 1600.0 | 1656.0 | 1620.0 | 178 | 181 |
| `1E9768` | 1450.0 | 1500.7 | 1468.1 | 178 | 179 |
| `1E9968` | 1600.0 | 1656.0 | 1620.0 | 182 | 182 |
| `1E9B68` | 1600.0 | 1656.0 | 1620.0 | 182 | 182 |
| `1E9D68` | 1600.0 | 1656.0 | 1620.0 | 179 | 182 |
| `1E9F68` | 1600.0 | 1656.0 | 1620.0 | 179 | 182 |

### 6.2 Banques hors A2L (14) — alignées V1b

| Banque | Adresse | max ORI | max ACE | max V1 | octets ORI→V1 | octets ACE→V1 |
|---|---|---:|---:|---:|---:|---:|
| 01 | `1EA168` | 1600.0 | 1656.0 | 1620.0 | 177 | 182 |
| 02 | `1EA368` | 1450.0 | 1500.7 | 1468.1 | 178 | 179 |
| 03 | `1EA568` | 1600.0 | 1656.0 | 1620.0 | 176 | 180 |
| 04 | `1EA768` | 1600.0 | 1656.0 | 1620.0 | 176 | 180 |
| 05 | `1EA968` | 1600.0 | 1656.0 | 1620.0 | 176 | 180 |
| 06 | `1EAB68` | 1600.0 | 1656.0 | 1620.0 | 178 | 181 |
| 07 | `1EAD68` | 1600.0 | 1656.0 | 1620.0 | 176 | 182 |
| 08 | `1EAF68` | 1450.0 | 1500.7 | 1468.1 | 178 | 180 |
| 09 | `1EB168` | 1600.0 | 1656.0 | 1620.0 | 169 | 182 |
| 10 | `1EB368` | 1600.0 | 1656.0 | 1620.0 | 178 | 182 |
| 11 | `1EB568` | 1600.0 | 1656.0 | 1620.0 | 173 | 182 |
| 12 | `1EB768` | 1600.0 | 1656.0 | 1620.0 | 180 | 182 |
| 13 | `1EB968` | 1600.0 | 1656.0 | 1620.0 | 179 | 182 |
| 14 | `1EBB68` | 1600.0 | 1656.0 | 1620.0 | 179 | 182 |

### 6.3 Limiteurs rail hors A2L

| Id | Adresse | max ORI | max ACE | max V1 | octets ORI→V1 | octets ACE→V1 |
|---|---|---:|---:|---:|---:|---:|
| limA | `1EBDD8` | 1600.0 | 1656.0 | 1620.0 | 87 | 87 |
| limB | `1EBE58` | 1600.0 | 1656.0 | 1620.0 | 87 | 87 |

**Avant V1b :** seules les 7 A2L à ~1620 ; 14+2 encore ACE (~1656). **Maintenant : 21 blocs rail cohérents** (7+14+2).

## 7. Hérité d’ACE (≠ ORI, mais V1 = ACE)

| Map | Adresse | max ORI | max V1 (=ACE) | octets ORI→V1 | ACE→V1 |
|---|---|---:|---:|---:|---:|
| `turbo_base3B` | `1C04AC` | 2420.1 | 2504.6 | 312 | 0 |
| `turbo_atm6A` | `1C6A2C` | 2500.0 | 2650.0 | 256 | 0 |
| `nm2iq_base_mg3A` | `1D7E38` | 52.3 | 54.9 | 170 | 0 |
| `soi_base_int_trq2A` | `18C380` | 8.9 | 8.9 | 123 | 0 |
| `tqlim_tegt_temp` | `1D35A8` | 290.0 | 350.0 | 386 | 0 |
| `tqlim_speed2A` | `1CEED4` | 300.0 | 350.0 | 96 | 0 |
| `vmax3` | `18047C` | 190.0 | 6553.5 | 2 | 0 |
| `airctl_hysteresisC` | `1D0100` | 234.0 | 0.0 | 21 | 0 |

Plus : **masques DTC FAP/EGR** `19E000–1A3FFF` (identiques ACE).

## 8. Non retouché volontairement vs ACE

- Turbo base / ATM
- nm2iq / SOI
- Autres tqlim (speed, tegt, fuel_temp…) sauf `tqlim_base_pu_4A`
- Deletes DTC

## 9. Checklist flash / log

1. Flash `…MOD_V1_350wot_smooth.NOCS` avec KESS **CHK**
2. Clear DTC
3. Log : couple, AccPed, rail, MAP, régime
4. Attendu vs ORI : Stage1 présent, rail ~1620 (pas ~1677), WOT ~330–350 Nm, hardcut 4800, partiels plus soft qu’ACE

## 10. Fichiers liés

- `RECETTE-V1.md`
- `VERIFY-V1-DIFF.txt`
- `VERIFY-V1-RAIL-FAMILY.txt`
- `patch_v1_rail_family.py`
- Backup : `…V1_350wot_smooth.NOCS.bak_pre_rail_family`

---
*Généré depuis binaires ORI / ACE / V1 — octets ORI→V1 = 25718, ACE→V1 = 6473.*
