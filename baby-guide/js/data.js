const amazon = (asin, search) =>
  asin ? `https://www.amazon.fr/dp/${asin}` : `https://www.amazon.fr/s?k=${encodeURIComponent(search)}`;

const img = (asin) =>
  asin ? `https://images-eu.ssl-images-amazon.com/images/P/${asin}.01._SX300_.jpg` : "";

window.PRODUCTS = {
  mom: [
    {
      group: "Shower",
      icon: "🚿",
      items: [
        {
          brand: "La Roche-Posay",
          title: "Lipikar Huile Lavante AP+ Relipidante 400 ml + éco-recharge",
          price: "€46.87",
          needed: "no",
          verdict: "skip",
          note: "Not needed after birth. This is a pricey dry/eczema wash, not a maternity must.",
          compare: "Use supermarket Dove Sensitive, Neutral 0%, or the baby Mustela Bio gel on your body instead.",
          search: "La Roche-Posay Lipikar Huile Lavante AP+ 400ml eco recharge",
          asin: ""
        }
      ]
    },
    {
      group: "Breast pumps",
      icon: "🍼",
      items: [
        {
          brand: "Philips Avent",
          title: "Manual breast pump SCF430/01",
          price: "€24.90",
          needed: "optional",
          verdict: "keep",
          note: "Keep this one if you buy a pump. Manual is enough at the start. Matches Avent bottles.",
          compare: "Better than Medela Harmony here because you already planned Avent bottles. Buy one pump, not both. Wait 3–4 weeks after latch if you want.",
          search: "Philips Avent tire-lait manuel SCF430/01",
          asin: ""
        },
        {
          brand: "Medela",
          title: "Harmony Flex manual pump",
          price: "€23.00",
          needed: "no",
          verdict: "skip",
          note: "Same job as the Avent manual pump. Do not buy both.",
          compare: "Leave this. Harmony is good, but mixing Medela pump + Avent bottles is extra bits for no gain.",
          search: "Medela Harmony Flex tire-lait manuel",
          asin: ""
        }
      ]
    },
    {
      group: "Postpartum underwear & pads",
      icon: "🩲",
      items: [
        {
          brand: "Tigex",
          title: "Stretch net maternity briefs, pack of 5 (buy 10 total)",
          price: "€7.90",
          needed: "yes",
          verdict: "keep",
          note: "Washable mesh that holds a pad. Five is tight in this humidity — 10 is the right number.",
          compare: "Use with Abena pads after the heavy first days. Pants for the flood, mesh + pads after.",
          search: "Tigex slips filet stretch maternité lot de 5",
          asin: ""
        },
        {
          brand: "Always Discreet",
          title: "Postpartum disposable panties, size L, 2 × 8",
          price: "€20.80–€21.90",
          needed: "yes",
          verdict: "keep",
          note: "You already like pants. Size L is right. Use these for the heavy first days.",
          compare: "Do not also buy a huge pile of pads. Pants first, then mesh + Abena when bleeding is lighter.",
          search: "Always Discreet Postpartum culottes taille L",
          asin: ""
        },
        {
          brand: "Abena",
          title: "Premium maternity pads, 2 × 14 (28 pads)",
          price: "€16.49",
          needed: "yes",
          verdict: "compare",
          note: "Real maternity pads for mesh briefs. Good follow-up after Always pants.",
          compare: "Keep a pack if you use Tigex mesh. Skip a second huge pack if the pants already cover week one.",
          search: "Abena Maternity pads premium 14",
          asin: ""
        }
      ]
    },
    {
      group: "Carrier",
      icon: "👶",
      items: [
        {
          brand: "Koala Babycare",
          title: "Baby carrier / wrap, up to 9 kg",
          price: "€49.99",
          needed: "optional",
          verdict: "later",
          note: "Nice if you want him on you at home. Not a first-week must — you are home a lot and have a car.",
          compare: "Leave for later. A towel or the Boppy covers early feeds.",
          search: "Koala Babycare baby carrier 9 kg",
          asin: ""
        }
      ]
    },
    {
      group: "Milk storage",
      icon: "🧊",
      items: [
        {
          brand: "Medela",
          title: "Easy Pour breast milk bags 210 ml × 50",
          price: "€15.99",
          needed: "optional",
          verdict: "keep",
          note: "If you pump later, one 50-pack is enough. Easy-pour spout. Throw away after one freeze–thaw.",
          compare: "Keep Medela, leave Lansinoh bags. Bags do not need to match the pump.",
          search: "Medela Easy Pour sacs de conservation 50",
          asin: ""
        },
        {
          brand: "Lansinoh",
          title: "Breast milk storage bags × 50",
          price: "€14.90",
          needed: "no",
          verdict: "skip",
          note: "Same job as Medela Easy Pour. Do not buy both.",
          compare: "Leave this. Medela’s pour spout is a bit easier.",
          search: "Lansinoh sacs conservation lait maternel 50",
          asin: ""
        }
      ]
    },
    {
      group: "Perineum care",
      icon: "💧",
      items: [
        {
          brand: "Frida Mom",
          title: "MomWasher / upside-down peri bottle",
          price: "See Amazon",
          needed: "yes",
          verdict: "keep",
          note: "This is the bottle that actually sprays up while you sit. That angle is the real reason it costs more — not just the name.",
          compare: "Better than Nuby if Nuby does not invert well. Skip the Lansinoh spray. If Frida is too dear, wait for Lansinoh 360 ml wash bottle (not the purple spray).",
          search: "Frida Mom peri bottle upside down",
          asin: ""
        },
        {
          brand: "Lansinoh",
          title: "Perineum regenerating spray 100 ml",
          price: "€13.90",
          needed: "no",
          verdict: "skip",
          note: "This is a scented product, not the water bottle. Water from the peri bottle does the useful part.",
          compare: "Do not confuse with the Lansinoh 360 ml wash bottle (often unavailable). Skip this spray.",
          search: "Lansinoh spray régénérant périnée 100 ml",
          asin: ""
        },
        {
          brand: "Nuby / Dr. Talbot's",
          title: "Perineal postpartum bottle 360 ml",
          price: "€9.99",
          needed: "no",
          verdict: "skip",
          note: "Has a bent neck, but may not spray as well fully upside down as Frida or the Lansinoh wash bottle.",
          compare: "Leave this if you buy Frida. Do not buy both.",
          search: "Nuby Dr Talbot peri bottle 360 ml",
          asin: ""
        }
      ]
    },
    {
      group: "Nipple cream",
      icon: "💛",
      items: [
        {
          brand: "Medela",
          title: "Purelan lanolin 37 g",
          price: "€9.40",
          needed: "yes",
          verdict: "keep",
          note: "One lanolin cream is enough. This tube is a real size. Safe while breastfeeding.",
          compare: "Keep Purelan 37 g. Leave the Lansinoh 10 ml travel tube — almost the same price for a tiny amount.",
          search: "Medela Purelan 37g",
          asin: ""
        },
        {
          brand: "Lansinoh",
          title: "HPA lanolin 10 ml travel size",
          price: "€9.90",
          needed: "no",
          verdict: "skip",
          note: "Same lanolin job as Purelan, but this is a travel size at a bad price.",
          compare: "If you ever prefer Lansinoh, buy the 40 ml tube, not 10 ml.",
          search: "Lansinoh HPA lanoline 10 ml",
          asin: ""
        }
      ]
    }
  ],
  baby: [
    {
      group: "Skin & bath",
      icon: "🛁",
      items: [
        {
          brand: "Mustela",
          title: "Crème hydratante bio visage & corps 150 ml",
          price: "€11.76",
          needed: "optional",
          verdict: "later",
          note: "Unscented bio cream. Fine from birth, but you already planned coconut oil after the bath.",
          compare: "Do not buy this and coconut oil. Oil first; cream only if the skin is still flaky from AC.",
          search: "Mustela crème hydratante bébé bio 150 ml",
          asin: "B0GCX7LR16"
        },
        {
          brand: "Mustela",
          title: "Stelatopia gel lavant peau atopique 500 ml",
          price: "€15.69",
          needed: "no",
          verdict: "skip",
          note: "This is for eczema / very dry skin. Too rich for a normal newborn in Suriname heat.",
          compare: "Replace with Mustela Gel Lavant Bio sans parfum 400 ml pump (not this, not the refill pouch first).",
          search: "Mustela Stelatopia gel lavant 500 ml",
          asin: "B07YQ5LW2Q"
        },
        {
          brand: "Twinly",
          title: "Bubbly changing table + bath 2-in-1",
          price: "€123.40",
          needed: "no",
          verdict: "skip",
          note: "Not needed. Folds stay wet and mould in this climate. Changing storage on a bath is awkward.",
          compare: "Same idea as the local Alana Plus ($143). A simple hard tub + a dry changing mat + a basket is enough.",
          search: "Twinly Bubbly table à langer baignoire",
          asin: ""
        }
      ]
    },
    {
      group: "Health",
      icon: "🌡️",
      items: [
        {
          brand: "Chicco",
          title: "Baby boy manicure set (file, scissors, clippers, brush)",
          price: "€8.90",
          needed: "yes",
          verdict: "keep",
          note: "Cheap box is OK. Use the file now. Scissors later. Leave clippers in the box the first weeks.",
          compare: "Better than a 9-piece Babymoov kit. A glass baby file is nicer in humidity, but this will do.",
          search: "Chicco set manucure bébé garçon",
          asin: ""
        },
        {
          brand: "Thermoval",
          title: "Rapid electronic thermometer",
          price: "€9.20",
          needed: "yes",
          verdict: "keep",
          note: "The right fever thermometer. Medical, CE marked. One is enough.",
          compare: "Do not also buy the Babymoov kit thermometer. Rectal is the most reliable for a newborn.",
          search: "Thermoval rapid thermomètre",
          asin: "B00QFFC58O"
        },
        {
          brand: "Cooper",
          title: "Physiological serum 0.9%, 30 × 5 ml",
          price: "€2.59",
          needed: "yes",
          verdict: "keep",
          note: "Saline drops for nose (and eyes). More useful than a mouche-bébé at the start.",
          compare: "Keep. Pharmacy Gifrer/Gilbert 5 ml unidoses are the same job if cheaper locally.",
          search: "Cooper sérum physiologique 30 unidoses 5 ml",
          asin: ""
        },
        {
          brand: "Nivea",
          title: "Kids Protect & Play Sensitive SPF 50+ spray 200 ml",
          price: "€6.80",
          needed: "later",
          verdict: "later",
          note: "Right sunscreen: unscented, SPF 50+. From 6 months. Clothes and shade first for a newborn.",
          compare: "Keep this bottle for later. Do not spray the face.",
          search: "Nivea Kids Protect Play Sensitive SPF 50 200 ml",
          asin: ""
        }
      ]
    },
    {
      group: "Bags & organisers",
      icon: "🎒",
      items: [
        {
          brand: "KeaBabies",
          title: "Diaper bag backpack, dark olive",
          price: "€62.34",
          needed: "optional",
          verdict: "compare",
          note: "Fine backpack, but you only need one bag. Not urgent.",
          compare: "Dikaslon (~€43) does the same job cheaper and includes a changing mat. Leave HAMUR.",
          search: "KeaBabies diaper bag backpack",
          asin: ""
        },
        {
          brand: "HAMUR HOME",
          title: "Small 2-in-1 wipes / travel pouch",
          price: "€14.90",
          needed: "no",
          verdict: "skip",
          note: "Not needed. A cheap toiletry zip bag from a local shop is enough.",
          compare: "Skip. Do not buy this plus a full backpack.",
          search: "HAMUR HOME baby diaper bag pouch",
          asin: ""
        },
        {
          brand: "Dikaslon",
          title: "18-pocket changing backpack + mat",
          price: "€42.98",
          needed: "optional",
          verdict: "keep",
          note: "If you want a backpack, this is the cheaper of the two and includes a mat.",
          compare: "Pick Dikaslon or KeaBabies, not both. Can wait.",
          search: "Dikaslon baby changing bag 18 pocket",
          asin: ""
        }
      ]
    },
    {
      group: "Wipes, cotton & nappies",
      icon: "🧻",
      items: [
        {
          brand: "Huggies",
          title: "Pure sensitive wipes, 10 packs (560)",
          price: "See options",
          needed: "no",
          verdict: "skip",
          note: "Mega carton. Wipes dry out in Suriname humidity. Home first weeks: water + washcloth.",
          compare: "If any wipes: one small Pampers 99% water pack (48–60), not 560.",
          search: "Huggies Pure lingettes 560",
          asin: ""
        },
        {
          brand: "Pampers",
          title: "99% water wipes, 9 × 60 (540)",
          price: "€18.00",
          needed: "optional",
          verdict: "compare",
          note: "Right type of wipe (99% water). Wrong quantity before birth.",
          compare: "Keep the type, not this 540 count. Buy one small pack for outings.",
          search: "Pampers 99% eau lingettes 540",
          asin: ""
        },
        {
          brand: "Carryboo",
          title: "Organic cotton pads × 150",
          price: "€4.25",
          needed: "optional",
          verdict: "keep",
          note: "Cheap extra for changes if you want disposable cotton. Washcloths first.",
          compare: "150 is a sensible size. Skip a 450 pack.",
          search: "Carryboo coton 150 bio bébé",
          asin: ""
        },
        {
          brand: "Huggies",
          title: "Extra Care nappies size 1 (2–5 kg), 160",
          price: "€31.01 (€0.19)",
          needed: "yes",
          verdict: "keep",
          note: "Unscented Extra Care is the right kind. Size 1 to start. Better value than Harmony.",
          compare: "If you ship any: this, not Pampers Harmony at €0.33. Better still: a small size 1 in Paramaribo first — he may leave size 1 fast.",
          search: "Huggies Extra Care taille 1 160",
          asin: ""
        },
        {
          brand: "Pampers",
          title: "Harmony nappies size 1, 180",
          price: "€60.18 (€0.33)",
          needed: "no",
          verdict: "skip",
          note: "Also unscented and fine, but almost double the price per nappy.",
          compare: "Leave. Huggies Extra Care does the same job cheaper.",
          search: "Pampers Harmonie taille 1 180",
          asin: ""
        },
        {
          brand: "Ubbi",
          title: "Disposable diaper sacks, lavender, 200",
          price: "€7.99",
          needed: "no",
          verdict: "skip",
          note: "Not needed. Scented. A lidded bin at home is enough.",
          compare: "Skip Ubbi and Babyono.",
          search: "Ubbi diaper sacks 200 lavender",
          asin: ""
        },
        {
          brand: "Babyono",
          title: "Scented disposable diaper bags, 100",
          price: "€8.39",
          needed: "no",
          verdict: "skip",
          note: "Same as Ubbi, more expensive per bag, also scented.",
          compare: "Skip both nappy-sack brands.",
          search: "Babyono sacs à couches parfumés 100",
          asin: ""
        }
      ]
    },
    {
      group: "Sleep (bedside cribs)",
      icon: "🛏️",
      items: [
        {
          brand: "Kinderkraft",
          title: "Neste Up 2 co-sleeping cot",
          price: "€79.90",
          needed: "yes",
          verdict: "compare",
          note: "Budget bedside crib. Fine if you want to spend less. Room-share at least 6 months; stop cododo when he sits / ~9 kg.",
          compare: "Pick Neste Up 2 or Tori, not Iora. Tori is better in heat (mesh, folds smaller). Add a mosquito net.",
          search: "Kinderkraft Neste Up 2 cododo",
          asin: ""
        },
        {
          brand: "Maxi-Cosi",
          title: "Iora co-sleeping crib",
          price: "€132.90",
          needed: "no",
          verdict: "skip",
          note: "Bulkier, more storage under the bed that holds humidity. Extra money for little extra safety.",
          compare: "Leave Iora. Tori or Neste Up 2.",
          search: "Maxi-Cosi Iora cododo",
          asin: ""
        },
        {
          brand: "Maxi-Cosi",
          title: "Tori 2-in-1 co-sleeping crib",
          price: "€99.99",
          needed: "yes",
          verdict: "keep",
          note: "Preferred crib: compact fold, mesh, lighter. Better for Suriname storage and climate.",
          compare: "Keep Tori if you can. Neste Up 2 if money is tight. One crib only. Need a mosquito net.",
          search: "Maxi-Cosi Tori cododo",
          asin: ""
        }
      ]
    },
    {
      group: "Dummies & bottles",
      icon: "😋",
      items: [
        {
          brand: "Philips Avent",
          title: "Soothie pacifiers, pack of 2, 0–6 months",
          price: "€9.90",
          needed: "optional",
          verdict: "keep",
          note: "Hospital-style one-piece dummy. Start here. Not everyone needs a dummy.",
          compare: "Soothie first. Ultra Soft is plan B if he refuses these. Clip: short, breakaway, awake only — Soothie has no ring.",
          search: "Philips Avent Soothie 0-6 mois lot de 2",
          asin: ""
        },
        {
          brand: "Philips Avent",
          title: "Ultra Soft pacifiers, pack of 4, 0–6 months",
          price: "€14.99",
          needed: "no",
          verdict: "later",
          note: "Softer collar, extra dummies. Do not buy with Soothie on day one.",
          compare: "Wait. Buy only if Soothie does not work.",
          search: "Philips Avent Ultra Soft 0-6 mois lot de 4",
          asin: ""
        },
        {
          brand: "Philips Avent",
          title: "Newborn bottle kit, Natural Response + AirFree + brush",
          price: "€27.29",
          needed: "yes",
          verdict: "keep",
          note: "Right brand. Breast first; bottles are backup. You only need 2 × 125 ml and the brush. Start débit 1. No sterilizer — boil ~5 min.",
          compare: "Keep the kit for value, store extra bottles. Do not add a drying rack.",
          search: "Philips Avent kit biberons Réponse Naturelle AirFree nouveau-né",
          asin: ""
        }
      ]
    },
    {
      group: "Feeding pillow",
      icon: "🛋️",
      items: [
        {
          brand: "Chicco Boppy",
          title: "Deluxe nursing pillow, Fish Fun",
          price: "€39.99",
          needed: "optional",
          verdict: "later",
          note: "Helps your arms while feeding. A rolled towel works at the start.",
          compare: "Optional. If it has a nest mode: awake and watching only, never for sleep.",
          search: "Chicco Boppy coussin d'allaitement",
          asin: ""
        }
      ]
    },
    {
      group: "Stroller",
      icon: "🚗",
      items: [
        {
          brand: "Maxi-Cosi",
          title: "Zelia S Trio 3-in-1 (includes CabrioFix S car seat)",
          price: "€359.99",
          needed: "optional",
          verdict: "later",
          note: "Zelia S is a good town stroller, but this trio adds a second infant seat. You already have a car seat.",
          compare: "Do not buy the trio until you send the link of the seat you have. Prefer the stroller without a second 0+ seat.",
          search: "Maxi-Cosi Zelia S Trio CabrioFix S",
          asin: "B09KS5HT2R"
        }
      ]
    }
  ]
};

window.MISSING = {
  mom: [
    "Washable cotton nursing pads (10–14) + one small disposable pack (Avent 60) for hospital/outings",
    "You already have blue absorbent mats for bed/sofa — no Amazon mattress protector",
    "Body wash: Dove Sensitive or Neutral 0% at the supermarket (not Lipikar)",
    "Nursing bras and nightshirts — buy locally",
    "Optional: cold pack for the perineum (ice in a cloth), not soap"
  ],
  baby: [
    "Mustela Gel Lavant Bio sans parfum 400 ml pump (not Stelatopia)",
    "Nappy cream: Eryplast or Sudocrem",
    "One small Pampers 99% water pack (48–60), not 540",
    "Mosquito net for the bedside crib",
    "Hydrofiel / washcloths 8–10, sleep sack TOG 0.5, tight crib sheets",
    "Some 50/56 clothes — you buy clothes outside",
    "Send the car seat link before any stroller"
  ]
};
