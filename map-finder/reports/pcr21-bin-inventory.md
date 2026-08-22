# PCR 2.1 / Continental SM2* — banque de softs

Généré localement. **25 softs uniques** (9 avant + 16 ajoutés depuis Damos-Big-Archive / MHH).

## Tous les softs

| Soft | Banque | Famille | HW | Engine | Taille | Atlas | Phase2 any/exact |
|------|--------|---------|----|--------|--------|-------|------------------|
| **0874** | new | SM2F0 | 03L906023PH | CAYCJ623 | 2097152 | `atlas/0874.json` | 32.7% / 16.3% |
| **2527** | new | SM2G0LG | 03L906023PH | CAYCJ623 | 2097152 | `atlas/2527.json` | 98.0% / 85.7% |
| **4875** | old | SM2E0 | 03L906023A | CAYBJ623 | 2097152 | `atlas/4875.json` | 73.5% / 73.5% |
| **4881** | new | SM2E0 | 03L906023AN | CAYCJ623 | 2097152 | `atlas/4881.json` | 73.5% / 73.5% |
| **5249** | old | SM2G0M | 03L906023C | CAYCJ623 | 2097152 | `atlas/5249.json` | 98.0% / 18.4% |
| **5687** | new | SM2E0 | 03L906023G | CAYCJ623 | 2097152 | `atlas/5687.json` | 98.0% / 55.1% |
| **5697** | new | SM2E0 | 03L906023AG | CAYCJ623 | 2097152 | `atlas/5697.json` | 100.0% / 75.5% |
| **5862** | new | SM2E0 | 03L906023A | CAYBJ623 | 2097152 | `atlas/5862.json` | 100.0% / 75.5% |
| **5863** | new | SM2E0 | 03L906023B | CAYCJ623 | 2097152 | `atlas/5863.json` | 100.0% / 75.5% |
| **6302** | new | SM2F0 | 03L906023DQ | CAYCJ623 | 2097152 | `atlas/6302.json` | 89.8% / 44.9% |
| **6927** | old | SM2G0M | 03L906023AB | CAYCJ623 | 2097152 | `atlas/6927.json` | 100.0% / 64.3% |
| **6929** | old | SM2G0M | 03L906023PA | CAYEJ623 | 2097152 | `atlas/6929.json` | — |
| **8790** | old | SM2G0M | 03L906023M | CAYCJ623 | 2097152 | `atlas/8790.json` | 100.0% / 68.1% |
| **8799** | new | SM2F0 | 03L906023NF | CAYCJ623 | 2097152 | `atlas/8799.json` | 91.8% / 46.9% |
| **8843** | new | SM2F0 | 03L906023MS | CAYCJ623 | 2097152 | `atlas/8843.json` | 91.8% / 46.9% |
| **8866** | new | SM2F0 | 03L906023MM | CAYCJ623 | 2097152 | `atlas/8866.json` | 91.8% / 46.9% |
| **9970** | new | SM2G0M | 03L906023G | CAYCJ623 | 2097152 | `atlas/9970.json` | 22.4% / 18.4% |
| **9971** | old | SM2G0M | 03L906023LC | CAYBJ623 | 2097152 | `atlas/9971.json` | 85.7% / 18.4% |
| **9972** | old | SM2G0M | 03L906023BL | CAYAJ623 | 2097152 | `atlas/9972.json` | 95.1% / 67.0% |
| **9973** | new | SM2G0M | 03L906023FS | CAYCJ623 | 2097152 | `atlas/9973.json` | 75.5% / 32.7% |
| **9977** | new | SM2G0P | 03L906023N | CAYCJ623 | 2097152 | `atlas/9977.json` | 100.0% / 34.7% |
| **9978** | new | SM2G0P | 03L906023AR | CAYCJ623 | 2097152 | `atlas/9978.json` | 100.0% / 38.8% |
| **9979** | old | SM2G0P | 03L906023TB |  | 2097152 | `atlas/9979.json` | 100.0% / 83.7% |
| **9980** | old | SM2G0M |  | CAYCJ623 | 2097152 | `atlas/9980.json` | 100.0% / 83.7% |
| **9983** | new | SM2G0P | 03L906023A | CAYCJ623 | 2097152 | `atlas/9983.json` | 100.0% / 22.4% |

## Softs ajoutés cette passe

`0874`, `2527`, `4881`, `5687`, `5697`, `5862`, `5863`, `6302`, `8799`, `8843`, `8866`, `9970`, `9973`, `9977`, `9978`, `9983`

Bins dans `map-finder/bins/{soft}-{hw}-{fam}.bin`. Plusieurs dumps archive sont **TUN** (EGR/DPF/Stage1) : utiles pour les adresses, pas comme ORI à flasher.

### Notes

- `4875` a maintenant un cal **2 Mo** (`4875-03L906023A-SM2E0DB-2MB.bin`) en plus du dump 1 Mo.
- `0874` : stamp ECU `0874---` sur Touran 03L906023PH Exclusive (Stage1). Inhabituel, conservé.
- `2527` : seule famille `SM2G0LG` (Touran PH).
- `9977` : déjà dans `bins/` MHH, atlas créé maintenant.
- Ibiza Stage1 `SM2G0P3` / 03L906023LC est aussi stamp **9980** — non ingéré pour ne pas écraser l’atlas Golf 9980.
