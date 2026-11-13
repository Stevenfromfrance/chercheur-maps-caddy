# Calibrage Weak — régime à vide (votre mesure)

## Mesure déjà faite (à garder)

```
Poignée à fond, roue sans charge
Voltage: 77.6V
RPM: 8325
Throttle: 242 / 3.72V
Current: ~19A   ← normal à vide
Weak: ON
System OK
```

**Règle :** tout le Weak se cale sur ce régime à vide ≈ **8300–8400 RPM**.

---

## Suite logique des réglages (ordre app)

### 1. MaxSpeed
```
Actuel: 12000RPM
Mettre: 9000RPM
```
Un peu au-dessus du vide (8325). Trop haut = Weak mal calé.

### 2. RatedSpeed
```
Actuel: 6864RPM
Mettre: 6500RPM
```
≈ 78% du régime à vide. C’est là que le couple “plein” s’arrête et que le Weak commence.

### 3. LimitSpeed
```
Actuel: 5000RPM   ← trop bas (vous tournez déjà à 8325)
Mettre: 8500RPM
```
Limite juste sous / près du vide. Sinon le contrôleur bride trop tôt.

### 4. BackSpeed
```
Laisser: 400RPM
```

### 5. Weak Character
```
Laisser: 0-Fast
```

### 6. WeakResponse
```
Actuel: 3
Essayer: 2
```
Plus bas = Weak moins agressif à vide (souvent plus propre). Si trop mou sur route → remonter à 3.

### 7. Ratios in Speed (recoller à 8325)

Mettre la courbe comme ça (ordre RPM) :

```
500RPM   100%
1000RPM  100%
1500RPM  100%
2000RPM  100%
2500RPM  100%
3000RPM  100%
3500RPM  100%
4000RPM  100%
4500RPM  100%
5000RPM  100%
5500RPM  100%
6000RPM  95%
6500RPM  90%     ← autour RatedSpeed
7000RPM  80%
7500RPM  65%
8000RPM  45%
8500RPM  20%     ← près du vide 8325
9000RPM  0%      ← = MaxSpeed
```

**Avant :** la courbe baissait dès 5000 et coupait à 8500 → trop tôt pour un vide à 8325.

### 8. LD / LQ / FAIF
```
Ne pas toucher (900 / 329 / 128)
```

### 9. Save
```
Save → OFF → batterie 10 sec → ON
```

### 10. Retest à vide (même test)

Poignée à fond, roue sans charge, noter :

```
RPM cible: 8200–8800
Current: 15–40A (normal à vide)
Weak: peut s’allumer près du max
Temp MOS/Motor: stables
Pas de bruit bizarre / vibration
```

Si RPM plafonne trop bas → monter un peu `LimitSpeed` / `MaxSpeed`.  
Si vibration en haut → baisser `WeakResponse` (2 → 1) ou adoucir 8000–8500%.

---

## Ce qu’on peut “améliorer” à vide

Oui, un peu :

| Objectif | Action |
|----------|--------|
| Régime max plus propre | `MaxSpeed` 9000 + courbe jusqu’à 8500 |
| Moins de bride trop tôt | `LimitSpeed` 5000 → 8500 |
| Weak mieux calé | `RatedSpeed` ~6500 + courbe ci-dessus |
| Moins agressif | `WeakResponse` 3 → 2 |

**Important :** à vide le courant restera bas (~20A). C’est normal.  
Le vrai test puissance = **sur route / en charge**, pas à vide.

---

## Méthode pour la prochaine fois

1. Batterie bien chargée (~80–84V pour 72V)
2. Roue en l’air
3. Poignée à fond 5–10 sec
4. Noter **RPM max** + **Voltage**
5. Puis :
```
RatedSpeed ≈ RPM_vide × 0.75 à 0.80
MaxSpeed   ≈ RPM_vide × 1.05 à 1.10
LimitSpeed ≈ RPM_vide × 1.00 à 1.05
Weak commence autour de RatedSpeed
Courbe → 0% à MaxSpeed
```

Votre base actuelle : **RPM_vide = 8325 @ 77.6V**.

---

## Ne pas changer pour ce calibrage

```
PolePairs: 4
RatedVoltage: 72V
MaxLineCurr: 200A
MaxPhaseCurr: 450A
Batt RatedCapacity: 80AH
PhaseExchange: No Exchange
```
