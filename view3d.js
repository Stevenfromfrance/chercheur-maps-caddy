/* Map 3D — WinOLS-style surface from MAP_GRIDS (canvas 2D projection, no deps) */
(function () {
  const canvas = document.getElementById('v3d-canvas');
  const metaEl = document.getElementById('v3d-meta');
  const sel = document.getElementById('v3d-map');
  if (!canvas || !sel) return;

  const ctx = canvas.getContext('2d');
  let mode = 'right'; // left | right | diff
  let mapId = '';
  // WinOLS-like default: look down at the carpet, origin (low X / low Y) near-left
  let rotY = -0.72;
  let rotX = 0.58;
  let zoom = 1;
  let drag = null;
  let hover = null;
  // flipDepth: reverse RPM/row along depth (Y axis of the map)
  let flipDepth = false;

  function grids() {
    return (typeof MAP_GRIDS !== 'undefined' && MAP_GRIDS) || window.MAP_GRIDS || [];
  }
  function findGrid(id) {
    const list = grids();
    return list.find((g) => g.id === id) || list[0];
  }
  function pairKeys() {
    if (window.COMPARE && window.COMPARE.sides) return window.COMPARE.sides();
    return ['ori', 'ace'];
  }
  function lab(k) {
    return window.COMPARE && window.COMPARE.label ? window.COMPARE.label(k) : String(k).toUpperCase();
  }
  function series(g, key) {
    if (!g) return [];
    if (key === 'v2') return g.v2 || g.v1 || g.ace || [];
    if (key === 'v1') return g.v1 || g.ace || [];
    return g[key] || [];
  }
  function heatColor(t) {
    t = Math.max(0, Math.min(1, t));
    // cold blue → green → hot red (WinOLS-ish)
    const stops = [
      [20, 40, 90],
      [40, 170, 90],
      [220, 200, 40],
      [220, 60, 50],
    ];
    const x = t * (stops.length - 1);
    const i = Math.floor(x);
    const f = x - i;
    const a = stops[Math.min(i, stops.length - 1)];
    const b = stops[Math.min(i + 1, stops.length - 1)];
    const r = Math.round(a[0] + (b[0] - a[0]) * f);
    const g = Math.round(a[1] + (b[1] - a[1]) * f);
    const bl = Math.round(a[2] + (b[2] - a[2]) * f);
    return 'rgb(' + r + ',' + g + ',' + bl + ')';
  }
  function diffColor(d, maxAbs) {
    const t = Math.max(-1, Math.min(1, d / (maxAbs || 1)));
    if (Math.abs(t) < 0.02) return 'rgb(40,48,56)';
    if (t > 0) {
      const k = t;
      return 'rgb(' + Math.round(40 + 180 * k) + ',' + Math.round(48 + 140 * k) + ',' + Math.round(56 - 20 * k) + ')';
    }
    const k = -t;
    return 'rgb(' + Math.round(40 + 160 * k) + ',' + Math.round(48 - 10 * k) + ',' + Math.round(56 + 10 * k) + ')';
  }

  function fillSelect() {
    const list = grids();
    if (!list.length) return;
    const groups = [
      { key: 'priority', label: 'Top 12 Stage 1' },
      { key: 'a2l', label: 'Autres maps A2L touchées' },
      { key: 'provisoire', label: 'Hors A2L / provisoire (bin)' },
      { key: 'dtc', label: 'DTC OFF (masques)' },
    ];
    sel.innerHTML = groups.map((gr) => {
      const opts = list
        .filter((g) => (g.group || (String(g.id).startsWith('DTC_') ? 'dtc' : (g.kind === 'mask' ? 'dtc' : 'a2l'))) === gr.key)
        .map((g) => '<option value="' + g.id + '">' + g.id + ' — ' + g.name + ' (' + g.addr + ')</option>')
        .join('');
      return opts ? '<optgroup label="' + gr.label + '">' + opts + '</optgroup>' : '';
    }).join('');
    if (!sel.innerHTML.trim()) {
      sel.innerHTML = list.map((g) =>
        '<option value="' + g.id + '">' + g.id + ' — ' + g.name + '</option>'
      ).join('');
    }
    if (!mapId) mapId = (typeof v2dId !== 'undefined' && v2dId) || list[0].id;
    if ([...sel.options].some((o) => o.value === mapId)) sel.value = mapId;
  }

  function resize() {
    const wrap = canvas.parentElement;
    const cssW = Math.max(640, (wrap && wrap.clientWidth) || 960);
    const cssH = Math.max(420, Math.min(560, window.innerHeight * 0.55));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function project(x, y, z, W, H) {
    // Model: X right, Y up (value), Z depth (map Y / RPM).
    // Pitch sign must put the NEAR ground edge at the BOTTOM of the canvas
    // (previous +pitch foreshortening put near at the top → “à l’envers”).
    const cy = Math.cos(rotY), sy = Math.sin(rotY);
    const cx = Math.cos(rotX), sx = Math.sin(rotX);
    let x1 = x * cy + z * sy;
    let z1 = -x * sy + z * cy;
    let y1 = y * cx + z1 * sx;
    z1 = -y * sx + z1 * cx;
    const persp = 2.8 / (2.8 + z1);
    const s = 180 * zoom * persp;
    return {
      x: W * 0.5 + x1 * s,
      y: H * 0.52 - y1 * s,
      z: z1,
      p: persp,
    };
  }

  /** Column → world X in [-1, 1] (pedal / axisX), left → right like Grille 2D. */
  function colToX(c, cols) {
    return (c / Math.max(1, cols - 1)) * 2 - 1;
  }
  /** Row → world Z depth. Default: row 0 (top of Grille 2D) at near edge (z=-1). */
  function rowToZ(r, rows) {
    const z = (r / Math.max(1, rows - 1)) * 2 - 1;
    return flipDepth ? -z : z;
  }

  function valuesForMode(g) {
    const keys = pairKeys();
    const L = series(g, keys[0]);
    const R = series(g, keys[1]);
    const n = Math.min(L.length, R.length, g.cols * g.rows);
    const out = new Float64Array(n);
    let minV = Infinity, maxV = -Infinity, maxAbs = 0;
    for (let i = 0; i < n; i++) {
      let v;
      if (mode === 'left') v = +L[i];
      else if (mode === 'right') v = +R[i];
      else v = +R[i] - +L[i];
      out[i] = v;
      if (Number.isFinite(v)) {
        minV = Math.min(minV, v);
        maxV = Math.max(maxV, v);
        maxAbs = Math.max(maxAbs, Math.abs(v));
      }
    }
    if (!Number.isFinite(minV)) { minV = 0; maxV = 1; }
    if (maxV <= minV) maxV = minV + 1;
    return { out, minV, maxV, maxAbs, L, R, n };
  }

  function draw() {
    resize();
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    ctx.clearRect(0, 0, W, H);

    // atmosphere
    const grd = ctx.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, '#0c1218');
    grd.addColorStop(1, '#06080c');
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    const g = findGrid(mapId);
    if (!g) {
      ctx.fillStyle = '#8a9aaa';
      ctx.font = '14px Barlow, sans-serif';
      ctx.fillText('Aucune map chargée (MAP_GRIDS).', 24, H / 2);
      return;
    }

    let cols = g.cols | 0;
    let rows = g.rows | 0;
    let { out, minV, maxV, maxAbs, L, R, n } = valuesForMode(g);
    // Extrude 1D maps so the surface still renders
    if (rows < 2 || cols < 2) {
      const src = out;
      const srcL = L, srcR = R;
      if (rows < 2) {
        rows = 2;
        const next = new Float64Array(cols * 2);
        const nL = [], nR = [];
        for (let c = 0; c < cols; c++) {
          next[c] = src[c] || 0;
          next[cols + c] = src[c] || 0;
          nL.push(srcL[c], srcL[c]);
          nR.push(srcR[c], srcR[c]);
        }
        // fix nL/nR layout: row-major
        const L2 = [], R2 = [];
        for (let r = 0; r < 2; r++) for (let c = 0; c < cols; c++) {
          L2.push(srcL[c]); R2.push(srcR[c]);
        }
        out = next; L = L2; R = R2; n = out.length;
      } else if (cols < 2) {
        cols = 2;
        const next = new Float64Array(rows * 2);
        const L2 = [], R2 = [];
        for (let r = 0; r < rows; r++) {
          next[r * 2] = src[r] || 0;
          next[r * 2 + 1] = src[r] || 0;
          L2.push(srcL[r], srcL[r]);
          R2.push(srcR[r], srcR[r]);
        }
        out = next; L = L2; R = R2; n = out.length;
      }
    }
    const keys = pairKeys();
    const isDiff = mode === 'diff';

    // build quads with average depth for painter's algorithm
    const quads = [];
    const scaleElev = isDiff ? (maxAbs || 1) : (maxV - minV || 1);
    const baseElev = isDiff ? 0 : minV;
    function elev(v) { return ((v - baseElev) / scaleElev) * 0.9; }
    for (let r = 0; r < rows - 1; r++) {
      for (let c = 0; c < cols - 1; c++) {
        const i00 = r * cols + c;
        const i10 = r * cols + (c + 1);
        const i01 = (r + 1) * cols + c;
        const i11 = (r + 1) * cols + (c + 1);
        if (i11 >= n) continue;
        const xs = [colToX(c, cols), colToX(c + 1, cols)];
        const zs = [rowToZ(r, rows), rowToZ(r + 1, rows)];
        const pts = [
          project(xs[0], elev(out[i00]), zs[0], W, H),
          project(xs[1], elev(out[i10]), zs[0], W, H),
          project(xs[1], elev(out[i11]), zs[1], W, H),
          project(xs[0], elev(out[i01]), zs[1], W, H),
        ];
        const avgZ = (pts[0].z + pts[1].z + pts[2].z + pts[3].z) / 4;
        const avgV = (out[i00] + out[i10] + out[i01] + out[i11]) / 4;
        const chg = Math.abs((R[i00] || 0) - (L[i00] || 0)) > 1e-9 ||
          Math.abs((R[i10] || 0) - (L[i10] || 0)) > 1e-9 ||
          Math.abs((R[i01] || 0) - (L[i01] || 0)) > 1e-9 ||
          Math.abs((R[i11] || 0) - (L[i11] || 0)) > 1e-9;
        quads.push({ pts, avgZ, avgV, chg, r, c });
      }
    }
    quads.sort((a, b) => b.avgZ - a.avgZ);

    // ground grid
    ctx.strokeStyle = 'rgba(80,100,120,0.25)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const t = (i / 4) * 2 - 1;
      const a = project(t, 0, -1, W, H);
      const b = project(t, 0, 1, W, H);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      const c = project(-1, 0, t, W, H);
      const d = project(1, 0, t, W, H);
      ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(d.x, d.y); ctx.stroke();
    }

    for (const q of quads) {
      const t = isDiff
        ? (q.avgV / (maxAbs || 1) + 1) / 2
        : (q.avgV - minV) / (maxV - minV || 1);
      ctx.beginPath();
      ctx.moveTo(q.pts[0].x, q.pts[0].y);
      for (let k = 1; k < 4; k++) ctx.lineTo(q.pts[k].x, q.pts[k].y);
      ctx.closePath();
      ctx.fillStyle = isDiff ? diffColor(q.avgV, maxAbs || 1) : heatColor(t);
      ctx.globalAlpha = 0.92;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = q.chg ? 'rgba(245,215,110,0.85)' : 'rgba(0,0,0,0.35)';
      ctx.lineWidth = q.chg ? 1.4 : 0.6;
      ctx.stroke();
    }

    // hover marker
    if (hover && hover.r < rows && hover.c < cols) {
      const i = hover.r * cols + hover.c;
      if (i < n) {
        const x = colToX(hover.c, cols);
        const z = rowToZ(hover.r, rows);
        const p = project(x, elev(out[i]), z, W, H);
        ctx.fillStyle = '#3ecf7a';
        ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#e8f0f8';
        ctx.font = '12px IBM Plex Mono, monospace';
        ctx.textAlign = 'left';
        const txt = '[' + hover.c + ',' + hover.r + '] = ' +
          (isDiff ? ((out[i] >= 0 ? '+' : '') + out[i].toFixed(2)) : out[i].toFixed(2)) +
          ' ' + (g.unit || '');
        ctx.fillText(txt, p.x + 10, p.y - 8);
      }
    }

    // axes labels
    ctx.fillStyle = '#8a9aaa';
    ctx.font = '12px Barlow, sans-serif';
    ctx.textAlign = 'left';
    const ax = g.axisXName || 'X';
    const ay = g.axisYName || 'Y';
    const depthDir = flipDepth ? ' (inversée)' : '';
    ctx.fillText(ax + (g.axisXUnit ? ' (' + g.axisXUnit + ')' : '') + ' → droite', 16, H - 18);
    ctx.fillText(ay + (g.axisYUnit ? ' (' + g.axisYUnit + ')' : '') + ' → profondeur' + depthDir, 16, H - 36);
    ctx.fillText('Z = ' + (g.unit || 'valeur') + ' (hauteur)', 16, H - 54);

    const Lk = keys[0], Rk = keys[1];
    if (metaEl) {
      metaEl.innerHTML =
        '<b>' + g.id + '</b> — ' + g.name +
        ' · <button class="addr" data-addr="' + g.addr + '">' + g.addr + '</button>' +
        ' · ' + cols + '×' + rows +
        ' · mode <b>' + (mode === 'diff' ? ('Écart ' + lab(Rk) + '−' + lab(Lk)) : (mode === 'left' ? lab(Lk) : lab(Rk))) + '</b>' +
        ' · Z ' + minV.toFixed(1) + ' … ' + maxV.toFixed(1) + ' ' + (g.unit || '') +
        ' · glisser = orbit · molette = zoom';
    }

    // sync mode button labels
    const bl = document.getElementById('v3d-mode-left');
    const br = document.getElementById('v3d-mode-right');
    const bd = document.getElementById('v3d-mode-diff');
    if (bl) bl.textContent = lab(Lk);
    if (br) br.textContent = lab(Rk);
    if (bd) bd.textContent = 'Écart ' + lab(Rk) + '−' + lab(Lk);
  }

  function openMap3d(id) {
    if (!id || !findGrid(id)) return;
    mapId = id;
    if ([...sel.options].some((o) => o.value === id)) sel.value = id;
    if (typeof window.showPage === 'function') window.showPage('view3d');
    draw();
  }

  function syncModeButtons() {
    document.querySelectorAll('#view3d .v3d-modes button').forEach((b) => {
      b.classList.toggle('on', b.dataset.mode === mode);
    });
  }

  fillSelect();
  sel.addEventListener('change', () => { mapId = sel.value; draw(); });
  document.querySelectorAll('#view3d .v3d-modes button').forEach((b) => {
    b.addEventListener('click', () => {
      mode = b.dataset.mode;
      syncModeButtons();
      draw();
    });
  });
  function syncFlipButton() {
    const btn = document.getElementById('v3d-flip');
    if (btn) btn.classList.toggle('on', flipDepth);
  }
  document.getElementById('v3d-reset')?.addEventListener('click', () => {
    rotY = -0.72; rotX = 0.58; zoom = 1; draw();
  });
  document.getElementById('v3d-flip')?.addEventListener('click', () => {
    flipDepth = !flipDepth;
    syncFlipButton();
    draw();
  });
  document.getElementById('v3d-to-2d')?.addEventListener('click', () => {
    if (typeof openMap2d === 'function') openMap2d(mapId);
    else if (typeof window.openMap2d === 'function') window.openMap2d(mapId);
  });

  canvas.addEventListener('mousedown', (e) => {
    drag = { x: e.clientX, y: e.clientY, rotX, rotY };
  });
  window.addEventListener('mousemove', (e) => {
    if (!drag) return;
    rotY = drag.rotY + (e.clientX - drag.x) * 0.008;
    rotX = Math.max(0.15, Math.min(1.35, drag.rotX + (e.clientY - drag.y) * 0.008));
    draw();
  });
  window.addEventListener('mouseup', () => { drag = null; });
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    zoom = Math.max(0.45, Math.min(2.8, zoom * (e.deltaY > 0 ? 0.92 : 1.08)));
    draw();
  }, { passive: false });

  // approximate hover by nearest projected cell
  canvas.addEventListener('mousemove', (e) => {
    if (drag) return;
    const g = findGrid(mapId);
    if (!g) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const W = rect.width, H = rect.height;
    const keys = pairKeys();
    const { out, minV, maxV, maxAbs, n } = valuesForMode(g);
    const isDiff = mode === 'diff';
    let best = null, bestD = 40;
    for (let r = 0; r < g.rows; r++) {
      for (let c = 0; c < g.cols; c++) {
        const i = r * g.cols + c;
        if (i >= n) continue;
        const x = colToX(c, g.cols);
        const z = rowToZ(r, g.rows);
        const scaleZ = isDiff ? (maxAbs || 1) : (maxV - minV || 1);
        const base = isDiff ? 0 : minV;
        const p = project(x, ((out[i] - base) / scaleZ) * 0.9, z, W, H);
        const d = Math.hypot(p.x - mx, p.y - my);
        if (d < bestD) { bestD = d; best = { r, c }; }
      }
    }
    const prev = hover;
    hover = best;
    if (JSON.stringify(prev) !== JSON.stringify(hover)) draw();
  });

  window.addEventListener('resize', () => draw());
  window.addEventListener('hashchange', () => {
    if (location.hash.replace(/^#/, '') === 'view3d') draw();
  });

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button.open3d');
    if (!btn) return;
    if (btn.closest('#maps-prio')) return;
    e.preventDefault();
    openMap3d(btn.dataset.mapId);
  });

  window.openMap3d = openMap3d;
  window.view3dRefreshPair = () => {
    fillSelect();
    syncModeButtons();
    draw();
  };

  // initial after MAP_GRIDS exists
  syncModeButtons();
  syncFlipButton();
  if (mapId) draw();
  else {
    const t = setInterval(() => {
      if (grids().length) {
        clearInterval(t);
        fillSelect();
        draw();
      }
    }, 50);
    setTimeout(() => clearInterval(t), 5000);
  }
})();

/* Aperçu 3D dans une fiche (canvas dédié, sans quitter l’onglet) */
window.mountMap3dPreview = function (canvas, mapId) {
  if (!canvas || !mapId) return { draw: function () {}, setMode: function () {}, destroy: function () {} };
  const ctx = canvas.getContext('2d');
  let rotY = -0.72;
  let rotX = 0.58;
  let zoom = 1.05;
  let mode = 'right';
  let drag = null;
  let destroyed = false;

  function grids() {
    return (typeof MAP_GRIDS !== 'undefined' && MAP_GRIDS) || window.MAP_GRIDS || [];
  }
  function findGrid(id) {
    const list = grids();
    return list.find((g) => g.id === id) || null;
  }
  function pairKeys() {
    if (window.COMPARE && window.COMPARE.sides) return window.COMPARE.sides();
    return ['ori', 'ace'];
  }
  function series(g, key) {
    if (!g) return [];
    if (key === 'v2') return g.v2 || g.v1 || g.ace || [];
    if (key === 'v1') return g.v1 || g.ace || [];
    return g[key] || [];
  }
  function heatColor(t) {
    t = Math.max(0, Math.min(1, t));
    const stops = [[20, 40, 90], [40, 170, 90], [220, 200, 40], [220, 60, 50]];
    const x = t * (stops.length - 1);
    const i = Math.floor(x);
    const f = x - i;
    const a = stops[Math.min(i, stops.length - 1)];
    const b = stops[Math.min(i + 1, stops.length - 1)];
    return 'rgb(' + Math.round(a[0] + (b[0] - a[0]) * f) + ',' +
      Math.round(a[1] + (b[1] - a[1]) * f) + ',' +
      Math.round(a[2] + (b[2] - a[2]) * f) + ')';
  }
  function diffColor(d, maxAbs) {
    const t = Math.max(-1, Math.min(1, d / (maxAbs || 1)));
    if (Math.abs(t) < 0.02) return 'rgb(40,48,56)';
    if (t > 0) return 'rgb(' + Math.round(40 + 180 * t) + ',' + Math.round(48 + 140 * t) + ',' + Math.round(56 - 20 * t) + ')';
    const k = -t;
    return 'rgb(' + Math.round(40 + 160 * k) + ',' + Math.round(48 - 10 * k) + ',' + Math.round(56 + 10 * k) + ')';
  }
  function project(x, y, z, W, H) {
    const cy = Math.cos(rotY), sy = Math.sin(rotY);
    const cx = Math.cos(rotX), sx = Math.sin(rotX);
    let x1 = x * cy + z * sy;
    let z1 = -x * sy + z * cy;
    let y1 = y * cx + z1 * sx;
    z1 = -y * sx + z1 * cx;
    const persp = 2.8 / (2.8 + z1);
    const s = 160 * zoom * persp;
    return { x: W * 0.5 + x1 * s, y: H * 0.55 - y1 * s, z: z1 };
  }
  function colToX(c, cols) { return (c / Math.max(1, cols - 1)) * 2 - 1; }
  function rowToZ(r, rows) { return (r / Math.max(1, rows - 1)) * 2 - 1; }

  function valuesFor(g) {
    const keys = pairKeys();
    const L = series(g, keys[0]);
    const R = series(g, keys[1]);
    const n = Math.min(L.length, R.length, (g.cols || 1) * (g.rows || 1));
    const out = new Float64Array(n);
    let minV = Infinity, maxV = -Infinity, maxAbs = 0;
    for (let i = 0; i < n; i++) {
      const v = mode === 'left' ? +L[i] : (mode === 'right' ? +R[i] : +R[i] - +L[i]);
      out[i] = v;
      if (Number.isFinite(v)) {
        minV = Math.min(minV, v);
        maxV = Math.max(maxV, v);
        maxAbs = Math.max(maxAbs, Math.abs(v));
      }
    }
    if (!Number.isFinite(minV)) { minV = 0; maxV = 1; }
    if (maxV <= minV) maxV = minV + 1;
    return { out, minV, maxV, maxAbs, L, R, n };
  }

  function resize() {
    const wrap = canvas.parentElement;
    const cssW = Math.max(280, (wrap && wrap.clientWidth) || 480);
    const cssH = 280;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.width = '100%';
    canvas.style.height = cssH + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function draw() {
    if (destroyed) return;
    resize();
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    ctx.clearRect(0, 0, W, H);
    const grd = ctx.createLinearGradient(0, 0, 0, H);
    grd.addColorStop(0, '#0c1218');
    grd.addColorStop(1, '#06080c');
    ctx.fillStyle = grd;
    ctx.fillRect(0, 0, W, H);

    const g = findGrid(mapId);
    if (!g) {
      ctx.fillStyle = '#8a9aaa';
      ctx.font = '13px Barlow, sans-serif';
      ctx.fillText('Map introuvable', 16, H / 2);
      return;
    }

    let cols = g.cols | 0;
    let rows = g.rows | 0;
    let { out, minV, maxV, maxAbs, L, R, n } = valuesFor(g);
    if (rows < 2 || cols < 2) {
      const src = out, srcL = L, srcR = R;
      if (rows < 2) {
        rows = 2;
        const next = new Float64Array(cols * 2);
        const L2 = [], R2 = [];
        for (let r = 0; r < 2; r++) for (let c = 0; c < cols; c++) {
          next[r * cols + c] = src[c] || 0;
          L2.push(srcL[c]); R2.push(srcR[c]);
        }
        out = next; L = L2; R = R2; n = out.length;
      } else {
        cols = 2;
        const next = new Float64Array(rows * 2);
        const L2 = [], R2 = [];
        for (let r = 0; r < rows; r++) {
          next[r * 2] = src[r] || 0;
          next[r * 2 + 1] = src[r] || 0;
          L2.push(srcL[r], srcL[r]);
          R2.push(srcR[r], srcR[r]);
        }
        out = next; L = L2; R = R2; n = out.length;
      }
    }

    const isDiff = mode === 'diff';
    const scaleElev = isDiff ? (maxAbs || 1) : (maxV - minV || 1);
    const baseElev = isDiff ? 0 : minV;
    function elev(v) { return ((v - baseElev) / scaleElev) * 0.9; }

    const quads = [];
    for (let r = 0; r < rows - 1; r++) {
      for (let c = 0; c < cols - 1; c++) {
        const i00 = r * cols + c;
        const i10 = r * cols + (c + 1);
        const i01 = (r + 1) * cols + c;
        const i11 = (r + 1) * cols + (c + 1);
        if (i11 >= n) continue;
        const pts = [
          project(colToX(c, cols), elev(out[i00]), rowToZ(r, rows), W, H),
          project(colToX(c + 1, cols), elev(out[i10]), rowToZ(r, rows), W, H),
          project(colToX(c + 1, cols), elev(out[i11]), rowToZ(r + 1, rows), W, H),
          project(colToX(c, cols), elev(out[i01]), rowToZ(r + 1, rows), W, H),
        ];
        const avgZ = (pts[0].z + pts[1].z + pts[2].z + pts[3].z) / 4;
        const avgV = (out[i00] + out[i10] + out[i01] + out[i11]) / 4;
        const chg = Math.abs((R[i00] || 0) - (L[i00] || 0)) > 1e-9 ||
          Math.abs((R[i10] || 0) - (L[i10] || 0)) > 1e-9 ||
          Math.abs((R[i01] || 0) - (L[i01] || 0)) > 1e-9 ||
          Math.abs((R[i11] || 0) - (L[i11] || 0)) > 1e-9;
        quads.push({ pts, avgZ, avgV, chg });
      }
    }
    quads.sort((a, b) => b.avgZ - a.avgZ);

    ctx.strokeStyle = 'rgba(80,100,120,0.22)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const t = (i / 4) * 2 - 1;
      const a = project(t, 0, -1, W, H);
      const b = project(t, 0, 1, W, H);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      const c = project(-1, 0, t, W, H);
      const d = project(1, 0, t, W, H);
      ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(d.x, d.y); ctx.stroke();
    }

    for (const q of quads) {
      const t = isDiff
        ? (q.avgV / (maxAbs || 1) + 1) / 2
        : (q.avgV - minV) / (maxV - minV || 1);
      ctx.beginPath();
      ctx.moveTo(q.pts[0].x, q.pts[0].y);
      for (let k = 1; k < 4; k++) ctx.lineTo(q.pts[k].x, q.pts[k].y);
      ctx.closePath();
      ctx.fillStyle = isDiff ? diffColor(q.avgV, maxAbs || 1) : heatColor(t);
      ctx.globalAlpha = 0.92;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.strokeStyle = q.chg ? 'rgba(245,215,110,0.85)' : 'rgba(0,0,0,0.35)';
      ctx.lineWidth = q.chg ? 1.2 : 0.5;
      ctx.stroke();
    }
  }

  function onDown(e) {
    const p = e.touches ? e.touches[0] : e;
    drag = { x: p.clientX, y: p.clientY, rotX, rotY };
  }
  function onMove(e) {
    if (!drag) return;
    const p = e.touches ? e.touches[0] : e;
    rotY = drag.rotY + (p.clientX - drag.x) * 0.008;
    rotX = Math.max(0.15, Math.min(1.35, drag.rotX + (p.clientY - drag.y) * 0.008));
    draw();
  }
  function onUp() { drag = null; }
  function onWheel(e) {
    e.preventDefault();
    zoom = Math.max(0.45, Math.min(2.8, zoom * (e.deltaY > 0 ? 0.92 : 1.08)));
    draw();
  }

  function onTouchMove(e) {
    e.preventDefault();
    onMove(e);
  }
  canvas.addEventListener('mousedown', onDown);
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
  canvas.addEventListener('touchstart', onDown, { passive: true });
  canvas.addEventListener('touchmove', onTouchMove, { passive: false });
  canvas.addEventListener('touchend', onUp);
  canvas.addEventListener('wheel', onWheel, { passive: false });
  const onWinResize = () => draw();
  window.addEventListener('resize', onWinResize);
  requestAnimationFrame(draw);

  return {
    draw,
    setMode: function (m) { mode = m; draw(); },
    destroy: function () {
      destroyed = true;
      canvas.removeEventListener('mousedown', onDown);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      canvas.removeEventListener('touchstart', onDown);
      canvas.removeEventListener('touchmove', onTouchMove);
      canvas.removeEventListener('touchend', onUp);
      canvas.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', onWinResize);
    }
  };
};
