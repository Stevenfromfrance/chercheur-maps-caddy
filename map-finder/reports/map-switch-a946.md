# D000A946 + switch soft/RACE — 2026-08-23

A0=`D0010800`. RAM=`D000A946` disp A0 `-24250` (`0xa146`).

Site rail B `800B5A96` : `ld.bu d5` = **index Y** de `interp_2d_B` grille `1E9BC8`.
Ce n est **pas** un switch Stage1 entier (AccPed). C est un mode rail.

## lea [a0+disp] : 28 sites

### WRITE st.b @ `801164CA` a15
```
   801164B2  08 50        op16 08 50
   801164B4  14 ff        ld.bu d15, [a15]
   801164B6  14 20        ld.bu d0, [a2]
   801164B8  12 04        op16 12 04
   801164BA  6d f9 87 bf  call 0x8004e3c8
   801164BE  3b 00 08 00  op32 3b
   801164C2  34 f2        op16 34 f2
   801164C4  14 ff        ld.bu d15, [a15]
   801164C6  3f 0f 09 80  op32 3f
>> 801164CA  d9 0f 46 a1  lea a15, [a0-0x5eba]  ; ram D000A946
   801164CE  d9 12 8d 5a  lea a2, [a1+0x5a8d]  ; A019628D winols 19628D
   801164D2  14 2f        ld.bu d15, [a2]
   801164D4  34 ff        op16 34 ff
   801164D6  00 90        ret
   801164D8  86 1f        sha d15, #1
```

### WRITE st.b @ `80135A04` a15
```
   801359EC  d4 d7        ld.a a7, [a13]
   801359EE  d9 0f 47 a1  lea a15, [a0-0x5eb9]  ; ram D000A947
   801359F2  6d f8 f7 b9  call 0x8004cde0 map_interp_N
   801359F6  34 f2        op16 34 f2
   801359F8  00 90        ret
   801359FA  3b b0 00 40  op32 3b
   801359FE  6d f9 61 c1  call 0x8006dcc0
   80135A02  76 28        op16 76 28
>> 80135A04  d9 0f 46 a1  lea a15, [a0-0x5eba]  ; ram D000A946
   80135A08  d9 02 47 a1  lea a2, [a0-0x5eb9]  ; ram D000A947
   80135A0C  14 2f        ld.bu d15, [a2]
   80135A0E  34 ff        op16 34 ff
   80135A10  00 90        ret
   80135A12  d9 0f 46 a1  lea a15, [a0-0x5eba]  ; ram D000A946
```

### WRITE st.b @ `80135A12` a15
```
   801359FA  3b b0 00 40  op32 3b
   801359FE  6d f9 61 c1  call 0x8006dcc0
   80135A02  76 28        op16 76 28
   80135A04  d9 0f 46 a1  lea a15, [a0-0x5eba]  ; ram D000A946
   80135A08  d9 02 47 a1  lea a2, [a0-0x5eb9]  ; ram D000A947
   80135A0C  14 2f        ld.bu d15, [a2]
   80135A0E  34 ff        op16 34 ff
   80135A10  00 90        ret
>> 80135A12  d9 0f 46 a1  lea a15, [a0-0x5eba]  ; ram D000A946
   80135A16  d9 12 8d 5a  lea a2, [a1+0x5a8d]  ; A019628D winols 19628D
   80135A1A  14 2f        ld.bu d15, [a2]
   80135A1C  34 ff        op16 34 ff
   80135A1E  00 90        ret
   80135A20  d9 0f 52 f1  lea a15, [a0-0xeae]  ; ram D000F952
```

## Resume lectures vs ecritures

- `ld.bu` : 25
- `st.b` : 3

Writes stricts : **3**

## Flag flash cote site B (`A1+0x1872` = `192072`)

```
   800B5A64  c0 08        op16 c0 08
   800B5A66  6d fc 9d b6  call 0x8004c7a0 interp_2d
   800B5A6A  02 2b        mov d11, d2
>> 800B5A6C  d9 12 72 18  lea a2, [a1+0x1872]  ; A0192072 winols 192072
   800B5A70  14 2f        ld.bu d15, [a2]
   800B5A72  6e 16        jz d15, +22
   800B5A74  91 f0 01 4a  movh.a a4, 0xa01f0000
   800B5A78  d9 44 c8 9b  lea a4, [a4-0x6438]
   800B5A7C  91 f0 01 5a  movh.a a5, 0xa01f0000
```

