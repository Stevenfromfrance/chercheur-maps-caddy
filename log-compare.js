/* Log Analyser / Comparator — SAVAGESEAR atelier VCDS */
(function () {
  'use strict';

  const DEMO_URL = 'vcds_v2_compare.json';
  const LS_HIST = 'chercheur-log-compare-hist-caddy9979';
  const LS_SLOT = 'chercheur-log-compare-slots-caddy9979';
  const HARDCUT_RPM = 4800;
  const ACE_RAIL_BAR = 1656;
  const ACE_TQ = 380;
  const ACE_MAP = 2650;

  const COL_A = '#f5c542';
  const COL_B = '#e23a1a';
  const COL_MUTED = 'rgba(163,158,150,0.55)';
  const COL_GRID = 'rgba(46,41,38,0.9)';
  const COL_OK = '#3ecf7a';
  const COL_BAD = '#ff5c5c';

  const VCDS_KEYS = [
    { id: 'boost_req', re: /charge\s*air\s*pressure.*specif|MAP_SP|specified\s*charge|consigne\s*(turbo|boost|sural)|lade(druck)?.*soll/i },
    { id: 'boost_mbar', re: /charge\s*air\s*pressure.*actual|MAP_MMV|actual\s*charge|boost\s*pressure|pression\s*(de\s*)?suralimentation|lade(druck)?.*ist/i },
    { id: 'rail_bar', re: /fuel\s*high[-\s]?press|high\s*fuel\s*press|FUP_|rail\s*pressure|fuel\s*rail|pression\s*rail|rail(druck)?/i },
    { id: 'torque_nm', re: /engine\s*torque|TQI_SP|couple\s*moteur|motormoment|torque\s*request|drivers?\s*wish|wunschmoment/i },
    { id: 'rpm', re: /engine\s*rpm|engine\s*speed|motordrehzahl|drehzahl|\brpm\b|tr\/min|régime/i },
    { id: 'speed', re: /vehicle\s*speed|vitesse\s*(véhicule|vehicule)|geschwindigkeit/i },
    { id: 'maf', re: /air\s*mass|mass\s*air|debitmasse|luftmasse|\bmaf\b/i },
    { id: 'pedal', re: /accelerator|pedale|pedal\s*position|fahrpedal|gaspedal/i },
  ];

  const METRICS = [
    { id: 'rpm', label: 'RPM', unit: '', yMax: 5200 },
    { id: 'map_bar', label: 'MAP', unit: ' bar abs', yMax: 2.8 },
    { id: 'tq', label: 'Couple', unit: ' Nm', yMax: 400 },
    { id: 'rail', label: 'Rail', unit: ' MPa', yMax: 200 },
    { id: 'ped', label: 'Pédale', unit: ' %', yMax: 100 },
    { id: 'spd', label: 'Vitesse', unit: ' km/h', yMax: 120 },
  ];

  const state = {
    a: null,
    b: null,
    metric: 'rpm',
    pullA: 0,
    pullB: 0,
    mode: 'overlay', // overlay | side
  };

  const $ = (id) => document.getElementById(id);

  function parseNum(s) {
    if (s == null) return NaN;
    let t = String(s).trim().replace(/\s/g, '').replace(',', '.');
    t = t.replace(/[^\d.\-+eE]/g, '');
    const n = parseFloat(t);
    return Number.isFinite(n) ? n : NaN;
  }

  function detectSep(headerLine) {
    const sc = (headerLine.match(/;/g) || []).length;
    const cc = (headerLine.match(/,/g) || []).length;
    const tc = (headerLine.match(/\t/g) || []).length;
    if (tc >= sc && tc >= cc && tc > 0) return '\t';
    if (sc >= cc) return ';';
    return ',';
  }

  function classifyHeader(h) {
    for (const k of VCDS_KEYS) if (k.re.test(h)) return k.id;
    return null;
  }

  function unitFactor(unit, id) {
    const u = String(unit || '').trim().toLowerCase().replace(/\s/g, '');
    if (id === 'rail_bar') {
      if (u === 'mpa') return 10;
      if (u === 'kpa') return 0.01;
      if (u === 'bar') return 1;
    }
    if (id === 'boost_mbar' || id === 'boost_req') {
      if (u === 'hpa' || u === 'mbar') return 1;
      if (u === 'kpa') return 10;
      if (u === 'bar') return 1000;
    }
    return 1;
  }

  function findStampRow(lines) {
    for (let i = 0; i < lines.length; i++) {
      if (/,STAMP,/i.test(lines[i]) && /Engine RPM|Engine torque|Charge air|Fuel high/i.test(lines[i]))
        return i;
    }
    for (let i = 0; i < lines.length; i++) {
      if (/,STAMP,/i.test(lines[i])) return i;
    }
    return -1;
  }

  /** Parse VCDS CSV → time series + peaks */
  function parseVcdsSeries(text, name) {
    const rawLines = String(text || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
    const lines = rawLines.filter((l) => l.trim());
    const series = [];
    const peaks = {};
    const colsFound = {};
    let ecuInfo = '';
    let mode = 'none';

    for (const l of lines.slice(0, 8)) {
      if (/ADVMB|906\s*023|PCR|TDI/i.test(l)) {
        ecuInfo = l.split(',').slice(0, 4).filter(Boolean).join(' · ');
        break;
      }
    }

    const stampIdx = findStampRow(lines);
    if (stampIdx >= 0) {
      const sep = detectSep(lines[stampIdx]);
      const headers = lines[stampIdx].split(sep).map((h) => h.trim().replace(/^"|"$/g, ''));
      const units = (lines[stampIdx + 1] || '').split(sep).map((h) => h.trim());
      const mapIdx = {};
      const factors = {};
      let stampCol = -1;
      headers.forEach((h, i) => {
        if (/^STAMP$/i.test(h)) { stampCol = i; return; }
        if (/^TIME$/i.test(h) || /^Marker$/i.test(h) || !h) return;
        const id = classifyHeader(h);
        if (!id) return;
        // Prefer actual over specified when same id already mapped (rail act vs sp)
        if (mapIdx[id] != null) {
          const prevH = headers[mapIdx[id]] || '';
          if (/specif|soll|consigne|request/i.test(h) && !/specif|soll|consigne|request/i.test(prevH)) return;
          if (/actual|ist|réel|reel/i.test(prevH) && !/actual|ist|réel|reel/i.test(h)) return;
        }
        mapIdx[id] = i;
        factors[id] = unitFactor(units[i] || '', id);
        colsFound[id] = h + (units[i] ? ' [' + units[i].trim() + ']' : '');
      });

      // Also keep boost_req / boost_mbar separately if both present
      headers.forEach((h, i) => {
        const id = classifyHeader(h);
        if (!id) return;
        if ((id === 'boost_req' || id === 'boost_mbar' || id === 'rail_bar') && mapIdx[id] == null) {
          mapIdx[id] = i;
          factors[id] = unitFactor(units[i] || '', id);
          colsFound[id] = h;
        }
      });

      if (Object.keys(mapIdx).length) {
        mode = 'vcds-advmb';
        for (let r = stampIdx + 2; r < lines.length; r++) {
          const cells = lines[r].split(sep);
          if (cells.length < 3) continue;
          const row = { t: series.length ? series[series.length - 1].t + 0.05 : 0 };
          if (stampCol >= 0) {
            const st = parseNum(cells[stampCol]);
            if (Number.isFinite(st)) row.t = st;
          }
          let useful = false;
          for (const [id, i] of Object.entries(mapIdx)) {
            const n = parseNum(cells[i]);
            if (!Number.isFinite(n)) continue;
            useful = true;
            const v = n * (factors[id] || 1);
            row[id] = v;
            if (peaks[id] == null || v > peaks[id]) peaks[id] = v;
          }
          if (useful) series.push(row);
        }
      }
    }

    // Generic CSV fallback
    if (mode === 'none' && lines.length >= 2) {
      const sep = detectSep(lines[0]);
      const headers = lines[0].split(sep).map((h) => h.trim().replace(/^"|"$/g, ''));
      const mapIdx = {};
      let tCol = -1;
      headers.forEach((h, i) => {
        if (/^t(ime)?$|^stamp$/i.test(h)) { tCol = i; return; }
        const id = classifyHeader(h);
        if (id) { mapIdx[i] = id; colsFound[id] = h; }
      });
      if (Object.keys(mapIdx).length) {
        mode = 'csv';
        for (let r = 1; r < lines.length; r++) {
          const cells = lines[r].split(sep);
          const row = { t: tCol >= 0 ? parseNum(cells[tCol]) : r * 0.05 };
          if (!Number.isFinite(row.t)) row.t = r * 0.05;
          let useful = false;
          for (const [iStr, id] of Object.entries(mapIdx)) {
            const n = parseNum(cells[+iStr]);
            if (!Number.isFinite(n)) continue;
            useful = true;
            row[id] = n;
            if (peaks[id] == null || n > peaks[id]) peaks[id] = n;
          }
          if (useful) series.push(row);
        }
      }
    }

    if (!series.length) {
      return null;
    }

    const normalized = series.map((r) => normalizeRow(r));
    const pulls = findPulls(normalized);
    const hardcuts = findHardcuts(normalized);
    const launches = findLaunches(normalized);

    return {
      name: name || 'Log',
      mode,
      ecuInfo,
      colsFound,
      peaks,
      series: normalized,
      duration_s: normalized[normalized.length - 1].t - normalized[0].t,
      pulls,
      hardcuts,
      launches,
      source: 'csv',
    };
  }

  function normalizeRow(r) {
    const out = {
      t: r.t,
      rpm: r.rpm ?? null,
      spd: r.speed ?? null,
      ped: r.pedal ?? null,
      tq: r.torque_nm ?? null,
      map_act: r.boost_mbar ?? null,
      map_sp: r.boost_req ?? null,
      rail_bar: r.rail_bar ?? null,
      maf: r.maf ?? null,
    };
    out.rail = out.rail_bar != null ? out.rail_bar / 10 : null; // MPa for charts
    out.map_bar = out.map_act != null ? out.map_act / 1000 : null;
    out.map_sp_bar = out.map_sp != null ? out.map_sp / 1000 : null;
    return out;
  }

  function findPulls(rows, pedMin, minLen, maxGap) {
    pedMin = pedMin == null ? 55 : pedMin;
    minLen = minLen == null ? 4 : minLen;
    maxGap = maxGap == null ? 4 : maxGap;
    const candidates = [];
    let i = 0;
    const n = rows.length;
    while (i < n) {
      const ri = rows[i];
      if ((ri.ped == null || ri.ped < pedMin) || (ri.spd != null && ri.spd < 15)) {
        i++;
        continue;
      }
      const start = i;
      let j = i;
      while (j + 1 < n) {
        const cur = rows[j];
        const nxt = rows[j + 1];
        if (nxt.t - cur.t > maxGap) break;
        if ((nxt.ped == null || nxt.ped < 40) && nxt.rpm != null && cur.rpm != null && nxt.rpm < cur.rpm - 300) break;
        if (nxt.spd != null && rows[start].spd != null && nxt.spd + 1 < rows[start].spd && (nxt.ped == null || nxt.ped < pedMin)) break;
        j++;
        if ((nxt.ped == null || nxt.ped < 20) && j - start >= minLen) break;
      }
      const seg = rows.slice(start, j + 1);
      if (seg.length >= minLen) {
        const spd0 = seg[0].spd;
        const spd1 = seg[seg.length - 1].spd;
        const spdGain = (spd0 != null && spd1 != null) ? spd1 - spd0 : 0;
        const rpmPeak = maxOf(seg, 'rpm');
        const tqPeak = maxOf(seg, 'tq');
        const mapPeak = maxOf(seg, 'map_act');
        if (spdGain >= 8 && rpmPeak >= 2200 && tqPeak >= 150) {
          candidates.push({
            start_t: seg[0].t,
            end_t: seg[seg.length - 1].t,
            spd0, spd1, spd_gain: spdGain,
            rpm_peak: rpmPeak,
            tq_peak: tqPeak,
            map_peak: mapPeak,
            score: tqPeak * 0.5 + (mapPeak || 0) * 0.05 + spdGain * 2 + rpmPeak * 0.01,
            rows: seg,
          });
        }
      }
      i = Math.max(j + 1, i + 1);
    }
    candidates.sort((a, b) => b.score - a.score);
    const kept = [];
    for (const c of candidates) {
      if (kept.some((k) => Math.abs(c.start_t - k.start_t) < 8)) continue;
      kept.push(c);
      if (kept.length >= 4) break;
    }
    return kept.map((p, idx) => ({
      label: 'Pull ' + (idx + 1),
      start_t: p.start_t,
      end_t: p.end_t,
      spd0: p.spd0,
      spd1: p.spd1,
      spd_gain: p.spd_gain,
      rpm_peak: p.rpm_peak,
      tq_peak: p.tq_peak,
      map_peak: p.map_peak,
      series: downsample(p.rows, 80).map((r) => ({
        dt: round(r.t - p.start_t, 2),
        rpm: r.rpm,
        spd: r.spd,
        ped: r.ped,
        tq: r.tq,
        map_act: r.map_act,
        map_sp: r.map_sp,
        map_bar: r.map_bar,
        map_sp_bar: r.map_sp_bar,
        rail: r.rail,
      })),
    }));
  }

  function findHardcuts(rows) {
    const out = [];
    for (let i = 1; i < rows.length; i++) {
      const prev = rows[i - 1];
      const cur = rows[i];
      if (prev.rpm == null || cur.rpm == null) continue;
      if (prev.rpm >= 4200 && prev.rpm - cur.rpm > 800 && (prev.ped == null || prev.ped >= 50)) {
        out.push({ t: prev.t, rpm0: prev.rpm, rpm1: cur.rpm, ped: prev.ped, spd: prev.spd, tq: prev.tq });
      }
    }
    return out;
  }

  function findLaunches(rows) {
    return rows.filter((r) => (r.ped == null || r.ped >= 70) && (r.spd == null || r.spd <= 5) && (r.rpm != null && r.rpm >= 2000));
  }

  function maxOf(arr, key) {
    let m = -Infinity;
    for (const r of arr) {
      const v = r[key];
      if (v != null && v > m) m = v;
    }
    return m === -Infinity ? 0 : m;
  }

  function downsample(rows, maxPts) {
    if (rows.length <= maxPts) return rows;
    const step = Math.max(1, Math.floor(rows.length / maxPts));
    const out = [];
    for (let i = 0; i < rows.length; i += step) out.push(rows[i]);
    if (out[out.length - 1] !== rows[rows.length - 1]) out.push(rows[rows.length - 1]);
    return out;
  }

  function round(n, d) {
    const f = Math.pow(10, d || 0);
    return Math.round(n * f) / f;
  }

  function fmt(n, d) {
    if (n == null || !Number.isFinite(n)) return '—';
    return Number(n).toFixed(d == null ? 0 : d);
  }

  function deltaCls(d, higherIsBetter) {
    if (d == null || !Number.isFinite(d) || Math.abs(d) < 1e-9) return 'flat';
    const up = d > 0;
    if (higherIsBetter == null) return up ? 'up' : 'down';
    if (higherIsBetter) return up ? 'up' : 'down';
    return up ? 'down' : 'up';
  }

  /** Build Log object from precomputed JSON (demo) */
  function fromDemoLog(raw) {
    const pulls = (raw.pulls || []).map((p) => ({
      label: p.label,
      start_t: p.start_t,
      end_t: p.end_t,
      spd0: p.spd0,
      spd1: p.spd1,
      spd_gain: p.spd_gain,
      rpm_peak: p.rpm_peak,
      tq_peak: p.tq_peak,
      map_peak: p.map_peak,
      series: (p.series || []).map((s) => ({
        dt: s.dt,
        rpm: s.rpm,
        spd: s.spd,
        ped: s.ped,
        tq: s.tq,
        map_act: s.map_act,
        map_sp: s.map_sp,
        map_bar: s.map_act != null ? s.map_act / 1000 : null,
        map_sp_bar: s.map_sp != null ? s.map_sp / 1000 : null,
        rail: s.rail,
      })),
    }));
    return {
      name: raw.name,
      mode: 'demo',
      ecuInfo: 'Caddy 1.6 TDI PCR2.1 (démo)',
      colsFound: {},
      peaks: {
        rpm: raw.rpm_max,
        speed: raw.spd_max,
        torque_nm: raw.tq_max,
        boost_mbar: raw.map_act_max,
        boost_req: raw.map_sp_max,
        rail_bar: raw.rail_max_mpa != null ? raw.rail_max_mpa * 10 : null,
        maf: raw.air_max,
      },
      series: [],
      duration_s: raw.duration_s,
      pulls,
      hardcuts: inferHardcutsFromPulls(pulls),
      launches: [],
      source: 'demo',
    };
  }

  function inferHardcutsFromPulls(pulls) {
    const out = [];
    for (const p of pulls) {
      const s = p.series || [];
      for (let i = 1; i < s.length; i++) {
        const a = s[i - 1];
        const b = s[i];
        if (a.rpm >= 4200 && a.rpm - b.rpm > 800 && (a.ped == null || a.ped >= 40)) {
          out.push({ t: p.start_t + a.dt, rpm0: a.rpm, rpm1: b.rpm, ped: a.ped, spd: a.spd, tq: a.tq });
        }
      }
    }
    return out;
  }

  /* —— Summary engine —— */
  function buildSummary(a, b) {
    const pos = [];
    const neg = [];
    const changes = [];
    const actions = [];

    const metrics = [
      { key: 'torque_nm', label: 'Couple max', unit: ' Nm', better: true, warnAbove: ACE_TQ },
      { key: 'boost_mbar', label: 'MAP réel max', unit: ' mbar', better: true, warnAbove: ACE_MAP },
      { key: 'rail_bar', label: 'Rail max', unit: ' bar', better: false, warnAbove: ACE_RAIL_BAR + 20 },
      { key: 'rpm', label: 'RPM max', unit: '', better: null },
      { key: 'speed', label: 'Vitesse max', unit: ' km/h', better: true },
      { key: 'maf', label: 'Air mass max', unit: ' g/s', better: true },
    ];

    for (const m of metrics) {
      const va = a.peaks[m.key];
      const vb = b.peaks[m.key];
      if (va == null || vb == null) continue;
      const d = vb - va;
      const pct = va !== 0 ? (d / va) * 100 : 0;
      changes.push({
        label: m.label,
        a: va,
        b: vb,
        d,
        pct,
        unit: m.unit,
        cls: deltaCls(d, m.better),
      });
      if (Math.abs(d) < (m.key === 'rail_bar' ? 5 : m.key === 'boost_mbar' ? 15 : 2)) continue;
      const arrow = d > 0 ? '↑' : '↓';
      const line = m.label + ' : ' + fmt(va, m.key === 'maf' ? 1 : 0) + ' → ' + fmt(vb, m.key === 'maf' ? 1 : 0) + m.unit +
        ' (' + arrow + Math.abs(d).toFixed(m.key === 'maf' ? 1 : 0) + m.unit + ', ' + (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%)';
      if (m.better === true && d > 0) pos.push(line);
      else if (m.better === true && d < 0) neg.push(line + ' — moins de charge / perf sur B');
      else if (m.better === false && d > 0) neg.push(line + ' — pression plus haute (surveiller pompe HP)');
      else if (m.better === false && d < 0) pos.push(line + ' — plus safe côté rail');
      else changes[changes.length - 1]._note = line;
    }

    // Best pull compare
    const pa = a.pulls[0];
    const pb = b.pulls[0];
    if (pa && pb) {
      const gainA = pa.spd_gain;
      const gainB = pb.spd_gain;
      const durA = pa.end_t - pa.start_t;
      const durB = pb.end_t - pb.start_t;
      changes.push({
        label: 'Meilleur pull — gain vitesse',
        a: gainA, b: gainB, d: gainB - gainA, unit: ' km/h',
        cls: deltaCls(gainB - gainA, true),
        extra: fmt(pa.spd0) + '→' + fmt(pa.spd1) + ' vs ' + fmt(pb.spd0) + '→' + fmt(pb.spd1),
      });
      if (gainB > gainA + 2) pos.push('Pull B gagne plus de vitesse (+' + fmt(gainB - gainA) + ' km/h) — accélération plus efficace.');
      else if (gainA > gainB + 2) neg.push('Pull A gagnait plus de vitesse (+' + fmt(gainA - gainB) + ' km/h) — B moins tranchant ou pull plus court.');

      if (pb.tq_peak > pa.tq_peak + 3) pos.push('Couple de pull B plus haut (' + fmt(pa.tq_peak) + ' → ' + fmt(pb.tq_peak) + ' Nm).');
      else if (pa.tq_peak > pb.tq_peak + 3) neg.push('Couple de pull B plus bas (' + fmt(pa.tq_peak) + ' → ' + fmt(pb.tq_peak) + ' Nm).');

      if (durB + 0.4 < durA && gainB >= gainA - 2) pos.push('Pull B plus court pour un gain similaire — sensation plus nerveuse.');
    }

    // Hardcut / launch
    const hcA = a.hardcuts.length;
    const hcB = b.hardcuts.length;
    if (hcB > hcA) pos.push('Hardcut plus visible sur B (' + hcA + ' → ' + hcB + ' coupures) — limiteur régime / clutch prot actif.');
    else if (hcA > 0 && hcB === 0) neg.push('Hardcut vu sur A mais pas sur B — vérifier tqlim_cluth_prot / régime atteint.');
    else if (hcB > 0) pos.push(hcB + ' hardcut(s) détecté(s) sur B (chute RPM > 800 sous charge haute).');

    const laA = a.launches.length;
    const laB = b.launches.length;
    if (laB > laA) pos.push('Plus de points launch-like sur B (pédale≥70, spd≤5, rpm≥2000) — ' + laB + ' pts.');
    else if (laA > 0 && laB === 0) changes.push({ label: 'Launch', a: laA, b: 0, d: -laA, unit: ' pts', cls: 'flat' });

    // Safety vs ACE
    const railB = b.peaks.rail_bar;
    if (railB != null) {
      if (railB > ACE_RAIL_BAR + 40) {
        neg.push('Rail B à ' + fmt(railB) + ' bar — au-dessus d’ACE (' + ACE_RAIL_BAR + '). Risque pompe HP / injecteurs.');
        actions.push('Ouvre rail_base_int_trq2B @ 1E9368 — baisse un peu avant nouvel essai dur.');
      } else if (railB > ACE_RAIL_BAR + 10) {
        neg.push('Rail B légèrement au-dessus d’ACE (' + fmt(railB) + ' vs ' + ACE_RAIL_BAR + ' bar) — pic court acceptable, soutenu non.');
        actions.push('Vérifie si le pic rail est 1–2 lignes ou soutenu à plein gaz.');
      } else {
        pos.push('Rail B sous plafond ACE (' + fmt(railB) + ' ≤ ' + ACE_RAIL_BAR + ' bar).');
      }
    }

    const tqB = b.peaks.torque_nm;
    if (tqB != null && tqB > ACE_TQ + 5) {
      neg.push('Couple B > plafond ACE AccPed (' + fmt(tqB) + ' > ' + ACE_TQ + ' Nm) — soft différent ou log hors fichier.');
      actions.push('Compare AccPed_trq4A @ 1CF9C0 avec le dump flashé.');
    } else if (tqB != null && tqB >= 320) {
      pos.push('Couple B bien chargé (' + fmt(tqB) + ' Nm) — essai utile pour valider la carto.');
    } else if (tqB != null && tqB < 280) {
      neg.push('Couple B bas (' + fmt(tqB) + ' Nm) — essai trop soft pour juger la carto.');
      actions.push('Refais un log en 3ᵉ/4ᵉ plein gaz jusqu’à ~3500–4500 tr/min.');
    }

    const mapB = b.peaks.boost_mbar;
    if (mapB != null && mapB > ACE_MAP) {
      neg.push('MAP B overboost vs limiteur ACE (' + fmt(mapB) + ' > ' + ACE_MAP + ' mbar).');
      actions.push('Check turbo_atm6A @ 1C6A2C + durites / actuator.');
    }

    // MAP tracking on best pull B
    if (pb && pb.series && pb.series.length) {
      const errs = pb.series.filter((s) => s.map_act != null && s.map_sp != null && (s.ped == null || s.ped >= 60));
      if (errs.length) {
        const gaps = errs.map((s) => s.map_act - s.map_sp);
        const avg = gaps.reduce((x, y) => x + y, 0) / gaps.length;
        if (avg < -80) {
          neg.push('Turbo B n’atteint pas la consigne (écart moyen ' + fmt(avg) + ' mbar) — fuite / actuator / map trop haute.');
          actions.push('Croise MAP consigne vs réel sur le graphique — regarde turbo_base3B.');
        } else if (Math.abs(avg) < 60) {
          pos.push('Régulation turbo B OK (écart moyen consigne/réel ~' + fmt(avg) + ' mbar).');
        }
      }
    }

    // RPM ceiling V2 story
    const rpmB = b.peaks.rpm;
    if (rpmB != null && rpmB >= 4700 && rpmB <= 4900 && hcB > 0) {
      pos.push('RPM B plafonne ~' + fmt(rpmB) + ' avec hardcut — cohérent avec limiteur V3 ITALIE @ 4800.');
    } else if (rpmB != null && rpmB > 5000) {
      neg.push('RPM B > 5000 — limiteur régime trop haut ou inactif.');
      actions.push('Vérifie limiteur régime / tqlim clutch prot.');
    }

    if (!a.pulls.length && !b.pulls.length) {
      neg.push('Aucun pull WOT détecté — pédale/vitesse insuffisantes ou canaux manquants.');
      actions.push('Dans VCDS, enregistre RPM, couple, MAP act/sp, rail, pédale, vitesse.');
    }

    if (!pos.length && !neg.length) {
      pos.push('Les deux logs sont très proches — pas de dérive majeure détectée.');
    }

    let verdict = 'stable';
    let verdictTxt = 'Logs proches — suivi stable.';
    if (neg.length >= 3 || neg.some((n) => /overboost|Risque pompe|soft différent/i.test(n))) {
      verdict = 'bad';
      verdictTxt = 'Points rouges à traiter avant de pousser la carto.';
    } else if (pos.length > neg.length && pos.length >= 2) {
      verdict = 'good';
      verdictTxt = 'B s’améliore vs A — bons signes, surveille les alertes restantes.';
    } else if (neg.length > pos.length) {
      verdict = 'warn';
      verdictTxt = 'B moins clean / plus risqué que A — lis les négatifs avant nouvel essai.';
    } else if (pos.length && neg.length) {
      verdict = 'warn';
      verdictTxt = 'Mitigé — des gains, mais aussi des points à corriger.';
    }

    return { pos, neg, changes, actions, verdict, verdictTxt, pullA: pa || null, pullB: pb || null };
  }

  /* —— Charts —— */
  function metricValue(pt, metricId) {
    if (metricId === 'rpm') return pt.rpm;
    if (metricId === 'map_bar') return pt.map_bar != null ? pt.map_bar : (pt.map_act != null ? pt.map_act / 1000 : null);
    if (metricId === 'tq') return pt.tq;
    if (metricId === 'rail') return pt.rail;
    if (metricId === 'ped') return pt.ped;
    if (metricId === 'spd') return pt.spd;
    return null;
  }

  function drawCharts() {
    const canvas = $('lc-canvas');
    if (!canvas || !state.a || !state.b) return;
    const wrap = canvas.parentElement;
    const cssW = Math.max(640, (wrap && wrap.clientWidth) || 960);
    const cssH = state.mode === 'side' ? 420 : 340;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const pad = { l: 52, r: 18, t: 28, b: 36 };
    const met = METRICS.find((m) => m.id === state.metric) || METRICS[0];
    const pullA = state.a.pulls[state.pullA] || state.a.pulls[0];
    const pullB = state.b.pulls[state.pullB] || state.b.pulls[0];
    const seriesA = pullA ? pullA.series : [];
    const seriesB = pullB ? pullB.series : [];

    ctx.clearRect(0, 0, cssW, cssH);
    ctx.fillStyle = '#131210';
    ctx.fillRect(0, 0, cssW, cssH);

    // subtle stripe
    ctx.save();
    ctx.globalAlpha = 0.04;
    ctx.strokeStyle = '#e23a1a';
    for (let x = -cssH; x < cssW; x += 14) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + cssH, cssH);
      ctx.stroke();
    }
    ctx.restore();

    if (state.mode === 'side') {
      drawPanel(ctx, pad.l, pad.t, (cssW - pad.l - pad.r - 12) / 2, cssH - pad.t - pad.b, seriesA, COL_A, met, state.a.name + ' · ' + (pullA ? pullA.label : '—'));
      drawPanel(ctx, pad.l + (cssW - pad.l - pad.r - 12) / 2 + 12, pad.t, (cssW - pad.l - pad.r - 12) / 2, cssH - pad.t - pad.b, seriesB, COL_B, met, state.b.name + ' · ' + (pullB ? pullB.label : '—'));
    } else {
      const plotW = cssW - pad.l - pad.r;
      const plotH = cssH - pad.t - pad.b;
      const xs = [...seriesA.map((p) => p.dt), ...seriesB.map((p) => p.dt)];
      const ys = [...seriesA, ...seriesB].map((p) => metricValue(p, met.id)).filter((v) => v != null);
      const xMax = Math.max(1, ...xs, 0.1);
      const yMin = 0;
      const yMax = Math.max(met.yMax * 0.4, ...(ys.length ? ys : [met.yMax]), met.yMax * 0.2) * 1.08;

      drawGrid(ctx, pad.l, pad.t, plotW, plotH, xMax, yMin, yMax, met);
      if (met.id === 'rpm') {
        const y = pad.t + plotH - ((HARDCUT_RPM - yMin) / (yMax - yMin)) * plotH;
        ctx.strokeStyle = 'rgba(226,58,26,0.55)';
        ctx.setLineDash([6, 5]);
        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(pad.l + plotW, y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(226,58,26,0.85)';
        ctx.font = '600 11px Barlow, sans-serif';
        ctx.fillText('hardcut 4800', pad.l + 6, y - 4);
      }
      drawLine(ctx, seriesA, met.id, pad.l, pad.t, plotW, plotH, xMax, yMin, yMax, COL_A, 2.4);
      drawLine(ctx, seriesB, met.id, pad.l, pad.t, plotW, plotH, xMax, yMin, yMax, COL_B, 2.4);
      if (met.id === 'map_bar') {
        drawLine(ctx, seriesA, 'map_sp_bar_proxy', pad.l, pad.t, plotW, plotH, xMax, yMin, yMax, COL_A, 1.2, true, (p) => p.map_sp_bar);
        drawLine(ctx, seriesB, 'map_sp_bar_proxy', pad.l, pad.t, plotW, plotH, xMax, yMin, yMax, COL_B, 1.2, true, (p) => p.map_sp_bar);
      }
      ctx.fillStyle = '#f3f1ef';
      ctx.font = '600 13px Oswald, sans-serif';
      ctx.fillText(met.label + ' — overlay meilleurs pulls', pad.l, 18);
      // legend
      legendDot(ctx, cssW - 200, 14, COL_A, shortName(state.a.name));
      legendDot(ctx, cssW - 100, 14, COL_B, shortName(state.b.name));
    }
  }

  function shortName(n) {
    return String(n || 'Log').replace(/^Log\s*/i, 'L').slice(0, 18);
  }

  function drawPanel(ctx, x, y, w, h, series, color, met, title) {
    ctx.fillStyle = '#181614';
    ctx.strokeStyle = '#2e2926';
    ctx.lineWidth = 1;
    ctx.fillRect(x, y, w, h);
    ctx.strokeRect(x, y, w, h);
    const xs = series.map((p) => p.dt);
    const ys = series.map((p) => metricValue(p, met.id)).filter((v) => v != null);
    const xMax = Math.max(1, ...xs, 0.1);
    const yMin = 0;
    const yMax = Math.max(met.yMax * 0.4, ...(ys.length ? ys : [met.yMax])) * 1.08;
    const inner = { l: x + 40, t: y + 24, w: w - 52, h: h - 48 };
    drawGrid(ctx, inner.l, inner.t, inner.w, inner.h, xMax, yMin, yMax, met);
    drawLine(ctx, series, met.id, inner.l, inner.t, inner.w, inner.h, xMax, yMin, yMax, color, 2.2);
    ctx.fillStyle = '#f3f1ef';
    ctx.font = '600 12px Oswald, sans-serif';
    ctx.fillText(title, x + 10, y + 16);
  }

  function drawGrid(ctx, x, y, w, h, xMax, yMin, yMax, met) {
    ctx.strokeStyle = COL_GRID;
    ctx.lineWidth = 1;
    ctx.strokeRect(x, y, w, h);
    ctx.fillStyle = COL_MUTED;
    ctx.font = '500 10px IBM Plex Mono, monospace';
    for (let i = 0; i <= 4; i++) {
      const yy = y + (h * i) / 4;
      ctx.beginPath();
      ctx.moveTo(x, yy);
      ctx.lineTo(x + w, yy);
      ctx.strokeStyle = 'rgba(46,41,38,0.75)';
      ctx.stroke();
      const val = yMax - ((yMax - yMin) * i) / 4;
      ctx.fillStyle = '#a39e96';
      ctx.textAlign = 'right';
      ctx.fillText(fmt(val, met.id === 'map_bar' ? 2 : 0), x - 6, yy + 3);
    }
    for (let i = 0; i <= 4; i++) {
      const xx = x + (w * i) / 4;
      ctx.beginPath();
      ctx.moveTo(xx, y);
      ctx.lineTo(xx, y + h);
      ctx.strokeStyle = 'rgba(46,41,38,0.55)';
      ctx.stroke();
      const t = (xMax * i) / 4;
      ctx.fillStyle = '#a39e96';
      ctx.textAlign = 'center';
      ctx.fillText(t.toFixed(1) + 's', xx, y + h + 16);
    }
    ctx.textAlign = 'left';
    ctx.fillStyle = '#a39e96';
    ctx.fillText(met.label + met.unit, x, y + h + 30);
  }

  function drawLine(ctx, series, metricId, x, y, w, h, xMax, yMin, yMax, color, lw, dashed, getter) {
    const pts = [];
    for (const p of series) {
      const v = getter ? getter(p) : metricValue(p, metricId);
      if (v == null || !Number.isFinite(v)) continue;
      const px = x + (p.dt / xMax) * w;
      const py = y + h - ((v - yMin) / (yMax - yMin)) * h;
      pts.push({ px, py });
    }
    if (pts.length < 2) return;
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = lw;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    if (dashed) ctx.setLineDash([5, 4]);
    else ctx.setLineDash([]);
    ctx.globalAlpha = dashed ? 0.55 : 1;
    ctx.moveTo(pts[0].px, pts[0].py);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].px, pts[i].py);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    if (!dashed) {
      const last = pts[pts.length - 1];
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(last.px, last.py, 3.2, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function legendDot(ctx, x, y, color, label) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#f3f1ef';
    ctx.font = '500 11px Barlow, sans-serif';
    ctx.fillText(label, x + 8, y + 4);
  }

  /* —— UI render —— */
  function setStatus(slot, msg) {
    const el = $(slot === 'a' ? 'lc-status-a' : 'lc-status-b');
    if (el) el.textContent = msg || '';
  }

  function describeLog(log) {
    if (!log) return 'Aucun log';
    const parts = [
      log.series.length ? log.series.length + ' pts' : (log.source === 'demo' ? 'démo JSON' : ''),
      log.duration_s != null ? fmt(log.duration_s, 0) + 's' : '',
      log.pulls.length + ' pull(s)',
      log.hardcuts.length ? log.hardcuts.length + ' hardcut(s)' : '',
    ].filter(Boolean);
    return parts.join(' · ');
  }

  function renderDiffCards(summary) {
    const box = $('lc-diff-cards');
    if (!box || !summary) { if (box) box.innerHTML = ''; return; }
    box.innerHTML = '';
    const show = summary.changes.filter((c) => c.label);
    for (const c of show.slice(0, 8)) {
      const el = document.createElement('div');
      el.className = 'lc-diff ' + (c.cls || 'flat');
      const sign = c.d > 0 ? '+' : '';
      el.innerHTML =
        '<div class="lc-diff-lab">' + escapeHtml(c.label) + '</div>' +
        '<div class="lc-diff-vals"><span class="a">' + fmt(c.a, absDec(c)) + '</span>' +
        '<span class="arrow">→</span><span class="b">' + fmt(c.b, absDec(c)) + '</span>' +
        '<span class="unit">' + escapeHtml(c.unit || '') + '</span></div>' +
        '<div class="lc-diff-delta">' + sign + fmt(c.d, absDec(c)) + (c.unit || '') +
        (c.pct != null ? ' <small>(' + (c.pct >= 0 ? '+' : '') + c.pct.toFixed(1) + '%)</small>' : '') + '</div>' +
        (c.extra ? '<div class="lc-diff-extra">' + escapeHtml(c.extra) + '</div>' : '');
      box.appendChild(el);
    }
  }

  function absDec(c) {
    if (/MAP|Air|maf/i.test(c.label) && /mbar|g\/s/i.test(c.unit || '')) return c.unit.indexOf('g') >= 0 ? 1 : 0;
    if (/bar abs|MAP/.test(c.label)) return 2;
    return 0;
  }

  function renderSummary(summary) {
    const el = $('lc-summary');
    if (!el || !summary) { if (el) el.innerHTML = ''; return; }
    const vClass = summary.verdict === 'good' ? 'ok' : summary.verdict === 'bad' ? 'bad' : 'warn';
    let html = '<div class="lc-bilan bilan">';
    html += '<h3>Résumé comparatif</h3>';
    html += '<p class="verdict-line lc-verdict ' + vClass + '"><b>' + escapeHtml(summary.verdictTxt) + '</b></p>';
    html += '<div class="lc-cols">';
    html += '<div class="lc-col pos"><h4>Points positifs</h4><ul>';
    html += (summary.pos.length ? summary.pos : ['—']).map((t) => '<li>' + escapeHtml(t) + '</li>').join('');
    html += '</ul></div>';
    html += '<div class="lc-col neg"><h4>Points négatifs</h4><ul>';
    html += (summary.neg.length ? summary.neg : ['—']).map((t) => '<li>' + escapeHtml(t) + '</li>').join('');
    html += '</ul></div>';
    html += '</div>';
    if (summary.actions.length) {
      html += '<div class="lc-actions"><h4>Actions atelier</h4><ol>';
      html += summary.actions.map((t) => '<li>' + escapeHtml(t) + '</li>').join('');
      html += '</ol></div>';
    }
    if (summary.pullA && summary.pullB) {
      html += '<p class="lc-pull-note">Pulls affichés : <b>A</b> ' + escapeHtml(summary.pullA.label) +
        ' (' + fmt(summary.pullA.spd0) + '→' + fmt(summary.pullA.spd1) + ' km/h, TQ ' + fmt(summary.pullA.tq_peak) +
        ') · <b>B</b> ' + escapeHtml(summary.pullB.label) +
        ' (' + fmt(summary.pullB.spd0) + '→' + fmt(summary.pullB.spd1) + ' km/h, TQ ' + fmt(summary.pullB.tq_peak) + ')</p>';
    }
    html += '</div>';
    el.innerHTML = html;
  }

  function fillPullSelects() {
    fillPull('lc-pull-a', state.a, state.pullA, (v) => { state.pullA = v; });
    fillPull('lc-pull-b', state.b, state.pullB, (v) => { state.pullB = v; });
  }

  function fillPull(id, log, selected, onSet) {
    const sel = $(id);
    if (!sel) return;
    sel.innerHTML = '';
    if (!log || !log.pulls.length) {
      sel.innerHTML = '<option value="0">Aucun pull</option>';
      return;
    }
    log.pulls.forEach((p, i) => {
      const o = document.createElement('option');
      o.value = String(i);
      o.textContent = p.label + ' · ' + fmt(p.spd0) + '→' + fmt(p.spd1) + ' · ' + fmt(p.tq_peak) + ' Nm';
      if (i === selected) o.selected = true;
      sel.appendChild(o);
    });
      sel.onchange = () => {
      onSet(+sel.value || 0);
      refreshCompare();
    };
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function refreshCompare() {
    if (!state.a || !state.b) return;
    const aView = Object.assign({}, state.a, {
      pulls: rotatePulls(state.a.pulls, state.pullA),
    });
    const bView = Object.assign({}, state.b, {
      pulls: rotatePulls(state.b.pulls, state.pullB),
    });
    const summary = buildSummary(aView, bView);
    state._summary = summary;
    renderDiffCards(summary);
    renderSummary(summary);
    drawCharts();
    const st = $('lc-compare-status');
    if (st) st.textContent = 'A: ' + describeLog(state.a) + '  |  B: ' + describeLog(state.b);
  }

  function rotatePulls(pulls, idx) {
    if (!pulls || !pulls.length) return pulls || [];
    const i = Math.max(0, Math.min(idx || 0, pulls.length - 1));
    if (i === 0) return pulls;
    return [pulls[i]].concat(pulls.filter((_, j) => j !== i));
  }

  function runCompare() {
    if (!state.a || !state.b) {
      const st = $('lc-compare-status');
      if (st) st.textContent = 'Charge Log A et Log B (ou démo V3 ITALIE) avant de comparer.';
      return;
    }
    state.pullA = 0;
    state.pullB = 0;
    fillPullSelects();
    refreshCompare();
    try {
      localStorage.setItem(LS_SLOT, JSON.stringify({
        nameA: state.a.name,
        nameB: state.b.name,
        peaksA: state.a.peaks,
        peaksB: state.b.peaks,
        at: Date.now(),
      }));
    } catch (_) {}
  }

  function loadFile(slot, file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      const nameInput = $(slot === 'a' ? 'lc-name-a' : 'lc-name-b');
      const name = (nameInput && nameInput.value.trim()) || file.name.replace(/\.[^.]+$/, '') || ('Log ' + slot.toUpperCase());
      if (nameInput && !nameInput.value.trim()) nameInput.value = name;
      const log = parseVcdsSeries(text, name);
      if (!log) {
        setStatus(slot, 'CSV illisible — format VCDS ADVMB attendu.');
        return;
      }
      state[slot] = log;
      const ta = $(slot === 'a' ? 'lc-paste-a' : 'lc-paste-b');
      if (ta) ta.value = text.slice(0, 4000) + (text.length > 4000 ? '\n…' : '');
      setStatus(slot, 'OK · ' + describeLog(log));
      if (state.a && state.b) runCompare();
    };
    reader.readAsText(file);
  }

  function loadPaste(slot) {
    const ta = $(slot === 'a' ? 'lc-paste-a' : 'lc-paste-b');
    const nameInput = $(slot === 'a' ? 'lc-name-a' : 'lc-name-b');
    const text = ta ? ta.value : '';
    if (!text.trim()) {
      setStatus(slot, 'Colle le CSV ou charge un fichier.');
      return;
    }
    // If truncated preview from previous load, ignore
    if (/\n…\s*$/.test(text) && text.length < 5000) {
      setStatus(slot, 'Contenu tronqué — recharge le fichier CSV.');
      return;
    }
    const name = (nameInput && nameInput.value.trim()) || ('Log ' + slot.toUpperCase());
    const log = parseVcdsSeries(text, name);
    if (!log) {
      setStatus(slot, 'CSV illisible.');
      return;
    }
    state[slot] = log;
    setStatus(slot, 'OK · ' + describeLog(log));
    if (state.a && state.b) runCompare();
  }

  async function loadDemo() {
    const st = $('lc-compare-status');
    try {
      if (st) st.textContent = 'Chargement démo V3 ITALIE…';
      const res = await fetch(DEMO_URL);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      const logs = data.logs || [];
      if (logs.length < 2) throw new Error('JSON incomplet');
      state.a = fromDemoLog(logs[0]);
      state.b = fromDemoLog(logs[1]);
      if ($('lc-name-a')) $('lc-name-a').value = state.a.name;
      if ($('lc-name-b')) $('lc-name-b').value = state.b.name;
      setStatus('a', 'Démo · ' + describeLog(state.a));
      setStatus('b', 'Démo · ' + describeLog(state.b));
      runCompare();
      if (st) st.textContent = 'Démo V3 ITALIE chargée — session 18:52 vs 19:02 (hardcut/launch).';
    } catch (err) {
      if (st) st.textContent = 'Échec démo : ' + (err.message || err);
    }
  }

  function saveHistory() {
    if (!state.a || !state.b || !state._summary) {
      const st = $('lc-compare-status');
      if (st) st.textContent = 'Compare d’abord deux logs avant de sauver.';
      return;
    }
    const note = ($('lc-hist-note') && $('lc-hist-note').value.trim()) || '';
    const entry = {
      id: 'h' + Date.now(),
      at: Date.now(),
      nameA: state.a.name,
      nameB: state.b.name,
      verdict: state._summary.verdict,
      verdictTxt: state._summary.verdictTxt,
      note,
      peaksA: state.a.peaks,
      peaksB: state.b.peaks,
      pos: state._summary.pos.slice(0, 4),
      neg: state._summary.neg.slice(0, 4),
      pullA: state.a.pulls[0] ? { spd0: state.a.pulls[0].spd0, spd1: state.a.pulls[0].spd1, tq: state.a.pulls[0].tq_peak } : null,
      pullB: state.b.pulls[0] ? { spd0: state.b.pulls[0].spd0, spd1: state.b.pulls[0].spd1, tq: state.b.pulls[0].tq_peak } : null,
    };
    const hist = readHist();
    hist.unshift(entry);
    while (hist.length > 30) hist.pop();
    try {
      localStorage.setItem(LS_HIST, JSON.stringify(hist));
    } catch (_) {}
    if ($('lc-hist-note')) $('lc-hist-note').value = '';
    renderHistory();
    const st = $('lc-compare-status');
    if (st) st.textContent = 'Comparaison sauvée dans le suivi (' + hist.length + ').';
  }

  function readHist() {
    try {
      const raw = localStorage.getItem(LS_HIST);
      const arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (_) {
      return [];
    }
  }

  function renderHistory() {
    const box = $('lc-history');
    if (!box) return;
    const hist = readHist();
    if (!hist.length) {
      box.innerHTML = '<p class="lc-hist-empty">Aucun suivi encore — après chaque essai carto, compare A (avant) vs B (après) puis <b>Sauver dans le suivi</b>.</p>';
      return;
    }
    box.innerHTML = hist.map((h) => {
      const d = new Date(h.at);
      const date = d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
      const vClass = h.verdict === 'good' ? 'ok' : h.verdict === 'bad' ? 'bad' : 'warn';
      return '<article class="lc-hist-card ' + vClass + '" data-id="' + escapeHtml(h.id) + '">' +
        '<div class="lc-hist-top"><span class="lc-hist-date">' + escapeHtml(date) + '</span>' +
        '<span class="tag">' + escapeHtml(h.verdict || '') + '</span>' +
        '<button type="button" class="lc-hist-del" data-del="' + escapeHtml(h.id) + '" title="Supprimer">×</button></div>' +
        '<div class="lc-hist-names"><b>A</b> ' + escapeHtml(h.nameA) + ' <span class="arrow">→</span> <b>B</b> ' + escapeHtml(h.nameB) + '</div>' +
        '<p class="lc-hist-verdict">' + escapeHtml(h.verdictTxt || '') + '</p>' +
        (h.note ? '<p class="lc-hist-note">📝 ' + escapeHtml(h.note) + '</p>' : '') +
        '<div class="lc-hist-peaks">' +
        peakChip('TQ', h.peaksA && h.peaksA.torque_nm, h.peaksB && h.peaksB.torque_nm, 'Nm') +
        peakChip('MAP', h.peaksA && h.peaksA.boost_mbar, h.peaksB && h.peaksB.boost_mbar, 'mbar') +
        peakChip('Rail', h.peaksA && h.peaksA.rail_bar, h.peaksB && h.peaksB.rail_bar, 'bar') +
        '</div></article>';
    }).join('');
  }

  function peakChip(lab, a, b, unit) {
    if (a == null && b == null) return '';
    const d = (a != null && b != null) ? b - a : null;
    const cls = d == null ? '' : (d > 0 ? 'up' : d < 0 ? 'down' : 'flat');
    return '<span class="lc-chip ' + cls + '"><i>' + lab + '</i> ' + fmt(a) + '→' + fmt(b) + ' ' + unit + '</span>';
  }

  function bind() {
    const root = $('log-compare');
    if (!root) return;

    $('lc-file-a')?.addEventListener('change', (e) => {
      const f = e.target.files && e.target.files[0];
      loadFile('a', f);
    });
    $('lc-file-b')?.addEventListener('change', (e) => {
      const f = e.target.files && e.target.files[0];
      loadFile('b', f);
    });
    $('lc-parse-a')?.addEventListener('click', () => loadPaste('a'));
    $('lc-parse-b')?.addEventListener('click', () => loadPaste('b'));
    $('lc-compare')?.addEventListener('click', runCompare);
    $('lc-demo')?.addEventListener('click', loadDemo);
    $('lc-save-hist')?.addEventListener('click', saveHistory);
    $('lc-clear')?.addEventListener('click', () => {
      state.a = state.b = null;
      state._summary = null;
      ['lc-paste-a', 'lc-paste-b', 'lc-name-a', 'lc-name-b'].forEach((id) => { if ($(id)) $(id).value = ''; });
      setStatus('a', '');
      setStatus('b', '');
      if ($('lc-diff-cards')) $('lc-diff-cards').innerHTML = '';
      if ($('lc-summary')) $('lc-summary').innerHTML = '';
      if ($('lc-compare-status')) $('lc-compare-status').textContent = 'Effacé.';
      const c = $('lc-canvas');
      if (c) {
        const ctx = c.getContext('2d');
        ctx.clearRect(0, 0, c.width, c.height);
      }
    });

    root.querySelectorAll('[data-lc-metric]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.metric = btn.getAttribute('data-lc-metric');
        root.querySelectorAll('[data-lc-metric]').forEach((b) => b.classList.toggle('on', b === btn));
        drawCharts();
      });
    });
    root.querySelectorAll('[data-lc-mode]').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.mode = btn.getAttribute('data-lc-mode');
        root.querySelectorAll('[data-lc-mode]').forEach((b) => b.classList.toggle('on', b === btn));
        drawCharts();
      });
    });

    $('lc-history')?.addEventListener('click', (e) => {
      const del = e.target.closest('[data-del]');
      if (!del) return;
      const id = del.getAttribute('data-del');
      const hist = readHist().filter((h) => h.id !== id);
      try { localStorage.setItem(LS_HIST, JSON.stringify(hist)); } catch (_) {}
      renderHistory();
    });

    window.addEventListener('resize', () => {
      if (state.a && state.b) drawCharts();
    });
    window.addEventListener('pagechange', (e) => {
      if (e.detail && e.detail.page === 'log-compare' && state.a && state.b) {
        requestAnimationFrame(drawCharts);
      }
    });

    renderHistory();

    // Auto-load demo once if empty (nice first impression on GitHub Pages)
    const params = new URLSearchParams(location.search);
    if (params.get('demo') === '1' || location.hash === '#log-compare') {
      // delay until page shown
      setTimeout(() => {
        if (!state.a && !state.b) loadDemo();
      }, 200);
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind);
  else bind();
})();
