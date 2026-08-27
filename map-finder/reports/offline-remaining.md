# Offline remaining — 2026-08-22

Sans clic Ghidra, sans WinOLS. Golf 9980 fullflash `03L997558A` + banque PCR (atlas + bins).

## 1) Hors-A2L 9980

`ghidra/golf9980_horsA2L_identified.csv` — **176** grilles interp sans IdName WinOLS.

| conf | n | signification |
|------|---|---------------|
| high | 2 | match famille A2L pres du start |
| medium | 46 | **dans** une map deja nommee (sous-vue, pas une nouvelle) |
| low | 128 | hors des ~299 maps A2L WinOLS |
| (dont fill 8000/A000) | 39 | bruit, pas une map |

Low **identiques 9979** + grille diverse (uniq>=10) : **49** — inconnues A2L mais **meme payload que le Caddy** (pas un gisement Golf-only).

Low **≠ 9979** + uniq>=10 + pas fill : **2** candidates « vraie inconnue / payload Golf ».

| offset | call-site | uniq_u16 | zone |
|--------|-----------|----------|------|
| `0x1C92B4` | `0x80087954` | 29 | cal 1C9xxx, meme bloc que duration `800879xx` (axes flash `19A438` / `19D438`) |
| `0x180688` | `0x800E9E8C` | 16 | zone speed `18xxxx` pres de vmax, axe `17B558` |

Je peux classer. Je ne peux **pas** baptiser OEM une grille low sans A2L ou log.

## 2) ram_2754 / rail / turbo / vmax (Golf 9980 code)

### ram_2754 clutch Y (`D0002754`)
lea ABS: **1**
- `800FC260` lea a15  st.h_near=False
       800FC250  02 24        mov d4, d2
       800FC252  d9 44 78 08  op32 d9
       800FC256  d9 55 08 d9  op32 d9
       800FC25A  6d fa 23 85  call 0x8004cca0 map_interp_C
       800FC25E  02 84        mov d4, d8
    >> 800FC260  c5 df 54 d2  lea a15, 0xd0002754
       800FC264  8f f2 3f f0  op32 8f
       800FC268  09 f5 c0 08  ld.hu d5, [a15+0x0]
       800FC26C  6d fa fc 98  call 0x8004f464
autres ABS (ld/st opcode) : 1  `800FC260` op=c5
movh.a+lea BOL : **0**
ptr u32 `54 27 00 D0` dans le code : **0** 
lea+st.h dans `D0002700–27FF` (bloc clutch/SOI) : **51** cellules — le voisin **`ram_2752`** a le **meme helper** que clutch X :

```
800FB5CA  call FUN_8004f3bc
800FB5CE  ld.w d15, [a10]+0x88
800FB5D0  add  d15, d2
800FB5D2  st.h [a15], d15          ; ram_2752, PAS ram_2754
```

lecture `800FC260` d5=indirect (axe Y clutch/SOI)
**Verdict ram_2754:** pas de writer `lea+st.h` / `movh+lea`. Voisin `ram_2752` oui. Cellule 2754 remplie ailleurs (ptr / autre tache).

### vmax3 `18047C`
valeur Golf fullflash : `076C` = 190.0 km/h (facteur 0.1)
`A018047C`  ABS=0  movh+lea=0  ptr32=0
`8018047C`  ABS=0  movh+lea=0  ptr32=0
`A018047E`  ABS=0  movh+lea=0  ptr32=0
`8018047E`  ABS=0  movh+lea=0  ptr32=0
contexte `180470–18048F` : `01 00 00 01 dc 05 9a 19 33 03 9a 01 6c 07 6c 07 f4 01 00 00 00 00 66 86 8f 82 38 4a 38 4a d0 07`
**Verdict:** scalaire cal, pas d interpolateur. Lecture code toujours indirecte (table / index), pas un `lea ABS` unique.

### Rail / turbo — entrees aux call-sites
- **rail B `800B5A96`**
  A4=A01E9BC8 A5=A01EC8F0 A6=A01EF8D0 A12=A01F4930 A13=A01F4904
  d4=— d5=—  how=ld.hu_bo/indirect / —
- **rail 2d `800F5114`**
  A4=A01E9DE0 A5=A01F5D84 A6=A01F5DB4 A13=D0000414
  d4=— d5=—  how=ld.hu_bo/indirect / ld.hu_bo/indirect
- **rail D `800C1964`**
  (A* inconnus dans 256 o)
  d4=— d5=—  how=ld.hu_bo/indirect / —
- **turbo 2d `800E0ECA`**
  A4=A01C0714 A5=A019B5D4 A6=A019C754 A14=D0002D8C
  d4=0xd0002d8c d5=—  how=ld.hu_bo+a14 / —
- **turbo C `800F8F0A`**
  A4=A01C088C A5=A019F4DC
  d4=— d5=—  how=ld.hu_bo/indirect / —

**Writer turbo X `ram_2D8C`** (juste avant `800E0ECA`) :

```
800E0E9C  lea  a14, ram_2D8C
800E0EA2  st.h [a14], d15
```

`d15` vient d un calcul pile (`ld.bu` + ops) — recette propre, comme smoke/clutch X.

Rail : axes via `a15` / pile, pas de `ram_XXXX` unique. Writer rail = toujours ouvert.

## 3) Autres softs PCR — adresses Stage1

SM2G0P proche Caddy : **9977, 9978, 9983** + Golf **9980**. **9972** = SM2G0M (Polo) — autre famille, offsets souvent ≠. Ce n est **pas** la chaine code Ghidra 9980 : juste fingerprints / atlas.

ORI 9979 : `C:\Users\theda\OneDrive\Documents\Reprog-Stage1\06-Vehicules\Caddy-CAYE-2013-03L906023PA-2531\ORI\Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin`

### Adresses atlas (start WinOLS)

| Map | 9979 | 9977 | 9978 | 9980 atlas | 9983 | 9972 | Golf Ghidra |
|-----|------|------|------|------------|------|------|-------------|
| `AccPed_trq4A` | `1CF9C0` | `1CF9C0` | `1CF9C0` | `1CF9C0` | `1CF9C0` | `1CF99C` | `1CFFC0` |
| `tqlim_cluth_prot` | `1D0860` | `1D0860` | `1D0860` | `1D0860` | `1D0860` | `1D083C` | `1D0860` |
| `tqlim_base_pu_4A` | `1D3190` | `1D3190` | `1D3190` | `1D3190` | `1D3190` | `1D316C` | `1D3190` |
| `smoke_mapA` | `1D1D18` | `1D1D18` | `1D1D18` | `1D1D18` | `1D1D18` | `1D1CF4` | `1D1D18` |
| `turbo_base3B` | `1C04AC` | `1C04AC` | `1C04AC` | `1C04AC` | `1C04AC` | `1C0488` | `1C04AC` |
| `rail_base_int_trq2B` | `1E9368` | `1E9368` | `1E9368` | `1E9368` | `1E9368` | `1E9344` | `1E9368` |
| `duration_inj6A` | `1CDC84` | `1CDC84` | `1CDC84` | `1CDC84` | `1CDC84` | `1CDC60` | `1CDC84` |
| `soi_base_int_trq2A` | `18C380` | `18C380` | `18C380` | `18C380` | `18C380` | `18C394` | `18C380` |
| `vmax3` | `18047C` | `18A2FE` | `18A2FE` | `18047C` | `18A2FE` | `18047C` | `18047C` |

Note : atlas 9980 est clone 9979 (`AccPed` `1CF9C0`). Ghidra sur **03L997558A** a valide `AccPed` a **`1CFFC0`** — le dump cal `03L997557P` n est pas le fullflash du projet Ghidra.

### 64 octets : Golf Ghidra vs bin (adresse de *ce* soft)

| Map | vs 9979 ORI | 9977 | 9978 | 9983 | 9972 |
|-----|-------------|------|------|------|------|
| `AccPed_trq4A` | diff 46/64 | diff 56/64 | diff 55/64 | diff 56/64 | diff 46/64 |
| `tqlim_cluth_prot` | ident | ident | ident | diff 7/64 | ident |
| `tqlim_base_pu_4A` | ident | diff 64/64 | ident | ident | diff 64/64 |
| `smoke_mapA` | ident | ident | ident | ident | diff 57/64 |
| `turbo_base3B` | ident | ident | ident | ident | diff 61/64 |
| `rail_base_int_trq2B` | ident | ident | ident | ident | diff 52/64 |
| `duration_inj6A` | ident | ident | ident | ident | ident |
| `soi_base_int_trq2A` | ident | ident | ident | ident | diff 44/64 |
| `vmax3` | ident | ident | ident | ident | ident |

### vmax3 physique (km/h)

- 9979 ORI 190.0 · Golf Ghidra 190.0 · 9977 190.0 · 9978 190.0 · 9983 190.0 · 9972 190.0

### AccPed max (Nm, facteur 0.03125 offset −1024)

- **9977** `@1CF9C0` max raw 45827 → **408.1 Nm**
- **9978** `@1CF9C0` max raw 44928 → **380.0 Nm**
- **9983** `@1CF9C0` max raw 49144 → **511.8 Nm**
- **9972** `@1CF99C` max raw 42165 → **293.7 Nm**
- **Golf Ghidra** `@1CFFC0` max raw 42496 → **304.0 Nm**

9977/9978/9983 dumps MHH : AccPed souvent deja Stage1 (~400 Nm). Bon pour **trouver l adresse**, pas comme ORI a flasher.

## 4) Ce que je peux / ne peux pas boucler seul

| Sujet | Autonome | Reste |
|-------|----------|-------|
| Hors-A2L | classer high/medium/low, lister les low ≠9979 | nom OEM |
| 9977/9978/9972 | adresses Stage1 via atlas/phase2 | importer un fullflash Ghidra par soft |
| ram_2754 | confirmer : pas de writer `lea+st.h` | Ghidra GUI sur un XREF data, ou log |
| Rail / turbo | call-sites + emu registres | resoudre `a15` pile (long) |
| vmax3 | valeur + adresse par soft | lecture code (table) |

Rien a cliquer de ton cote pour cette passe.

