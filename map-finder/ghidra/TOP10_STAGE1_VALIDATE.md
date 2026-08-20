# Top 10–14 — validation manuelle Stage1 (Golf 9980)

Checklist débutant : ouvrir Ghidra → **Ctrl+G** → coller l’adresse **80…** → regarder la grille / le commentaire plate → **File → Save**.

## Rappels (à lire une fois)

| Outil | Adresse | Exemple |
|-------|---------|---------|
| **WinOLS** | offset flash (6 hex) | `1D0AA8` ou `0x1D0AA8` |
| **Ghidra** | base `0x80` + offset | **`801D0AA8`** (pas `1D0AA8`, pas `A01D0AA8`) |
| Vue PFLASH (`A0…`) | axes / pointeurs TriCore | ne pas utiliser pour Ctrl+G |

- **HIGH** = empreinte unique → début de map probable (OK pour confier un label si le contenu matche).
- **MEDIUM** = pointeur **dans** une map connue (`delta` ≠ 0) → IdName = **zone / famille**, pas forcément le début. **Commentaire seulement** — surtout **ne pas rename AccPed** à la légère.
- Après chaque session : **File → Save**.

Sources : `golf9980_hub_grids_HIGH.txt`, `golf9980_hub_grids_MEDIUM_stage1.csv` / `.txt`, atlas AccPed 9979.

Ordre : **AccPed → tqlim → smoke → turbo HIGH**.

---

## Checklist

| # | Rôle | IdName | WinOLS | Ghidra (80…) | Hub | Conf. | À vérifier dans Ghidra (1 ligne) |
|---|------|--------|--------|--------------|-----|-------|----------------------------------|
| 1 | AccPed (wish pédale→Nm) | `AccPed_trq4A` | `1CFFC0` | `801CFFC0` | 2d | **HIGH** | Ctrl+G → début map AccPed (delta 0) ; grille couple/pédale cohérente ; plate HIGH présente |
| 2 | AccPed | `AccPed_trq4A` | `1CFCE4` | `801CFCE4` | D/F/I/K | **HIGH** | Ctrl+G → autre instance AccPed HIGH ; comparer forme à #1 (mêmes axes ?) |
| 3 | AccPed | `AccPed_trq4A` | `1CFAE4` | `801CFAE4` | F | **HIGH** | Ctrl+G → 3ᵉ AccPed HIGH ; noter si soft ≠ 9979 au même offset |
| 4 | AccPed | `AccPed_trq4A` | `1D0AA8` | `801D0AA8` | B | MEDIUM | Ctrl+G → **dans** map `@1D0A5C+0x4C` ; ne pas rename ; commenter zone seulement |
| 5 | AccPed | `AccPed_trq4A` | `1D0ACC` | `801D0ACC` | N | MEDIUM | Ctrl+G → même famille AccPed `+0x70` ; croiser call-site hub N |
| 6 | tqlim (limiteur couple) | `tqlim_base_pu_4A` | `1D32CC` | `801D32CC` | B | MEDIUM | Ctrl+G → zone limiteur `@1D3190+0x13C` ; valeurs type plafond Nm |
| 7 | tqlim | `tqlim_base_pu_4A` | `1D330C` | `801D330C` | C | MEDIUM | Ctrl+G → autre hub sur même limiteur `+0x17C` ; pas le début |
| 8 | tqlim | `tqlim_base_pu_4A` | `1D332C` | `801D332C` | E | MEDIUM | Ctrl+G → `+0x19C` ; souvent aligné 9979 (même 64 o) |
| 9 | smoke (lim. fumée) | `smoke_mapA` | `1D0F34` | `801D0F34` | C | MEDIUM | Ctrl+G → presque début (`+0x8` sur `@1D0F2C`) ; fumée/IQ plausible |
| 10 | smoke | `smoke_mapA` | `1D0F80` | `801D0F80` | I | MEDIUM | Ctrl+G → même map smoke `+0x54` ; hub I |
| 11 | smoke | `smoke_mapA` | `1D282C` | `801D282C` | I | MEDIUM | Ctrl+G → autre bloc smoke `@1D27C8+0x64` ; uniq_u16 élevé |
| 12 | turbo (consigne) | `turbo_base3B` | `1C09B0` | `801C09B0` | D/G/I | **HIGH** | Ctrl+G → turbo HIGH multi-hub ; grille boost vs RPM/charge |
| 13 | turbo | `turbo_base3B` | `1C1B50` | `801C1B50` | 2d | **HIGH** | Ctrl+G → 2ᵉ turbo HIGH ; comparer à atlas 9979 |
| 14 | turbo | `turbo_base3B` | `1C206C` | `801C206C` | F/K | **HIGH** | Ctrl+G → 3ᵉ turbo HIGH ; utile Stage1 si AccPed/tqlim/smoke OK |

---

## Méthode courte (3 puis le reste)

1. Valider **#1 → #3** (AccPed **HIGH**) : adresses `801CFFC0`, `801CFCE4`, `801CFAE4`.
2. Si OK → enchaîner **#4–#11** (AccPed MEDIUM, tqlim, smoke).
3. Finir avec **#12–#14** (turbo HIGH) si tu bosses le boost.
4. **File → Save** avant de fermer Ghidra.

Page site (GitHub Pages) : [`../../stage1-hubs-golf9980.html`](../../stage1-hubs-golf9980.html) · liste MEDIUM : [`../reports/golf9980-medium-stage1.html`](../reports/golf9980-medium-stage1.html) · JSON : [`../reports/golf9980-medium-stage1.json`](../reports/golf9980-medium-stage1.json).
