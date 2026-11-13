# OBDLink → macOS : cartographie communication Bluetooth

Référence atelier pour reproduire (légalement) la couche **dongle ↔ app**, sans décompiler l’IPA OBDLink.

Sources publiques utilisées :
- [OBDLink Family Reference and Programming Manual (FRPM)](https://www.obdsol.com) — chip STN, commandes AT/ST
- [OBDLink CX Adapter Notes (dev)](https://support.obdlink.com/support/solutions/articles/43000746707-obdlink-cx-adapter-notes) — BLE GATT officiel
- Docs app OBDLink (features, réseaux, logging)

---

## 1. Verdict important

| Couche | Propriétaire ? | Ce qu’on peut faire sur macOS |
|---|---|---|
| Transport Bluetooth (BLE UART / SPP) | **Non** — documenté | CoreBluetooth (CX) ou IOBluetooth RFCOMM (MX+/LX) |
| Langage dongle (AT / ST / hex OBD) | **Non** — FRPM STN | Session ASCII `\r`, prompt `>` |
| SAE Mode 01–09 (RPM, DTC, VIN…) | **Non** — norme OBD-II | Requêtes `010C`, `03`, `0902`… |
| OEM Enhanced (ABS, SRS, MS-CAN Ford…) | **Oui côté app** (bases PID + UDS) | Possible via bus brut (`STPX`, headers) **si** on connaît les requêtes constructeur |
| UI dashboards / trip / maps | App OBDLink | À reconstruire |

L’app iPhone ne parle **pas** un protocole secret au dongle : elle ouvre un **pipe série ASCII** vers le STN, puis envoie les mêmes commandes qu’un terminal ELM327/STN.

---

## 2. Quel dongle as-tu ?

Sur iPhone, seuls **CX** (BLE) et **MX+** (Bluetooth Classic MFi) sont supportés.

| Adapter | Radio | macOS API | MS-CAN / SW-CAN | Notes |
|---|---|---|---|---|
| **CX** | BLE 5.1 only | `CoreBluetooth` | Non (HS-CAN + ISO/KWP) | Optimisé BMW / CAN moderne. Bonding 5 min après power-on |
| **MX+** | BT Classic 3.0 (+ MFi iOS) | `IOBluetooth` RFCOMM/SPP | Oui (Ford MS-CAN, GM SW-CAN) | Sur iOS = ExternalAccessory ; sur Mac = SPP classique |
| **LX** | BT Classic | RFCOMM | Non | Pas iOS |
| **EX** | USB | `IOKit` serial / CDC | MS-CAN | Hors Bluetooth |

**Pour l’atelier VAG (Caddy / A5 / Golf)** : un **CX** ou **MX+** suffit pour OBD-II législatif (HS-CAN). Les modules OEM hors OBD (ABS, boîte…) demandent du UDS constructeur — MX+ aide surtout Ford/GM via MS/SW-CAN, pas magiquement VAG.

---

## 3. Stack de communication (ce que fait l’app)

```
┌─────────────────┐     BLE GATT UART          ┌──────────────┐     OBD bus      ┌──────┐
│  App (iOS/Mac)  │◄──── FFF2 write / FFF1 ────►│  STN chip    │◄──── CAN/KWP ───►│ ECU  │
│  CoreBluetooth  │      notify (CX)           │  OBDLink     │                  └──────┘
└─────────────────┘                            └──────────────┘
        │                                              ▲
        │  ou RFCOMM SPP (MX+)                         │
        └──────── ASCII AT/ST/OBD ─────────────────────┘
```

### 3.1 BLE — OBDLink CX (officiel)

| Rôle | UUID |
|---|---|
| Device Information | `180A` (Manufacturer, Model, FW STN, Soft BT) |
| UART service | `FFF0` |
| Notify (RX dongle → app) | `FFF1` |
| Write / WriteWithoutResponse (TX app → dongle) | `FFF2` |
| Interne (ne pas toucher) | `FEF5` |

Règles critiques CX :
1. Scan BLE → connect → discover services
2. **Subscribe FFF1** (ou write FFF2) déclenche le pairing iOS/macOS
3. Bonding accepté seulement **pendant ~5 min après power-on** → sinon power-cycle
4. PIN legacy éventuel : `123456`
5. MTU max dongle **247** ; chunker les écritures à `maximumWriteValueLength`
6. Pas de QueuedWrites
7. Service `FEF5` = usage interne fabricant

### 3.2 Bluetooth Classic — MX+ / LX

- Profil **SPP / RFCOMM** : flux d’octets série
- Sur **iOS** : MFi + `ExternalAccessory` (protocol string propriétaire Apple/OBDLink)
- Sur **macOS** : connexion RFCOMM directe (pas besoin MFi) — bien plus simple pour notre app Mac
- Baud effectif géré par le modem BT du dongle (non configurable comme un USB)

### 3.3 Framing série (commun à tous)

- Charset : ASCII
- Fin de commande : **`CR` (`0x0D`)** — spaces ignorés
- Réponse : lignes `CR` (option `ATL1` → `CR+LF`)
- Prêt pour la suite : caractère **`>`**
- **Toujours attendre `>` avant la commande suivante**
- Un seul `CR` seul = répéter la dernière commande
- Au boot : banner type `ELM327 v1.4b` puis `>`

Trois familles de messages :
1. **AT…** — compat ELM327 (config / reset)
2. **ST…** — extensions STN (préférées, plus puissantes)
3. **hex OBD** — `010C`, `03`, `0902`… transmis sur le bus véhicule

---

## 4. Séquence d’init typique (comme l’app)

```text
ATZ          → reset (banner + >)
ATE0         → echo off
ATL0         → pas de LF
ATS0         → pas d’espaces
ATH1         → headers ON (recommandé)
ATSP0        → auto protocol (legacy)  — mieux: laisser auto ou STP 0 / détection
0100         → PIDs supportés 01-20 (ouvre aussi le protocole)
ATI / STI    → identité
STDI / STSN  → hardware / serial
STVR         → tension batterie
0902         → VIN
```

Variante STN plus propre :

```text
ATZ
ATE0
ATL0
ATS0
ATH1
ATCAF1
STPTO 300
0100
STPR
STPRS
STVR
```

Pour forcer ISO 15765 11-bit 500k (voitures récentes) :

```text
STP 33
STPO
```

---

## 5. Ce que l’app OBDLink fait côté fonctionnalités

Cartographie produit → ce qu’il faut côté Mac pour l’équivaloir.

| Module app | Sous le capot | Priorité atelier |
|---|---|---|
| Connection Wizard | Scan BT + pairing + choix réseau diag | P0 |
| Dashboards / gauges | Poll Mode 01 PIDs (RPM, vitesse, MAP, AFR…) | P0 |
| Diagnostics DTC | Mode 03 / 07 / 0A + clear Mode 04 | P0 |
| Freeze frame | Mode 02 | P1 |
| Monitors / I/M / Mode 06 | Mode 01 readiness + Mode 06 | P1 |
| Vehicle info | Mode 09 (VIN, CALID, CVN) | P0 |
| Logs CSV / binary | Sampling périodique PIDs + GPS téléphone | P1 |
| Graphs live | 1–4 PIDs en boucle | P1 |
| Trips / Maps | GPS host + PID vitesse | P2 |
| Vehicle Editor | Calcul conso / couple (MAF, MAP, VE…) | P2 |
| User-defined PIDs | Formules + headers custom | P1 |
| Manufacturer PIDs | Bases GM/Subaru embarquées | P2 |
| Enhanced OEM add-ons | UDS / bus OEM (ABS, SRS, TCM…) | P3 — IP app |
| Firmware update | Bootloader STN via canal série | P3 |
| MS-CAN / SW-CAN | `STP 5x` / `STP 6x` (MX+ only) | Si Ford/GM |

Réseaux proposés dans le wizard (selon dongle) :
- **Generic OBD2** (HS-CAN / ISO / J1850 selon auto-detect)
- Ford MS-CAN / GM SW-CAN (MX+)
- Autres modules OEM via add-ons payants (sauf MX+ unlimited)

---

## 6. Protocoles STN (`STP p`) utiles

### Législatif / classique

| `p` | Protocole |
|---|---|
| 11 / 12 | J1850 PWM / VPW |
| 22 / 24 / 25 | ISO 9141-2 / KWP 5-baud / KWP fast |
| **33** | **ISO 15765, 11-bit, 500 kbps** ← majorité post-2008 |
| 34 | ISO 15765, 29-bit, 500 kbps |
| 35 / 36 | ISO 15765 250 kbps |

### Bus constructeur (MX+)

| `p` | Bus |
|---|---|
| 51–54 | **MS-CAN** ~125 kbps (Ford pins 3/11) |
| 61–64 | **SW-CAN / GMLAN** ~33.3 kbps (GM pin 1) |

Un seul canal CAN physique actif à la fois (HS / MS / SW).

---

## 7. Commandes essentielles pour notre app Mac

### Identité / santé

| Cmd | Rôle |
|---|---|
| `ATZ` / `ATWS` | Reset froid / warm |
| `ATI` / `STI` / `STIX` | Version ELM / firmware STN |
| `STDI` / `STSN` / `STMFR` | Hardware ID / serial / manufacturer |
| `STVR` | Tension batterie (préférer à `ATRV`) |
| `STRSTNVM` | Factory reset NVM |

### Session OBD

| Cmd | Rôle |
|---|---|
| `ATE0` `ATL0` `ATS0` | Session clean |
| `ATH1` | Headers pour debug multi-ECU |
| `ATCAF1` | Auto PCI CAN |
| `ATAL` | Messages > 7 bytes |
| `STP p` / `STPO` / `STPC` | Set / open / close protocol |
| `STPR` / `STPRS` | Protocol number / string |
| `STPTO ms` | Timeout réponse |
| `STPX …` | Frame arbitraire (UDS / raw) |

### Bluetooth modem (MX+/LX, rare côté app)

| Cmd | Rôle |
|---|---|
| `STBTDN name` | Nom broadcast |
| `STBTCOD hhhhhh` | Class of Device |

### Monitoring / perf

| Cmd | Rôle |
|---|---|
| `ATMA` / ST monitors | Sniffer bus |
| Filters `STFPA` / `STFBA`… | Pass / block filters |
| Periodic `STPPMA` | Messages périodiques |

---

## 8. Requêtes OBD SAE courantes

| Hex | Signification | Formule typique |
|---|---|---|
| `0100` | PIDs supportés 01–20 | bitmap |
| `010C` | RPM | `((A*256)+B)/4` |
| `010D` | Vitesse km/h | `A` |
| `0105` | Eau °C | `A-40` |
| `010B` | MAP kPa | `A` |
| `0110` | MAF g/s | `((A*256)+B)/100` |
| `0111` | Accélérateur % | `A*100/255` |
| `0142` | Tension module | `((A*256)+B)/1000` |
| `03` | DTCs confirmés | parse `43…` |
| `07` | DTCs pending | |
| `04` | Clear DTCs + MIL | ignition ON, moteur OFF |
| `0902` | VIN | multi-frame |
| `0904` | Calibration ID | |

Réponse mode 01 : `41` + PID + data (ex. `410C1AF8` → RPM).

---

## 9. Architecture recommandée app macOS

```
┌──────────────────────────────────────────────┐
│  UI SwiftUI (dashboards, DTC, logs, VIN)     │
├──────────────────────────────────────────────┤
│  ObdSession                                  │
│   - queue commandes (wait for '>')           │
│   - parseur lignes / multi-frame ISO-TP      │
│   - registry PIDs + formules                 │
├───────────────┬──────────────────────────────┤
│ BleTransport  │  RfcommTransport             │
│ CoreBluetooth │  IOBluetooth RFCOMM          │
│ CX FFF0/1/2   │  MX+ / LX                    │
└───────────────┴──────────────────────────────┘
```

Règles d’implémentation :
1. **Une seule commande in-flight** jusqu’au `>`
2. Buffer RX thread-safe ; assembler jusqu’à `>`
3. Timeout configurable (`STPTO` + timeout app)
4. Chunk BLE ≤ MTU − overhead
5. Sur CX : mode « first pair » avec fenêtre humaine > 5 s, power-cycle si > 5 min
6. Ne jamais paralleliser deux apps sur le même dongle
7. Clear codes uniquement contact ON / moteur OFF

Pseudo-flux Swift (CX) :

```swift
// 1. scan namePrefix "OBDLink" / "CX"
// 2. connect + discover FFF0
// 3. setNotifyValue(true) on FFF1  // déclenche pairing
// 4. write "ATZ\r" on FFF2 (chunked)
// 5. wait buffer contains ">"
// 6. send init sequence then poll PIDs
```

---

## 10. Ce qu’on ne récupère PAS en « reverse » de l’app iPhone

Sans IPA + REA local (et hors périmètre ici) :

- Bases **Enhanced OEM** (requêtes UDS ABS/SRS VAG, etc.)
- Mapping commercial add-ons Ford/Toyota/Nissan…
- Logique exacte UI / calculs trip propriétaires
- Protocol string MFi iOS (inutile sur Mac pour SPP)

Pour VAG atelier (notre cas maps) : commencer par **OBD législatif + UDS générique** (`22`/`2E` si on a les DIDs), pas par reverse de l’IPA.

---

## 11. Plan produit macOS (phases)

### Phase A — Pipe + session (1 livrable)
- Connect CX (BLE) et/ou MX+ (RFCOMM)
- Init STN, VIN, tension, RPM, vitesse
- Affichage live + log CSV

### Phase B — Diagnostic
- DTC read/clear, freeze frame, readiness, Mode 09

### Phase C — Atelier SavageSear
- PIDs custom (rail, boost, IQ…) via headers / `STPX`
- Export CSV compatible nos viewers `logs-v5*`
- Profils véhicule liés aux cartos (Caddy PCR2.1, A5 EDC17…)

### Phase D — OEM (optionnel)
- Catalogue UDS VAG maintenu par nous (pas copié OBDLink)

---

## 12. Checklist capture sur ton iPhone (si tu veux valider)

Sans reverse d’IPA, tu peux confirmer le modèle :

1. Réglages Bluetooth → nom exact (`OBDLink CX …` / `OBDLink MX+ …`)
2. Dans l’app : Settings → adapter model / firmware
3. Brancher, noter si Pair button (MX+/LX) ou bonding BLE (CX)
4. Envoyer-nous : **modèle + FW STN** → on fige le transport Mac

Option avancée chez toi (pas dans ce cloud) : Packet Logger / `nRF Connect` pendant une session CX pour vérifier FFF1/FFF2 — doit coller à la doc officielle ci-dessus.

---

## Références

- FRPM STN / OBDLink — commandes AT & ST
- https://support.obdlink.com/support/solutions/articles/43000746707-obdlink-cx-adapter-notes
- https://www.obdlink.com/obd-apps/obdlink-app/
- https://support.obdlink.com/support/solutions/articles/43000713351-which-obdlink-adapter-is-right-for-me-
