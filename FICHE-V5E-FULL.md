# FICHE V5e — pack complet (launch 0 + tqlim V6f + AccPed V6e)

**Fichier :** `Caddy_CAYE_03L906023TB_9979_MOD_V5e_launch0_tqlimV6f_accpedV6e.NOCS`  
**Base :** V5d (`tegtORI + launch110` → launch remis à 0)

## Contenu

| Couche | V5d | **V5e** |
|---|---|---|
| AccPed | fill V5 | **V6e** soft 0–23% + hold 75–85% + WOT fill 4000→5355 |
| tqlim_base | 370 plat puis cliff @4000 | **V6f** fill 4000→~347 / 4200→~332 / 4600→~291 (≥4800 inchangé) |
| Launch hold | 110/85 @2700–3000 | **0 / 0** (axe inchangé → hold pratique **~2800**, pas 2500) |
| tegt / smoke / HC | ORI / 375 / 4800 | **inchangé** |
| Turbo / rail / SOI | héritage ACE | **inchangé** |

Octets ≠ V5d : **490**

## Pourquoi

1. Soft 3ᵉ WOT confirmé ~3865–4236 → tqlim cliff + AccPed WOT fill
2. Tip-in ville trop sec → AccPed soft vers ORI
3. Launch 110 non validé + tu veux 0 Nm → hold à **2800** (axe déjà là), couple 0

## Flash

1. KESS **CHK**
2. Clear DTC
3. Logs : fiche A4 `fiche-logs-vcds-a4-v5e.html` (max 4–6 IDE / run)

## VERIFY

`VERIFY-V5E.txt` · hardcut 4801 OK · axis launch 2700/2800/3000 inchangé · tqlim max Δ +84.5 Nm @ATM1000

## Risques

- tqlim plus haut ≥4000 → plus de couple / fumée / EGT possible : surveiller
- AccPed soft = moins de couple bas pédale (voulu)
- Launch 0 = plus de lag spool possible au départ (comme V2) mais hold plus haut (~2800)

## Logs prioritaires (fréquence max)

| Run | IDE | Fichier |
|---|---|---|
| VILLE_SOFT | 4 | `CADDY_9979_V5e_VILLE_SOFT_…csv` |
| ROUTE_SOFT | 6 | `CADDY_9979_V5e_ROUTE_SOFT_…csv` |
| DEPART | 5 | `CADDY_9979_V5e_DEPART_…csv` |
| HARDCUT | 4 | `CADDY_9979_V5e_HARDCUT_…csv` |

Voir `fiche-logs-vcds-a4-v5e.html` + `log-aide.html`.
