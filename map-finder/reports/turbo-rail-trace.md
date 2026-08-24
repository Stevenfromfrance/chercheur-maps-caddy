# Turbo ram_2D8C + rail a15 — 2026-08-23

Offline, Golf 9980 fullflash. Pas de clic Ghidra.

## 1) Turbo — qui nourrit d15

Writer `800E0EA2` `st.h [a14], d15` dans `ram_2D8C`. Ce n est **pas** un capteur calcule : `d15` est un **ld.h [a15]** juste avant le store. `a15` est un pointeur indexe.

```
   800E0E6C  14 ff        ld.bu d15, [a15]
   800E0E6E  3e 05        op16 3e 05
   800E0E70  da 01        op16 da 01
   800E0E72  d9 0d bc 53  lea a13, [a0+0x53bc]
   800E0E76  3c 04        op16 3c 04
   800E0E78  da 00        op16 da 00
   800E0E7A  d9 0d bc 53  lea a13, [a0+0x53bc]
   800E0E7E  34 df        op16 34 df
   800E0E80  d8 05        ld.a a15, [a10]+0x14
   800E0E82  14 ff        ld.bu d15, [a15]
   800E0E84  d8 07        ld.a a15, [a10]+0x1c
   800E0E86  14 f0        ld.bu d0, [a15]
   800E0E88  86 40        sha d0, #4
   800E0E8A  d8 01        ld.a a15, [a10]+0x4
   800E0E8C  86 1f        sha d15, #1
   800E0E8E  49 ff 30 fa  lea a15, [a15-0x10]
   800E0E92  c2 ef        add d15, #-2
   800E0E94  f4 af        st.a [a10], a15
   800E0E96  01 f0 00 f6  addsc.a a15, a15, d0, #0
   800E0E9A  10 ff        addsc.a a15, a15, d15, #0
>> 800E0E9C  c5 de cc 62  lea a14, 0xd0002d8c
   800E0EA0  94 ff        ld.h d15, [a15]
   800E0EA2  b4 ef        st.h [a14], d15
   800E0EA4  94 cf        ld.h d15, [a12]
   800E0EA6  42 bf        add d15, d11
   800E0EA8  91 c0 01 4a  movh.a a4, 0xa01c0000
   800E0EAC  37 0f 70 50  extr
   800E0EB0  91 a0 01 5a  movh.a a5, 0xa01a0000
   800E0EB4  91 a0 01 6a  movh.a a6, 0xa01a0000
```

Lecture de la sequence (encodages Ghidra `tricore.sinc`) :

| VA | Quoi |
|----|------|
| `800E0E80` | `ld.a a15, [SP+0x14]` puis `ld.bu d15, [a15]` — **index A** (octet) |
| `800E0E84` | `ld.a a15, [SP+0x1C]` puis `ld.bu d0, [a15]` — **index B** |
| `800E0E88` | `sha d0, #4` → B*16 |
| `800E0E8A` | `ld.a a15, [SP+0x04]` — **base table** |
| `800E0E8C` | `sha d15, #1` → A*2 |
| `800E0E8E` | `lea a15, [a15-16]` |
| `800E0E92` | `add d15, #-2` |
| `800E0E96` | `addsc.a a15, a15, d0, #0` → base + B*16 |
| `800E0E9A` | `addsc.a a15, a15, d15, #0` → + A*2 - 2 |
| `800E0EA0` | **`ld.h d15, [a15]`** cellule u16 |
| `800E0EA2` | `st.h ram_2D8C, d15` |

**Formule :** `ram_2D8C = *(u16*)( table - 16 + (idxB<<4) + (idxA*2 - 2) )`

A0 global (init `80031234`) : `movh.a a0, D0010000` + `lea a0, +0x800` → **`A0 = D0010800`**. A1 = `A0190800` (axes flash).

| Slot pile | Pointeur resolu | Role |
|-----------|-----------------|------|
| SP+4 (table) | `D0011D74` (alt `D000FD34` si l autre `lea`) | base de la petite table u16 |
| SP+0x14 idx A | octet a `D000DADF` (`a0-0x2D21`) | index ligne |
| SP+0x1C idx B | octet a `D000DADE` (`a0-0x2D22`) | index colonne (*16) |

Ce n est **pas** un capteur (MAP/RPM). C est une **table RAM** indexee par deux octets, copiee dans `ram_2D8C`, puis l interp `800E0ECA` s en sert comme axe X (grille `1C0714` dans `turbo_base3B`). Recette cousine du smoke, mais la source est RAM (`D0011D74`) pas une case flash `1D3FB4`.

Stores pile vers `a10` dans les ~0x280 o avant :
- `800E0C3E  st.a [a10]+0x10, a15`
- `800E0CD4  st.a [a10]+0x1c, a15`
- `800E0CF0  st.a [a10]+0x1c, a15`
- `800E0D18  st.a [a10]+0x1c, a15`
- `800E0D2E  st.a [a10]+0x1c, a15`
- `800E0DD4  st.a [a10]+0x14, a15`
- `800E0DF0  st.a [a10]+0x14, a15`
- `800E0E18  st.a [a10]+0x14, a15`
- `800E0E2E  st.a [a10]+0x14, a15`
- `800E0E58  st.w d2, [a10+0x20]`

lea ABS / movh.a dans les ~0x200 o avant le bloc :
- `800E0C92  movh.a a15, 0xd0010000`
- `800E0CFA  movh.a a15, 0xd0010000`
- `800E0D40  movh.a a4, 0xa01a0000`
- `800E0D58  movh.a a14, 0xd0010000`
- `800E0D92  movh.a a15, 0xd0010000`
- `800E0DFA  movh.a a15, 0xd0010000`

Au CALL interp `800E0ECA` : A4=`A01C0714` A5=`A019B5D4` A6=`A019C754` A14=`D0002D8C`
A4 grille = WinOLS `1C0714` (dans turbo_base3B). Axes flash A5/A6 = `19B5D4` / `19C754`.

## 2) Rail — a15 resolu via A0=`D0010800`

Les `lea a15, [a0+disp]` ne sont plus du bruit : **A0 est fixe**.

| Site | Entree | Cellule | Comment |
|------|--------|---------|---------|
| 2d `800F5114` | X `d4` | **`D000B6AE`** (`a0-0x5152`) | `ld.hu` |
| 2d `800F5114` | Y `d5` | **`D000E6E8`** (`a0-0x2118`) | `ld.hu` — aussi vue cote turbo |
| D `800C1964` | X `d4` | **`D000E6E8`** | meme cellule que Y du site 2d |
| B `800B5A96` | Y `d5` | **`D000A946`** (`a0-0x5EBA`) | `ld.bu` = mode/index, pas une grandeur physique |
| B `800B5A22` (interp avant) | X `d4` | **`D000E6E8`** | `ld.hu` clair |
| B `800B5A62` | X `d4` | `[a15]` **sans reload** apres helpers — a15 peut etre casse | pas fiable |

`ram_0414` (A13 sur le 2d) : deux `lea`, **pas** de `st.h` a cote — lecture / contexte, pas le writer.

## 2b) Rail — listing call-sites

### B `800B5A96` grille `1E9BC8`

```
   800B5A56  01 4a 02 2a  op01 dest=a2 a4 d10 n=2 aux=0x280
   800B5A5A  d9 44 c8 bb  lea a4, [a4-0x4438]
   800B5A5E  40 d5        mov.aa a5, a13
   800B5A60  40 c6        mov.aa a6, a12
   800B5A62  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800B5A66  6d fc 9d b6  call 0x8004c7a0 interp_2d
   800B5A6A  02 2b        mov d11, d2
   800B5A6C  d9 12 72 18  lea a2, [a1+0x1872]
   800B5A70  14 2f        ld.bu d15, [a2]
   800B5A72  6e 16        jz d15, +22
   800B5A74  91 f0 01 4a  movh.a a4, 0xa01f0000
   800B5A78  d9 44 c8 9b  lea a4, [a4-0x6438]
   800B5A7C  91 f0 01 5a  movh.a a5, 0xa01f0000
   800B5A80  d9 55 f0 c8  lea a5, [a5-0x3710]
   800B5A84  91 f0 01 6a  movh.a a6, 0xa01f0000
   800B5A88  d9 66 d0 f8  lea a6, [a6-0x730]
   800B5A8C  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800B5A90  d9 0f 46 a1  lea a15, [a0-0x5eba]
   800B5A94  14 f5        ld.bu d5, [a15]
>> 800B5A96  6d fc 65 b7  call 0x8004c960 interp_2d_B
   800B5A9A  0b 2a 90 a1  op32 0b
```

emu A* : A4=A01E9BC8 A5=A01EC8F0 A6=A01EF8D0 A12=A01F4930 A13=A01F4904
d4=indirect (ld.hu_bo/indirect)  d5=indirect (—)
lea/movh avant :
- `800B59C8  movh.a a15, 0xd0010000`
- `800B59FC  movh.a a12, 0xa01f0000`
- `800B5A00  movh.a a13, 0xa01f0000`
- `800B5A0E  movh.a a4, 0xa01f0000`
- `800B5A38  movh.a a5, 0xa01f0000`
- `800B5A54  movh.a a4, 0xa01f0000`
- `800B5A74  movh.a a4, 0xa01f0000`
- `800B5A7C  movh.a a5, 0xa01f0000`
- `800B5A84  movh.a a6, 0xa01f0000`

### 2d `800F5114` grille `1E9DE0`

```
   800F50D4  ae ae        op16 ae ae
   800F50D6  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800F50DA  d9 0f e8 de  lea a15, [a0-0x2118]
   800F50DE  09 f5 c0 08  ld.hu d5, [a15+0x0]
   800F50E2  6d fa 5f bb  call 0x8004c7a0 interp_2d
   800F50E6  25 d2 dc ba  op32 25
   800F50EA  3c 61        op16 3c 61
   800F50EC  91 f0 01 4a  movh.a a4, 0xa01f0000
   800F50F0  d9 44 e0 9d  lea a4, [a4-0x6220]
   800F50F4  91 f0 01 5a  movh.a a5, 0xa01f0000
   800F50F8  d9 55 84 5d  lea a5, [a5+0x5d84]
   800F50FC  91 f0 01 6a  movh.a a6, 0xa01f0000
   800F5100  d9 66 b4 5d  lea a6, [a6+0x5db4]
   800F5104  d9 0f ae ae  lea a15, [a0-0x5152]
   800F5108  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800F510C  d9 0f e8 de  lea a15, [a0-0x2118]
   800F5110  09 f5 c0 08  ld.hu d5, [a15+0x0]
>> 800F5114  6d fa 46 bb  call 0x8004c7a0 interp_2d
   800F5118  25 d2 dc ba  op32 25
```

emu A* : A4=A01E9DE0 A5=A01F5D84 A6=A01F5DB4 A13=D0000414
d4=indirect (ld.hu_bo/indirect)  d5=indirect (ld.hu_bo/indirect)
lea/movh avant :
- `800F5014  lea a13, 0xd0000414`
- `800F5036  lea a13, 0xd0000414`
- `800F5044  movh.a a4, 0xa01f0000`
- `800F504C  movh.a a5, 0xa01f0000`
- `800F5054  movh.a a6, 0xa01f0000`
- `800F50BA  movh.a a4, 0xa01f0000`
- `800F50C2  movh.a a5, 0xa01f0000`
- `800F50CA  movh.a a6, 0xa01f0000`
- `800F50EC  movh.a a4, 0xa01f0000`
- `800F50F4  movh.a a5, 0xa01f0000`
- `800F50FC  movh.a a6, 0xa01f0000`

### D `800C1964` grille `1E98C0`

```
   800C1924  6d fc 6e 56  call 0x8004c600 map_interp_K
   800C1928  0c a1        op16 0c a1
   800C192A  53 ef 20 f0  op32 53
   800C192E  91 f0 01 fa  movh.a a15, 0xa01f0000
   800C1932  d9 ff 04 c9  lea a15, [a15-0x36fc]
   800C1936  10 f4        addsc.a a4, a15, d15, #0
   800C1938  6d fc c4 50  call 0x8004bac0 map_interp_I
   800C193C  06 42        op16 06 42
   800C193E  06 f2        op16 06 f2
   800C1940  02 24        mov d4, d2
   800C1942  6d fc bb 6e  call 0x8004f6b8
   800C1946  02 2f        mov d15, d2
   800C1948  09 a0 41 08  ld.b d0, [a10+0x1]
   800C194C  53 20 22 00  op32 53
   800C1950  91 f0 01 fa  movh.a a15, 0xa01f0000
   800C1954  d9 ff c0 98  lea a15, [a15-0x6740]
   800C1958  01 f0 00 46  addsc.a a4, a15, d0, #0
   800C195C  d9 0f e8 de  lea a15, [a0-0x2118]
   800C1960  09 f4 c0 08  ld.hu d4, [a15+0x0]
>> 800C1964  6d fc 0e 5b  call 0x8004cf80 map_interp_D
   800C1968  bb 00 00 08  op32 bb
```

emu A* : (vides)
d4=indirect (ld.hu_bo/indirect)  d5=indirect (—)
lea/movh avant :
- `800C1892  lea a15, 0xd0001990`
- `800C18A4  lea a15, 0xd0001990`
- `800C1914  movh.a a15, 0xa01f0000`
- `800C192E  movh.a a15, 0xa01f0000`
- `800C1950  movh.a a15, 0xa01f0000`
stores pile :
- `800C1896  st.a [a10]+0xc, a15`
- `800C18A8  st.a [a10]+0xc, a15`

### Writer `ram_0414` (vu a A13 sur le site 2d)

- `800F5014` lea a13  st.h_near=False
- `800F5036` lea a13  st.h_near=False

## 3) Bin 9977 — code ou cal seule ?

- Golf fullflash : `size=2097152  ff_in_0-cal=10%  call_6D_64k=65  lea_C5_64k=89`
- 9977 `03L906023N` : `size=2097152  ff_in_0-cal=100%  call_6D_64k=0  lea_C5_64k=0`

Si 9977 a ~0 CALL dans les 64k, c est une **image cal 2 Mo** (pas de chaine code). Un import Ghidra n aiderait pas : il n y a rien a desassembler. Il faudrait un dump **fullflash** (boot+app) comme le Golf `03L997558A`.

