# -*- coding: utf-8 -*-
"""Import + analyse logs V5f soirée → logs-v5f/data.json + copie CSV.

  python tools/import_v5f_logs.py
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

SRC = Path(r"c:\Ross-Tech\VCDS\Logs")
REPO = Path(r"C:\Users\theda\OneDrive\Bureau\chercheur-maps-caddy")
OUT = REPO / "logs-v5f"
CSV_DIR = OUT / "csv"

LOGS = [
    ("ville", "LOGVILLE", "VILLE", "Tip-in / ville (sans clim ?)"),
    ("ville_clim", "LOGVILLECLIM", "VILLE CLIM", "Ville avec clim"),
    ("route_1_3", "LOGROUTESOFT13IEMEVITESSE", "ROUTE 1/3", "ROUTE_SOFT 1ʳᵉ/3ᵉ WOT"),
    ("route_2_4", "LOGROUTESOFT24IEMEVITESSE", "ROUTE 2/4", "ROUTE_SOFT 2ᵉ/4ᵉ WOT"),
    ("depart", "LOGLAUCHC1", "DEPART", "Launch hold @~2800"),
    ("hardcut", "LOGHARCUT", "HARDCUT", "Coupe ~4800"),
    ("clim", "LOGCLIM", "CLIM", "Essai clim (court)"),
    ("a100", "LOG-0A100", "0–100", "Accélération 0–100"),
    ("a100_noclim", "LOG0A100SANSCLIM", "0–100 SANS CLIM", "0–100 sans clim"),
    ("misc", "LOG-01-IDE00021_&3.CSV", "MISC court", "Très court / test"),
]

# stamp,col pairs after Marker
IDE_MAP = {
    "Engine RPM": ("rpm", "/min"),
    "Vehicle speed": ("spd", "km/h"),
    "Accelerator pedal position": ("ped", "%"),
    "Engine torque-TQI_SP": ("tq", "Nm"),
    "Charge air pressure: specified value-MAP_SP_MMV": ("map_sp", "hPa"),
    "Charge air pressure: actual value-MAP_MMV": ("map_act", "hPa"),
    "Fuel high-pressure: actual value-FUP_FIL": ("fup_a", "MPa"),
    "High fuel pressure: specified value-FUP_SP_KPA": ("fup_sp", "kPa"),
    "Air mass: actual value:": ("air", "g/s"),
    "Coolant temperature": ("cool", "°C"),
}


def parse_csv(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    header = lines[0] if lines else ""
    ecu = lines[1] if len(lines) > 1 else ""
    # find STAMP row
    stamp_i = None
    for i, ln in enumerate(lines):
        if ln.startswith(",STAMP") or ln.startswith("Marker") and i + 1 < len(lines) and "STAMP" in lines[i + 1]:
            if ln.startswith(",STAMP"):
                stamp_i = i
                break
            stamp_i = i + 1
            break
    if stamp_i is None:
        for i, ln in enumerate(lines):
            if "STAMP" in ln and "Engine RPM" in ln:
                stamp_i = i
                break
    if stamp_i is None:
        return {"error": "no stamp", "rows": [], "keys": []}

    stamp_cols = [c.strip() for c in lines[stamp_i].split(",")]
    # pairs: col1=STAMP name? actually: empty, STAMP, Engine RPM, STAMP, Vehicle...
    # indices: 1=t0, 2=rpm, 3=t1, 4=spd, ...
    channels = []
    j = 1
    while j + 1 < len(stamp_cols):
        name = stamp_cols[j + 1]
        if name and name != "STAMP":
            key = None
            for label, (k, _u) in IDE_MAP.items():
                if name.startswith(label) or label in name:
                    key = k
                    break
            if key is None:
                # shorten
                key = name.split("-")[0][:12].lower().replace(" ", "_")
            channels.append((j, j + 1, key, name))
        j += 2

    rows = []
    for ln in lines[stamp_i + 1 :]:
        if not ln.strip() or ln.startswith("Marker"):
            continue
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) < 3:
            continue
        rec = {}
        t_vals = []
        ok = False
        for t_i, v_i, key, _name in channels:
            if v_i >= len(parts) or t_i >= len(parts):
                continue
            try:
                t = float(parts[t_i]) if parts[t_i] else None
                v = float(parts[v_i]) if parts[v_i] else None
            except ValueError:
                continue
            if t is None or v is None:
                continue
            t_vals.append(t)
            rec[key] = v
            ok = True
        if not ok:
            continue
        rec["t"] = t_vals[0] if t_vals else 0.0
        rows.append(rec)

    keys = sorted({k for r in rows for k in r if k != "t"})
    return {
        "header": header,
        "ecu": ecu,
        "channels": [{"key": k, "name": n} for _, _, k, n in channels],
        "keys": keys,
        "rows": rows,
        "n": len(rows),
        "duration_s": round(rows[-1]["t"] - rows[0]["t"], 2) if len(rows) > 1 else 0.0,
        "dt_med": _median_dt(rows),
    }


def _median_dt(rows: list) -> float | None:
    if len(rows) < 3:
        return None
    dts = [rows[i]["t"] - rows[i - 1]["t"] for i in range(1, len(rows))]
    dts = [d for d in dts if d > 0]
    if not dts:
        return None
    dts.sort()
    return round(dts[len(dts) // 2], 3)


def series_of(rows: list, key: str) -> dict | None:
    pts = [(r["t"], r[key]) for r in rows if key in r]
    if not pts:
        return None
    return {"t": [p[0] for p in pts], "v": [p[1] for p in pts]}


def stats_of(rows: list) -> dict:
    def mx(k):
        vs = [r[k] for r in rows if k in r]
        return max(vs) if vs else None

    def mn(k):
        vs = [r[k] for r in rows if k in r]
        return min(vs) if vs else None

    s = {
        "n": len(rows),
        "rpm_max": mx("rpm"),
        "spd_max": mx("spd"),
        "ped_max": mx("ped"),
        "tq_max": mx("tq"),
        "map_act_max": mx("map_act"),
        "map_sp_max": mx("map_sp"),
        "cool_min": mn("cool"),
        "cool_max": mx("cool"),
    }
    wot = [r for r in rows if r.get("ped", 0) >= 70]
    s["wot_n"] = len(wot)
    if wot:
        s["wot_tq_max"] = max(r.get("tq", 0) for r in wot)
        s["wot_rpm_min"] = min(r["rpm"] for r in wot if "rpm" in r)
        s["wot_rpm_max"] = max(r["rpm"] for r in wot if "rpm" in r)
        # soft samples same-ish gear: ped high, rpm rising band
        soft = []
        for r in wot:
            if r.get("tq") is None or r.get("rpm") is None:
                continue
            if r["rpm"] >= 3600:
                soft.append(
                    {
                        "t": round(r["t"], 2),
                        "rpm": round(r["rpm"]),
                        "spd": r.get("spd"),
                        "ped": round(r.get("ped", 0), 1),
                        "tq": round(r["tq"], 1),
                        "map_sp": r.get("map_sp"),
                        "map_act": r.get("map_act"),
                    }
                )
        soft.sort(key=lambda x: x["rpm"])
        s["wot_hi_rpm"] = soft[:12]
        # midband
        mid = [
            r
            for r in wot
            if 2200 <= r.get("rpm", 0) <= 3400 and r.get("tq") is not None
        ]
        if mid:
            s["wot_mid_tq_max"] = round(max(r["tq"] for r in mid), 1)
            s["wot_mid_tq_mean"] = round(sum(r["tq"] for r in mid) / len(mid), 1)
    # launch hold
    holds = [
        r
        for r in rows
        if r.get("spd", 99) <= 2
        and r.get("rpm", 0) >= 2400
        and r.get("ped", 0) >= 60
    ]
    s["launch_hold_n"] = len(holds)
    if holds:
        s["launch_samples"] = [
            {
                "t": round(r["t"], 2),
                "rpm": round(r.get("rpm", 0)),
                "ped": round(r.get("ped", 0), 1),
                "tq": round(r.get("tq", 0), 1),
                "spd": r.get("spd"),
                "map_act": r.get("map_act"),
            }
            for r in holds[:8]
        ]
    # hardcuts: rpm drop >800 while ped high
    cuts = []
    for i in range(1, len(rows)):
        a, b = rows[i - 1], rows[i]
        if a.get("ped", 0) < 60 or b.get("ped", 0) < 50:
            continue
        if "rpm" not in a or "rpm" not in b:
            continue
        if a["rpm"] >= 4500 and b["rpm"] <= a["rpm"] - 800:
            cuts.append(
                {
                    "t": round(b["t"], 2),
                    "rpm_from": round(a["rpm"]),
                    "rpm_to": round(b["rpm"]),
                    "tq_from": round(a.get("tq", 0), 1),
                    "tq_to": round(b.get("tq", 0), 1),
                    "ped": round(b.get("ped", 0), 1),
                }
            )
    s["hardcuts"] = cuts
    return s


def analyze_verdict(logs: list) -> dict:
    ok, ko, nexts = [], [], []
    # sample rate
    dts = [L["dt_med"] for L in logs if L.get("dt_med")]
    if dts and min(dts) < 0.6:
        ok.append(
            {
                "title": "Fréquence VCDS améliorée",
                "detail": f"Δt médian ~{min(dts):.2f}–{max(dts):.2f} s (vs ~2 s sur V5d Steven). Moins d’IDE = mieux.",
            }
        )
    else:
        ko.append(
            {
                "title": "Échantillonnage encore lent",
                "detail": f"Δt médian {dts} — vérifier Blk Int / Group UDS / nb IDE.",
            }
        )

    route = [L for L in logs if L["id"].startswith("route")]
    hi_ok = False
    mid_ok = False
    for L in route:
        st = L["stats"]
        hi = st.get("wot_hi_rpm") or []
        if hi:
            tqs = [p["tq"] for p in hi]
            # compare plateau mid vs 3800+
            if st.get("wot_mid_tq_max") and tqs:
                mid = st["wot_mid_tq_max"]
                hi_mean = sum(tqs) / len(tqs)
                if hi_mean >= mid * 0.75 or max(tqs) >= 280:
                    hi_ok = True
                if mid >= 300:
                    mid_ok = True
        if st.get("wot_tq_max") and st["wot_tq_max"] >= 300:
            mid_ok = True

    if mid_ok:
        ok.append(
            {
                "title": "Couple mid / WOT présent",
                "detail": "TQI WOT midband ≥ ~300 Nm sur au moins un pull ROUTE — Stage1 couple OK.",
            }
        )
    else:
        ko.append(
            {
                "title": "Couple mid peu visible",
                "detail": "Pas de plateau WOT ≥300 Nm clair — vérifier pulls / pédale.",
            }
        )

    if hi_ok:
        ok.append(
            {
                "title": "Haut régime allonge mieux qu’avant",
                "detail": "Points WOT ≥3600 avec TQI encore utile (vs soft V5d ~214–255). tqlim V6f + AccPed fill crédibles.",
            }
        )
    else:
        ko.append(
            {
                "title": "Haut régime encore à confirmer",
                "detail": "Peu de points WOT ≥3600 exploitables — ou TQI encore bas.",
            }
        )

    # MAP tracking on route
    map_notes = []
    for L in route:
        rows = L["rows"]
        wot = [r for r in rows if r.get("ped", 0) >= 70 and "map_sp" in r and "map_act" in r]
        if not wot:
            continue
        lags = [abs(r["map_sp"] - r["map_act"]) for r in wot]
        map_notes.append((L["id"], max(lags), sum(lags) / len(lags)))
    if map_notes:
        worst = max(map_notes, key=lambda x: x[1])
        if worst[1] > 300:
            ko.append(
                {
                    "title": "MAP parfois décroche",
                    "detail": f"Écart SP/ACT max ~{worst[1]:.0f} hPa sur {worst[0]} — possible lien fumée / air.",
                }
            )
            nexts.append("Si fumée @3600–4000 + MAP_ACT << MAP_SP → peaufiner smoke/air, pas tegt d’abord.")
        else:
            ok.append(
                {
                    "title": "MAP suit sous WOT",
                    "detail": f"Écart SP/ACT raisonnable (max ~{worst[1]:.0f} hPa).",
                }
            )

    # launch
    dep = next((L for L in logs if L["id"] == "depart"), None)
    if dep:
        hs = dep["stats"].get("launch_samples") or []
        if hs:
            tqs = [h["tq"] for h in hs]
            peds = [h["ped"] for h in hs]
            if max(peds) >= 70 and max(tqs) < 40:
                ok.append(
                    {
                        "title": "Launch 0 Nm validé au hold",
                        "detail": f"Hold pédale haute, TQI ~{min(tqs):.0f}–{max(tqs):.0f} Nm @~2800 — cohérent V5f launch 0.",
                    }
                )
            elif max(peds) < 60:
                ko.append(
                    {
                        "title": "Launch : pédale pas assez à fond au hold",
                        "detail": "Comme V5d — refaire DEPART procédure stricte.",
                    }
                )
            else:
                ok.append(
                    {
                        "title": "Launch logué",
                        "detail": f"Hold samples TQI={tqs} ped={peds} — à croiser ressenti lag.",
                    }
                )
        else:
            ko.append(
                {
                    "title": "Launch hold non isolé",
                    "detail": "Pas de point spd≈0 + rpm≥2400 + ped haute clair.",
                }
            )

    # hardcut
    hc = next((L for L in logs if L["id"] == "hardcut"), None)
    if hc and hc["stats"].get("hardcuts"):
        ok.append(
            {
                "title": "Hardcut ~4800 OK",
                "detail": f"Coupes vues : {hc['stats']['hardcuts']}",
            }
        )
    elif hc:
        ko.append(
            {
                "title": "Hardcut non clair dans le CSV",
                "detail": "RPM max=" + str(hc["stats"].get("rpm_max")),
            }
        )

    # ville soft tip-in — qualitative: low ped variance of tq spikes
    ville = next((L for L in logs if L["id"] == "ville"), None)
    if ville and ville["stats"].get("ped_max", 100) < 70:
        ok.append(
            {
                "title": "VILLE partiels (pas WOT)",
                "detail": f"Ped max {ville['stats']['ped_max']}% — adapté tip-in. Ressenti soft confirmé par toi.",
            }
        )

    nexts.extend(
        [
            "Garder AccPed soft + tqlim V6f + tegt320 si ressenti OK.",
            "Fumée visible : 1 log ROUTE dense MAP+TQI ; si MAP suit → smoke prudent, pas +tegt.",
            "Mid « moins de punch » : souvent habitude ; si CSV mid ≥300 Nm → polish AccPed hold seulement.",
            "Launch lag au lâcher net : normal en 0 Nm — option V5g spool 90–110 si tu veux sprint.",
        ]
    )

    grade = "GO Stage1 daily V5f — peaufinage optionnel (fumée / mid / launch spool)"
    if len([k for k in ko if "Haut" in k["title"] or "Couple mid" in k["title"]]) >= 2:
        grade = "À retravailler — manque preuves couple mid/haut"

    return {
        "summary": "Validation V5f soirée (peu d’IDE). Voir OK/KO ci-dessous.",
        "grade": grade,
        "ok": ok,
        "ko": ko,
        "next": nexts,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    packed = []
    for lid, fname, label, goal in LOGS:
        src = SRC / fname
        if not src.exists():
            print("MISSING", src)
            continue
        dest_name = fname if fname.lower().endswith(".csv") else fname + ".csv"
        dest = CSV_DIR / dest_name
        shutil.copy2(src, dest)
        parsed = parse_csv(dest)
        if parsed.get("error") or not parsed["rows"]:
            print("FAIL parse", fname, parsed.get("error"), "n", parsed.get("n"))
            continue
        st = stats_of(parsed["rows"])
        st["duration_s"] = parsed["duration_s"]
        st["dt_med"] = parsed["dt_med"]
        series = {}
        for k in ("rpm", "spd", "ped", "tq", "map_sp", "map_act", "cool", "fup_a", "air"):
            s = series_of(parsed["rows"], k)
            if s:
                series[k] = s
        entry = {
            "id": lid,
            "label": label,
            "goal": goal,
            "csv": f"csv/{dest_name}",
            "meta": {
                "header": parsed["header"][:180],
                "ecu": parsed["ecu"][:80],
                "source": fname,
                "channels": parsed["channels"],
            },
            "stats": st,
            "series": series,
            "dt_med": parsed["dt_med"],
            "rows": parsed["rows"],  # temp for verdict; strip later
        }
        packed.append(entry)
        print(
            f"{lid}: n={st['n']} dt={st['dt_med']} tq_max={st.get('tq_max')} "
            f"rpm_max={st.get('rpm_max')} wot={st.get('wot_n')} hi={len(st.get('wot_hi_rpm') or [])}"
        )

    verdict = analyze_verdict(packed)
    # strip heavy rows from JSON
    for e in packed:
        e.pop("rows", None)

    per_log = {}
    for e in packed:
        st = e["stats"]
        status = "ok"
        note = f"n={st['n']} · Δt≈{st.get('dt_med')}s · TQI max {st.get('tq_max')}"
        if e["id"] == "depart":
            if st.get("launch_hold_n", 0) == 0:
                status = "warn"
                note += " · hold à vérifier"
            else:
                note += f" · hold pts={st['launch_hold_n']}"
        if e["id"] == "hardcut" and not st.get("hardcuts"):
            status = "warn"
            note += " · cut flou"
        if e["id"].startswith("route") and (st.get("wot_tq_max") or 0) < 280:
            status = "warn"
        per_log[e["id"]] = {"status": status, "note": note}

    verdict["per_log"] = per_log

    data = {
        "vehicle": "Caddy CAYE · 03L906023TB · soft 9979",
        "carto": "V5f FINAL · launch0 + tqlimV6f + AccPedV6e + tegt~320",
        "date": "2026-09-13",
        "session": "soir · feeling jour + logs soir",
        "ides": [
            {"key": "rpm", "ide": "IDE00021", "name": "Engine RPM", "unit": "/min"},
            {"key": "spd", "ide": "IDE00075", "name": "Vehicle speed", "unit": "km/h"},
            {"key": "ped", "ide": "IDE00086", "name": "Accelerator pedal position", "unit": "%"},
            {"key": "tq", "ide": "IDE00100", "name": "Engine torque-TQI_SP", "unit": "Nm"},
            {"key": "map_sp", "ide": "IDE00190", "name": "MAP_SP_MMV", "unit": "hPa"},
            {"key": "map_act", "ide": "IDE00191", "name": "MAP_MMV", "unit": "hPa"},
        ],
        "targets": {
            "ville": "tip-in doux 0–30%",
            "route": "TQI tient mieux 3800→4200 vs V5d",
            "depart": "hold TQI≈0 @~2800",
            "hardcut": "~4800",
            "tegt": "moins bridé à chaud que ORI 290 (cible ~320)",
        },
        "verdict": verdict,
        "logs": packed,
    }
    (OUT / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Wrote", OUT / "data.json")
    print("GRADE:", verdict["grade"])
    for x in verdict["ok"]:
        print(" OK", x["title"])
    for x in verdict["ko"]:
        print(" KO", x["title"])


if __name__ == "__main__":
    main()
