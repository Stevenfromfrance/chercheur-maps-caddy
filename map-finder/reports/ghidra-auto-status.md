# Ghidra auto status — Golf 9980 PCR2.1

Date: 2026-08-22  
Project: `C:\Users\theda\Tools\ghidra-projects\PCR21_Golf9980.gpr`  
Bin: `Golf6_03L997558A_9980_FULLFLASH.bin` @ `0x80000000`

## Fait

### Headless (matin)

1. **NameHubStage1Validated.py** — 357 addrs (AccPed protege).
2. **NameInterpFamilies.py** — hubs 2d + B..O.
3. **KickFromCallSites.py** — 225 call-sites Stage1. Functions: **1516**.
4. **DumpCallSiteFns.py** — 129 sites uniques.

### GUI + offline (apres-midi) — parents decodes

Le premier kick partait **sur le CALL** → Ghidra ne decode que vers l avant → `??` au-dessus (il fallait `D` a la main).

- **KickParents.py** (Script Manager) : `call_sites=225 extra_seeds=30 lookback=0x100 disasm_ok=248 fail=0`.
- **trace_ram_writers.py** (offline, Ghidra ouvert) : writers `lea ABS` + `st.h`.
- KickFromCallSites demarre maintenant `LOOKBACK=0x100` **avant** le CALL.

Relancer tout (fermer Ghidra GUI d abord) :

```bat
python map-finder\ghidra\trace_ram_writers.py
map-finder\ghidra\apply_stage1_validated_headless.bat
```

GUI deja ouvert : File → Save → Script Manager → `KickParents` → Run → File → Save.

Sorties :

- `map-finder/ghidra/golf9980_stage1_code_xrefs.md`
- `map-finder/ghidra/golf9980_callsite_functions.txt`
- `map-finder/ghidra/golf9980_ram_writers.txt`
- `map-finder/ghidra/golf9980_parent_seeds.txt`

## Chaines parents — validees (GUI + emu)

TriCore n encadre pas les maps par un ptr 32-bit. Consommateurs = **CALL hub**. THUNK / `CALL_TERMINATOR` / `??` **apres** le call = cosmétique, ignorer.

### 1) Launch / hardcut — `tqlim_cluth_prot` `1D0860` — **ecriture + lecture**

**Ecriture unique** de `ram_273C` (`D000273C`) :

```
800FB7D6  call FUN_8004f3bc          ; helper min/max / 1D (d2)
800FB7DA  ld.w d15, [a10]0x88
800FB7DC  add  d15, d2
800FB7DE  lea  a15, ram_273C
800FB7E2  st.h [a15], d15            ; ram_273C = [SP+0x88] + helper
```

Puis flag `ld.bu [a12]` / `jz LAB_800fb87c` (interrupteur, pas l ecriture).

**Lecture** (interp) :

| Call-site | Hub | Notes |
|-----------|-----|--------|
| `800FC2EE` / `800FC2F6` | C | sibling, meme RAM, grille `1993E0` |
| `800FC314` | C | grille dans map +0xC (`1D086C`) — axe RPM `1A8BCC` |
| `800FC25A` | C | autre tranche `1D0878` |
| `80074040` | F | autre hub, meme map +0x5C |

Axes clutch : X `ram_273C` (calculee), Y `ram_2754` (lue `800FC260`, **pas** de `st.h` direct).

### 2) AccPed wish — `AccPed_trq4A` `1CFFC0` — **lecture capteurs**

Pas de `st.h` sur `APP_r` / `nmot` ici (capteurs remplis ailleurs).

| Adresse | Quoi |
|---------|------|
| `800CC48E` | `lea a14, APP_r` `D0002198` |
| `800CC492` | label `AccPed_load_1CFFC0` |
| `800CC4AA` | `call interp_2d` wish couple |
| `800CC4CC` | `lea a15, nmot` `D000219A` |
| `800CC4D4` | `call interp_2d` nm2iq (`1D7F80`) |

Autres copies AccPed : `800EC250` (F), `800E2DFC` (D).

### 3) tqlim — `tqlim_base_pu_4A` `1D3190` — 3 tranches

| Call-site | Hub | Grille |
|-----------|-----|--------|
| `8008736E` | B | `1D32CC` (+0x13C) |
| `800DDACE` | C | `1D330C` (+0x17C) |
| `800DDA36` | E | `1D332C` (+0x19C) |

Axes **pas** des `ram_XXXX` nommees : X via ptr `[a12]`, Y souvent `ld.bu`. Moins propre que clutch/AccPed.

## Rail / smoke / vmax — offline 2026-08-22 (pas de clic GUI)

### Rail `rail_base_int_trq2B`

| Call-site | Hub | Grille (A4) | Entrees |
|-----------|-----|-------------|---------|
| `800B5A96` | B | `1E9BC8` | X `[a15]` u16, Y `ld.bu [a15]` (octet / mode) |
| `800F5114` | 2d | `1E9DE0` | X/Y via `a15` (ptr), `A13=D0000414` (`ram_0414`) |
| `800C1964` | D | `1E98C0` | X `[a15]` apres helper `8004F6B8` |

X du site 2d = `D000B6AE` (copie filtrée de `D0013874`). Chaîne complète : `reports/rail-to-the-end.md`. Y/`E6E8` = ratio, pas une cal flash.

### Smoke `smoke_mapA` `1D1D18` — **writers trouves** (offline 22:32)

Meme recette que `ram_273C`,  ~0x70 octets **avant** le `call` `800F4BA8`.

**X `ram_1D60`** — 7 ecritures deroulees `800F4A38`–`800F4AB0` :

```
lea  a14, ram_1D60
lea  a15, flash 1D3FB4 / 1D3FB2 / 1D3FB0… (step -2)
ld.hu d15, [a15]
st.h [a14], d15          ; copie un u16 cal dans ram_1D60
j    LAB_800f4ae8        ; un seul point de la courbe 1D est garde
```

Ce n est pas un capteur : c est une **copie de calib flash** selectionnee par des sauts, puis lue comme axe X du smoke.

**Y `ram_1D62`** — une ecriture :

```
800F4AFA  lea  a15, ram_1D62
800F4B02  ld.hu d15, [a2]
800F4B06  st.h [a15], d15
```

Puis `800F4BA8` `call interp_2d_B` grille `1D1F00` (dans `smoke_mapA` +0x1E8).

L autre site `80074DB2` interpolle aussi `smoke_mapA` (`1D1E64`) sans cette paire RAM.

### Duration `duration_inj6A` `1CDC84`

| Call-site | Hub | Grille | Entrees |
|-----------|-----|--------|---------|
| `80074EBE` | 2d | `1CDE04` (+0x180) | axes flash `1A2734` / `1AD8D0` (Y = meme axe que smoke `80074DB2`) |
| `800959B6` | C | `1CDE44` | `A15=D0003010` ; `st.h [a15], d2` avant le call |
| `8008B652` | C | `1CDE50` | X `ram_1AB8` (`D0001AB8`) |

### SOI `soi_base_int_trq2A`

Colle au bloc clutch (pas un module separe) :

| Call-site | Hub | Grille | RAM |
|-----------|-----|--------|-----|
| `800FC2C8` | C | `1993E0` | Y = **`ram_2754`** (meme Y que launch/hardcut) |
| `800FB4CC` | 2d | `1993F0` | X/Y `ram_2780` / `ram_2782` |

**Writer `ram_2780`** (meme fonction que clutch, ~0x100 avant `800FB7DE`) :

```
800FB6D6  call 0x8004be18
800FB6DA  st.h [a15], d2
800FB6DC  ld.hu d15, [a15]
800FB6E0  lea  a15, ram_2780
800FB6E4  st.h [a15], d15
```

**Duration writer propre** (meme helper `FUN_8004f3bc` que clutch) : `80087A34` call puis `80087A38` `st.h [a14], d2` → `ram_2496` (`D0002496`), ensuite interp `duration_inj6A` @ `80087B26`.
| `80092FE6` | B | `193BC4` | X `D0002BEC` ; **`st.h [a14], d2`** = resultat interp reecrit dans cette RAM |

`800FC2F6` / `800FC314` (clutch) viennent **juste apres** le SOI `800FC2C8` : meme decision, tables SOI puis limiteur embrayage.

### vmax3 `18047C` (scalaire 2 octets)

Pas de CALL interp (attendu). Pas de `lea ABS` / ptr `A018047C` / `8018047C` dans le code `0x0–0x180000`. Lecture via **table / indirection**, pas encore resolue. Les `movh.a a*, 0xA0180000` visent d autres objets 18xxxx (maps interp), pas ce scalaire.

## Encore faible (pas bloquant pour packs)

Passe autonome 22 aout soir : `reports/offline-remaining.md`.

| Area | Status |
|------|--------|
| XREF Ghidra vers **debut** de map | 0 — passer par call-sites / hubs |
| Hors-A2L | 176 grilles classees ; **2** low ≠9979 (`1C92B4`, `180688`) — pas de nom OEM |
| Autres softs SM2G0P | adresses Stage1 = 9979 (sauf vmax `18A2FE` sur 9977/78/83). Pas la chaine code 9980 |
| `vmax3` | 190 km/h partout ; lecture code toujours indirecte |
| Writer `ram_2754` (clutch Y) | lecture seule. Voisin `ram_2752` @ `800FB5D2` (meme helper que clutch X) |
| Turbo X `ram_2D8C` | copie depuis table RAM `D0011D74` (index `D000DADF`/`DADE`). Table **remplie** en boucle `8014E040` |
| Rail X `D000B6AE` | copie de `D0013874`. Cible `D0013870` = interp_C `18D0F0`/`1930CC` (X=`D0018666`=`D000048A`/`D00019DC`). PT1 générique `FUN_8004d15c` (208 callers). A2L : `a2l/PCR21_Golf9980_RAIL_PATH.a2l` |
| Rail Y `D000E6E8` | quotient `FUN_80080f4c` (`dvinit.u`), X de courbe `197382`. Pas madd. Reset @ `80133A48`. |
| Rail bank index | `D000A946` = copie flash `19628D` (`0x80`), pas un switch client. Plan SOFT/RACE : `reports/map-switch-soft-race.md` |
| `airctl` `1D0100` | LOW, soft != 9979 |
| Auto Analyze full 1.5 Mo | non — kick 225 + KickParents suffit |

## Ne pas

- Flasher depuis ces labels (RE, pas OEM).
- Relancer KickParents en boucle (une fois suffit ; attendre Finished).
- Relancer Auto Analyze GUI pendant un headless (lock).
- Ctrl+G WinOLS `1D0860` — utiliser `800FC314` (base `80`, pas `A0`).
