# Guide logs VCDS — banc route (Caddy 9979)

ECU : `03L 906 023 TB` · Soft `9979`  
Page interactive : [log-aide.html](log-aide.html)

## Principe

- **1 log = 1 question** (rail, turbo, ville, hardcut, launch…)
- **Même route / même rapport** pour comparer les cartos (mini banc)
- Max **~12 IDE** dans VCDS (sinon sampling trop lent)
- CSV brut + soft flashé (`V2` / `V3`…) + ASR ON/OFF

## IDE core (toujours)

| IDE | Nom |
|---|---|
| IDE00021 | Engine RPM |
| IDE00075 | Vehicle speed |
| IDE00086 | Accelerator pedal |
| IDE00100 | Engine torque TQI |
| IDE00188 | Rail pressure actual |
| IDE00201 | Rail pressure specified |
| IDE00190 | MAP specified |
| IDE00191 | MAP actual |
| IDE00347 | Air mass |

Extras utiles si place : Coolant temp · Injection quantity · Torque limitation.

## Roadmap validation mappack

1. **ROUTE_RAIL** (priorité) — couple + rail
2. **ROUTE_TURBO** (priorité) — MAP consigne/réel
3. **VILLE** (priorité) — confort partiels
4. **HARCUT** — cut ~4800 en roulant
5. **DEPART** — launch (bonus V2/V3)
6. **ROUTE_INJ** — injection / smoke (bonus)

## Noms de fichiers

```
CADDY_{SOFT}_ROUTE_RAIL_YYYYMMDD.csv
CADDY_{SOFT}_ROUTE_TURBO_YYYYMMDD.csv
CADDY_{SOFT}_VILLE_YYYYMMDD.csv
CADDY_{SOFT}_HARCUT_YYYYMMDD.csv
CADDY_{SOFT}_DEPART_LAUNCH_YYYYMMDD.csv
CADDY_{SOFT}_ROUTE_INJ_YYYYMMDD.csv
```

Exemple : `CADDY_V3_ROUTE_RAIL_20260812.csv`

## Détail des runs

Utilise la page **log-aide.html** (boutons + copie IDE).  
Résumé :

### ROUTE_RAIL
- 3ᵉ/4ᵉ, WOT 1800→3500–4000 en charge
- Prouver : couple ~320–340, rail consigne ~1620, réel ≤~1650–1670 si possible

### ROUTE_TURBO
- Même route si possible
- Prouver : MAP specified vs actual sous charge

### VILLE
- 15–20 min, ASR ON, pas de WOT long
- Prouver : douceur vs ACE on/off

### HARCUT
- En roulant seulement, montée ~4800
- Prouver : couple → 0 zone 4800

### DEPART
- ASR OFF, frein à main, en prise
- Prouver : hold RPM + MAP/couple au hold + départ

### ROUTE_INJ
- Pull WOT + IQ si trouvé
- Prouver : air/IQ/fumée

## Après le log

1. Page chercheur → **VCDS** / **Logs** pour analyser
2. Ou envoi CSV dans le chat avec : soft + type de run + ASR + ressenti 1 ligne
