# Switch SOFT vs RACE — combo pédale (2026-08-23)

Objectif : **ton Caddy 9979** (atelier). La Golf 9980, c’est le **labo** : ton fichier Caddy ORI n’a **pas de code** (tout `FF` jusqu’à `180000`, seulement la cal). Sans fullflash, on ne peut pas trouver le hook. Même PCR, mêmes maps cal (`1D0860` clutch identique, rail start identique). AccPed Caddy = **`1CF9C0`**, pas `1CFFC0`.

Combo test : 3 coups d’accélérateur à l’arrêt. **Ne pas flasher** tant que le trampoline n’est pas porté sur un **fullflash Caddy** (lecture voiture), pas collé depuis la Golf.

---

## Verdict

Le plus simple, c’est un **combo pédale à l’arrêt**. Le PCR lit déjà tout. Zéro percage, zéro fil jusqu’à l’ECU.

Les caches à côté de l’ASR restent du plastique : un bouton recycle = deux fils. On **n’y va pas**.

`D000A946` n’est **pas** un switch client (octet de cal `19628D`).

---

## Combo (ce que tu feras dans la voiture)

Moteur allumé, **à l’arrêt**, **3 coups de pédale à fond** (appuyer / relâcher, appuyer / relâcher, appuyer / relâcher).

Ça **bascule** : SOFT → RACE → SOFT → …

| Condition | RAM PCR | Pourquoi |
|-----------|---------|----------|
| Arrêté | `D0002810` ≈ 0 | axe X de `tqlim_speed2A` @ `800A6B86` — atlas 9979 : *Vehicle speed* km/h |
| Moteur tourne, pas un launch | `nmot` `D000219A` dans la zone ralenti (pas 3000+ rpm) | évite un bascule pendant un DEPART |
| 3 fronts pédale | `APP_r` `D0002198` : monte au-dessus de ~88 % puis redescend sous ~15 % | facteur atlas APP `0.09765625` → ~900 / ~150 raw |
| Frein | **pas trouvé** (octet BLS pas nommé) | V1 sans frein ; 3 coups + à l’arrêt = assez pour pas le faire par accident |

Défaut / RAM pourrie / boot = **SOFT**.

Interdit pendant le combo : rouler, WOT sur route, DEPART / launch.

---

## Carto SOFT vs RACE (spec Steven)

**SOFT** = tous les jours = carto actuelle (V3-style).
**RACE** = la même base, plus de couple **une fois lancé**, pas plus de patate au décollage.

Traction FWD : trop de couple en 1re au dump = patinage, ESP qui clignote, tu **perds** du départ. Donc RACE ne « pousse » pas le launch en Nm.

| Quoi | SOFT | RACE |
|------|------|------|
| AccPed **0 → 50 %** | inchangé | **copie identique** (ville / 1re / partiels calmes) |
| AccPed **50 % → WOT** | actuel | **plus de wish couple**, sous les tqlim déjà validés |
| Launch `tqlim_cluth_prot` | hold **~2500** (V3 ITALIE) | hold **~2700** — même couple au dump, juste +200 rpm |
| Rail **max** | plafond actuel | **même plafond** (pas de bar en plus) |
| Turbo / vmax / hardcut | actuel | actuel |

Axe AccPed `1A90C2` (Golf **et** Caddy ORI, octets identiques) : 1 / 4 / 10 / 23 / **50** / 75 / 85 / 100 %. Colonnes ≤50 % = SOFT. Colonnes 75 / 85 / 100 % = RACE plus haut.

**Caddy atelier vs Golf Ghidra :** AccPed Caddy = `1CF9C0` ; Golf fullflash = `1CFFC0`. Le hook `800CC4AA` est prouvé sur le Golf. Sur le Caddy il faudra re-trouver le `call` (même famille, pas la même adresse grille). Vérif 2026-08-23 : `map-finder/reports/map-switch-verify.md`.

Si le rail est **déjà au plafond** en WOT SOFT, monter AccPed tout seul ne donne rien : on pourra un peu pousser la **consigne** rail, jamais le **max**.

### Couloir RACE (conservateur, plus que SOFT)

SOFT = V3 (V2 + launch 2500). V2 a **laissé de la marge** vs ACE. RACE = utiliser cette marge **après 50 %**, pas inventer un Stage 2.

| Map | SOFT (V2/V3) | RACE (plafond, on ne dépasse pas ACE) | Interdit |
|-----|----------------|----------------------------------------|----------|
| AccPed 0–50 % | V2 | = SOFT | plus de Nm au décollage |
| AccPed 50 %–WOT | V2 (partiels calmes, WOT ~350) | forme plus ACE, wish max **~380** | WOT au-delà si tqlim bloque |
| tqlim | ~348 Nm | **~350** (ACE) | 400+ Nm |
| rail_base | ~**1620** bar | vers **1656** ACE, pas plus | nouveau « max pompe » |
| smoke | cap **360** | vers **~380**, sous ACE 400 | plat 400 partout |
| turbo_base / ATM | ACE / **2650** mbar | **identique** | plus de boost ATM |
| launch | hold 2500 | hold **2700**, **même** Nm dump | plus de couple 1re |
| SOI / duration | V2 | inchangé | avancer le timing « pour gagner » |

Le gain RACE, c’est la **forme** (plus de réponse 50–100 %, un peu plus de rail/smoke dans le couloir ACE), pas un pic plus haut que le Stage 1 déjà validé.

Test switch : toujours **3 coups d’accélérateur à l’arrêt**. Le cave n’est pas encore dans le flash.

---

## Où ça vit dans le flash

| Quoi | Adresse | Taille |
|------|---------|--------|
| AccPed SOFT (actuel) | `1CFFC0` | 256 o (8×16 u16) |
| Trou FF pour RACE | `1CB064` | **3456 o** de `0xFF` (scan) |
| Copie RACE V1 | `1CB064` | 256 o (copie de `1CFFC0`, puis tu tunes) |
| Cave code trampoline | `8017FE04` | ~500 o de `00`, **0 pointeur** vers cette adresse dans le code |
| `map_sel` + état combo | `D0002890` | 8 o : 0 lea ABS, 0 `[a0]`, 0 movh, 0 st.h BOL/BO sur `2890`…`28BE` |

Les voisins `D000A948`+ **sont utilisés** (`st.b`) — on n’y touche pas.

Cave géante `800336E4` (50 Ko de `00`) : trop louche (trou de dump / banque vide). On n’y met rien.

---

## Logiciel (pas encore dans le bin)

```
boot                →  map_sel = 0   SOFT
3 coups à l’arrêt   →  map_sel ^= 1  RACE / SOFT
```

Hook : remplacer le `call interp_2d` à `800CC4AA` par un `call` vers `8017FE04`.
Le cave : lit APP / nmot / `D0002810`, compte les coups, puis appelle `interp_2d` avec `a4 = 1CFFC0` ou `1CB064`.

Safety dans le cave :

- changer de map seulement **à l’arrêt**
- pas si pédale déjà collée au plancher en roulant
- pas si régime type launch
- RACE = AccPed plus haut **après 50 %** + launch hold 2700 ; **même** rail max / vmax / Nm au dump

Checksum : même contrainte que le Stage1 actuel.

---

## Ordre

1. **Fait** — A946 = cal, pas un switch.
2. **Fait** — combo pédale choisi (plus simple que le fil).
3. **Fait** — RAM combo + trou RACE + cave + hook AccPed.
4. **Fait (lab WORK)** — trampoline cave + AccPed RACE cloné → `1CB064` (identique au live). Pas flashé.
5. **Ensuite** — tuner la copie RACE (WOT plus haut, launch 2700, rail vers 1656).
6. Flash : 2ᵉ ECU banc **ou** lecture full **ton** Caddy. Pas ce dump internet dans la voiture.

Scan brut : `map-finder/reports/map-switch-combo-scan.txt`.
Script : `map-finder/ghidra/plan_map_switch_combo.py`.

---

## Limite honnête

BND switchmAPP = du **code custom** dans le PCR. Nous aussi. Ce n’est pas un bit OEM.

`D0002810` = vitesse véhicule **par le rôle** (limiteur couple vs vitesse), pas un IdName Bosch. Le facteur km/h exact n’est pas dans notre A2L : « ≈ 0 » = arrêté.

Le cave `8017FE04` est du code **dans WORK seulement**. Ne pas flasher WORK dans le Caddy du quotidien.

## Lab 2026-08-23 — dump acheté (WORK)

ECU **reste dans le Caddy**. Ce fichier n’est **pas** à flasher dans la voiture.

| Fichier | Rôle |
|---------|------|
| `map-finder/bins/caddy-9979-TB-fullflash-ORI-DONOTTOUCH.bin` | original dump, on n’y touche plus |
| `map-finder/bins/caddy-9979-TB-fullflash-WORK.bin` | copie de labo patchée |

**Alignement AccPed :** le call `800CC4AA` lit **`1CFFC0`** (max **234.9 Nm** sur cet ORI), pas WinOLS `1CF9C0` (293.7 Nm). Axes Y différents (`1A8EA6` vs `1A8752`) — on **ne copie pas** `1CF9C0` par-dessus `1CFFC0`. RACE = clone de la grille **live** `1CFFC0` → `1CB064` (identique pour l’instant). Spare WinOLS à `1CB164`.

Hook **écrit**. Cave **196** o @ `8017FE04` (AccPed) + launch entry `0x8017FE10`. Combo 3 coups. `map_sel` @ `D0002890`.

**Test visuel (launch, pas AccPed) :** AccPed RACE = copie identique → tu ne sentiras rien à la pédale. Dump `1A612A` : 800 / 1000 / 1500 / 2000 / **2650** / 2700 / **2800** / 3200. SOFT hold col0 = 0 Nm dès **2650**. RACE `1CB264` : 0 Nm seulement à partir de **2800** (2650 et 2700 trop proches pour un test au compte-tours). SOFT `1D0860` inchangé.
Checksum PCR : pas recalculé ici. Un flash (plus tard, autre ECU ou lecture **ton** Caddy) = KESS **CHK**.
