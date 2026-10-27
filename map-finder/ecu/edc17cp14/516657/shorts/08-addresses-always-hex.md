# Short #8 : Addresses Are Always Hex

**Durée :** ~20 sec | **WinOLS basics** | **ECU :** EDC17 (démo BMW 390655)

## 🎯 Objectif

Retenir **la règle unique** : dans WinOLS, **les adresses sont toujours en hexadécimal**.

## 🔍 Phrase Clé

> **THE ONE RULE TO REMEMBER**  
> Addresses are always hex • WinOLS basics

## 📐 Exemples

| Tu lis | Hex | Pas décimal |
|---|---|---|
| `000010` | 16 | ≠ dix |
| `1D1496` | Injection Time A5 | ≠ « un million… » décimal |
| `1CF9C0` | AccPed Caddy | idem |

## ⚠️ Erreur Courante

```
❌ Calculer 000010 + 10 = 000020 en pensant « +10 décimal »
✅ En hex +10 = +16 décimal → ligne suivante OK
   Mais 000010 + 10 décimal écrit faux → adresse fausse
```

## ✅ Vérification

- [ ] Adresses notées avec préfixe `0x` ou clairement hex
- [ ] Scripts Python : `0x1D1496` pas `1913494` ambigu

## 🔗 Source

https://www.facebook.com/share/r/18K1JbYWVZ/  
**Image :** `../../../../../fiche-assets/edc17-short-08-facebook.jpg`  
**Détail :** `../../../../../EDC17-WINOLS-HEX-BASICS.md`
