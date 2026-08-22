# Ghidra — PCR 2.1 (analyse bin, pas de flash)

## Installé sur cette machine

- JDK 21 : `C:\Program Files\Microsoft\jdk-21*`
- Ghidra 11.4.3 : `C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC`
- Projet : `C:\Users\theda\Tools\ghidra-projects\PCR21`
- TriCore **intégré** (pas de plugin) : `tricore:LE:32:tc176x` (TC1766)

Le dump 2 Mo est chargé à **`0xA0000000`** (PFLASH cached).  
Map WinOLS `1CF9C0` → Ghidra `A01CF9C0`.

## Import ORI 9979 + labels atlas

```bat
cd map-finder\ghidra
python build_labels.py
import_ori_9979.bat
```

Puis lance `C:\Users\theda\Tools\ghidra_11.4.3_PUBLIC\ghidraRun.bat`  
→ ouvrir le projet **PCR21** → le programme importé.

## Dans Ghidra (première session)

1. `G` (Go to) → `tqlim_cluth_prot` ou `A01D0860`
2. Clic droit sur l’adresse → **References** → **Show References to Address**  
   = qui lit la map (le “comment Continental s’en sert”)
3. Auto-analyse plus tard : Analysis → Auto Analyze (long, 2 Mo TriCore)

## Golf 9980 full flash (code + cal)

Bin extrait : `C:\Users\theda\Tools\ghidra-projects\Golf6_03L997558A_9980_FULLFLASH.bin`  
Projet Ghidra : `PCR21_Golf9980`

```bat
map-finder\ghidra\import_golf9980_full.bat
map-finder\ghidra\open_ghidra.bat
```

Ouvre le projet **PCR21_Golf9980** (pas PCR21 cal-only).  
Base = **`0x80000000`** (vecteur reset `80031184`).  
WinOLS `1CF9C0` → Ghidra `801CF9C0` (pas `A01CF9C0`).  
`G` → `tqlim_cluth_prot` (`801D0860`) → References.  
Puis **Analysis → Auto Analyze** pour étendre le désassemblage.

Scripts Golf : `ImportAtlas_Golf9980.py`, `KickGolf9980.py`, `import_golf9980_full.bat`.

- `atlas_9979_labels.csv` — table adresse / nom
- `ImportAtlas_9979.py` — script Ghidra (labels)

## Familles interp (method 4) — one-shot Ghidra

Hubs minés (CSV séparés, un scan ne touche pas les autres) :

| Hub | Addr | Préfixe labels | CSV |
|-----|------|----------------|-----|
| `interp_2d` | `0x8004C7A0` | `fam_` | `golf9980_interp_families.csv` |
| `interp_2d_B` | `0x8004C960` | `B_fam_` | `golf9980_interp_B_families.csv` |
| `map_interp_C` | `0x8004CCA0` | `C_fam_` | `golf9980_interp_C_families.csv` |
| `map_interp_D` | `0x8004CF80` | `D_fam_` | `golf9980_interp_D_families.csv` |
| `map_interp_E`..`O` | (voir `HUBS` dans le scanner) | `E_fam_`..`O_fam_` | `golf9980_interp_E_families.csv`..`O` |

Préfixe **B_** = hub `interp_2d_B` (frère de `interp_2d`), pas un `map_interp_B`.

### 1) Scan Python (hors Ghidra) — déjà fait pour tous les hubs restants

```bat
cd map-finder\ghidra
python scan_interp_families.py --all-remaining
```

Ou hub par hub : `python scan_interp_families.py --hub map_interp_F`

Sorties par hub : `*_families.csv`, `*_families_stats.txt`, `*_HIGH.a2l`  
Copie auto vers `C:\Users\theda\ghidra_scripts\` si le dossier existe.

### 2) Labels Ghidra — UNE seule fois pour TOUS les hubs

1. Ouvre le projet **PCR21_Golf9980**
2. **File → Save**
3. **Window → Script Manager** → **Refresh** → filtre `NameInterpFamilies`
4. Lance **`NameInterpFamilies.py`** une fois  
   → console : une ligne par CSV (`2d`, `B`, `C`, … `O`)
5. Optionnel : **`NameInterpRams.py`**
6. **File → Save**
7. Vérif : `G` → `F_fam_...` / `G_fam_...` / `call_B_fam_...` ; ou hub → References

Ne pas relancer 12 scans séparés dans Ghidra — le script charge tous les CSV présents.

### 3) Régénérer l’A2L reverse (optionnel)

```bat
python map-finder\a2l\gen_golf9980_reverse_a2l.py
```

Ingeste automatiquement tous les CSV familles présents (`interp_2d` + `B` + `C`..`O`).  
Ce n’est **pas** un A2L OEM — ne pas flasher.

### 4) Atlas START fingerprints (clutch / rail / duration / vmax / DTC)

Hubs often land *inside* maps (MEDIUM). Offline pass probes atlas 9979 map
**starts** on the Golf 9980 bin:

```bat
cd map-finder\ghidra
python identify_atlas_starts.py
python build_stage1_validated_pack.py
```

Outputs: `golf9980_atlas_starts_identified.csv`, refreshed
`golf9980_stage1_validated.csv` (hub + atlas starts), A2L subset.

Ghidra one-shot (GUI): **NameHubStage1Validated.py**  
Headless (close Ghidra first if `.lock` present):

```bat
map-finder\ghidra\apply_stage1_validated_headless.bat
```

HIGH examples after this pass: `tqlim_cluth_prot` @ `801D0860`, rail banques,
`duration_inj6A`, `vmax*`, DTC DPF/EGR masks.
