# SAVAGESEAR · Chercheur maps ORI / ACE Tuning / V2 / V3 ITALIE

Outil atelier multi-calculateur (sélecteur en haut de page) :

| Calculateur | Soft | Mode |
|---|---|---|
| Siemens PCR 2.1 | 9979 Caddy | Atelier ORI / ACE / V2 / V3 ITALIE + VCDS |
| Bosch MEVD 17.2.5 | 531049 BMW 1 Series | Catalogue maps (import WinOLS `.kp`) |
| Bosch EDC17CP14 | 516657 A5 Sportback CGKA | Client Bertin — V1 Stage1 conservateur + DPF/EGR/FLAPS |

## PCR 2.1 (Caddy)

- **ORI vs ACE** — Stage 1 ACE Tuning
- **ORI vs V2** — ta carto (partiels soft, WOT 350)
- **ACE vs V2** — écart de ta V2 sur la base ACE
- **V2 vs V3 ITALIE** — carto du pote (hardcut `tqlim_cluth_prot` 4800 + launch 2500) — meilleure actuelle

Page **Valeurs** (`#valeurs`) : lecture type logiciel — une carto à la fois, maps modifiées à gauche, grille en gros à droite (jaune = case ≠ ORI).

## MEVD 17.2.5 (BMW)

Fichiers : `map-finder/ecu/mevd1725/531049/` · registre `data/ecus.json` · `python tools/parse_winols_kp.py`

Site : https://stevenfromfrance.github.io/chercheur-maps-caddy/

RE Golf 9980 — validation Stage1 / Top AccPed : [`stage1-hubs-golf9980.html`](https://stevenfromfrance.github.io/chercheur-maps-caddy/stage1-hubs-golf9980.html)

Client A5 Sportback CGKA EDC17CP14 : [`a5-cgka-edc17cp14.html`](https://stevenfromfrance.github.io/chercheur-maps-caddy/a5-cgka-edc17cp14.html)

Banque PCR2.1 (25 softs) : [`pcr21-banque.html`](https://stevenfromfrance.github.io/chercheur-maps-caddy/pcr21-banque.html)
