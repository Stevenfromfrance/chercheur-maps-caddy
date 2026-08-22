# A2L reverse PCR2.1 Golf 9980

Fichier : `PCR21_Golf9980_REVERSE.a2l`  
Copie : `C:\Users\theda\ghidra_scripts\PCR21_Golf9980_REVERSE.a2l`

**Ce n’est pas un A2L Continental / Siemens OEM.** Premier brouillon reverse (SW 9980, HW 03L997558A, projet SM2G0P). Incomplet. Ne pas flasher à partir de ce fichier.

## WinOLS démo vs licence complète

| Fonction | Démo Testversion | Licence + plugin |
|----------|------------------|------------------|
| Ouvrir un `.bin` / hexdump | oui | oui |
| **Import A2L / DAMOS** | **non** (plugin **OLS521** requis, ~785 € en plus) | oui |
| **Import map pack** `.kp` / `.json` / `.csv` | **oui** | oui |
| Sauvegarder / exporter tune | limité | oui |

L’import **A2L** (`Project → Damos & A2L Import`) n’est **pas** dans WinOLS de base : EVC le vend comme option **OLS521**. La démo ne l’a pas — d’où l’échec même si le `.a2l` est syntaxiquement correct.

**Contournement démo :** `Project → Import map pack` avec un fichier **`.json`** (ou `.kp`) exporté depuis un projet WinOLS complet. Tu as déjà un pack 9979 :

`Documents\Reprog-Stage1\…\OUTILS-WINOLS\Caddy-9979-Stage1-MAPPACK-WinOLS.json`

Sur le Golf 9980, ~82 % des maps atlas 9979 sont au **même offset** (`map-finder/reports/golf-9980.json`).

## Ouvrir dans WinOLS (licence + OLS521)

1. Ouvre le binaire Golf 9980 en **2 Mo** (full flash), pas un extrait cal seul si tes offsets sont en 0x1Cxxxx.
2. **Project → Damos & A2L Import** (pas « map pack »).
3. Choisis `map-finder/a2l/PCR21_Golf9980_REVERSE.a2l`. Offset : **0**.
4. Vérifie `AccPed_trq4A` @ `1CF9C0`, `turbo_base3B` @ `1C04AC`.

## Import map pack JSON (démo OK)

1. **File → Open** → `Golf6_03L997558A_9980_FULLFLASH.bin`
2. **Project → Import map pack** (Shift+Alt+I)
3. Fichier : `Caddy-9979-Stage1-MAPPACK-WinOLS.json`
4. Offset : **0** (puis « Automatic » si proposé)
5. Contrôle `AccPed_trq4A`, `tqlim_base_pu_4A`, etc. Les maps **hors atlas** (Ghidra) ne seront pas dans ce JSON.

Sans WinOLS du tout : Ghidra + `python map-finder/scan_bin.py` sur le bin Golf.

## Adresses Ghidra vs WinOLS

`WinOLS = Ghidra 80xxxxxx ou A0xxxxxx & 0x1FFFFF`  
Exemple : Ghidra `0xA01CBE40` → WinOLS `0x1CBE40`.

## Limites

- Tailles de grilles souvent inconnues : pas inventées (sauf AccPed-like **8×16** pour `fam_0001`).
- `AXIS_PTS` : adresse + compteur u16 lu 2 ou 4 octets avant l’axe si 2…64 ; **valeurs d’axe non dumpées**.
- Atlas 9979 inclus pour les IdNames (`AccPed_trq4A`, `turbo_base3B`, …) : même offset ≠ même contenu.
- Régénérer : `python map-finder/a2l/gen_golf9980_reverse_a2l.py`
- Sources familles : tous les `golf9980_interp*_families.csv` présents (`interp_2d` + `B` + `C`..`O`)

## Syntaxe WinOLS (MSG1003)

Le générateur produit du **stub ASCII** compatible WinOLS (comme `golf9980_interp_families_HIGH.a2l`) :

- `ASAP2_VERSION 1 60`, `RL_IDENTITY`, `NO_INPUT_QUANTITY`
- Pas de `FIX_AXIS_PAR`, `RL_AXIS`, `MEASUREMENT` RAM, ni UTF-8 (tirets `—`)
- Maps sans axes 9980 résolus → `VALUE` stub (plus de fausses grilles `FIX_AXIS`)

Si l’import échoue encore : fermer le `.a2l` dans WinOLS, régénérer, réimporter dans le **projet Golf 9980 .bin** (pas le Caddy FE1Q2VC).
