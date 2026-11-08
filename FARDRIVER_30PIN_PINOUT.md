# FarDriver ND72450 / NS24 — Pinout connecteur 30 broches

Source officielle : manuel FarDriver / SiAECOSYS Hall V1.5 §6.1

PDF imprimable : [`FARDRIVER_30PIN_PINOUT.pdf`](FARDRIVER_30PIN_PINOUT.pdf)

## Vue du connecteur (3 × 10)

```
21 BL     22 HALLC   23 485B/TXD  24 TEMP   25 —      26 GND    27 SV      28 ACC+   29 BW5V   30 60VC
Jaune/Vert  Bleu       Brun/Bleu    Blanc     (vide)    Noir      Vert/Blanc  Rouge/Blanc Brun/Vert Rose

11 BH     12 HALLB   13 485A/RXD  14 FD     15 CANH   16 GND    17 P       18 ALARM  19 W      20 KEY
Gris        Vert       Rouge/Noir   Noir/Blanc Rouge/Jaune Noir   Bleu/Rouge Marron   Brun/Rouge Orange

 1 HALLA   2 FW2     3 FW         4 HALL+   5 CANL   6 GND     7 GND      8 RE      9 SPA    10 KEY
Jaune       Bleu/Blanc Jaune/Blanc  Rouge     Brun/Jaune Noir    Noir      Brun/Blanc Violet   Orange
```

## Table complète

| N° | Code | Couleur | Fonction exacte | Priorité |
|----|------|---------|-----------------|----------|
| 1 | HALLA | Jaune | Signal Hall moteur A | Obligatoire |
| 2 | FW2 | Bleu/Blanc | Vitesse basse (masse = actif) | Option |
| 3 | FW | Jaune/Blanc | Vitesse haute (masse = actif) | Option |
| 4 | HALL+ | Rouge | Alim Hall moteur (~5–14V) | Obligatoire |
| 5 | CANL | Brun/Jaune | Bus CAN Low | Option |
| 6 | GND | Noir | Masse (Hall) | Obligatoire |
| 7 | GND | Noir | Masse (alarme / modes) | Obligatoire |
| 8 | RE | Brun/Blanc | Marche arrière (masse = actif) | Option |
| 9 | SPA | Violet | Sortie compteur vitesse analogique | Option |
| 10 | KEY | Orange | Contact / serrure électrique (+ batterie) | Obligatoire |
| 11 | BH | Gris | Frein haute (+12V / +batterie) | Selon frein |
| 12 | HALLB | Vert | Signal Hall moteur B | Obligatoire |
| 13 | 485A/RXD | Rouge/Noir | Série RX / pulse vitesse (SPD) | Bluetooth / écran |
| 14 | FD | Noir/Blanc | Signal antivol / lock | Alarme |
| 15 | CANH | Rouge/Jaune | Bus CAN High | Option |
| 16 | GND | Noir | Masse (reverse / Bluetooth) | Obligatoire |
| 17 | P | Bleu/Rouge | Cruise / parking | Option |
| 18 | ALARM | Marron | BOOST / alarme (selon config) | Option |
| 19 | W | Brun/Rouge | Phase lock antivol | Alarme |
| 20 | KEY | Orange | 2e KEY (alarme → contact) | Alarme / contact |
| 21 | BL | Jaune/Vert | Frein basse (masse = frein) | Selon frein |
| 22 | HALLC | Bleu | Signal Hall moteur C | Obligatoire |
| 23 | 485B/TXD | Brun/Bleu | Série TX (Bluetooth / PC) | Bluetooth / écran |
| 24 | TEMP | Blanc | Capteur température moteur | Option |
| 25 | — | — | Non utilisé | — |
| 26 | GND | Noir | Masse (throttle / frein basse) | Obligatoire |
| 27 | SV | Vert/Blanc | Signal accélérateur 0.5–4.3V | Obligatoire |
| 28 | ACC+ | Rouge/Blanc | +5V accélérateur | Obligatoire |
| 29 | BW5V | Brun/Vert | +5V module Bluetooth | Bluetooth |
| 30 | 60VC | Rose | + batterie pour alarme (sortie) | Alarme |

## Minimum pour rouler

Broches : **#1 #4 #6 #10 #12 #22 #26 #27 #28** + frein **#21 ou #11**  
+ bornes puissance : **B+ B− U V W**
