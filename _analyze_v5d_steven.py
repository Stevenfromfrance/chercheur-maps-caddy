"""Parse V5d Steven logs -> stats + JSON for github pages viewer."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_JSON = ROOT / "logs-v5d-steven" / "data.json"
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)

LOGS = [
    {
        "id": "ville",
        "label": "VILLE",
        "file": r"C:\Ross-Tech\VCDS\Logs\LOGVILLECADDYSTEVEN",
        "goal": "Warm-up froid→~90°C + conduite ville (rail/MAP/TQI stables, pas de défaut).",
    },
    {
        "id": "route_rail",
        "label": "ROUTE_RAIL",
        "file": r"C:\Ross-Tech\VCDS\Logs\LOGROUTERAILSTEVEN",
        "goal": "Pulls 3/4 · couple ~320–340 · rail sp~1620 bar · réel ≤~1670.",
    },
    {
        "id": "route_rail2",
        "label": "ROUTE_RAIL2",
        "file": r"C:\Ross-Tech\VCDS\Logs\LOGROUTERAIL2STEVEN",
        "goal": "2e pull plus poussé · même cibles rail/couple + RPM haut.",
    },
    {
        "id": "hardcut",
        "label": "HARDCUT",
        "file": r"C:\Ross-Tech\VCDS\Logs\LOGHARDCUTSTEVEN",
        "goal": "Coupe ~4800 rpm (V5d hardcut inchangé) sous WOT après push 2/3.",
    },
    {
        "id": "route_inj",
        "label": "ROUTE_INJ",
        "file": r"C:\Ross-Tech\VCDS\Logs\LOGROUTEINJSTEVEN",
        "goal": "Pulls 2/3/4 · FCO + air mass + couple sous charge.",
    },
    {
        "id": "launch_asr_off",
        "label": "LAUNCH ASR OFF",
        "file": r"C:\Ross-Tech\VCDS\Logs\LOGLAUNCHSTEVEN",
        "goal": "Hold ~2700–3000 · TQI_SP ~100–120 Nm (V5d 110/85) · puis départ.",
    },
    {
        "id": "launch_asr_on",
        "label": "LAUNCH ASR ON",
        "file": r"C:\Ross-Tech\VCDS\Logs\LOGLAUNCH2STEVEN",
        "goal": "Même départ avec ASR · comparer coupe couple / patinage.",
    },
]

IDE_META = [
    {"key": "rpm", "ide": "IDE00021", "name": "Engine RPM", "unit": "/min"},
    {"key": "cool", "ide": "IDE00025", "name": "Coolant temperature", "unit": "°C"},
    {"key": "spd", "ide": "IDE00075", "name": "Vehicle speed", "unit": "km/h"},
    {"key": "ped", "ide": "IDE00086", "name": "Accelerator pedal position", "unit": "%"},
    {"key": "tq", "ide": "IDE00100", "name": "Engine torque-TQI_SP", "unit": "Nm"},
    {"key": "fup_a", "ide": "IDE00188", "name": "Fuel high-pressure: actual value-FUP_FIL", "unit": "MPa"},
    {"key": "map_sp", "ide": "IDE00190", "name": "Charge air pressure: specified value-MAP_SP_MMV", "unit": "hPa"},
    {"key": "map_act", "ide": "IDE00191", "name": "Charge air pressure: actual value-MAP_MMV", "unit": "hPa"},
    {"key": "fup_sp", "ide": "IDE00201", "name": "High fuel pressure: specified value-FUP_SP_KPA", "unit": "MPa"},
    {"key": "air", "ide": "IDE00347", "name": "Air mass: actual value:", "unit": "g/s"},
    {"key": "fco", "ide": "IDE00371", "name": "Fuel consumption-FCO_T", "unit": "ml/s"},
]


def parse(path: Path) -> tuple[dict, list[dict]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    meta = {
        "header": lines[0] if lines else "",
        "ecu": lines[1] if len(lines) > 1 else "",
        "source": path.name,
    }
    header_idx = None
    for i, line in enumerate(lines):
        if "Engine RPM" in line and "STAMP" in line:
            header_idx = i
            break
    if header_idx is None:
        return meta, []

    has_fco = "Fuel consumption" in lines[header_idx]
    rows: list[dict] = []
    for line in lines[header_idx + 2 :]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 21:
            continue
        try:
            # Marker, (TIME,VAL)*N  — each channel has its own stamp
            # Use RPM stamp as primary time axis
            r = {
                "t": float(parts[1]),
                "rpm": float(parts[2]),
                "cool": float(parts[4]),
                "spd": float(parts[6]),
                "ped": float(parts[8]),
                "tq": float(parts[10]),
                "fup_a": float(parts[12]),
                "map_sp": float(parts[14]),
                "map_act": float(parts[16]),
                "fup_sp": float(parts[18]) / 1000.0,  # kPa -> MPa
                "air": float(parts[20]),
            }
            if has_fco and len(parts) >= 23 and parts[22] not in ("",):
                r["fco"] = float(parts[22])
            rows.append(r)
        except ValueError:
            continue
    return meta, rows


def series(rows: list[dict], key: str) -> dict:
    xs, ys = [], []
    for r in rows:
        if key not in r:
            continue
        xs.append(round(r["t"], 3))
        ys.append(round(r[key], 3))
    return {"t": xs, "v": ys}


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {}
    def mx(k):
        return max(r[k] for r in rows if k in r)

    def mn(k):
        return min(r[k] for r in rows if k in r)

    wot = [r for r in rows if r["ped"] >= 70]
    hardcuts = []
    for i in range(1, len(rows)):
        p, c = rows[i - 1], rows[i]
        if p["rpm"] >= 4200 and (p["rpm"] - c["rpm"]) > 800 and p["ped"] >= 40:
            hardcuts.append(
                {
                    "t": round(p["t"], 2),
                    "rpm_from": round(p["rpm"]),
                    "rpm_to": round(c["rpm"]),
                    "ped": p["ped"],
                    "tq_from": round(p["tq"], 1),
                    "tq_to": round(c["tq"], 1),
                }
            )

    launch = [
        r
        for r in rows
        if r["spd"] <= 3 and r["rpm"] >= 2400 and r["rpm"] <= 3400
    ]

    out = {
        "n": len(rows),
        "duration_s": round(rows[-1]["t"] - rows[0]["t"], 1),
        "cool_min": round(mn("cool"), 1),
        "cool_max": round(mx("cool"), 1),
        "rpm_max": round(mx("rpm")),
        "spd_max": round(mx("spd")),
        "ped_max": round(mx("ped"), 1),
        "tq_max": round(mx("tq"), 1),
        "map_act_max": round(mx("map_act")),
        "map_sp_max": round(mx("map_sp")),
        "map_act_bar_rel": round((mx("map_act") - 1013) / 1000, 2),
        "fup_a_max": round(mx("fup_a"), 1),
        "fup_a_bar": round(mx("fup_a") * 10),
        "fup_sp_max": round(mx("fup_sp"), 1),
        "air_max": round(mx("air"), 1),
        "wot_n": len(wot),
        "hardcuts": hardcuts,
        "launch_hold_pts": len(launch),
    }
    if wot:
        rail_err = [abs(r["fup_a"] - r["fup_sp"]) for r in wot]
        map_lag = [r["map_sp"] - r["map_act"] for r in wot]
        out["wot_tq_max"] = round(max(r["tq"] for r in wot), 1)
        out["wot_rpm_min"] = round(min(r["rpm"] for r in wot))
        out["wot_rpm_max"] = round(max(r["rpm"] for r in wot))
        out["wot_rail_err_max_mpa"] = round(max(rail_err), 2)
        out["wot_rail_err_mean_mpa"] = round(statistics.mean(rail_err), 2)
        out["wot_map_lag_max_hpa"] = round(max(map_lag))
        out["wot_map_lag_mean_hpa"] = round(statistics.mean(map_lag))
        out["wot_tq_ge_300"] = sum(1 for r in wot if r["tq"] >= 300)
        top = sorted(wot, key=lambda r: -r["tq"])[:5]
        out["wot_top"] = [
            {
                "t": round(r["t"], 1),
                "rpm": round(r["rpm"]),
                "spd": round(r["spd"]),
                "ped": r["ped"],
                "tq": round(r["tq"], 1),
                "map_act": round(r["map_act"]),
                "map_sp": round(r["map_sp"]),
                "fup_a": round(r["fup_a"], 1),
                "fup_sp": round(r["fup_sp"], 1),
            }
            for r in top
        ]
    if launch:
        out["launch_samples"] = [
            {
                "t": round(r["t"], 1),
                "rpm": round(r["rpm"]),
                "ped": r["ped"],
                "tq": round(r["tq"], 1),
                "spd": r["spd"],
                "map_act": round(r["map_act"]),
                "map_sp": round(r["map_sp"]),
                "fup_a": round(r["fup_a"], 1),
            }
            for r in launch
        ]
    return out


def main():
    payload = {
        "vehicle": "Caddy CAYE · 03L906023TB · soft 9979",
        "carto": "V5d · tegtORI + launch110 (base V5b tqlim370)",
        "date": "2026-09-12",
        "ides": IDE_META,
        "targets": {
            "tq_wot": "320–340 Nm (TQI_SP)",
            "rail_sp": "~162 MPa (~1620 bar)",
            "rail_act": "≤ ~167 MPa sous WOT",
            "map": "suivi MAP_SP vs MAP_ACT, lag raisonnable",
            "hardcut": "~4800 rpm",
            "launch_hold": "TQI_SP ~100–120 Nm @2700–3000 (ASR OFF, pied à fond)",
        },
        "verdict": {
            "summary": "Stage1 V5d validé sur couple / rail / MAP / hardcut. Launch hold 110 Nm non prouvé (pédale trop basse au hold).",
            "grade": "GO Stage1 daily — relaunch DEPART propre pour valider le hold",
            "ok": [
                {
                    "title": "Couple WOT dans la cible",
                    "detail": "TQI_SP max 334–338 Nm sur ROUTE_RAIL / RAIL2 / INJ / HARDCUT — pile dans 320–340 (tqlim 370 + stack V5).",
                },
                {
                    "title": "Rail suit sous charge stable",
                    "detail": "Sous WOT à couple ≥300 : réel ≈ consigne (ex. 162.4 vs 162.0 MPa @3832). Pics réel ~165–167 MPa, plafond OK.",
                },
                {
                    "title": "Turbo / MAP",
                    "detail": "MAP act max ~2606 hPa (~1.59 bar rel) sur RAIL1 ; suivi SP/ACT correct hors tip-in. Air mass max ~108–111 g/s.",
                },
                {
                    "title": "Hardcut ~4800",
                    "detail": "Deux coupes visibles 4754→2999 et 4785→2944 sous pédale haute — cohérent avec hardcut 4800 inchangé en V5d.",
                },
                {
                    "title": "VILLE warm-up",
                    "detail": "38→88°C en ~10 min, conduite partiels (ped max 64%), pas de comportement on/off. Rail/MAP calmes.",
                },
            ],
            "ko": [
                {
                    "title": "Launch hold non validé",
                    "detail": "ASR OFF : au hold ~2800 rpm la pédale est à 17–32% (pas plein gaz). TQI~100 Nm @2878 ressemble au hold mais ce n’est pas un DEPART procédure. ASR ON : couple encore plus coupé (tq 9–36 Nm à spd=0).",
                },
                {
                    "title": "Échantillonnage route trop lent",
                    "detail": "ROUTE/HARDCUT/LAUNCH : ~2 s entre points (8–19 lignes). Les pics et le cut exact sont flous. Réduire les canaux ou log plus court.",
                },
                {
                    "title": "Erreurs rail « fausses » en tip-in",
                    "detail": "Sur changements de rapport, FUP_SP chute (ex. 66 MPa) alors que FUP_FIL reste haut — artefact de stamp / transition, pas un défaut Stage1.",
                },
            ],
            "next": [
                "Refaire 1× DEPART (log-aide DEPART) : ASR OFF, 1ʳᵉ, frein à main, hold ~2800 plein gaz 2–3 s puis départ.",
                "Cible hold : TQI_SP ~100–120 Nm, MAP qui monte, speed=0 pendant le hold.",
                "Option : 1 pull ROUTE_RAIL plus long (même 3ᵉ/4ᵉ) avec moins de canaux pour densifier le CSV.",
            ],
            "per_log": {
                "ville": {"status": "ok", "note": "Warm-up + ville OK. Pas de WOT — normal."},
                "route_rail": {"status": "ok", "note": "Pull propre : 338 Nm, rail 162 MPa, MAP 1.59 bar."},
                "route_rail2": {"status": "ok", "note": "334 Nm, RPM 4698, rail max 167 MPa. OK."},
                "hardcut": {"status": "ok", "note": "Cut ~4750–4785 confirmé ×2 + couple 333 Nm avant."},
                "route_inj": {"status": "ok", "note": "333 Nm, air 109 g/s, FCO présent. Court mais lisible."},
                "launch_asr_off": {"status": "ko", "note": "Pas de pied à fond au hold — relaunch."},
                "launch_asr_on": {"status": "warn", "note": "Utile en comparaison ASR, pas pour valider hold 110."},
            },
        },
        "logs": [],
    }

    csv_names = {
        "ville": "LOGVILLECADDYSTEVEN.csv",
        "route_rail": "LOGROUTERAILSTEVEN.csv",
        "route_rail2": "LOGROUTERAIL2STEVEN.csv",
        "hardcut": "LOGHARDCUTSTEVEN.csv",
        "route_inj": "LOGROUTEINJSTEVEN.csv",
        "launch_asr_off": "LOGLAUNCHSTEVEN.csv",
        "launch_asr_on": "LOGLAUNCH2STEVEN.csv",
    }

    for spec in LOGS:
        path = Path(spec["file"])
        meta, rows = parse(path)
        stats = summarize(rows)
        print("=" * 72)
        print(spec["label"], path.name)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        entry = {
            **{k: v for k, v in spec.items() if k != "file"},
            "csv": "csv/" + csv_names[spec["id"]],
            "meta": meta,
            "stats": stats,
            "series": {m["key"]: series(rows, m["key"]) for m in IDE_META},
        }
        # drop empty series
        entry["series"] = {k: v for k, v in entry["series"].items() if v["t"]}
        payload["logs"].append(entry)

    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print("Wrote", OUT_JSON, "bytes", OUT_JSON.stat().st_size)


if __name__ == "__main__":
    main()
