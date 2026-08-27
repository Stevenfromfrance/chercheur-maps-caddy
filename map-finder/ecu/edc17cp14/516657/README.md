# Audi A5 Sportback CGKA · EDC17CP14 · SW 516657 / 0008

Client Bertin. ORI lu en boot K-TAG plugin 151 (MICRO + EEPROM).

- `ORI_FLS.fls` — flash interne 2 Mo (fichier carto)
- `BACKUP_MICRO.mpc` — IROM TC1796 (restore)
- `BACKUP_EEPROM.epr` — EEPROM 128 ko (ne pas patcher pour un Stage 1)
- `identity.json` — IDs + offsets

Pack visé : Stage 1 conservateur, DPF off, EGR off, DTC liés. Hardcut = V2. Pas de launch (boîte 0AW).

**Pas de flash** sans maps identifiées (A2L 0008 exact ou similar 0005 recalé) et sans trier G83 / EGT S3 / FAP.

## V1.1 livrée (à flasher)

`A5_516657_V1.1_S1named_DPF_EGR_noCHK.fls` — Stage 1 **named** (mappack ami) + DPF/EGR/FLAPS DaVinci.
Couple +8 %, IQ +7 %, turbo +6 %, rail +5 %. Pas de cases vides, pas SOI/durée/VGT, pas smoke.
Détail : `LIVRAISON-V1.1.txt`. Checksum avant flash. Pas de TVA / lambda.

V1 aveugle (+12 % cal) reste en archive : `A5_516657_V1_S1cons_DPF_EGR_noCHK.fls`.

## DAMOS (Damos-Big-Archive, 93 Go — scan 57k fichiers)

Pas d’A2L **0008 / 516657 / B3UX**. Plus proche déjà copié : `damos-similar-0005/`
(`8K1907401K` ver **0005**, Bosch **504886**, **B3UN**, projet A2L `P714` / `C714B3UN`).

- WinOLS : ouvrir **notre** `ORI_FLS.fls` → importer l’A2L 0005 en **similar** (noms oui, offsets 0005→0008 non)
- Réf Stage 2 **même SW** : `ref-a4-516657-stage2/` (A4 2.7, 8499 octets vs ori — localiser les maps, ne pas flasher)
- Ignorer : CGKB 163 ch `.ols`, CP04 `8K1907401D/F`, versions 0001–0004, Tiguan 2.0 CP14 A2L
Page site : [`a5-cgka-edc17cp14.html`](../../../a5-cgka-edc17cp14.html)
