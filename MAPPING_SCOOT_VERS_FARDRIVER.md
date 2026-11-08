# Mapping Faisceau Scooter → FarDriver ND72450 (NS24)

**Objectif:** Brancher le faisceau d’origine de ton scooter (contrôleur noir à ailettes encore monté) sur le FarDriver.

**FarDriver:** Jiangsu Fardriver NS24 — `ND72450_14_A_HA86` — 72V / 200A / 450A

---

## Ce que montre ta photo (côté scooter)

Sur la photo du compartiment :

| Élément visible | C’est quoi |
|-----------------|------------|
| Gros boîtier noir à ailettes | Ancien contrôleur (à démonter) |
| 3 gros fils Jaune / Vert / Bleu (gauche) | Phases moteur |
| Gros Rouge + Gros Noir (bas) | Batterie +72V et masse |
| Gros connecteur orange/translucide (droite) | Faisceau signaux (accélérateur, freins, contact, compteur…) |
| Petit connecteur blanc en dessous | Autre groupe de signaux |
| Petits connecteurs blancs/noirs lâches | Freins, feux, accessoires |
| Câble mécanique + ressort (haut droite) | Frein mécanique / contacteur frein |

**Principe:** Tu ne changes pas le faisceau du scooter. Tu débranches l’ancien contrôleur, et tu reconnectes chaque fonction sur le faisceau FarDriver (celui avec les petits connecteurs colorés + alarme).

---

## 1. Puissance (à faire en dernier)

### Batterie

| Scooter | FarDriver | Remarque |
|---------|-----------|----------|
| Gros **Rouge** (+ batterie) | Borne **B+** (bague rouge) | Fusible 200A obligatoire |
| Gros **Noir** (− batterie) | Borne **B−** (bague noire) | Masse |

### Phases moteur

| Scooter / moteur | FarDriver |
|------------------|-----------|
| Gros **Jaune** | Borne **U** (jaune) |
| Gros **Vert** | Borne **V** (verte) |
| Gros **Bleu** | Borne **W** (bleue) |

Si le moteur part à l’envers → inverser 2 phases parmi les 3, ou refaire l’auto-apprentissage FarDriver.

---

## 2. Ce qu’il faut brancher en priorité (pour que ça roule)

Sans ces 4 groupes, le scooter ne démarre pas correctement :

1. Batterie B+/B−
2. Phases moteur U/V/W
3. Capteurs Hall moteur
4. Contact (KEY orange)
5. Accélérateur (3 fils)
6. Freins (au moins un)

Le reste (alarme, compteur, modes) vient après.

---

## 3. Mapping des connecteurs FarDriver (ton faisceau neuf)

### A) Capteurs Hall moteur — label « NS霍尔 » / « HALL »

| FarDriver | Couleur | Rôle | Côté scooter |
|-----------|---------|------|--------------|
| HALL+ | Rouge | Alim Hall (~5–12V) | Rouge Hall moteur |
| GND | Noir | Masse Hall | Noir Hall moteur |
| HALL A | Jaune | Signal A | Jaune Hall moteur |
| HALL B | Vert | Signal B | Vert Hall moteur |
| HALL C | Bleu | Signal C | Bleu Hall moteur |
| TEMP | Blanc (si présent) | Température moteur | Blanc moteur, sinon laisser libre |

**Sur le scooter:** le faisceau Hall sort du moteur (avec les phases). Cherche un connecteur 5 ou 6 broches près du moteur / derrière le contrôleur.

---

### B) Accélérateur (throttle) — connecteur gris/blanc 3 broches

Sur ton faisceau FarDriver (photo tenue en main) :

| FarDriver | Couleur | Rôle | Côté scooter |
|-----------|---------|------|--------------|
| ACC+ | Rouge / Rouge-blanc | +5V | Rouge accélérateur |
| GND | Noir | Masse | Noir accélérateur |
| SV | Vert / Vert-blanc | Signal 0.8→4.5V | Vert (ou blanc) accélérateur |

**Test multimètre:** au repos ~0.8–1.2V, plein gaz ~4.0–4.5V sur le fil signal.

**Sur le scooter:** part du guidon (poignée droite) → souvent dans le gros connecteur orange du contrôleur d’origine.

---

### C) Contact / serrure électrique (KEY)

| FarDriver | Couleur | Rôle | Côté scooter |
|-----------|---------|------|--------------|
| KEY | **Orange** | Contact ON = + batterie | Fil contact / clé / alarme |

C’est le fil que tu tenais avec le noir et le jaune-vert.

Sans KEY → le FarDriver reste éteint (même batterie branchée).

**Sur le scooter:** souvent le fil qui sort du contacteur à clé, ou le fil orange de l’alarme (sortie contact).

---

### D) Freins

Le FarDriver a 2 types :

| FarDriver | Couleur | Type | Quand l’utiliser |
|-----------|---------|------|------------------|
| BL | **Jaune-vert** | Frein basse (masse) | Si le levier ferme sur la masse |
| BH | **Gris** | Frein haute (+12V) | Si le levier envoie du +12V |

| FarDriver | Couleur | Rôle |
|-----------|---------|------|
| GND frein | Noir | Masse commune frein basse |

**Sur ta photo scooter:** le contacteur de frein est probablement près du câble mécanique (haut droite) + petits connecteurs 2 fils.

**Test:**
1. Multimètre continuité sur le connecteur frein scooter
2. Frein relâché = ouvert / frein serré = fermé → frein **basse** → brancher sur **jaune-vert + noir**
3. Si au freinage tu mesures du +12V → frein **haute** → brancher sur **gris (BH)**

---

### E) Alarme / antivol (module noir + télécommande)

Déjà présent sur ton faisceau FarDriver :

| FarDriver / alarme | Couleur | Rôle |
|--------------------|---------|------|
| Alim alarme + | Rose / Rouge (60VC) | + batterie (via contrôleur) |
| Alim alarme − | Noir | Masse |
| Contact via alarme | Orange | Sortie KEY vers contrôleur |
| Signal antivol | Blanc / Marron | Verrouillage moteur |
| Bleu / Rose / Violet | Divers | Start distant / klaxon / lock |

**Sur le scooter:** si tu as déjà une alarme d’origine, tu peux :
- soit utiliser **l’alarme FarDriver** fournie avec le faisceau,
- soit garder l’alarme scooter et ne brancher que son fil **contact (orange)** sur KEY FarDriver.

Ne pas brancher 2 alarmes en conflit sur le même KEY.

---

## 4. Ce qui est optionnel au début

| Connecteur FarDriver | Couleurs typiques | Fonction | Besoin pour rouler ? |
|----------------------|-------------------|----------|----------------------|
| Violet / Marron 2 broches | Violet + Marron | Compteur vitesse / mode | Non |
| Jaune / Jaune-bleu + boucle noire | — | Modes vitesse / jumper | Non |
| Blanc 3 broches marron/gris | — | Accessoires / display | Non |
| Violet + Bleu bullet | — | Signaux divers | Non |
| 485 / One-line (brun/bleu) | — | Afficheur FarDriver | Seulement si nouvel écran |
| CAN H/L | Rouge-jaune / Brun-jaune | Bus CAN | Non pour démarrer |
| Reverse | Brun-blanc | Marche arrière | Non |
| Cruise / Boost | Bleu-rouge / Marron | Cruise | Non |

---

## 5. Plan de branchement concret (ordre)

### Étape 0 — Préparation
1. Batterie **débranchée**
2. Démonter l’ancien contrôleur noir
3. Étiqueter chaque connecteur scooter avant de débrancher (photo + scotch nommé)
4. Sortir le faisceau FarDriver à côté

### Étape 1 — Puissance
1. Phases : Jaune→U, Vert→V, Bleu→W
2. Batterie : Rouge→B+, Noir→B− (+ fusible 200A)
3. Ne pas remettre la batterie tout de suite

### Étape 2 — Hall
1. Brancher le 5/6 fils Hall moteur sur le connecteur Hall FarDriver (couleurs identiques)

### Étape 3 — Contact
1. Fil contact scooter (ou sortie orange alarme) → **Orange KEY** FarDriver

### Étape 4 — Accélérateur
1. 3 fils guidon → connecteur 3 broches FarDriver (Rouge=+5V, Noir=GND, Vert=signal)

### Étape 5 — Freins
1. Identifier type (basse ou haute) au multimètre
2. Brancher sur BL (jaune-vert) ou BH (gris)

### Étape 6 — Premier allumage
1. Roue arrière **surélevée**
2. Batterie ON
3. Contact ON → FarDriver s’allume
4. Frein → moteur bloqué
5. Accélérateur doux → roue tourne
6. Faire l’**auto-apprentissage** FarDriver (Bluetooth / app) si besoin

---

## 6. Tableau “fil scooter → fil FarDriver” (à remplir)

| Fonction | Fil scooter (couleur / connecteur) | Fil FarDriver | Test OK ? |
|----------|-------------------------------------|---------------|-----------|
| Batterie + | Gros Rouge | B+ rouge | ☐ |
| Batterie − | Gros Noir | B− noir | ☐ |
| Phase U | Gros Jaune | U jaune | ☐ |
| Phase V | Gros Vert | V vert | ☐ |
| Phase W | Gros Bleu | W bleu | ☐ |
| Hall + | Rouge Hall | Rouge HALL+ | ☐ |
| Hall GND | Noir Hall | Noir GND | ☐ |
| Hall A/B/C | J/V/B Hall | J/V/B Hall | ☐ |
| Contact | _________ | Orange KEY | ☐ |
| Throttle +5V | _________ | Rouge/blanc | ☐ |
| Throttle GND | _________ | Noir | ☐ |
| Throttle signal | _________ | Vert/blanc | ☐ |
| Frein | _________ | Jaune-vert ou Gris | ☐ |
| Alarme | _________ | Module FarDriver | ☐ |

---

## 7. Comment identifier les fils dans le gros connecteur orange du scooter

Le connecteur orange d’origine regroupe presque tout. Pour le décoder :

1. Batterie débranchée, débrancher le connecteur orange de l’ancien contrôleur
2. Remettre la batterie / contact
3. Multimètre DC :
   - Fil à **~72V** = KEY / alim contact
   - Fil à **~5V** stable = alim throttle ou Hall
   - Fil **0V** = masse
   - Fil qui **monte de ~1V à ~4.5V** en tournant la poignée = signal accélérateur
4. Sur les 2 fils frein : continuité qui change en serrant le levier

Note chaque résultat dans le tableau ci-dessus.

---

## 8. Erreurs fréquentes sur cette adaptation

| Erreur | Conséquence |
|--------|-------------|
| Inverser B+ et B− | FarDriver grillé |
| Oublier KEY orange | Rien ne s’allume |
| Hall mal branchés | Saccades / erreur Hall |
| Frein toujours actif | Moteur refuse d’avancer |
| Brancher frein haute sur entrée basse | Freinage / regen bizarre |
| Garder alarme scooter + alarme FarDriver sur KEY | Contact aléatoire |
| Pas d’auto-apprentissage | Couple faible / bruit |

---

## 9. Minimum pour un premier essai

Branche seulement :
1. B+ / B−
2. U / V / W
3. Hall
4. KEY orange
5. Accélérateur 3 fils
6. 1 frein

Laisse de côté : compteur d’origine, modes vitesse, clignotants, GPS, 2e alarme.

Quand ça roule, tu ajoutes le reste un par un.

---

## 10. Photos utiles à me renvoyer (si tu bloques)

Pour finir l’identification exacte, envoie :
1. Gros plan du **connecteur orange** débranché (côté fils)
2. Connecteur **Hall moteur** (5/6 fils)
3. Connecteur **accélérateur** au guidon
4. Les **2 connecteurs frein**
5. Le fil qui vient du **contact / clé**

Avec ça on complète le tableau ligne par ligne à 100 %.

---

**Sources pinout FarDriver:** manuel ND72450 / NS24 (KEY orange, throttle rouge-blanc / noir / vert-blanc, Hall R-N-J-V-B, frein BL jaune-vert, BH gris).
