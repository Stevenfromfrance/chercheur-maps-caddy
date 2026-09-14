# FICHE V5f — FINAL (V5e + EGT lim milieu ~320)

**Fichier :** `Caddy_CAYE_03L906023TB_9979_MOD_V5f_final_tegt320.NOCS`  
**Base :** V5e (`launch0 + tqlimV6f + AccPedV6e`)  
**Rôle :** carto flash finale atelier (derniers avancés)

## Contenu

| Couche | V5e | **V5f FINAL** |
|---|---|---|
| AccPed | V6e | **inchangé** |
| tqlim_base | V6f fill haut régime | **inchangé** |
| Launch | 0 Nm @2700/2800/3000 | **inchangé** (hold pratique **~2800**) |
| **tqlim_tegt** | ORI max **290** | **milieu ORI↔ACE** blend 50 % → max **~320** (ACE=350) |
| smoke / HC / turbo / rail | inchangé | **inchangé** |

Octets ≠ V5e : **386**

## Pourquoi tegt milieu

- Jour chaud = moins de pêche → ORI 290 trop strict possible
- ACE 350 = plafond Stage1 connu, mais V5e monte déjà le haut régime
- Compromis **~320** = entre safe ORI et ACE, sans aller au-dessus d’ACE

## Flash

1. KESS **CHK**
2. Clear DTC
3. Logs : `fiche-logs-vcds-a4-v5e.html` (mêmes runs, soft = **V5f**)

## Risques

- tegt plus haut qu’ORI → un peu moins de frein couple à EGT élevée (voulu)
- Toujours surveiller fumée / EGT ressenti / MAP sur ROUTE_SOFT

## VERIFY

Voir `VERIFY-V5F.txt`.
