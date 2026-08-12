# Procédures log VCDS — Caddy CAYE PCR2.1 soft 9979

ECU : `03L 906 023 TB` · Soft `9979`  
Outil : VCDS → **01-Engine** → **Advanced Measuring Values** (pas les groupes 08)

---

## IDE à cocher (tous les types de log)

Tape chaque numéro dans le filtre VCDS et coche :

| IDE | Nom |
|---|---|
| **IDE00021** | Engine RPM |
| **IDE00075** | Vehicle speed |
| **IDE00086** | Accelerator pedal position |
| **IDE00100** | Engine torque (TQI_SP) |
| **IDE00188** | Fuel rail pressure actual |
| **IDE00201** | Fuel rail pressure specified |
| **IDE00190** | MAP / charge air specified |
| **IDE00191** | MAP / charge air actual |
| **IDE00347** | Air mass actual |

Option utile : chercher `Torque limit` si dispo.

---

## 1) LOG VILLE (confort / partiels)

**But :** vérifier que la carto reste douce (pas on/off), pas de fumée / à-coups.

**Conditions**
- Trafic normal, 15–20 min
- ASR ON (usage réel)
- Pas de WOT prolongé

**Séquence**
1. Contact + moteur chaud idéalement
2. Advanced Measuring Values → cocher les IDE ci-dessus
3. **Log → Start**
4. Conduite ville normale (arrêts, 2ᵉ/3ᵉ, légers coups d’accélérateur)
5. **Stop** → Save

**Nom fichier suggéré :** `CADDY_VILLE_YYYYMMDD.CSV`

**Réussite si :** couple progressif, pas de pics rail fous, conduite agréable.

---

## 2) LOG ROUTE (Stage1 / rail / turbo)

**But :** valider couple, rail consigne/réel, MAP sous charge.

**Conditions**
- Route dégagée, légal
- 3ᵉ ou 4ᵉ
- ASR ON
- Moteur chaud

**Séquence**
1. Coche IDE → **Log Start**
2. Accélération franche (plein gaz) de ~1800 jusqu’à ~3500–4000 tr/min **en charge**
3. Relâche, recommence 1–2 fois si possible
4. **Stop** → Save

**Nom fichier suggéré :** `CADDY_ROUTE_WOT_YYYYMMDD.CSV`

**Réussite si :**
- couple pic ~320–340 Nm (Stage1 V1/V2)
- rail consigne ~1620 ; réel de préférence ≤ ~1650–1670
- MAP suit la consigne (pas d’écart énorme)

**Interdit :** log seulement en décélération / frein moteur.

---

## 3) LOG DEPART (launch / frein à main)

**But :** voir hold régime + MAP/couple au hold + trou au départ.

**Conditions**
- Endroit sûr
- **ASR OFF** (test)
- 1ʳᵉ , frein à main, **en prise** (sans débrayer au hold)
- Puis départ contrôlé

**Séquence**
1. Coche IDE → **Log Start**
2. Plein gaz, frein à main : tenir 2–3 s (noter le régime hold)
3. Lâcher frein à main / démarrer proprement
4. **Stop** → Save

**Nom fichier suggéré :** `CADDY_DEPART_LAUNCH_YYYYMMDD.CSV`

**Réussite si :** régime hold stable (V2 ~2500 / V3 ~2700–3000), CSV avec speed≈0 puis speed>0.

**Interdit :** mélanger avec un test hardcut 4800 dans le même fichier (sinon le préciser).

---

## 4) LOG HARCUT (~4800)

**But :** confirmer coupure couple haute régime **en roulant**.

**Conditions**
- 3ᵉ ou 4ᵉ, vitesse > 0
- ASR ON ou OFF (noter lequel)
- Pas frein à main / pas launch

**Séquence**
1. **Log Start**
2. Montée régime franche jusqu’à la zone 4500–4800
3. **Stop** → Save

**Nom fichier suggéré :** `CADDY_HARCUT_YYYYMMDD.CSV`

**Réussite si :** couple qui tombe vers 0 près de ~4800 avec pédale encore haute (si possible).

---

## Envoi du log

- Envoyer le **CSV brut** (pas une photo d’écran)
- Indiquer : soft flashé (V2 / V3 / …) + type de log + ASR ON/OFF
