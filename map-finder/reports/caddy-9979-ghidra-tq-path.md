# Caddy 9979 — chemin couple (Ghidra proxy 9980 + sondage V5d)

**But :** avant un flash AccPed V6e, vérifier si le mou @3800–4200 (wish≈333, TQI≈214–255) vient d’un limiteur carto consommé en code.

**Méthode :** call-sites Golf 9980 (même famille PCR / offsets Stage1 souvent = 9979) + valeurs V5d Caddy aux points log.

## Verdict court

**AccPed V6e n’est pas le fix du mou @3800.** Wish AccPed ≈333 Nm là où TQI log tombe à 214–255.

### Levier carto le plus solide (base de données + axes)

| Map | Addr | Fait V5d | Impact mou |
|---|---|---|---|
| **`tqlim_base_pu_4A`** | `1D3190` | **370 Nm jusqu’à 3750**, puis **278 @4000**, **257 @4200**, **234 @4400** (ATM≈1000) | Explique une partie du soft **≥4000** ; **pas** le soft @3814 (limite encore ~346) |
| **`tqlim_tegt_temp`** | `1D35A8` | V5d = **ORI** (pas ACE). Axe EGT commence à **780 °C** ; dès 780 °C → ~238 Nm @3750 / ~226 @4000. ACE était plat **350** jusqu’à ~910 °C | Candidate **si** EGT ≥780 en WOT long ; inactif sous 780 (sinon impossible d’avoir vu 333 midband) |
| `smoke_mapA@1D2270` | `1D2270` | ~360–373 aux probes | Pas clip (banque primary) |
| Autres smoke | `1D1D18`… | Basses à MAP faible | Midband TQI 333 les écarte comme banques actives |
| AccPed 100 % | `1CF9C0` | ~333 @3800–4000 | **Pas** le trou @3800 ; fill V6e utile seulement **>4000→cut** |

### Sondage V5d — valeur carte @ points log (interp)

> Note : sonde `tqlim_tegt` avec EGT=620 était **sous l’axe** (min 780) → clamp 1ʳᵉ colonne. Corrigé ci-dessus.

| Map | addr | @hold 3832 | @soft 3814 | @soft 3865 | @soft 4006 | clip soft? |
|---|---|---:|---:|---:|---:|:---:|
| `tqlim_speed2A` | `1CEED4` | 350 | 350 | 350 | 350 | no |
| `AccPed_trq4A` | `1CF9C0` | 333 | 333 | 333 | 331 | no |
| `AccPed_trq4A@1CFAC0` | `1CFAC0` | 333 | 333 | 333 | 331 | no |
| `AccPed_trq4A@1CFBC0` | `1CFBC0` | 333 | 333 | 333 | 331 | no |
| `AccPed_trq4A@1CFCC0` | `1CFCC0` | 333 | 333 | 333 | 331 | no |
| `AccPed_trq4A@1CFDC0` | `1CFDC0` | 333 | 333 | 333 | 331 | no |
| `AccPed_trq4A@1CFEC0` | `1CFEC0` | 333 | 333 | 333 | 331 | no |
| `AccPed_trq4A@1CFFC0` | `1CFFC0` | 330 | 330 | 330 | 327 | no |
| `AccPed_trq4A@1D0640` | `1D0640` | 318 | 318 | 318 | 318 | no |
| `tqlim_cluth_prot` | `1D0860` | 1024 | 1024 | 1024 | 1024 | no |
| `smoke_mapA` | `1D1D18` | 320 | 243 | 304 | 199 | YES |
| `smoke_mapA@1D1FC4` | `1D1FC4` | 320 | 243 | 304 | 199 | YES |
| `smoke_mapA@1D2270` | `1D2270` | 373 | 368 | 371 | 360 | no |
| `smoke_mapA@1D251C` | `1D251C` | 291 | 231 | 281 | 192 | YES |
| `smoke_mapA@1D27C8` | `1D27C8` | 297 | 234 | 285 | 182 | YES |
| `tqlim_fuel_temp2` | `1D2C1C` | 400 | 400 | 400 | 400 | no |
| `tqlim_base_pu_4A` | `1D3190` | 340 | 346 | 328 | 277 | YES |
| `tqlim_fuel_temp2A` | `1D3390` | 1024 | 1024 | 1024 | 1024 | no |
| `tqlim_tegt_temp` | `1D35A8` | 234 | 235 | 233 | 226 | YES |

**Suspects clip (<~293 Nm sur soft) :** `smoke_mapA`@1D1D18→199, `smoke_mapA@1D1FC4`@1D1FC4→199, `smoke_mapA@1D251C`@1D251C→192, `smoke_mapA@1D27C8`@1D27C8→182, `tqlim_base_pu_4A`@1D3190→277, `tqlim_tegt_temp`@1D35A8→226

- `tqlim_tegt_temp` : axe EGT **780→930 °C**. V5d=ORI (~238 Nm dès 780 @3750). ACE=350 plat. Call-sites Ghidra : `80097294`, `8009725C`, `8009900A`, `800991D4`.
- `tqlim_base_pu_4A` : cliff RPM **3750→4000** (370→278). Call-sites : `8008736E`, `800DDACE`, `800DDA36`.

## Conclusion pour AccPed V6e

| Hypothèse | Statut |
|---|---|
| AccPed wish trop bas @3800 | **Faux** (wish≈333, TQI soft) |
| `tqlim_base` clip | **Oui au-delà de ~3900–4000** ; faible @3814 |
| `tqlim_tegt` ORI clip | **Possible si EGT≥780** (WOT long) ; call-sites présents en code 9980 |
| smoke primary clip | **Non** |
| turbo_base trop bas | **Non vs ACE** ; MAP_SP parfois sous demande |
| AccPed fill 4000→5000 | Utile haut de bande **après** tqlim_base, pas le trou mid |

### Next (ordre)

1. **Log ROUTE dense** WOT 3000→cut + si possible EGT / surveiller si TQI suit le cliff `tqlim_base` à 4000.
2. **Preview carto** : fill `tqlim_base` 4000–4600 (remonter vers 330–350, pas 370 plat) **avant** AccPed V6e.
3. Option : re-monter `tqlim_tegt` partiel vers ACE (V5d l’a remis ORI) — seulement si logs EGT le justifient.
4. AccPed V6e = polish traction cut, **pas** le premier levier.

_Généré / mis à jour après piste Ghidra + sondage axes._

## Call-sites Ghidra (Golf 9980 → offsets 9979)

TriCore ne pose souvent **pas** de XREF ptr 32-bit vers le début de map ; les consommateurs = **CALL hub interp**. Proxy code = fullflash Golf 9980 (adresses Stage1 souvent identiques 9979 — colonne CSV).

### `turbo_base3B` @ `1C04AC` — 1 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x800e0eca` | 2d | `1C0714` | oui |

Parent emu `@ 0x800e0eca` :
- D4=3489672588 (ld.hu_bo+a14) · D5=None ()
- A: A4=0xa01c0714, A5=0xa019b5d4, A6=0xa019c754, A14=0xd0002d8c
- PFLASH: 0xa01c0714, 0xa019b5d4, 0xa019c754
- RAM: 0xd0002d8c

### `duration_inj6A` @ `1CDC84` — 6 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x80074ebe` | 2d | `1CDE04` | oui |
| `0x8007e3d0` | F | `1CDE5C` | oui |
| `0x8008b652` | C | `1CDE50` | oui |
| `0x800959b6` | C | `1CDE44` | oui |
| `0x800d6784` | B | `1CDE8C` | oui |
| `0x800f8d96` | I | `1CDF60` | oui |

Parent emu `@ 0x80074ebe` :
- D4=None () · D5=None (ld.hu_bo/indirect)
- A: A4=0xa01cde04, A5=0xa01a2734, A6=0xa01ad8d0, A15=0xa01ad8d0
- PFLASH: 0xa01ad8d0, 0xa01cde04, 0xa01a2734, 0xa01ad8d0

Parent emu `@ 0x8007e3d0` :
- D4=None (ld.hu_bo/indirect) · D5=None ()
- A: A4=0xa01a57f0, A15=0xa01cde5c
- PFLASH: 0xa01a163c, 0xa01a57f0, 0xa01cde5c

### `tqlim_speed2A` @ `1CEED4` — 2 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x800a6b86` | 2d | `1CEEF4` | oui |
| `0x800b0394` | 2d | `1CEF18` | oui |

Parent emu `@ 0x800a6b86` :
- D4=None () · D5=None (ld.hu_bo/indirect)
- A: A4=0xa01ceef4, A5=0xa01a3444, A6=0xa01a1448, A13=0xd0002812, A14=0xd0002810
- PFLASH: 0xa01ceef4, 0xa01a3444, 0xa01a1448

Parent emu `@ 0x800b0394` :
- D4=None (ld.hu_bo/indirect) · D5=None ()
- A: A4=0xa01cef18, A5=0xa01b38d4, A6=0xa01a67c4
- PFLASH: 0xa01cef18, 0xa01b38d4, 0xa01a67c4

### `AccPed_trq4A` @ `1CF9C0` — 2 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x80116c8e` | E | `1CFA3C` | ? |
| `0x80116cae` | C | `1CFA30` | ? |

Parent emu `@ 0x80116c8e` :
- D4=3489673556 (ld.hu_abs) · D5=None (ld.hu_bo/indirect)
- PFLASH: 0xa01cfa3c

Parent emu `@ 0x80116cae` :
- D4=None (ld.hu_bo/indirect) · D5=None (ld.hu_bo/indirect)
- A: A4=0xa01cfa30, A5=0xa01a46c0
- PFLASH: 0xa01cfa3c, 0xa01cfa30, 0xa01a46c0

### `tqlim_cluth_prot` @ `1D0860` — 3 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x80074040` | F | `1D08BC` | oui |
| `0x800fc25a` | C | `1D0878` | oui |
| `0x800fc314` | C | `1D086C` | oui |

Parent emu `@ 0x80074040` :
- D4=None (ld.hu_bo/indirect) · D5=None ()
- A: A4=0xa01d08bc
- PFLASH: 0xa01ce85c, 0xa019f6c0, 0xa01d08bc

Parent emu `@ 0x800fc25a` :
- D4=None (ld.hu_bo/indirect) · D5=None (ld.hu_bo/indirect)
- A: A4=0xa01d0878, A5=0xa01ad908, A6=0xa01ab87c, A12=0xa01ab87c, A13=0xa01b3914, A14=0xa01d184c
- PFLASH: 0xa01d0878, 0xa01ad908

### `smoke_mapA` @ `1D1D18` — 2 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x80074db2` | 2d | `1D1E64` | oui |
| `0x800f4ba8` | B | `1D1F00` | oui |

Parent emu `@ 0x80074db2` :
- D4=None () · D5=None ()
- A: A4=0xa01d1e64, A5=0xa019f6f8, A6=0xa01ad8d0, A15=0xa01ad8d0
- PFLASH: 0xa01ad8d0, 0xa01d1e64, 0xa019f6f8, 0xa01ad8d0

Parent emu `@ 0x800f4ba8` :
- D4=3489668448 (ld.hu_bo+a14) · D5=None (ld.hu_bo/indirect)
- A: A4=0xa01d1f00, A5=0xa01b38c0, A6=0xa01a06d4, A14=0xd0001d60, A15=0xd0001d62
- PFLASH: 0xa01d1f00, 0xa01b38c0, 0xa01a06d4
- RAM: 0xd0001d62

### `smoke_mapA@1D2270` @ `1D2270` — 4 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x800ddb38` | C | `1D232C` | oui |
| `0x80105626` | D | `1D24BC` | oui |
| `0x801056a4` | D | `1D24AC` | oui |
| `0x80105de2` | 2d | `1D24CC` | oui |

Parent emu `@ 0x800ddb38` :
- D4=None (ld.hu_bo/indirect) · D5=None ()
- A: A4=0xa01d232c, A5=0xa01a6628
- PFLASH: 0xa01d0a2c, 0xa019e5d4, 0xa01d232c, 0xa01a6628

Parent emu `@ 0x80105626` :
- D4=None (ld.hu_bo/indirect) · D5=None (ld.hu_bo/indirect)
- A: A4=0xa01d24bc, A5=0xa01d04a8, A6=0xa01d5488
- PFLASH: 0xa01d24bc

### `tqlim_base_pu_4A` @ `1D3190` — 3 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x8008736e` | B | `1D32CC` | ? |
| `0x800dda36` | E | `1D332C` | oui |
| `0x800ddace` | C | `1D330C` | ? |

Parent emu `@ 0x8008736e` :
- D4=None (ld.hu_bo/indirect) · D5=None ()
- A: A4=0xa01d32cc, A5=0xa01b4894, A6=0xa01b2868, A13=0xa01b2868, A14=0xa01b4894
- PFLASH: 0xa01b4894, 0xa01d32cc, 0xa01b4894, 0xa01b2868

Parent emu `@ 0x800dda36` :
- D4=None (ld.hu_bo/indirect) · D5=None ()
- A: A4=0xa01d332c, A5=0xa01b792c, A15=0xa01b792c
- PFLASH: 0xa01b792c, 0xa01d332c, 0xa01b792c

### `tqlim_fuel_temp2A` @ `1D3390` — 1 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x800edca2` | 2d | `1D33D8` | oui |

Parent emu `@ 0x800edca2` :
- D4=None (ld.hu_bo/indirect) · D5=None (ld.hu_bo/indirect)
- A: A4=0xa01d33d8, A5=0xa01b183c, A6=0xa01b3824, A12=0xd0002f4e
- PFLASH: 0xa01d33d8, 0xa01b183c, 0xa01b3824

### `tqlim_tegt_temp` @ `1D35A8` — 4 call-site(s)

| Call | Hub | WinOLS hit | id. 9979? |
|---|---|---|---|
| `0x8009725c` | K | `1D3670` | oui |
| `0x80097294` | D | `1D3618` | oui |
| `0x8009900a` | H | `1D3712` | oui |
| `0x800991d4` | H | `1D3738` | oui |

Parent emu `@ 0x8009725c` :
- D4=None () · D5=None ()
- PFLASH: 0xa01d3670

Parent emu `@ 0x80097294` :
- D4=3489670220 (ld.hu_bo+a14) · D5=None ()
- A: A14=0xd000244c
- PFLASH: 0xa01d3670, 0xa01d47c8, 0xa01d3618
- RAM: 0xd000244c

## Chaîne connue (Golf 9980, applicable layout 9979)

1. **AccPed** `1CF9C0` / copies — wish pédale→Nm (capteurs APP_r / nmot).
2. **tqlim_base** `1D3190` — plafond ATM×RPM : **370 jusqu’à 3750**, puis chute (278@4000…) — calls `8008736E` / `800DDACE` / `800DDA36`.
3. **tqlim_tegt** `1D35A8` — si EGT≥780 (V5d=ORI agressif) — calls `80097294`…
4. **smoke** `1D2270` — lim fumée MAP×RPM.
5. **nm2iq** puis **duration** — conversion / temps injection.
6. **turbo_base** — consigne boost ; V5d=ACE.

Hiérarchie Amesis : `TQI ≈ min(wish, tqlim*, smoke, …)`.  
@3800 hold : wish≈333, tqlim_base≈340+, smoke≈370 → OK.  
@≥4000 : **tqlim_base** peut devenir le min.  
@EGT≥780 : **tqlim_tegt ORI** peut devenir le min (~220–240).

## Conclusion pour AccPed V6e

| Hypothèse | Statut |
|---|---|
| AccPed wish trop bas @3800 | **Faux** (wish≈333, TQI soft) |
| `tqlim_base` clip | **Oui ≥~4000** ; faible @3814 |
| `tqlim_tegt` ORI clip | **Possible si EGT≥780** |
| smoke primary clip | **Non** |
| turbo_base trop bas | **Non vs ACE** |
| AccPed fill 4000→5000 | Polish cut **après** tqlim_base |

### Next (ordre)

1. Log ROUTE dense WOT 3000→cut (voir si TQI suit le cliff `tqlim_base` @4000).
2. Preview : fill `tqlim_base` 4000–4600 (vers ~330–350) **avant** AccPed V6e.
3. Option tegt partiel vers ACE si EGT le justifie.
4. AccPed V6e = dernier polish, pas le premier levier.

_Généré par `ghidra/caddy_9979_tq_path_probe.py` + correction axes tegt/tqlim._
