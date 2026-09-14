# FICHE V5g — 360 Nm long band (dernier Stage1 stock)

**Fichier :** `Caddy_CAYE_03L906023TB_9979_MOD_V5g_360_longband.NOCS`  
**Base :** V5f FINAL (`tegt~320` + launch0 + tqlimV6f + AccPedV6e)  
**Rôle :** évolution MAX full stock avant pièces (filtre / IC / turbo / embrayage)

## Plan chiffré (forme)

| Zone | Cible |
|---|---|
| Tip-in 0–~23 % pédale | **Soft gardé** (vers ORI) |
| 1500–2000 + partiels | **Plus réactif** (ACE + bonus, sans on-off) |
| WOT ~2000–3800 | **~360 Nm** plateau |
| Dès **3800** | Roll-off **progressif** (anti-falaise) |
| ≥4200–4500 | Descente claire (pas 360 jusqu’au cut) |

**Pourquoi roll-off @3800 (pas 3600) :** logs V5f montrent MAP qui suit encore vers ~4000 ;
garder le plateau jusqu’à 3800 allonge la plage utile ; commencer plus tôt (3600) raccourcit
sans gain safety net. Au-delà de ~4200 on ne force pas (GTC12 stock).

**Tip-in vs 1500–2000 :** `soft_k` seulement pédale basse → ORI. La réactivité touche
pédale **≥~45 %** entre **~1400–2600** rpm — donc premier millimètre toujours doux,
reprises mid plus accrocheuses.

## Chaîne couple

| Couche | V5f | **V5g** |
|---|---|---|
| AccPed | V6e (~333–338 WOT) | **V6g** soft + réactif 1.5–2k + WOT **360** + roll-off |
| tqlim_base | V6f (~370 + fill) | **V6g** 370 plat → roll-off dès 3800 |
| tqlim_tegt | blend 50 % → max **~320** | **V6g** EGT&lt;800 → jusqu’à **360** mid ; chaud = blend 0.85 |
| smoke | **375** | **inchangé** (marge au-dessus de 360) |
| rail | héritage | **inchangé** (ne pas forcer la pompe) |
| Launch / HC | 0 @2700–3000 / 4800 | **inchangé** |

Ordre : **wish 360 &lt; tqlim 370 ≤ smoke 375**.

Octets ≠ V5f : **862**

## Flash

1. KESS **CHK**
2. Clear DTC
3. Soft noté **V5g**

## Risques

- +~20–25 Nm vs V5f → un peu plus de fumée / EGT possible : **ROUTE_AIR + miroir**
- tegt plus permissif à EGT modérée → jour chaud moins « mou », mais surveiller
- Rail non touché : si FUP réel décroche → ne pas monter rail, redescendre wish

## Logs post-flash (IDE exacts 9979)

Voir aussi `fiche-campagne-dev-carto.html` / `log-aide.html`.

### VILLE_TIPIN — tip-in soft conservé
- IDE00021 Engine RPM
- IDE00075 Vehicle speed
- IDE00086 Accelerator pedal position
- IDE00100 Engine torque-TQI_SP  
Fichier : `CADDY_V5g_VILLE_TIPIN_YYYYMMDD.csv`

### VILLE_REACT — reprises 1500–2000
- mêmes 4 IDE · pédale ~45–70 % · 3ᵉ  
Fichier : `CADDY_V5g_VILLE_REACT_YYYYMMDD.csv`

### ROUTE_CLIFF — plateau 360 + roll-off
- IDE00021 · IDE00075 · IDE00086 · IDE00100 · IDE00190 MAP_SP · IDE00191 MAP_ACT  
WOT 2000→4600 · prouver ~355–360 mid puis descente douce  
Fichier : `CADDY_V5g_ROUTE_CLIFF_YYYYMMDD.csv`

### ROUTE_AIR — fumée / air
- IDE00021 · IDE00086 · IDE00100 · IDE00191 · IDE00347 Air mass · IDE00025 Coolant  
+ note fumée miroir  
Fichier : `CADDY_V5g_ROUTE_AIR_YYYYMMDD.csv`

### ROUTE_RAIL — pompe
- IDE00021 · IDE00075 · IDE00086 · IDE00100 · IDE00188 FUP_FIL · IDE00201 FUP_SP  
Consigne ~1620 bar · réel ≤~1650–1670 pic  
Fichier : `CADDY_V5g_ROUTE_RAIL_YYYYMMDD.csv`

### ROUTE_HOT — tegt
- mêmes IDE que CLIFF · jour chaud · clim notée  
Fichier : `CADDY_V5g_ROUTE_HOT_YYYYMMDD.csv`

## VERIFY

Voir `VERIFY-V5G.txt`.
