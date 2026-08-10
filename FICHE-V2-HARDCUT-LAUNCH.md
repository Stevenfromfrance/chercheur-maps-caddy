# FICHE V2 — ami hardcut + launch (sur base V1)

**Fichier :** `Caddy_CAYE_03L906023TB_9979_MOD_V2_hardcut_launch.NOCS`  
**Source :** `caddy 1_6 tdi - stage 1 dpf off egr off + hardcut 4.8k + launch 2.5k`  
**Base :** V1 (272 octets différents seulement)

## Ce que l’ami a fait

1. **Annulé ton softcut AccPed / tqlim_base**  
   Tu avais mis 0 Nm dès ~5000 rpm (AccPed) et dès 4800 (tqlim).  
   L’ami a remis les valeurs ORI (descente douce) à ces régimes.

2. **Hardcut via `tqlim_cluth_prot` (clutch protection)**  
   - Axe RPM remappé : `800, 1000, 2000, 2500, 2501, 3000, 4800, 4801`  
   - Ligne **4801 rpm = 0 Nm** sur toute la map → coupure dure  
   - Adresse map `1D0860` · axe Y `1A612A`

3. **Launch test ~2500 rpm**  
   - Même map clutch-prot  
   - À ratio vitesse/régime ≈ 0 (véhicule arrêté / embrayage), couple → 0 autour de 2500–2501  
   - **À valider au log VCDS** (pas encore prouvé en route)

## Diffs octets

| Paire | Octets |
|---|---:|
| V1 → V2 | **272** |
| ORI → V2 | ~25496 |
| ACE → V2 | ~6422 |

## Points d’attention / risques

- Le hardcut **ne passe plus** par AccPed / tqlim_base : il dépend de `tqlim_cluth_prot`. Si cette map n’est pas active dans le chemin couple, le cut 4800 peut ne pas tenir.
- À **4800 rpm** (pas 4801), seul le 1er point (ratio≈0) est à 0 — hardcut “plein” surtout à **4801**.
- Launch = expérimental : tester frein à main + log régime/couple avant usage route.
- Le reste de ta V1 (350 WOT, rail 1620, smoke, deletes) est **conservé**.

## Flash

- Fichier à flasher si tu valides V2 : `...MOD_V2_hardcut_launch.NOCS` (KESS **CHK**)
- Sinon reste sur V1 jusqu’à validation log du hardcut / launch
