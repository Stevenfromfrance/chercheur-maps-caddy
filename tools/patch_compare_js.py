# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "index.html"
t = p.read_text(encoding="utf-8")
start = t.find("let v2dMode = 'diff';")
close = t.find("\n</script>\n\n<script>\n</script>", start)
if start < 0 or close < 0:
    raise SystemExit(f"markers not found start={start} close={close}")

new_js = r'''
window.COMPARE = {
  pair: 'ori-ace',
  hints: {
    'ori-ace': 'Stage1 ACE (réf. préparateur)',
    'ori-v1': 'Ta carto V1 vs stock (partiels soft · WOT 350 · hardcut 4800)',
    'ace-v1': 'Écart V1 sur base ACE (ce que tu as retouché)'
  },
  sides: function () {
    if (this.pair === 'ori-v1') return ['ori', 'v1'];
    if (this.pair === 'ace-v1') return ['ace', 'v1'];
    return ['ori', 'ace'];
  },
  label: function (key) {
    return ({ ori: 'ORI', ace: 'ACE', v1: 'V1' })[key] || key.toUpperCase();
  }
};

let v2dMode = 'diff';
let v2dId = (MAP_GRIDS[0] && MAP_GRIDS[0].id) || '';

function series(g, key) {
  if (key === 'v1') return (g.v1 && g.v1.length) ? g.v1 : g.ace;
  return g[key];
}
function seriesMax(g, key) {
  if (key === 'v1') return (g.v1Max != null) ? g.v1Max : g.aceMax;
  if (key === 'ori') return g.oriMax;
  return g.aceMax;
}
function changedCount(g) {
  const sides = window.COMPARE.sides();
  const L = sides[0], R = sides[1];
  if (L === 'ori' && R === 'ace') return g.changedCells;
  if (L === 'ori' && R === 'v1') return g.changedCellsV1Ori != null ? g.changedCellsV1Ori : g.changedCells;
  if (L === 'ace' && R === 'v1') return g.changedCellsV1Ace != null ? g.changedCellsV1Ace : 0;
  return g.changedCells;
}

function heatColor(t) {
  t = Math.max(0, Math.min(1, t));
  const stops = [
    [0.00, [20, 40, 90]],
    [0.25, [30, 120, 180]],
    [0.50, [40, 170, 90]],
    [0.75, [220, 180, 40]],
    [1.00, [220, 60, 50]],
  ];
  let a = stops[0], b = stops[stops.length - 1];
  for (let i = 0; i < stops.length - 1; i++) {
    if (t >= stops[i][0] && t <= stops[i + 1][0]) { a = stops[i]; b = stops[i + 1]; break; }
  }
  const u = (t - a[0]) / ((b[0] - a[0]) || 1);
  const rgb = a[1].map((v, i) => Math.round(v + (b[1][i] - v) * u));
  return 'rgb(' + rgb.join(',') + ')';
}

function diffColor(d, maxAbs) {
  if (!maxAbs || Math.abs(d) < 1e-9) return '#1a2430';
  const t = Math.min(1, Math.abs(d) / maxAbs);
  if (d > 0) {
    const g = Math.round(40 + 140 * t);
    const r = Math.round(30 + 180 * t);
    return 'rgb(' + r + ',' + g + ',40)';
  }
  const r = Math.round(80 + 140 * t);
  return 'rgb(' + r + ',50,50)';
}

function fmt(v, prec) {
  if (!Number.isFinite(v)) return '—';
  return Number(v).toFixed(prec == null ? 1 : prec);
}

function findGrid(id) {
  return MAP_GRIDS.find((g) => g.id === id) || MAP_GRIDS[0];
}

function buildTable(g, mode, title) {
  const sides = window.COMPARE.sides();
  const Lk = sides[0], Rk = sides[1];
  const left = series(g, Lk);
  const right = series(g, Rk);
  const Llab = window.COMPARE.label(Lk);
  const Rlab = window.COMPARE.label(Rk);
  const cols = g.cols || 1;
  const rows = Math.max(1, Math.ceil(left.length / cols));
  const prec = g.precision != null ? g.precision : 1;
  let minV = Infinity, maxV = -Infinity, maxAbs = 0;
  for (let i = 0; i < left.length; i++) {
    const o = left[i], a = right[i], d = a - o;
    if (mode === 'left' || mode === 'ori') { minV = Math.min(minV, o); maxV = Math.max(maxV, o); }
    else if (mode === 'right' || mode === 'ace') { minV = Math.min(minV, a); maxV = Math.max(maxV, a); }
    else { maxAbs = Math.max(maxAbs, Math.abs(d)); }
  }
  if (mode !== 'diff' && !(maxV > minV)) { minV = 0; maxV = 1; }

  let html = '<div class="v2d-pane"><h4>' + title + '</h4><table class="winols"><thead><tr>';
  html += '<th class="corner">' + (g.axisYName || 'Y') + ' \\ ' + (g.axisXName || 'X') + '</th>';
  for (let c = 0; c < cols; c++) {
    const xv = g.axisX && g.axisX[c] != null ? g.axisX[c] : c;
    const xu = g.axisXUnit ? ' ' + g.axisXUnit : '';
    html += '<th title="X[' + c + ']">' + xv + xu + '</th>';
  }
  html += '</tr></thead><tbody>';

  for (let r = 0; r < rows; r++) {
    const yv = g.axisY && g.axisY[r] != null ? g.axisY[r] : r;
    const yu = g.axisYUnit ? ' ' + g.axisYUnit : '';
    html += '<tr><td class="axis" title="Y[' + r + ']">' + yv + yu + '</td>';
    for (let c = 0; c < cols; c++) {
      const i = r * cols + c;
      if (i >= left.length) { html += '<td class="cell"> </td>'; continue; }
      const o = left[i], a = right[i], d = a - o;
      const chg = o !== a;
      let show, bg, tip;
      const m = (mode === 'ori') ? 'left' : (mode === 'ace' ? 'right' : mode);
      if (m === 'left') {
        show = fmt(o, prec);
        bg = heatColor((o - minV) / (maxV - minV));
        tip = Llab + ' ' + show + ' ' + g.unit;
      } else if (m === 'right') {
        show = fmt(a, prec);
        bg = heatColor((a - minV) / (maxV - minV));
        tip = Rlab + ' ' + show + ' ' + g.unit;
      } else {
        show = (d > 0 ? '+' : '') + fmt(d, prec);
        bg = diffColor(d, maxAbs);
        tip = Llab + ' ' + fmt(o, prec) + ' → ' + Rlab + ' ' + fmt(a, prec) + ' (' + show + ' ' + g.unit + ')';
      }
      const cls = 'cell' + (chg ? ' chg' : ' same');
      html += '<td class="' + cls + '" style="background:' + bg + '" data-tip="' + tip.replace(/"/g, '&quot;') + '">' + show + '</td>';
    }
    html += '</tr>';
  }
  html += '</tbody></table></div>';
  return html;
}

function syncPairLabels() {
  const sides = window.COMPARE.sides();
  const Lk = sides[0], Rk = sides[1];
  const L = window.COMPARE.label(Lk);
  const R = window.COMPARE.label(Rk);
  const hint = document.getElementById('pair-hint');
  if (hint) hint.textContent = window.COMPARE.hints[window.COMPARE.pair] || '';
  const setTxt = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
  setTxt('v2d-mode-left', L);
  setTxt('v2d-mode-right', R);
  setTxt('v2d-mode-diff', 'Écart ' + R + '−' + L);
  setTxt('hex-mode-left', L);
  setTxt('hex-mode-right', R);
  setTxt('hex-mode-split', L + ' | ' + R);
  document.querySelectorAll('button.open2d').forEach((b) => {
    b.textContent = 'Voir grille 2D ' + L + ' / ' + R;
  });
  document.querySelectorAll('#maps-prio article').forEach((art) => {
    const btn = art.querySelector('button.open2d');
    if (!btn) return;
    const id = btn.getAttribute('data-map-id');
    const g = findGrid(id);
    if (!g) return;
    const vals = art.querySelector('.vals');
    if (!vals) return;
    const lo = seriesMax(g, Lk), hi = seriesMax(g, Rk);
    const d = hi - lo;
    const cls = d > 0.05 ? 'up' : (d < -0.05 ? 'down' : '');
    let dTxt = (d >= 0 ? '+' : '') + Number(d).toFixed(1);
    let hiTxt = String(hi);
    if (g.id === 'vmax3' && hi > 500) { hiTxt = 'desactive (FFFF)'; dTxt = 'off'; }
    vals.innerHTML = L + ' max <b>' + lo + '</b> → ' + R + ' <b>' + hiTxt + '</b> <span class="' + cls + '">' + dTxt + '</span>';
  });
}

function renderView2d() {
  const g = findGrid(v2dId);
  if (!g) return;
  const sides = window.COMPARE.sides();
  const Lk = sides[0], Rk = sides[1];
  const L = window.COMPARE.label(Lk);
  const R = window.COMPARE.label(Rk);
  const meta = document.getElementById('v2d-meta');
  const host = document.getElementById('v2d-grids');
  meta.innerHTML =
    '<b>' + g.id + '</b> — ' + g.name +
    ' · <button class="addr" data-addr="' + g.addr + '">' + g.addr + '</button> → ' +
    '<button class="addr" data-addr="' + g.end + '">' + g.end + '</button>' +
    ' · ' + g.cols + '×' + g.rows + ' · unité <b>' + (g.unit || '—') + '</b>' +
    ' · cellules modifiées <b>' + changedCount(g) + '</b> / ' + g.ori.length +
    ' · max ' + L + ' <b>' + seriesMax(g, Lk) + '</b> → ' + R + ' <b>' + seriesMax(g, Rk) + '</b>';

  if (v2dMode === 'split') {
    host.className = 'v2d-wrap v2d-split';
    host.innerHTML = buildTable(g, 'left', L) + buildTable(g, 'right', R);
  } else {
    host.className = 'v2d-wrap';
    const titles = {
      left: L,
      right: R,
      ori: L,
      ace: R,
      diff: 'Écart ' + R + ' − ' + L + ' (jaune = case touchée)'
    };
    host.innerHTML = buildTable(g, v2dMode, titles[v2dMode] || v2dMode);
  }
}

function openMap2d(id) {
  if (!id || !findGrid(id)) return;
  v2dId = id;
  const sel = document.getElementById('v2d-map');
  if (sel) sel.value = id;
  document.querySelectorAll('.v2d-modes button').forEach((b) => {
    b.classList.toggle('on', b.dataset.mode === v2dMode);
  });
  renderView2d();
  const sec = document.getElementById('view2d');
  if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function applyComparePair(pair) {
  window.COMPARE.pair = pair;
  document.querySelectorAll('.pair-btn').forEach((b) => {
    b.classList.toggle('on', b.getAttribute('data-pair') === pair);
  });
  syncPairLabels();
  renderView2d();
  if (typeof window.hexRefreshPair === 'function') window.hexRefreshPair();
  try { localStorage.setItem('chercheur-compare-pair', pair); } catch (_) {}
}

(function initView2d() {
  const sel = document.getElementById('v2d-map');
  if (!sel || !MAP_GRIDS.length) return;
  sel.innerHTML = MAP_GRIDS.map((g) =>
    '<option value="' + g.id + '">' + g.id + ' — ' + g.name + ' (' + g.addr + ')</option>'
  ).join('');
  sel.value = v2dId;
  sel.addEventListener('change', () => { v2dId = sel.value; renderView2d(); });
  document.querySelectorAll('.v2d-modes button').forEach((b) => {
    b.addEventListener('click', () => {
      v2dMode = b.dataset.mode;
      document.querySelectorAll('.v2d-modes button').forEach((x) => x.classList.toggle('on', x === b));
      renderView2d();
    });
  });
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button.open2d');
    if (btn) { e.preventDefault(); openMap2d(btn.dataset.mapId); }
  });
  document.querySelector('.pair-bar')?.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-pair]');
    if (!btn) return;
    applyComparePair(btn.getAttribute('data-pair'));
  });
  const tip = document.getElementById('v2d-tip');
  document.getElementById('v2d-grids').addEventListener('mousemove', (e) => {
    const td = e.target.closest('td.cell');
    if (!td || !td.dataset.tip) { tip.style.display = 'none'; return; }
    tip.style.display = 'block';
    tip.innerHTML = td.dataset.tip;
    tip.style.left = Math.min(e.clientX + 14, window.innerWidth - 300) + 'px';
    tip.style.top = (e.clientY + 14) + 'px';
  });
  document.getElementById('v2d-grids').addEventListener('mouseleave', () => { tip.style.display = 'none'; });
  let saved = 'ori-ace';
  try { saved = localStorage.getItem('chercheur-compare-pair') || 'ori-ace'; } catch (_) {}
  applyComparePair(saved);
})();

'''

p.write_text(t[:start] + new_js + t[close:], encoding="utf-8")
print("OK replaced", start, "->", close)
