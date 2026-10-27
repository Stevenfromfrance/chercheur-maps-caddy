# EDC17CP14 — Shorts Méthodologie

Guides courts (15–60 sec) pour EDC17 — issus des Reels Facebook + **Lesson 21**.

## ⚠️ Prérequis

1. Lire `01` → `03` (factors WinOLS) **avant** toute map  
2. Lesson 21 complète : `../../../../../EDC17-LESSON21-TUNING-GUIDE.md`

## 📋 Index (17 shorts)

### A. Conversions WinOLS (#1–#4)
| # | Fichier | Sujet |
|---|---|---|
| 1 | [01-rpm-factor-x2.md](01-rpm-factor-x2.md) | RPM ×2 → factor **0.5** |
| 2 | [02-pedal-axis-8192.md](02-pedal-axis-8192.md) | 8192 = **100 %** pédale |
| 3 | [03-torque-factor-01.md](03-torque-factor-01.md) | Couple factor **0.1** |
| 4 | [04-raw-storage-before-conversion.md](04-raw-storage-before-conversion.md) | Vue RAW synthèse |

### B. Driver's Wish (#5–#7)
| # | Fichier | Sujet |
|---|---|---|
| 5 | [05-drivers-wish-rpm-pedal.md](05-drivers-wish-rpm-pedal.md) | Lecture 2D ; full dès 70 % |
| 6 | [06-pedal-sweep-2000rpm.md](06-pedal-sweep-2000rpm.md) | Sweep 0→12→40→88→403 |
| 7 | [07-first-map-drivers-wish.md](07-first-map-drivers-wish.md) | First map du système |

### C. Hexdump basics (#8–#10)
| # | Fichier | Sujet |
|---|---|---|
| 8 | [08-addresses-always-hex.md](08-addresses-always-hex.md) | Adresses = hex |
| 9 | [09-why-rows-end-in-f.md](09-why-rows-end-in-f.md) | Lignes `…0`→`…F` |
| 10 | [10-left-column-address.md](10-left-column-address.md) | Colonne gauche |

### D. Lesson 21 playbook (#11–#17)
| # | Fichier | Sujet |
|---|---|---|
| 11 | [11-torque-chain-downstream.md](11-torque-chain-downstream.md) | Wish→Lim→Fuel→Air |
| 12 | [12-gatekeepers-limiters.md](12-gatekeepers-limiters.md) | FAPS/FEGT/GBX/Limp |
| 13 | [13-fuel-duration-advance.md](13-fuel-duration-advance.md) | µs + ° BTDC ; +1–13 % |
| 14 | [14-lambda-1455.md](14-lambda-1455.md) | 14.55:1 ; λ 1.2–1.3 |
| 15 | [15-turbo-vgt-playbook.md](15-turbo-vgt-playbook.md) | VGT 95/5 ; boost +4–8 % |
| 16 | [16-edc16-vs-edc17.md](16-edc16-vs-edc17.md) | Evolution not revolution |
| 17 | [17-safe-increments-playbook.md](17-safe-increments-playbook.md) | Checklist incréments |

### E. YouTube EDC17CP14 (#18)
| # | Fichier | Sujet |
|---|---|---|
| 18 | [18-youtube-dpf-egr-hotstart.md](18-youtube-dpf-egr-hotstart.md) | DPF/EGR/Hot Start/Idle — A6 505999 vs A5 DaVinci |

## 🔄 vs PCR2.1 (Caddy)

| Concept | Caddy | EDC17 shorts |
|---|---|---|
| AccPed / wish | ✅ V5g | #5–#7 |
| wish ≤ tqlim ≤ smoke | ✅ | #11–#12 |
| InjTime soft | ❌ | #13 + A5 V1.5 |
| Factors 0.5 / % / 0.1 | N/A | #1–#3 **critiques** |
| EGR off | ✅ ACE | #17 + DaVinci |

## 📊 Scorecard A5 V1.5 vs Lesson 21

| Playbook | V1.5 | OK ? |
|---|---|:-:|
| InjTime +1–13 % | +1.7 % / cap +3 % | ✅ |
| Turbo +4–8 % | ~+6 % (V1.1) | ✅ |
| EGR = 0 | DaVinci | ✅ |
| Limiters before wish | plafonds ORI | ⚠️ |
| Limp raise 550 | non | ⏳ (0AW prudence) |
| Lambda 1.2–1.3 | nosmoke +5 % | ✅ approx |

## 🔗 Docs racine

- `EDC17-LESSON21-TUNING-GUIDE.md` ← **master Lesson 21**
- `EDC17-RPM-FACTOR-CRITICAL.md` · `EDC17-PEDAL-AXIS-CRITICAL.md` · `EDC17-TORQUE-FACTOR-CRITICAL.md`
- `EDC17-RAW-STORAGE-CRITICAL.md` · `EDC17-WINOLS-HEX-BASICS.md`
- `METHODOLOGIE-EDC17-RECAP.md`

---

**Statut :** **17/17 shorts** créés  
**Dernière maj :** 27 oct 2026
