# map-finder — PCR2.1 multi-soft map discovery

But : retrouver les maps (Stage 1, DPF/EGR+DTC, limiteur, launch, hardcut…)
sur **n’importe quel soft PCR 2.1**, en partant de la maîtrise soft **9979**.

## Phase 1 (fait)

1. `packs.json` — rôles / packs applicatifs  
2. `export_atlas_9979.py` — atlas machine-readable depuis MAP_GRIDS + A2L + ORI  
3. `atlas/9979.json` — gold standard (adresses, dims, fingerprints ORI)  
4. `scan_bin.py` — scan d’un dump vs fingerprints 9979

## Usage

```bash
# Régénérer l’atlas (si MAP_GRIDS / ORI changent)
python map-finder/export_atlas_9979.py

# Self-test (doit ~100% exact) — atlas choisi auto (SM2G0P / SM2G0M)
python map-finder/scan_bin.py "…/Caddy_CAYE_…_9979_ORI….bin"
python map-finder/scan_phase2.py path/to/ORI.bin

# Forcer un atlas
python map-finder/scan_bin.py path/to/ORI.bin --atlas atlas/6929.json

# Autre soft / dump
python map-finder/scan_bin.py path/to/autre_ORI.bin --show-miss
python map-finder/scan_bin.py path/to/autre_ORI.bin --pack stage1
python map-finder/scan_bin.py path/to/autre_ORI.bin --role clutch_prot
```

## Lecture des statuts

| Status | Sens |
|---|---|
| `exact_same_addr` | Même soft (ou copie) — map à la même adresse |
| `exact_relocated` | Payload ORI 9979 trouvé ailleurs (offset shift) |
| `context_only` | Bordures identiques, valeurs différentes → **slot trouvé**, soft différent |
| `offset_predict` | Phase 2 — slot prédit via cluster d’offset + validation physique |
| `miss` | Pas trouvé |

## Atlas famille SM2G0M (6929)

```bash
cd map-finder
python export_atlas_family.py --ori "…CADDY_FRERE_PA_6929_ORI.bin" --report reports/caddy-frere-6929-phase2.json --soft 6929
python scan_bin.py path/to/ORI.bin
python scan_phase2.py path/to/ORI.bin
# --atlas seulement pour forcer
```

## Phase 2

```bash
cd map-finder
python scan_phase2.py path/to/ORI.bin --json reports/out.json
python scan_phase2.py path/to/ORI.bin --pack stage1
```

Clusters d’offset séparés **cal** / **dtc** / **speed**, puis prédiction `addr + delta` + check Nm/mbar/…

## Ghidra (code PCR 2.1)

Installé hors dépôt : `C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC`  
Projet : `C:\Users\theda\Tools\ghidra-projects\PCR21`  
Détail : `map-finder/ghidra/README.md`

```bat
map-finder\ghidra\open_ghidra.bat
```

## Suite

- Affiner les misses restants (signatures smoke/turbo plus strictes)
- Templates de packs soft par soft
