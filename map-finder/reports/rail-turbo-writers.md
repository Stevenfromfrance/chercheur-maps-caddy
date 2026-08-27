# Writers rail + table turbo — 2026-08-23

A0 = `D0010800`. Offline Golf 9980.

## Verdict (stores stricts : `st.h` avant redefinition du registre)

Les `lea` sans store tout de suite sont des **lectures** (call-sites). Ci-dessous seuls les vrais writers.

### Rail X `D000B6AE` (axe du site 2d `800F5114`)

Un writer net :

```
801474E2  lea  a15, D000B6AE
801474E6  lea  a2,  D0013874        ; a0+0x3074
801474EA  ld.hu d15, [a2]
801474EE  st.h [a15], d15           ; B6AE = copie de 3874
```

`D0013874` est la cellule amont. Elle est mise a jour par `8004D15C` :

```
800BA0B0  lea a12, D0013874
          ld.hu d4, [a12]           ; valeur courante
          ld.hu d5, D0013870        ; voisine -4
          ld.hu d6, flash A019314A  ; courbe (A1+0x294A)
800BA0C8  call FUN_8004d15c
          st.h [a12], d2            ; filtre / 1D
```

Autre copie : `8012FCE6`  `D0013874 = D0013870` (3870 chargee depuis flash `A1-0x46AC`).

**Chaine rail X :** `D00019DC/D000048A` → `D0018666` → interp_C `18D0F0`/`1930CC` → `D0013870` → PT1 `FUN_8004d15c` → `D0013874` → **`D000B6AE`** → interp `rail_base` `1E9DE0`. Détail : `reports/rail-to-the-end.md`.

### Rail Y / partage `D000E6E8`

Famille de cellules cote a cote (`E6E8`, `E6EA`, `E6F0`, `E6F6`, `E6F8`).

| VA | Quoi |
|----|------|
| `80080FE4` | **writer live** `st.h [E6E8], d2` — `d2` = **quotient** `dvinit.u`/`dvstep` (`FUN_80080f4c`), clamp vs `D000F6C4` |
| `80080FF0` | branche alt : store `d15` (const/min) |
| `800C30DA` | copie depuis la voisine `D000E6F8` |
| `80133A48` | **zero** (`mov d0,#0`) tout le cluster — init / reset |

`E6E8` n est pas une consigne flash brute : c est une **RAM calculee** (puis lue comme X ou Y selon le site rail).

### Table turbo `D0011D74`

Pas un `st.h` direct sur la base. **Boucle de copie** `8014E040` :

```
a4  = D0011D74 + d1
a5  = D000FD34 + d1          ; table jumelle a0-0xACC
loop:
  ld.h  d1, [src]
  st.h  [D0011D74 + d1_base + (d0<<1)], d1
  d0++
```

La table que `ram_2D8C` indexe est **remplie en RAM** depuis un buffer (`a6`/`a12`, copie de `a4` ligne d avant) + jumelle `D000FD34`. Pas une map WinOLS d un bloc.

---

## Listing brut (heuristique large, faux positifs inclus)

## `D000B6AE`  rail X (site 2d d4)

disp vs A0 : `-20818` (`AEAE`)

lea ABS : **0**
lea [a0-0x5152] : **18**
- **WRITE** `800F9542` lea a15  puis ['st.h [a15], d2']
```
   800F9522  8c 84        op16 8c 84
   800F9524  91 a0 01 6a  movh.a a6, 0xa01a0000
   800F9528  d9 66 c8 a5  lea a6, [a6-0x5a38]
   800F952C  d9 0f 72 9e  lea a15, [a0-0x618e]
   800F9530  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800F9534  d8 02        ld.a a15, [a10]+0x8
   800F9536  09 f5 c0 08  ld.hu d5, [a15+0x0]
   800F953A  6d fa 33 99  call 0x8004c7a0 interp_2d
   800F953E  bb 00 00 f8  op32 bb
>> 800F9542  d9 0f ae ae  lea a15, [a0-0x5152]
   800F9546  a2 f2        sub d2, d15
   800F9548  f8 03        st.a [a10]+0xc, a15
   800F954A  02 25        mov d5, d2
   800F954C  d9 0f 74 30  lea a15, [a0+0x3074]
   800F9550  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800F9554  6d fa fc a6  call 0x8004e34c
```
- **WRITE** `801474E2` lea a15  puis ['st.h [a15], d15']
```
   801474C2  b4 79        st.h [a7], d9
   801474C4  d9 0f 50 53  lea a15, [a0+0x5350]
   801474C8  d9 14 cc 88  lea a4, [a1-0x7734]
   801474CC  91 a0 01 5a  movh.a a5, 0xa01a0000
   801474D0  d9 55 2c c5  lea a5, [a5-0x3ad4]
   801474D4  d9 02 e8 de  lea a2, [a0-0x2118]
   801474D8  09 24 c0 08  ld.hu d4, [a2+0x0]
   801474DC  6d f8 82 2c  call 0x8004cde0 map_interp_N
   801474E0  34 f2        op16 34 f2
>> 801474E2  d9 0f ae ae  lea a15, [a0-0x5152]
   801474E6  d9 02 74 30  lea a2, [a0+0x3074]
   801474EA  09 2f c0 08  ld.hu d15, [a2+0x0]
   801474EE  b4 ff        st.h [a15], d15
   801474F0  d9 0f 88 2e  lea a15, [a0+0x2e88]
   801474F4  09 ff c0 08  ld.hu d15, [a15+0x0]
```
st.h BOL [a0-0x5152] : **0**
st.h BO [a0-0x5152] : **0**
movh.a+lea → cible : **0**

## `D000E6E8`  rail Y / partage (d5 2d, d4 D)

disp vs A0 : `-8472` (`DEE8`)

lea ABS : **0**
lea [a0-0x2118] : **381**
- **WRITE** `80080FE0` lea a12  puis ['st.h [a12], d2']
```
   80080FC0  f0 de        op16 f0 de
   80080FC2  b4 f2        st.h [a15], d2
   80080FC4  d9 0f 5c 92  lea a15, [a0-0x6da4]
   80080FC8  14 ff        ld.bu d15, [a15]
   80080FCA  f6 f7        op16 f6 f7
   80080FCC  d9 0f c4 ee  lea a15, [a0-0x113c]
   80080FD0  09 ff c0 08  ld.hu d15, [a15+0x0]
   80080FD4  bf 2f 0f 80  op32 bf
   80080FD8  3b 00 fe f1  op32 3b
   80080FDC  7f f2 06 80  op32 7f
>> 80080FE0  d9 0c e8 de  lea a12, [a0-0x2118]
   80080FE4  b4 c2        st.h [a12], d2
   80080FE6  3c 08        op16 3c 08
   80080FE8  d9 0f e8 de  lea a15, [a0-0x2118]
   80080FEC  3b 00 fe f1  op32 3b
   80080FF0  b4 ff        st.h [a15], d15
   80080FF2  d9 0c e8 de  lea a12, [a0-0x2118]
```
- **WRITE** `80080FE8` lea a15  puis ['st.h [a15], d15']
```
   80080FC8  14 ff        ld.bu d15, [a15]
   80080FCA  f6 f7        op16 f6 f7
   80080FCC  d9 0f c4 ee  lea a15, [a0-0x113c]
   80080FD0  09 ff c0 08  ld.hu d15, [a15+0x0]
   80080FD4  bf 2f 0f 80  op32 bf
   80080FD8  3b 00 fe f1  op32 3b
   80080FDC  7f f2 06 80  op32 7f
   80080FE0  d9 0c e8 de  lea a12, [a0-0x2118]
   80080FE4  b4 c2        st.h [a12], d2
   80080FE6  3c 08        op16 3c 08
>> 80080FE8  d9 0f e8 de  lea a15, [a0-0x2118]
   80080FEC  3b 00 fe f1  op32 3b
   80080FF0  b4 ff        st.h [a15], d15
   80080FF2  d9 0c e8 de  lea a12, [a0-0x2118]
   80080FF6  09 cf c0 08  ld.hu d15, [a12+0x0]
   80080FFA  d9 0f ad 91  lea a15, [a0-0x6e53]
```
- **WRITE** `8009549C` lea a15  puis ['st.h [a15], d2']
```
   8009547C  d9 0f d2 02  lea a15, [a0+0x2d2]
   80095480  14 ff        ld.bu d15, [a15]
   80095482  6e 1f        jz d15, +31
   80095484  91 d0 01 4a  movh.a a4, 0xa01d0000
   80095488  d9 44 cc e2  lea a4, [a4-0x1d34]
   8009548C  91 b0 01 5a  movh.a a5, 0xa01b0000
   80095490  d9 55 fc 88  lea a5, [a5-0x7704]
   80095494  91 b0 01 6a  movh.a a6, 0xa01b0000
   80095498  d9 66 34 89  lea a6, [a6-0x76cc]
>> 8009549C  d9 0f e8 de  lea a15, [a0-0x2118]
   800954A0  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800954A4  d9 0f 73 41  lea a15, [a0+0x4173]
   800954A8  14 f5        ld.bu d5, [a15]
   800954AA  6d fd 5b ba  call 0x8004c960 interp_2d_B
   800954AE  bb 00 00 58  op32 bb
```
- **WRITE** `800954EA` lea a15  puis ['st.h [a15], d2']
```
   800954CA  01 4a d9 44  op01 dest=a4 a4 d10 n=1 aux=0x136
   800954CE  78 7f        op16 78 7f
   800954D0  3c 05        op16 3c 05
   800954D2  91 d0 01 4a  movh.a a4, 0xa01d0000
   800954D6  d9 44 ec 92  lea a4, [a4-0x6d14]
   800954DA  91 b0 01 5a  movh.a a5, 0xa01b0000
   800954DE  d9 55 fc 88  lea a5, [a5-0x7704]
   800954E2  91 b0 01 6a  movh.a a6, 0xa01b0000
   800954E6  d9 66 34 89  lea a6, [a6-0x76cc]
>> 800954EA  d9 0f e8 de  lea a15, [a0-0x2118]
   800954EE  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800954F2  d9 0f 73 41  lea a15, [a0+0x4173]
   800954F6  14 f5        ld.bu d5, [a15]
   800954F8  6d fd 34 ba  call 0x8004c960 interp_2d_B
   800954FC  bb 00 00 58  op32 bb
```
- **WRITE** `800B1060` lea a15  puis ['st.h [a15], d2']
```
   800B1040  11 d7 02 25  op32 11
   800B1044  05 d4 04 0a  op32 05
   800B1048  6d fc 00 e1  call 0x8004d248
   800B104C  02 2f        mov d15, d2
   800B104E  d9 0f 90 22  lea a15, [a0+0x2290]
   800B1052  14 f0        ld.bu d0, [a15]
   800B1054  df 00 1d 00  op32 df
   800B1058  91 a0 01 4a  movh.a a4, 0xa01a0000
   800B105C  d9 44 20 36  lea a4, [a4+0x3620]
>> 800B1060  d9 0f e8 de  lea a15, [a0-0x2118]
   800B1064  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800B1068  6d fc 8c df  call 0x8004cf80 map_interp_D
   800B106C  91 d0 01 4a  movh.a a4, 0xa01d0000
   800B1070  d9 44 08 4f  lea a4, [a4+0x4f08]
```
- **WRITE** `800BD7E6` lea a15  puis ['st.h [a15], d15']
```
   800BD7C6  6d fc 49 76  call 0x8004c458
   800BD7CA  3b e0 0f 50  op32 3b
   800BD7CE  02 24        mov d4, d2
   800BD7D0  6d fc 7a 88  call 0x8004e8c4
   800BD7D4  02 28        mov d8, d2
   800BD7D6  d9 1f e8 ba  lea a15, [a1-0x4518]
   800BD7DA  14 ff        ld.bu d15, [a15]
   800BD7DC  76 f5        op16 76 f5
   800BD7DE  da 00        op16 da 00
   800BD7E0  d9 0f da be  lea a15, [a0-0x4126]
   800BD7E4  3c 0a        op16 3c 0a
>> 800BD7E6  d9 0f e8 de  lea a15, [a0-0x2118]
   800BD7EA  09 ff c0 08  ld.hu d15, [a15+0x0]
   800BD7EE  86 2f        sha d15, #2
   800BD7F0  37 0f 70 f0  extr
   800BD7F4  d9 0f da be  lea a15, [a0-0x4126]
   800BD7F8  02 94        mov d4, d9
```
- **WRITE** `800C30CE` lea a15  puis ['st.h [a15], d0', 'st.h [a15], d15', 'st.h [a15], d15']
```
   800C30AE  da 00        op16 da 00
   800C30B0  d9 0f f8 de  lea a15, [a0-0x2108]
   800C30B4  b4 ff        st.h [a15], d15
   800C30B6  d9 0f 5c 92  lea a15, [a0-0x6da4]
   800C30BA  14 ff        ld.bu d15, [a15]
   800C30BC  8b 0f 20 f2  op32 8b
   800C30C0  f6 fe        op16 f6 fe
   800C30C2  d9 0f c4 ee  lea a15, [a0-0x113c]
   800C30C6  09 f0 c0 08  ld.hu d0, [a15+0x0]
   800C30CA  ff 20 09 80  op32 ff
>> 800C30CE  d9 0f e8 de  lea a15, [a0-0x2118]
   800C30D2  d9 02 f8 de  lea a2, [a0-0x2108]
   800C30D6  09 20 c0 08  ld.hu d0, [a2+0x0]
   800C30DA  b4 f0        st.h [a15], d0
   800C30DC  f6 ff        op16 f6 ff
   800C30DE  c5 df 72 22  lea a15, 0xd00024b2
```
- **WRITE** `800D05AA` lea a15  puis ['st.h [a15], d0']
```
   800D058A  05 d4 46 7d  op32 05
   800D058E  6d fb 6b f7  call 0x8004f464
   800D0592  25 d2 46 79  op32 25
   800D0596  c5 de 4a 71  lea a14, 0xd00015ca
   800D059A  91 d0 01 4a  movh.a a4, 0xa01d0000
   800D059E  d9 44 b0 30  lea a4, [a4+0x30b0]
   800D05A2  91 a0 01 5a  movh.a a5, 0xa01a0000
   800D05A6  d9 55 3c 46  lea a5, [a5+0x463c]
>> 800D05AA  d9 0f e8 de  lea a15, [a0-0x2118]
   800D05AE  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800D05B2  6d fb 77 e3  call 0x8004cca0 map_interp_C
   800D05B6  37 02 50 f0  extr
   800D05BA  c5 df 4c 71  lea a15, 0xd00015cc
```
- **WRITE** `800F0C64` lea a15  puis ['st.h [a15], d15']
```
   800F0C44  91 03 f4 af  movh.a
   800F0C48  da 00        op16 da 00
   800F0C4A  34 ff        op16 34 ff
   800F0C4C  d9 04 90 03  lea a4, [a0+0x390]
   800F0C50  34 4f        op16 34 4f
   800F0C52  d9 05 89 03  lea a5, [a0+0x389]
   800F0C56  34 5f        op16 34 5f
   800F0C58  1d 00 1c 01  op32 1d
   800F0C5C  91 80 01 4a  movh.a a4, 0xa0180000
   800F0C60  d9 44 84 a5  lea a4, [a4-0x5a7c]
>> 800F0C64  d9 0f e8 de  lea a15, [a0-0x2118]
   800F0C68  09 f4 c0 08  ld.hu d4, [a15+0x0]
   800F0C6C  6d fa 8a e1  call 0x8004cf80 map_interp_D
   800F0C70  91 10 00 dd  movh.a a13, 0xd0010000
   800F0C74  da 01        op16 da 01
   800F0C76  d9 dd d7 ba  lea a13, [a13-0x4529]
```
- **WRITE** `800F17B6` lea a15  puis ['st.h [a15], d2', 'st.h [a15], d2']
```
   800F1796  6d fa e3 e1  call 0x8004db5c map_interp_F
   800F179A  02 2f        mov d15, d2
   800F179C  09 a0 41 08  ld.b d0, [a10+0x1]
   800F17A0  d9 1f 70 e8  lea a15, [a1-0x1790]
   800F17A4  01 f0 03 46  addsc.a a4, a15, d0, #3
   800F17A8  6d fa da e1  call 0x8004db5c map_interp_F
   800F17AC  02 f4        mov d4, d15
   800F17AE  6d fa bb e8  call 0x8004e924
   800F17B2  3c 09        op16 3c 09
   800F17B4  82 02        mov d2, #0
>> 800F17B6  d9 0f e8 de  lea a15, [a0-0x2118]
   800F17BA  02 29        mov d9, d2
   800F17BC  f8 08        st.a [a10]+0x20, a15
   800F17BE  d9 0f a4 1e  lea a15, [a0+0x1ea4]
   800F17C2  f8 09        st.a [a10]+0x24, a15
   800F17C4  d8 07        ld.a a15, [a10]+0x1c
   800F17C6  14 ff        ld.bu d15, [a15]
   800F17C8  76 f7        op16 76 f7
```
- **WRITE** `80103DFA` lea a15  puis ['st.h [a15], d2']
```
   80103DDA  10 60        addsc.a a0, a6, d15, #0
   80103DDC  09 2f c0 08  ld.hu d15, [a2+0x0]
   80103DE0  b4 ff        st.h [a15], d15
   80103DE2  d9 12 c2 ea  lea a2, [a1-0x153e]
   80103DE6  09 2f c0 08  ld.hu d15, [a2+0x0]
   80103DEA  78 17        op16 78 17
   80103DEC  2e 92        op16 2e 92
   80103DEE  3c 02        op16 3c 02
   80103DF0  d8 13        ld.a a15, [a10]+0x4c
   80103DF2  09 ff c0 08  ld.hu d15, [a15+0x0]
   80103DF6  25 df 68 aa  op32 25
>> 80103DFA  d9 0f e8 de  lea a15, [a0-0x2118]
   80103DFE  f8 0c        st.a [a10]+0x30, a15
   80103E00  d9 0f 1c 60  lea a15, [a0+0x601c]
   80103E04  f8 02        st.a [a10]+0x8, a15
   80103E06  09 f4 c0 08  ld.hu d4, [a15+0x0]
   80103E0A  d8 0c        ld.a a15, [a10]+0x30
   80103E0C  09 f5 c0 08  ld.hu d5, [a15+0x0]
```
- **WRITE** `8011830E` lea a2  puis ['st.h [a2], d15']
```
   801182EE  ac 09        op16 ac 09
   801182F0  14 2f        ld.bu d15, [a2]
   801182F2  76 fe        op16 76 fe
   801182F4  d9 02 e8 de  lea a2, [a0-0x2118]
   801182F8  89 a2 9c 09  op32 89
   801182FC  09 2f c0 08  ld.hu d15, [a2+0x0]
   80118300  d9 12 7e e9  lea a2, [a1-0x1682]
   80118304  09 20 c0 08  ld.hu d0, [a2+0x0]
   80118308  7f f0 18 80  op32 7f
   8011830C  3c 0d        op16 3c 0d
>> 8011830E  d9 02 e8 de  lea a2, [a0-0x2118]
   80118312  89 a2 9c 09  op32 89
   80118316  09 2f c0 08  ld.hu d15, [a2+0x0]
   8011831A  d9 12 7c e9  lea a2, [a1-0x1684]
   8011831E  09 20 c0 08  ld.hu d0, [a2+0x0]
```
- **WRITE** `8013364C` lea a15  puis ['st.h [a15], d15']
```
   8013362C  94 ff        ld.h d15, [a15]
   8013362E  25 df 18 2b  op32 25
   80133632  d9 1f 12 7b  lea a15, [a1+0x7b12]
   80133636  09 ff c0 08  ld.hu d15, [a15+0x0]
   8013363A  25 df bc 69  op32 25
   8013363E  00 90        op16 00 90
   80133640  d9 0f 88 2e  lea a15, [a0+0x2e88]
   80133644  09 ff c0 08  ld.hu d15, [a15+0x0]
   80133648  25 df f8 89  op32 25
>> 8013364C  d9 0f e8 de  lea a15, [a0-0x2118]
   80133650  09 ff c0 08  ld.hu d15, [a15+0x0]
   80133654  25 df f4 89  op32 25
   80133658  d9 0f 50 7e  lea a15, [a0+0x7e50]
   8013365C  09 ff c0 08  ld.hu d15, [a15+0x0]
```
- **WRITE** `80133A44` lea a15  puis ['st.h [a15], d0', 'st.h [a15], d0', 'st.h [a15], d0', 'st.h [a15], d0', 'st.h [a15], d0', 'st.h [a15], d0']
```
   80133A24  d9 0f c6 ee  lea a15, [a0-0x113a]
   80133A28  9b 7f 00 f0  op32 9b
   80133A2C  59 0f dc 6d  op32 59
   80133A30  bb f0 ff 0f  op32 bb
   80133A34  b4 f0        st.h [a15], d0
   80133A36  d9 0f c8 ee  lea a15, [a0-0x1138]
   80133A3A  b4 f0        st.h [a15], d0
   80133A3C  82 00        mov d0, #0
   80133A3E  d9 0f f0 de  lea a15, [a0-0x2110]
   80133A42  b4 f0        st.h [a15], d0
>> 80133A44  d9 0f e8 de  lea a15, [a0-0x2118]
   80133A48  b4 f0        st.h [a15], d0
   80133A4A  d9 0f f8 de  lea a15, [a0-0x2108]
   80133A4E  b4 f0        st.h [a15], d0
   80133A50  d9 0f ea de  lea a15, [a0-0x2116]
   80133A54  b4 f0        st.h [a15], d0
   80133A56  d9 0f ad 91  lea a15, [a0-0x6e53]
```
- **WRITE** `80143D64` lea a15  puis ['st.h [a15], d15']
```
   80143D44  a0 22        op16 a0 22
   80143D46  50 f4        addsc.a a4, a15, d15, #1
   80143D48  c2 1f        add d15, #1
   80143D4A  b4 40        st.h [a4], d0
   80143D4C  fc 2d        op16 fc 2d
   80143D4E  00 90        op16 00 90
   80143D50  bb f0 ff ff  op32 bb
   80143D54  d9 0f 10 5e  lea a15, [a0+0x5e10]
   80143D58  b4 ff        st.h [a15], d15
   80143D5A  d9 0f 12 5e  lea a15, [a0+0x5e12]
   80143D5E  b4 ff        st.h [a15], d15
   80143D60  00 90        op16 00 90
   80143D62  00 00        op16 00 00
>> 80143D64  d9 0f e8 de  lea a15, [a0-0x2118]
   80143D68  09 ff c0 08  ld.hu d15, [a15+0x0]
   80143D6C  25 df 2c aa  op32 25
   80143D70  d9 0f d8 7e  lea a15, [a0+0x7ed8]
   80143D74  da 00        op16 da 00
   80143D76  b4 ff        st.h [a15], d15
```
st.h BOL [a0-0x2118] : **0**
st.h BO [a0-0x2118] : **0**
movh.a+lea → cible : **0**

## `D0011D74`  turbo table base (SP+4)

disp vs A0 : `+5492` (`1574`)

lea ABS : **0**
lea [a0+0x1574] : **8**
- **WRITE** `8014E040` lea a15  puis ['st.h [a15], d1', 'st.h [a15], d1']
```
   8014E020  cc bd        op16 cc bd
   8014E022  09 6f 04 49  st.w d15, [a6+0x104]
   8014E026  59 0f d0 bd  op32 59
   8014E02A  da 00        op16 da 00
   8014E02C  a0 77        op16 a0 77
   8014E02E  8f 4f 00 10  op32 8f
   8014E032  d9 0f 34 f5  lea a15, [a0-0xacc]
   8014E036  01 61 00 c6  addsc.a a12, a6, d1, #0
   8014E03A  01 f1 00 56  addsc.a a5, a15, d1, #0
   8014E03E  82 00        mov d0, #0
>> 8014E040  d9 0f 74 15  lea a15, [a0+0x1574]
   8014E044  01 f1 00 46  addsc.a a4, a15, d1, #0
   8014E048  49 cd 00 2a  lea a13, [a12+0x80]
   8014E04C  a0 7e        op16 a0 7e
   8014E04E  01 50 01 f6  addsc.a a15, a5, d0, #1
   8014E052  01 c0 01 26  addsc.a a2, a12, d0, #1
```
- **WRITE** `8014E09A` lea a15  puis ['st.h [a15], d1', 'st.h [a15], d1']
```
   8014E07A  00 49        op16 00 49
   8014E07C  19 0f d0 bd  op32 19
   8014E080  89 7f 04 49  op32 89
   8014E084  da 00        op16 da 00
   8014E086  a0 7c        op16 a0 7c
   8014E088  8f 4f 00 10  op32 8f
   8014E08C  d9 0f 34 f5  lea a15, [a0-0xacc]
   8014E090  01 71 00 d6  addsc.a a13, a7, d1, #0
   8014E094  01 f1 00 66  addsc.a a6, a15, d1, #0
   8014E098  82 00        mov d0, #0
>> 8014E09A  d9 0f 74 15  lea a15, [a0+0x1574]
   8014E09E  01 f1 00 46  addsc.a a4, a15, d1, #0
   8014E0A2  49 d5 00 2a  lea a5, [a13+0x80]
   8014E0A6  a0 7e        op16 a0 7e
   8014E0A8  01 d0 01 f6  addsc.a a15, a13, d0, #1
   8014E0AC  01 60 01 26  addsc.a a2, a6, d0, #1
```
st.h BOL [a0+0x1574] : **0**
st.h BO [a0+0x1574] : **0**
movh.a+lea → cible : **0**

## Table turbo — voisins `D0011D74`+0..64

- **WRITE** `8014E040`  ram `1D74`  a15  ['st.h [a15], d1', 'st.h [a15], d1']
```
   8014E02C  a0 77        op16 a0 77
   8014E02E  8f 4f 00 10  op32 8f
   8014E032  d9 0f 34 f5  lea a15, [a0-0xacc]
   8014E036  01 61 00 c6  addsc.a a12, a6, d1, #0
   8014E03A  01 f1 00 56  addsc.a a5, a15, d1, #0
   8014E03E  82 00        mov d0, #0
>> 8014E040  d9 0f 74 15  lea a15, [a0+0x1574]
   8014E044  01 f1 00 46  addsc.a a4, a15, d1, #0
   8014E048  49 cd 00 2a  lea a13, [a12+0x80]
   8014E04C  a0 7e        op16 a0 7e
   8014E04E  01 50 01 f6  addsc.a a15, a5, d0, #1
```
- **WRITE** `8014E09A`  ram `1D74`  a15  ['st.h [a15], d1', 'st.h [a15], d1']
```
   8014E086  a0 7c        op16 a0 7c
   8014E088  8f 4f 00 10  op32 8f
   8014E08C  d9 0f 34 f5  lea a15, [a0-0xacc]
   8014E090  01 71 00 d6  addsc.a a13, a7, d1, #0
   8014E094  01 f1 00 66  addsc.a a6, a15, d1, #0
   8014E098  82 00        mov d0, #0
>> 8014E09A  d9 0f 74 15  lea a15, [a0+0x1574]
   8014E09E  01 f1 00 46  addsc.a a4, a15, d1, #0
   8014E0A2  49 d5 00 2a  lea a5, [a13+0x80]
   8014E0A6  a0 7e        op16 a0 7e
   8014E0A8  01 d0 01 f6  addsc.a a15, a13, d0, #1
```
total stores dans la fenetre table : **2**

