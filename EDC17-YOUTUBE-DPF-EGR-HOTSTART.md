# YouTube — EDC17CP14 DPF / EGR / Hot Start / Idle RPM FIX

## 🎬 Source

| | |
|---|---|
| **URL** | https://youtu.be/dKaJ-WJMwcc |
| **Titre** | EDC17CP14 DPF - EGR - Hot Start - Idle RPM FIX |
| **Auteur** | Dragiša Trimunović |
| **Tags** | WinOLS · DaVinci · KESS · K-TAG · KT200 · Stage1 · AdBlue/SCR · Autel |
| **Vignette** | `fiche-assets/edc17-youtube-dKaJ-WJMwcc.jpg` |

## 📐 Contenu (vignette WinOLS)

Projet démo : **Audi A6 (DPF EGR)**, soft **505999** (≠ A5 Bertin **516657** — même famille EDC17CP14, **offsets différents**).

### Switches / maps visibles

| Adresse (A6 505999) | Nom / rôle | Action typique |
|---|---|---|
| `1EE34A` | Schalter erweiterten DPF Überwachungsfunktionen | **0100 → 0000** (off) |
| `1EE34B` | DPF switch activation logiciel filtre | off |
| `1EE34C` | DPF switch désactivation fonctionnalité FAP | selon méthode |
| `1ED84C` / `1EDC86` | Matrices évaluation DPF / regen (11×12) | delete / neutre |
| `1BC35A` / `1BC46C` | EGR hysteresis limits | EGR off |
| `1A1394` | SVTL (1×1) | lié deletes |
| `1F84FA` / `1F85D8` | **Hot start** / Start torque | fix démarrage chaud |
| (+ Idle RPM) | maps ralenti | fix idle |

### Checksum

Barre WinOLS : **`4 CS wrong`** après modif → **checksum obligatoire** avant flash (comme `noCHK` → CHK KESS sur A5).

---

## 🔄 Comparaison A5 Bertin (516657)

| Sujet | Vidéo (A6 505999) | Repo A5 V1.5 |
|--------|-------------------|--------------|
| ECU | EDC17CP14 | **EDC17CP14** ✅ même |
| Soft | 505999 | **516657 / 0008** |
| DPF/EGR | Switches manuels WinOLS (`1EE34x`…) | **Pack DaVinci** DPF+EGR+FLAPS |
| Adresses | `1EE34A` etc. | **Ne pas copier** — soft différent |
| Hot Start | Maps `1F84FA` / `1F85D8` | ❌ **pas dans V1.5** |
| Idle RPM FIX | Mentionné titre | ❌ **pas documenté** |
| Stage1 | Tag #stage1 | V1.5 Stage1 soft + deletes |
| Outils | WinOLS + KESS/KTAG/KT200 | K-TAG 151 BOOT + KESS OBD |
| CS | CS wrong affiché | `*_noCHK` → CHK avant flash |

### Méthode deletes : 2 approches

```
Vidéo : chasse switches 1x1 + matrices DPF/EGR map par map
A5    : appliquer binaire DaVinci entier (diff_davinci_packs.py / build_v1*)
```

**Avantage DaVinci A5 :** DTC liés inclus, moins d’oubli.  
**Avantage vidéo :** montre *où* sont Hot Start / Idle — utile si hard start post-delete (cf. Lesson 21 cranking).

---

## ⚠️ Points critiques pour A5

1. **Ne jamais coller les adresses 505999** sur 516657  
2. Hot Start / Idle = **trou méthodologique** actuel si démarrage chaud mauvais après DPF/EGR off  
3. Lesson 21 : cranking maps souvent à zéro sur EDC17 → « inject values » pour hard start — **aligné** avec ce tutoriel  
4. Toujours **checksum** après switches (écran CS wrong = même piège)

---

## ✅ Actions repo recommandées

- [x] Documenter la vidéo + comparer DaVinci  
- [ ] Chercher dans A5 ORI / A2L similar 0005 : équivalents Hot start / Idle / DPF Schalter  
- [ ] Si Bertin hard start après flash → short dédié + patch V1.6  
- [ ] Ne pas remplacer DaVinci par switches manuels sans diff DTC  

## 🔗 Liens repo

- `diff_davinci_packs.py` · `DTC_OFF_packs.md`  
- `build_v1.py` / `build_v11.py` (couche DaVinci)  
- Lesson 21 cranking : `EDC17-LESSON21-TUNING-GUIDE.md` §3 / §8  
- Short : `shorts/18-youtube-dpf-egr-hotstart.md`

---

**Dernière maj :** 27 oct 2026 12:50 UTC-3
