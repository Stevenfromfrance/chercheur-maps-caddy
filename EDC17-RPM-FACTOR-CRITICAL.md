# ⚠️ EDC17 RPM FACTOR — INFORMATION CRITIQUE

## 🎯 Découverte Majeure (Facebook Post)

**Source :** https://www.facebook.com/share/r/1JSyXmmAYL/?mibextid=wwXIfr

### Le Piège EDC17

> **EDC17 stores RPM ×2. The axis says 10,000 — the real value is 5000.**

## 📐 Facteur de Correction

**WinOLS Factor : 0.5**

### Exemple

| Affiché WinOLS (raw) | Valeur Réelle | Correction |
|---|---|---|
| 10,000 rpm | **5,000 rpm** | ×0.5 |
| 8,000 rpm | **4,000 rpm** | ×0.5 |
| 9,600 rpm | **4,800 rpm** | ×0.5 |

## ⚠️ Impact sur les Maps

### Hardcut 4800 rpm
```
Valeur WinOLS à saisir : 9600
Valeur réelle moteur : 4800 rpm
```

### Launch Control 2700 rpm
```
Valeur WinOLS à saisir : 5400
Valeur réelle moteur : 2700 rpm
```

### AccPed / Smoke / Rail — Axes RPM
Tous les axes RPM dans **toutes les maps EDC17** sont stockés ×2 :
- AccPed banques : axes RPM ×2
- Smoke limiters : axes RPM ×2
- Rail pressure : axes RPM ×2
- Torque limiters : axes RPM ×2
- Injection maps : axes RPM ×2

## 🔄 Comparaison PCR2.1 vs EDC17

| Aspect | PCR2.1 (Caddy) | EDC17 (A5) |
|--------|----------------|------------|
| **RPM storage** | ×1 (normal) | **×2 (doubled)** |
| **WinOLS factor** | 1.0 | **0.5** |
| **Hardcut 4800** | Saisir 4800 | Saisir **9600** |
| **Launch 2700** | Saisir 2700 | Saisir **5400** |

## 🛠️ Configuration WinOLS

### Import A2L Similar 0005

Quand on importe l'A2L similar 0005 (pas 0008 exact) :

1. **Vérifier les axes RPM** de chaque map
2. Si axe RPM affiché > 6000 rpm : **appliquer factor 0.5**
3. WinOLS → Map Properties → Axis → Factor : **0.5**

### Axes à Corriger (liste non exhaustive)

```
AccPed banques (0x1CF9C0, 0x1CFAC0, ...)
├── Axe Y (RPM) : factor 0.5
└── Axe X (pédale %) : factor 1.0

Torque Limiters (0x1D3190, ...)
├── Axe régime : factor 0.5
└── Axe atmosphérique : factor 1.0

Smoke Limiters (0x1D1D18, ...)
├── Axe RPM : factor 0.5
└── Autre axe : vérifier

Rail Pressure (0x1E9368, ...)
├── Axe RPM : factor 0.5
└── Axe couple : vérifier
```

## ❌ Erreurs Courantes

### Erreur #1 : Hardcut trop bas
```
❌ Saisir 4800 dans WinOLS (raw)
   → Hardcut réel = 2400 rpm (moteur cale !)

✅ Saisir 9600 dans WinOLS (raw)
   → Hardcut réel = 4800 rpm
```

### Erreur #2 : Launch trop haut
```
❌ Saisir 2700 dans WinOLS (raw)
   → Launch réel = 1350 rpm (pas assez)

✅ Saisir 5400 dans WinOLS (raw)
   → Launch réel = 2700 rpm
```

### Erreur #3 : Comparer A5 vs Caddy sans conversion
```
❌ "Le Caddy a hardcut 4800, je mets 4800 sur l'A5"
   → A5 hardcut réel = 2400 rpm

✅ "Le Caddy a hardcut 4800, je mets 9600 sur l'A5"
   → A5 hardcut réel = 4800 rpm
```

## 📋 Checklist EDC17

Avant toute modification de map EDC17 :

- [ ] Identifier si l'axe est RPM
- [ ] Vérifier la plage : >6000 raw → probablement ×2
- [ ] Appliquer factor 0.5 dans WinOLS
- [ ] **Doubler** mentalement toute valeur RPM vs PCR2.1
- [ ] Vérifier avec A2L 0005 similar (si noms cohérents)
- [ ] Logs VCDS : valider RPM réel moteur

## 🎓 Full Course

Le post Facebook mentionne un **"Full course"** avec lien dans le premier commentaire.

**Action :** Récupérer le lien du commentaire pour accès complet à la formation EDC17.

## 📊 Impact sur Fichiers Existants

### V1.5 A5 Bertin

**À vérifier :**
- `build_v1.py`, `build_v11.py` : hardcut, launch (si applicable)
- `A5_516657_V1.5_0AW_manifest.json` : RPM axes documented ?
- `LIVRAISON-V1.5-0AW.txt` : mention factor 0.5 ?

### Documentation à Mettre à Jour

- `METHODOLOGIE-EDC17-RECAP.md` : ajouter section RPM factor
- `METHODOLOGIE-SHORTS-TEMPLATE.md` : short dédié RPM ×2
- `analyze_v15_detailed.py` : appliquer factor 0.5 aux axes RPM
- `map-finder/ecu/edc17cp14/516657/README.md` : warning visible

## 🔗 Liens

- Facebook post : https://www.facebook.com/share/r/1JSyXmmAYL/?mibextid=wwXIfr
- Image post : https://scontent-dfw5-2.xx.fbcdn.net/v/t15.5256-10/861888560_1635140424742064_1372199737414846885_n.jpg

## ✅ TODO Urgent

1. **Récupérer lien "Full course"** (commentaire Facebook)
2. **Auditer tous les fichiers A5** : vérifier si factor 0.5 appliqué
3. **Créer SHORT #1 EDC17** : "RPM ×2 Factor"
4. **Mettre à jour README.md** A5 : warning en haut
5. **Script validation** : vérifier cohérence axes RPM dans binaires

---

**⚠️ CRITIQUE : Ne jamais oublier le factor 0.5 sur EDC17 !**

**Dernière mise à jour :** 27 oct 2026 12:23 UTC-3  
**Auteur :** Cloud Agent Cursor (via Facebook post recovery)
