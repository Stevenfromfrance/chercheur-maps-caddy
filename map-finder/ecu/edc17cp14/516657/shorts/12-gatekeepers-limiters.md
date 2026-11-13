# Short #12 : Gatekeepers — Limiters

**Durée :** ~45 sec | **Lesson 21**

## 🎯 Objectif

Comprendre que le wish est **plafonné** par des limiteurs — les remonter **proportionnellement**.

## 🔍 Phrase Clé

> Request 450 Nm + limiter 400 Nm → ECU enforces **400 Nm**.

## 📐 Limiters Clés

| Limiteur | Action tuner |
|---|---|
| FAPS (atm) | Ignorer &lt;900 hPa |
| FEGT (EGT) | Ne pas delete aveugle |
| Gearbox | Respecter R/1 / **0AW** |
| Cranking | Hard start possible |
| Error TQ / Limp | Raise (ex. 550) si Stage1 limpe |

## ⚠️ A5 Bertin

0AW fragile → **ne pas** monter limp/GBX comme une DSG. Plafonds ORI V1.5 = choix conservateur.

## 🔗 Source

Lesson 21 · `EDC17-LESSON21-TUNING-GUIDE.md`
