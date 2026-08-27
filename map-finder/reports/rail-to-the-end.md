# Rail jusqu au bout — 2026-08-23

A0=`D0010800` A1=`A0190800`. Offline Golf 9980. Pas de nom OEM.

Le « bout » ici = **flash + RAM capteur/ratio**, pas un IdName Bosch.

---

## Verdict

`FUN_8004d15c` n’est **pas** le calcul rail. C’est un **filtre 1D / PT1 générique** (208 callers, 38 octets, `ret` = `00 90`).

La grandeur rail X qui nourrit `rail_base` `1E9DE0` est :

```
D00019DC / D000048A          FUN_8004d0a4 (div.u générique, 66 callers)
        ↓
   D0018666                  X de la courbe
        ↓
   map_interp_C @ 8007D4D4
   a4 = 18D0F0   a5 = 1930CC
        ↓
   D0013872  → (flag D0013A52) →  D0013870     cible
        ↓
   FUN_8004d15c  (d4=3874  d5=3870  d6=u16 @ 19314A)
        ↓
   D0013874  → copie →  D000B6AE  → interp rail 1E9DE0
```

`D000E6E8` n’est **pas** un madd. C’est un **quotient** (`dvinit.u` + `dvstep` + `loop`). Chaîne :

```
objet RAM D00185C0  +  d14 live
        ↓
   FUN_8006cf78  (lookup indexé)  puis  FUN_8006d998  (ratio d4/d5)
        ↓
   D00175E8 / D00175DC
        ↓
   FUN_80080efa  (div → D000F6C6)
   FUN_80080f4c  (div d15/d4 → d2, clamp vs D000F6C4)
        ↓
   D000E6E8  = X de la courbe 197382  (FUN_8004bdc8)
            puis map_interp_H @ 1973A8
```

Init 3870 depuis flash `18C154` = **0** (défaut). Le live ne vient pas de là.

---

## 1) `FUN_8004d15c` @ `8004D15C` — filtre générique

Ret @ `8004D182` (len `0x26`). Call-site rail : `800BA0C8`.

```
jlt.u  d4, d5, …          ; courant vs cible
sub    d5, d4             ; delta = cible − courant
mul    d15, d5, d6        ; delta × gain (d6 = u16 flash 19314A)
sh / add / extr → d2      ; ramène vers d4
ret
```

Nouveau ≈ courant + (cible − courant) × gain / échelle.

Ce n’est **pas** spécifique rail : mêmes 38 octets aussi dans des boucles (`80079D06` écrit `d2` dans un buffer) et d’autres maps (`195152` comme `d6`).

Site rail :

```
800BA0B0  lea a12, D0013874
          ld.hu d4, [a12]           ; courant
          ld.hu d5, D0013870        ; cible
          ld.hu d6, flash 19314A    ; gain (une case dans une table 82xx)
800BA0C8  call FUN_8004d15c
          st.h [a12], d2
```

`19314A` = `0x8280` : pas une courbe isolée, une case dans un bloc qui se répète (`8255` / `822b` / `8316`…). Valeur autour de l’offset `0x8000`.

---

## 2) Cible `D0013870` — vraie consigne avant le filtre

Trois `st.h` stricts :

| VA | Quoi |
|----|------|
| `8007D4EA` | **live** : copie de `D0013872` (sortie interp_C) si flag `D0013A52` |
| `8007D4FA` | init : flash `18C154` → 3870 (`u16=0`) |
| `8012FCDC` | même init `18C154` → 3870 |

Interp qui alimente 3872 / 3870 :

```
8007D4C0  lea a15, D0013872          ; destination
          lea a4,  18D0F0            ; table / courbe
          lea a5,  1930CC            ; axe / sibling
          ld.hu d4, D0018666         ; X
8007D4D4  call map_interp_C
          st.h [a15], d2             ; 3872
          si D0013A52 : 3870 = 3872
```

`18D0F0` n’est pas dans l’atlas Stage1 (pas un start `18D180` / `18C380`). Valeurs ~`7E40`–`7E99` (décroissant). Pas de nom OEM.

---

## 3) X de cette courbe : `D0018666` = ratio

Writers live :

```
80071E38  lea a15, D00019DC
          ld.h  d5, D00019DC         ; dénominateur (RAM mesure)
          ld.w  d4, D000048A         ; numérateur (ABS, voisin ram_0414)
80071E4A  call FUN_8004d0a4          ; div.u d4/d5 → d2  (66 callers)
80071E4E  st.h  D0018666, d2

80071E5A  variante D00019DE / même helper
8014365A  autre voie : FUN_8004df60 (mul + sat) puis st.h 8666
```

`FUN_8004d0a4` = encore un helper générique (diviseur 32/32), pas « la fonction rail ».

`D000048A` est dans le même voisinage que `ram_0414` (`D0000414`) déjà vu comme `A13` du site rail 2d `800F5114`.

---

## 4) `D000E6E8` — quotient, pas madd

Writer live `80080FE4` `st.h [a12], d2` dans `FUN_80080f4c` (début après `ret` @ `80080F4A`).

`4b … a0` = `dvinit.u`, `6b` = `dvstep`, `fc` = `loop`, `a0 3f` = `mov.a a15, #15` (16 pas). Quotient dans E2/`d2`.

4 callers de `80080F4C` : `80081162`, `80091AC0`, `800DC760`, `8014177A`. Les 3 derniers ont le même préambule :

```
call FUN_80080ebc          ; index depuis D00185C0+0x41 + D00099B1 + D00099A8
mov  d4, #0
call FUN_8006cf78          ; lookup dans l’objet D00185C0 (index d4)
mov  d5, d14               ; grandeur live
lea  a15, D00175E8
mov  d4, d2
call FUN_8006d998          ; ratio d4/d5 (div.u, 15 callers)
call FUN_80080efa          ; charge D00175E8, div, st.h D000F6C6
call FUN_80080f4c          ; d15/d4 → d2 → D000E6E8 (min/max vs D000F6C4)
```

`D00185C0` n’est pas un u16 isolé : **objet** (stores aux offsets `+0x2E` / `+0x30` / `+0x32`, lectures `+0x41` / `+0x4E`).

Juste après le store E6E8, le même caller @ `80091AC0` :

```
lea a4,  197382
lea a15, D000E6E8
ld.hu d4, [a15]
call FUN_8004bdc8          ; interp 1D (longueur + breakpoints dans [a4])
lea a4,  1973A8
call map_interp_H
```

Donc E6E8 = **X calculé** (ratio) pour les courbes `197382` / `1973A8`. Pas la consigne bar rail.

Cluster voisin : `E6EA` `E6F0` `E6F6` `E6F8`. Zero-init @ `80133A48`.

`D000F6C4` (clamp) : pas un writer live utile — `80081104` est une **lecture** puis helper ; `80133A96` = init.

---

## 5) Flash touchée (WinOLS = 24 bits bas)

| WinOLS | Abs | Rôle |
|--------|-----|------|
| `18D0F0` | `A018D0F0` | table interp_C → 3872/3870 |
| `1930CC` | `A01930CC` | axe / sibling du même call |
| `19314A` | `A019314A` | gain PT1 de 3874 (une case) |
| `18C154` | `A018C154` | défaut 3870 = 0 (près SOI `18C380`) |
| `197382` | `A0197382` | courbe 1D, X = E6E8 |
| `1973A8` | `A01973A8` | map_interp_H, même bloc |

Aucune de ces adresses n’est le start atlas `rail_base` `1E9368`. La map rail **consommée** reste `1E9DE0` (site `800F5114`).

---

## Limite honnête

- Helpers (`8004D15C`, `8004D0A4`, `8006D998`, `80080F4C`) sont **partagés**. Les suivre « tout seuls » ne nomme rien.
- `18D0F0` / `1930CC` / `197382` / `D00019DC` : pas dans l’atlas Stage1, pas d’A2L → **pas de nom OEM**.
- `D00185C0` est un objet runtime (comme la table turbo `D0011D74`), pas une cal u16.
- Flasher depuis ces labels = faux.
