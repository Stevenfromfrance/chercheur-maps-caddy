# Prise 16 broches — Contrôleur d’origine S50

**Réf. étiquette :** `S50` · `TB-72/60-HS35` · `TC-ZY-01` · 72V · 50A · 2000W  
**Frein usine :** **High Level** (haute)  
**Fonctions usine :** E-ABS · antivol · 3 vitesses · marche arrière  

**Important :** la prise **8 broches = alarme** (hors sujet ici).  
La prise **16 broches = tout le guidon / véhicule** pour faire rouler le scoot.  
Les gros fils batterie + phases sont **hors** de cette prise.

---

## Ce qui sort de la 16 broches (par fonction)

Sur ce type S50 / contrôleur sine-wave CN, la 16 pin regroupe **exactement** les fonctions listées sur l’étiquette + le guidon :

| # | Fonction | Combien de fils | Couleur typique (famille S50 / haut niveau) | Rôle exact | FarDriver |
|---|----------|-----------------|---------------------------------------------|------------|-----------|
| 1 | **Contact / électro-serrure (KEY)** | 1 | **Orange** (parfois jaune) | +72V quand la clé est ON → allume le contrôleur | **KEY orange #10** |
| 2 | **Accélérateur +5V** | 1 | **Rouge** (fin) | Alim 5V de la poignée | **ACC+ rouge/blanc #28** |
| 3 | **Accélérateur signal** | 1 | **Vert** ou **blanc** | 0.8V → ~4.5V en tournant la poignée | **SV vert/blanc #27** |
| 4 | **Accélérateur masse** | 1 | **Noir** | Masse de la poignée | **GND #26** |
| 5 | **Frein haute (High Level)** | 1 | **Violet / mauve** | +12V (ou haut) quand tu serres le frein — **confirmé par l’étiquette** | **BH gris #11** |
| 6 | **Frein basse / E-ABS** (si présent) | 1 | **Jaune** ou **jaune-vert** | Masse quand frein serré (option / E-ABS) | **BL jaune-vert #21** |
| 7 | **3 vitesses — haute** | 1 | **Rose / rose-blanc** ou transparent | Relier à masse = mode rapide | **FW jaune/blanc #3** |
| 8 | **3 vitesses — basse** | 1 | **Gris** ou **bleu-blanc** | Relier à masse = mode lent | **FW2 bleu/blanc #2** |
| 9 | **Masse commune modes** | 1 | **Noir** | Masse partagée 3 vitesses / reverse | **GND** |
| 10 | **Marche arrière** | 1 | **Blanc** ou **brun-blanc** | Relier à masse = reverse | **RE brun/blanc #8** |
| 11 | **Compteur / signal vitesse** | 1 | **Bleu foncé** ou **jaune** | Impulsion vitesse vers l’afficheur | **SPA violet #9** (option) |
| 12 | **+12V accessoire** (parfois) | 1 | **Rouge** ou **rouge-blanc** | Sortie 12V petite puissance | Ne pas mettre sur FarDriver KEY |
| 13 | **Masses signal** | 1–2 | **Noir** | GND capteurs / frein | **GND** |

Les pins **vides** sur ta prise = fonctions non câblées en usine (normal).

---

## Ce qui N’EST PAS dans la 16 pin

| Élément | Où c’est |
|---------|----------|
| Batterie +72V / − | Gros **Rouge** / gros **Noir** (bornes) |
| Phases moteur U V W | Gros **Jaune** / **Vert** / **Bleu** (bornes) |
| Capteurs Hall moteur | Prise à part (souvent la **10 pin** à côté, ou prise moteur 5 fils) |
| Alarme / antivol | Ta **8 pin** |

---

## Comment reconnaître chaque fil (zéro erreur, 2 min)

Batterie branchée, contact ON, multimètre en **DC** (noir du multi sur B−) :

1. **~72V stable** → **KEY** (contact) → FarDriver orange  
2. **~5V stable** → alim accélérateur (**ACC+**)  
3. Fil qui **monte de ~1V à ~4.5V** en tournant la poignée → **signal gaz (SV)**  
4. **0 Ω** vers B− → **GND**  
5. Au frein : fil qui passe à **~12V** → **frein haute (BH)** — c’est ton cas (étiquette)  
6. Au frein : fil qui passe à **0V / continuité masse** → frein basse (BL) si présent  
7. Interrupteur 3 vitesses : continuité vers masse selon la position → fils **haute / basse**  
8. Bouton reverse : continuité vers masse → fil **RE**

---

## Minimum pour rouler (depuis la 16 pin seulement)

Branche seulement ça sur le FarDriver :

1. **KEY** (orange) → #10  
2. **Throttle** 3 fils → #28 / #27 / #26  
3. **Frein haute violet** → **BH #11** (pas le frein basse)  
4. (+ Hall + batterie + phases hors 16 pin)

Le reste (3 vitesses, reverse, compteur) après.

---

## Couleurs vues sur ta prise (inventaire photo)

Sur tes photos 16 pin (face orange), on voit notamment :  
**Rouge, Orange, Violet, Vert, Jaune, Blanc, Noir, Bleu, Gris, Brun, Rose** — et plusieurs **cases vides**.

Ça colle parfaitement au tableau de fonctions ci-dessus (contact + gaz + frein haute + 3 vitesses + reverse + compteur + masses).

> Les positions broche 1→16 exactes varient selon l’angle de photo.  
> Pour brancher sans erreur : **suis la fonction + test multimètre**, pas un numéro de case flou.
