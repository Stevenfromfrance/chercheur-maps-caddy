# Vérif SOFT/RACE — 2026-08-23

Relu **depuis les bins**, pas depuis la mémoire chat.

- Golf Ghidra : `Golf6_03L997558A_9980_FULLFLASH.bin`
- Caddy ORI : `Caddy_CAYE_03L906023TB_9979_ORI_2026-07-27.bin`

**Deux dumps.** Le code switch a été chassé sur le Golf. La carto Soft/Race atelier, c’est le **Caddy 9979**. Les adresses AccPed **ne sont pas les mêmes**.

---

## 1) Hook AccPed — Golf 9980 — **OK**

| Check | Résultat |
|-------|----------|
| `800CC4AA` a4 | `A01CFFC0` = grille `1CFFC0` |
| a14 | `D0002198` = APP_r |
| call | `6d fc 7b 01` |
| sites AccPed tuiles | **7 / 7** |

AccPed Golf `@1CFFC0` max = raw 42496 → **304.0 Nm** (proche stock). Ce n’est **pas** la V2 Caddy à 350 Nm.

---

## 2) Colonne 50 % pédale — **OK** (axe A2L, pas l’emu a5)

L’emu met a5=`1AA8E4` : ce n’est **pas** l’axe % pédale (valeurs ~0x9EF3). Fausse piste, corrigée.

L’axe AccPed atlas `1A90C2` est **identique** Golf et Caddy ORI :

`1.0, 4.0, 10.0, 23.0, **50.0**, 75.0, 85.0, 99.9 %`

Colonne 4 (0-based) = 50 %. Soft = colonnes 0–4. Race = 75 / 85 / 100 %.

---

## 3) Arrêt `D0002810` — **OK rôle, pas IdName**

Site `800A6B86` : a14=`D0002810`, a4=`1CEEF4` (intérieur `tqlim_speed2A` `1CEED4`).  
Atlas 9979 : cette map = limiteur couple vs **vitesse véhicule**.

On peut s’en servir pour « ≈ 0 = arrêté ». Facteur km/h exact : pas dans notre A2L reverse.

Frein BLS : **toujours pas trouvé**.

---

## 4) `D000A946` — **OK, pas un switch**

28 lea [a0] : 25 `ld.bu`, 3 `st.b`. Flash `19628D` = `0x80`.

---

## 5) Trou / cave / RAM — **OK scan**

| | |
|--|--|
| `1CB064` | 3456/3456 `FF` |
| cave `8017FE04` | 508/508 `00`, 0 pointeur dans le code |
| `D0002890` | 0 lea ABS / [a0] / movh / st.h BOL-BO |

Limite RAM : un accès par table n’apparaît pas ici. Pas une preuve à 100 %.

**Trampoline : pas écrit.** Rien à flasher pour le switch.

---

## 6) Chiffres Caddy 9979 (350 / 380 / 1620 / 1656)

Caddy ORI **relu** — colle l’atlas :

| Map | Mesure ORI | Atlas ori_max |
|-----|------------|---------------|
| AccPed `1CF9C0` | **293.7 Nm** | 293.7 |
| rail `1E9368` | **1600.0 bar** | 1600 |

ACE / V2 / V3 : **fichiers .bin pas trouvés** dans Reprog-Stage1 / caddy cartho (pack site chiffré).  
1620 / 1656 / 350 / 380 = **stats atlas 9979** (même facteurs que l’ORI qu’on vient de recoller). Pas re-mesurés sur ACE/V2 aujourd’hui.

Launch ~2500 = spec atelier V3 (`tqlim_cluth_prot`), **pas** re-lu rpm dans un bin V3 cette passe.

Un `STAGE_1` Golf trouvé à côté du Caddy (**511 Nm**) n’est **pas** ACE/V2. Ignoré.

---

## Confiance

| Sujet | Verdict |
|-------|---------|
| AccPed Golf `1CFFC0` + APP + call | **prouvé bin** |
| 50 % pédale `1A90C2` | **prouvé bin** Golf = Caddy ORI |
| `D0002810` = vitesse (rôle) | **solide, pas OEM name** |
| Frein | **inconnu** |
| A946 ≠ multi-map | **prouvé** |
| Trou FF / cave | **prouvé** |
| `D0002890` libre | **probable** |
| Rail 1620/1656, AccPed V2 350 / ACE 380 | **atlas Caddy, ORI recollé** |
| Launch 2500 | **atelier, pas re-mesuré** |
| 3 coups dans l’ECU | **pas généré** |

**Ne pas flasher le dump Golf dans le Caddy.** AccPed Caddy = `1CF9C0`. AccPed Golf Ghidra = `1CFFC0`.
