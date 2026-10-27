# Short #18 : YouTube EDC17CP14 — DPF / EGR / Hot Start / Idle

**Durée :** vidéo complète | **ECU :** EDC17CP14 | **Démo :** Audi A6 SW **505999**

## 🎯 Objectif

Savoir ce que couvre le tutoriel WinOLS et **ce qu’on peut / ne peut pas** copier sur A5 **516657**.

## 🔗 Vidéo

https://youtu.be/dKaJ-WJMwcc  
**Titre :** EDC17CP14 DPF - EGR - Hot Start - Idle RPM FIX

## 📐 Contenu

| Bloc | Exemple (505999) | Sur A5 516657 |
|---|---|---|
| DPF switches | `1EE34A` 0100→0000 | Via **DaVinci**, pas ces adresses |
| EGR curves | `1BC35A`… | DaVinci EGR+FLAPS |
| Hot start | `1F84FA` / `1F85D8` | **À chercher** (pas en V1.5) |
| Idle RPM | (titre) | **À chercher** |
| Checksum | CS wrong | noCHK → **CHK** avant flash |

## ⚠️ Règle d’or

```
❌ Copier adresses A6 505999 → A5 516657
✅ Même famille EDC17CP14 → même *logique*, offsets via A2L similar / DaVinci
```

## ✅ vs Repo A5

- Deletes : **DaVinci** déjà ✅  
- Manque : **Hot Start + Idle FIX** si hard start post-flash  
- Aligné Lesson 21 (cranking maps)

## 📎

`../../../../../EDC17-YOUTUBE-DPF-EGR-HOTSTART.md`  
`../../../../../fiche-assets/edc17-youtube-dKaJ-WJMwcc.jpg`
