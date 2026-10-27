# ⚠️ EDC17 WINOLS HEX BASICS — CRITIQUES #8 #9 #10

## 🎯 Sources Facebook

| # | Titre | Lien |
|---|---|---|
| 8 | **Addresses are always hex** | https://www.facebook.com/share/r/18K1JbYWVZ/ |
| 9 | **Why rows end in F** | https://www.facebook.com/share/r/19Vgvf6DAm/ |
| 10 | **Left column = the address** | https://www.facebook.com/share/r/1DwbGyC3tT/ |

Fichier démo images : **BMW EDC17 (Original), 390655** — Hexdump Default  
Images : `fiche-assets/edc17-short-08/09/10-facebook.jpg`

---

## 🔴 Critique #8 — THE ONE RULE TO REMEMBER

> **Addresses are always hex • WinOLS basics**

### Règle

Dans WinOLS / dumps ECU, **toutes les adresses sont en hexadécimal** (base 16).

| Décimal | Hex | Affiché WinOLS |
|---:|---|---|
| 0 | 0x0 | `000000` |
| 16 | 0x10 | `000010` |
| 256 | 0x100 | `000100` |
| 1909014 | 0x1D1496 | `1D1496` (Injection Time A5) |

### Erreurs courantes

```
❌ Traiter 1D1496 comme décimal
❌ Additionner adresses en base 10
✅ Toujours calculer en hex (ou convertir explicitement)
```

### vs PCR2.1 repo

Le repo Caddy utilise déjà des adresses hex (`0x1CF9C0`, `0x1D3190`…).  
**Même règle** — ce short formalise la base pour EDC17 débutants.

---

## 🔴 Critique #9 — WHY ROWS END IN F

> **Addresses start from zero • WinOLS basics**

### Pourquoi chaque ligne se termine en F ?

Hexdump WinOLS = **16 octets par ligne** (0→F) :

```
Adresse début ligne : …0
Octets colonnes     : 0 1 2 3 4 5 6 7 8 9 A B C D E F
Adresse dernier     : …F
Ligne suivante      : …0 (+0x10)
```

Exemple :
```
000000 : octets @ 000000 … 00000F
000010 : octets @ 000010 … 00001F
000020 : octets @ 000020 … 00002F
```

### Pourquoi « start from zero » ?

Indexation **0-based** : première colonne = offset **0**, pas 1.  
Donc 16 colonnes = offsets **0 à 15** = **0 à F** en hex.

### Astuce pratique

| Tu vois | Ça veut dire |
|---|---|
| Adresse `…0` | début de ligne 16 octets |
| Adresse `…F` | dernier octet de la ligne |
| Saut `+10` hex | ligne suivante |

---

## 🔴 Critique #10 — LEFT COLUMN = THE ADDRESS

> **LEFT COLUMN the address · LOCATED HERE**

### Layout Hexdump WinOLS

```
┌──────────┬──────────────────────────────┬─────────┐
│ ADRESSES │  16 octets hex (données)     │ Preview │
│ (gauche) │  centre                      │ (droite)│
└──────────┴──────────────────────────────┴─────────┘
     ↑
  C'EST ICI
```

1. **Colonne gauche** = adresse mémoire (hex)
2. **Grille centrale** = contenu (bytes)
3. **Colonne droite** = aperçu graphique / ASCII

Highlight short : premières adresses `000000`–`000030` encadrées.

### Workflow

1. Chercher une map → noter **adresse hex** (colonne gauche)
2. Aller à cette adresse (Go to / Ctrl+G)
3. Marquer map 2D/3D à partir de là
4. Appliquer factors (#1–#3) ensuite

---

## 🔗 Enchaînement Pédagogique

Ces 3 shorts = **socle hexdump** avant les maps :

```
#10 Où est l'adresse ? (colonne gauche)
#8  L'adresse est toujours en hex
#9  Pourquoi les lignes finissent en F (16 bytes, 0→F)
        ↓
#4  Vue raw map
#1–#3 Conversions
#7  First map = Driver's wish
#5–#6 Lecture AccPed
```

## 🔄 vs Méthodologie Existante Repo

| Aspect | PCR2.1 / A5 déjà | Ces shorts |
|--------|------------------|------------|
| Adresses hex dans scripts | ✅ `0x1D1496` etc. | Formalise pour débutants |
| Hexdump navigation | implicite | **explicite WinOLS UI** |
| BMW EDC17 390655 | autre SW | même famille EDC17 |

**Rien à changer dans les builds** — documentation formation uniquement.

## ✅ Checklist Hexdump

- [ ] Je sais où est la colonne adresses (gauche)
- [ ] Je sais que c'est du **hex**, pas du décimal
- [ ] Je comprends lignes de 16 octets (`…0` → `…F`)
- [ ] Je peux aller à `1D1496` sans confusion base 10

## 📎 Shorts Liés

- `shorts/08-addresses-always-hex.md`
- `shorts/09-why-rows-end-in-f.md`
- `shorts/10-left-column-address.md`

---

**⚠️ ADRESSES = TOUJOURS HEX · COLONNE GAUCHE · LIGNES 0→F.**

---

**Dernière mise à jour :** 27 oct 2026 12:41 UTC-3  
**Status :** ✅ WinOLS basics #8–#10
