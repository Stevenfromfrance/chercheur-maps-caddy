# Golf 9980 — consommateurs Stage1 (code)

Scan offline du fullflash + call-sites interp deja dans `golf9980_stage1_validated.csv`.
Pointeurs code: little-endian `80xxxxxx` / `A0xxxxxx` dans `0x000000-0x180000`.

- HIGH maps scannees: **65**
- HIGH avec pointeur absolu dans le code: **0**

Parents decodes (2026-08-22, emu + Ghidra KickParents) : voir
`map-finder/reports/ghidra-auto-status.md` (clutch writer `ram_273C`, AccPed `APP_r`/`nmot`,
rail/smoke/vmax).

## clutch_prot

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `tqlim_cluth_prot` | `1D0860` | `0x801D0860` | — | `0x800FC314` (C 0xC) writer X=`ram_273C` @ `800FB7E2`<br>`0x800FC25A` (C 0x18)<br>`0x80074040` (F 0x5C) |

## AccPed

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `AccPed_trq4A` | `1CFFC0` | `0x801CFFC0` | — | `0x800CC4AA` (2d/fam_D0002198_unkY_1CFFC0) APP_r `D0002198` puis nm2iq `0x800CC4D4` nmot `D000219A` |
| `AccPed_trq4A@1D0640` | `1D0640` | `0x801D0640` | — | `0x8009902A` (H 0xFA) |
| `AccPed_trq4A` | `1CFAE4` | `0x801CFAE4` | — | `0x800EC250` (F/F_fam_unkX_unkY_1CFAE4) |
| `AccPed_trq4A` | `1CFCE4` | `0x801CFCE4` | — | `0x800E2DFC` (D/D_fam_unkX_unkY_1CFCE4) |

## tqlim

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `tqlim_base_pu_4A` | `1D3190` | `0x801D3190` | — | `0x8008736E` (B 0x13C)<br>`0x800DDACE` (C 0x17C)<br>`0x800DDA36` (E 0x19C) |

## smoke

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `smoke_mapA` | `1D1D18` | `0x801D1D18` | — | `0x80074DB2` (2d 0x14C)<br>`0x800F4BA8` (B 0x1E8) RAM `D0001D60`/`D0001D62` |
| `smoke_mapA@1D1FC4` | `1D1FC4` | `0x801D1FC4` | — | `0x800879EC` (2d 0x120) |
| `smoke_mapA@1D2270` | `1D2270` | `0x801D2270` | — | `0x800DDB38` (C 0xBC)<br>`0x801056A4` (D 0x23C)<br>`0x80105626` (D 0x24C)<br>`0x80105DE2` (2d 0x25C) |
| `smoke_mapA@1D251C` | `1D251C` | `0x801D251C` | — | `0x80093D34` (K 0x138)<br>`0x800974A6` (G 0x1D8)<br>`0x8009904A` (H 0x1EA)<br>`0x80098FFC` (H 0x210) |
| `smoke_mapA@1D27C8` | `1D27C8` | `0x801D27C8` | — | `0x80081ECA` (I 0x64)<br>`0x8008E56C` (2d 0xB4)<br>`0x800F04A4` (2d 0x1A4)<br>`0x800B765C` (2d 0x204)<br>`0x8012E74A` (2d 0x268) |

## turbo

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `turbo_base3B` | `1C04AC` | `0x801C04AC` | — | `0x800E0ECA` (2d 0x268) |
| `turbo_base3B@1C072C` | `1C072C` | `0x801C072C` | — | `0x800F8F0A` (C 0x160)<br>`0x800E4684` (E 0x1AC)<br>`0x80112490` (D 0x214)<br>`0x80112530` (E 0x220)<br>`0x801123BE` (D 0x22C)<br>`0x800F58B8` (D 0x238) |
| `turbo_base3B@1C09AC` | `1C09AC` | `0x801C09AC` | — | `0x800F193C` (D 0x4)<br>`0x8009B086` (L 0x58)<br>`0x800E4110` (2d 0x98)<br>`0x80078AD6` (C 0xD8)<br>`0x80085C3A` (C 0xEC)<br>`0x8009ACB8` (O 0xF8)<br>`0x800A2EE2` (C 0x118)<br>`0x80078AB4` (C 0x124) |
| `turbo_base3B@1C0C2C` | `1C0C2C` | `0x801C0C2C` | — | — |
| `turbo_base3B@1C0EAC` | `1C0EAC` | `0x801C0EAC` | — | — |
| `turbo_base3B@1C112C` | `1C112C` | `0x801C112C` | — | — |
| `turbo_base3B@1C13AC` | `1C13AC` | `0x801C13AC` | — | — |
| `turbo_base3B@1C162C` | `1C162C` | `0x801C162C` | — | `0x800F05A6` (2d 0x254) |
| `turbo_base3B@1C18AC` | `1C18AC` | `0x801C18AC` | — | `0x800E2122` (D 0xA4)<br>`0x800E9084` (D 0xD0)<br>`0x800DF018` (2d 0x13C) |
| `turbo_base3B@1C1B2C` | `1C1B2C` | `0x801C1B2C` | — | `0x800F6186` (2d 0x24) |
| `turbo_base3B@1C1DAC` | `1C1DAC` | `0x801C1DAC` | — | — |
| `turbo_base3B@1C202C` | `1C202C` | `0x801C202C` | — | `0x800F16FE` (F 0x40) |
| `turbo_base3B@1C2A2C` | `1C2A2C` | `0x801C2A2C` | — | — |
| `turbo_base3B@1C2CAC` | `1C2CAC` | `0x801C2CAC` | — | — |
| `turbo_base3B@1C2F2C` | `1C2F2C` | `0x801C2F2C` | — | — |
| `turbo_base3B@1C31AC` | `1C31AC` | `0x801C31AC` | — | — |
| `turbo_base3B@1C342C` | `1C342C` | `0x801C342C` | — | — |
| `turbo_base3B@1C36AC` | `1C36AC` | `0x801C36AC` | — | `0x800CD140` (C 0x100)<br>`0x80096F00` (E 0x110)<br>`0x800BD03A` (B 0x148)<br>`0x800F065E` (F 0x1E4)<br>`0x800FC4FE` (2d 0x23C) |
| `turbo_base3B` | `1C09B0` | `0x801C09B0` | — | `0x800F193C` (D/D_fam_unkX_unkY_1C09B0) |
| `turbo_base3B` | `1C1B50` | `0x801C1B50` | — | `0x800F6186` (2d/fam_unkX_unkY_1C1B50) |
| `turbo_base3B` | `1C206C` | `0x801C206C` | — | `0x800F16FE` (F/F_fam_unkX_unkY_1C206C) |

## rail

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `rail_base_int_trq2B` | `1E9368` | `0x801E9368` | — | — |
| `rail_base_int_trq2B@1E9768` | `1E9768` | `0x801E9768` | — | `0x800C1964` (D 0x158) |
| `rail_base_int_trq2B@1E9968` | `1E9968` | `0x801E9968` | — | — |
| `rail_base_int_trq2B@1E9B68` | `1E9B68` | `0x801E9B68` | — | `0x800B5A96` (B 0x60) |
| `rail_base_int_trq2B@1E9D68` | `1E9D68` | `0x801E9D68` | — | `0x800F5114` (2d 0x78) |
| `rail_base_int_trq2B@1E9F68` | `1E9F68` | `0x801E9F68` | — | — |
| `rail_request_horsA2L_banque_01` | `1EA168` | `0x801EA168` | — | — |
| `rail_request_horsA2L_banque_02` | `1EA368` | `0x801EA368` | — | — |
| `rail_request_horsA2L_banque_03` | `1EA568` | `0x801EA568` | — | — |
| `rail_request_horsA2L_banque_04` | `1EA768` | `0x801EA768` | — | — |
| `rail_request_horsA2L_banque_05` | `1EA968` | `0x801EA968` | — | — |
| `rail_request_horsA2L_banque_06` | `1EAB68` | `0x801EAB68` | — | `0x80087D28` (F 0x194) |
| `rail_request_horsA2L_banque_07` | `1EAD68` | `0x801EAD68` | — | `0x800C4AAC` (C 0x48)<br>`0x800C4ACA` (C 0x54)<br>`0x800F50E2` (2d 0x80) |
| `rail_request_horsA2L_banque_08` | `1EAF68` | `0x801EAF68` | — | — |
| `rail_request_horsA2L_banque_09` | `1EB168` | `0x801EB168` | — | — |
| `rail_request_horsA2L_banque_10` | `1EB368` | `0x801EB368` | — | — |
| `rail_request_horsA2L_banque_11` | `1EB568` | `0x801EB568` | — | — |
| `rail_request_horsA2L_banque_12` | `1EB768` | `0x801EB768` | — | `0x800972C2` (F 0xD8)<br>`0x8009735E` (F 0x110)<br>`0x800B5DB4` (C 0x1BC)<br>`0x800B5E60` (C 0x1CC) |
| `rail_request_horsA2L_banque_13` | `1EB968` | `0x801EB968` | — | — |
| `rail_request_horsA2L_banque_14` | `1EBB68` | `0x801EBB68` | — | `0x800B5A66` (2d 0x60)<br>`0x80104034` (E 0xE4)<br>`0x80104930` (N 0x104)<br>`0x80103D8C` (N 0x110) |
| `rail_lim_horsA2L_A` | `1EBDD8` | `0x801EBDD8` | — | `0x80090758` (C 0x18) |
| `rail_lim_horsA2L_B` | `1EBE58` | `0x801EBE58` | — | — |

## duration

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `duration_inj6A` | `1CDC84` | `0x801CDC84` | — | `0x80074EBE` (2d 0x180)<br>`0x800959B6` (C 0x1C0)<br>`0x8008B652` (C 0x1CC)<br>`0x8007E3D0` (F 0x1D8)<br>`0x800D6784` (B 0x208)<br>`0x800F8D96` (I 0x2DC) |
| `duration_inj6A@1CDFE4` | `1CDFE4` | `0x801CDFE4` | — | `0x80087B26` (B 0x2B8)<br>`0x800954AA` (B 0x2E8)<br>`0x800FD86C` (2d 0x32C) |

## speed_limiter

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `vmax3` | `18047C` | `0x8018047C` | — | — (scalaire 2o ; pas de lea/CALL dans le code ; lecture indirecte) |
| `vmax3@18047E` | `18047E` | `0x8018047E` | — | — |
| `vmax2` | `18048A` | `0x8018048A` | — | — |
| `vmax2@18048C` | `18048C` | `0x8018048C` | — | — |
| `vmax3@18049E` | `18049E` | `0x8018049E` | — | — |
| `vmax3@1804A0` | `1804A0` | `0x801804A0` | — | — |
| `vmax3@1804A2` | `1804A2` | `0x801804A2` | — | — |

## egr_control

| Map | WinOLS | Ghidra | Ptrs code | Call-sites interp |
|---|---|---|---|---|
| `airctl_hysteresisC@1D0120` | `1D0120` | `0x801D0120` | — | — |
| `airctl_hysteresisC@1D0180` | `1D0180` | `0x801D0180` | — | — |

