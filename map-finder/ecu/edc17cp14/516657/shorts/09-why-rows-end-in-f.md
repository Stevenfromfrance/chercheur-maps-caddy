# Short #9 : Why Rows End in F

**Durée :** ~25 sec | **WinOLS basics** | **Prérequis :** Short #8

## 🎯 Objectif

Comprendre pourquoi chaque ligne hexdump se termine par une adresse en **F**.

## 🔍 Phrase Clé

> **WHY ROWS END IN F**  
> Addresses start from zero • WinOLS basics

## 📐 Explication

16 octets par ligne, index **0 → F** (zéro-based) :

```
000000 : [0][1][2]…[E][F]   ← dernier @ 00000F
000010 : [0][1][2]…[E][F]   ← dernier @ 00001F
000020 : …
```

Prochaine ligne = adresse + **0x10** (16 décimal).

## ✅ Vérification

- [ ] Début de ligne = adresse `…0`
- [ ] Fin de ligne = adresse `…F`
- [ ] 16 colonnes visibles au centre

## 🔗 Source

https://www.facebook.com/share/r/19Vgvf6DAm/  
**Image :** `../../../../../fiche-assets/edc17-short-09-facebook.jpg`  
**Détail :** `../../../../../EDC17-WINOLS-HEX-BASICS.md`
