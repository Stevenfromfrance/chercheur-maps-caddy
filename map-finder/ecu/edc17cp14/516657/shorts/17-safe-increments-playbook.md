# Short #17 : Safe Increments Playbook

**Durée :** ~45 sec | **Lesson 21**

## 🎯 Objectif

Appliquer des incréments **proportionnels**, jamais en aveugle.

## 📐 Checklist

| Levier | Incrément |
|---|---|
| Règle 30 % | +30 % wish → ~30–35 mm³ fuel |
| Turbo | +4–8 % ; leave 1k 0-boost |
| Fuel Duration | +1–13 % µs |
| EGR | activation = **0** |
| Limp Error TQ | raise (ex. 550) si besoin |

> Clear limiters **before** raising requests.  
> Every % = physical µs or mbar. Respect 14.55:1.

## ✅ A5 V1.5 Scorecard

| Item | Status |
|---|---|
| InjTime +1.7 % | ✅ dans 1–13 % |
| EGR off | ✅ |
| Turbo ~+6 % | ✅ dans 4–8 % |
| Limp raise | ⏳ non doc (0AW → prudence) |
| Limiters first | ⚠️ plafonds ORI = path partiel |

## 🔗 Source

Lesson 21 · `EDC17-LESSON21-TUNING-GUIDE.md`
