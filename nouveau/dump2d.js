/* Dump 2D — WinOLS-style binary line chart (hex-atlas windows) */
(function () {
  const ATLAS_URL = '../data/hex-atlas.json';
  const canvas = document.getElementById('d2-canvas');
  const statusEl = document.getElementById('d2-status');
  const metaEl = document.getElementById('d2-meta');
  const addrInput = document.getElementById('d2-addr');
  if (!canvas || !addrInput) return;

  const ctx = canvas.getContext('2d');
  let atlas = null;
  let windows = [];
  let bitWidth = 16; // 8 | 16 LoHi
  let cursor = 0x1CF9C0;
  let viewStart = cursor;
  let span = 256; // samples; 0 = full window
  let drag = null;

  function hx(n, w) {
    return (n >>> 0).toString(16).toUpperCase().padStart(w || 6, '0');
  }
  function parseAddr(s) {
    const t = String(s || '').trim().replace(/^0x/i, '');
    if (!/^[0-9a-fA-F]{1,8}$/.test(t)) return null;
    return parseInt(t, 16);
  }
  function b64ToBytes(b64) {
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function setStatus(t) {
    if (statusEl) statusEl.textContent = t;
  }
  function pairKeys() {
    if (window.COMPARE && window.COMPARE.sides) return window.COMPARE.sides();
    return ['ori', 'ace'];
  }
  function pairLabs() {
    const k = pairKeys();
    const lab = (x) => (window.COMPARE && window.COMPARE.label ? window.COMPARE.label(x) : x.toUpperCase());
    return [lab(k[0]), lab(k[1])];
  }
  function sideBytes(w, key) {
    if (key === 'v2') return w.v2 || w.v1 || w.ace;
    if (key === 'v1') return w.v1 || w.ace;
    return w[key];
  }
  function findWindow(addr) {
    for (const w of windows) {
      if (addr >= w.start && addr < w.start + w.ori.length) return w;
    }
    return null;
  }
  function nearestWindow(addr) {
    let best = null, bestDist = Infinity;
    for (const w of windows) {
      const end = w.start + w.ori.length - 1;
      const dist = addr < w.start ? w.start - addr : (addr > end ? addr - end : 0);
      if (dist < bestDist) { bestDist = dist; best = w; }
    }
    return best;
  }
  function readVal(bytes, off, width) {
    if (off < 0 || off >= bytes.length) return null;
    if (width === 8) return bytes[off];
    if (off + 1 >= bytes.length) return null;
    return bytes[off] | (bytes[off + 1] << 8); // LoHi
  }
  function step() { return bitWidth === 8 ? 1 : 2; }

  function resizeCanvas() {
    const wrap = canvas.parentElement;
    const cssW = Math.max(640, (wrap && wrap.clientWidth) || 1200);
    const cssH = 360;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function sampleSeries(w, key, startAddr, count) {
    const bytes = sideBytes(w, key);
    const st = step();
    const out = [];
    for (let i = 0; i < count; i++) {
      const abs = startAddr + i * st;
      const off = abs - w.start;
      const v = readVal(bytes, off, bitWidth);
      out.push(v == null ? NaN : v);
    }
    return out;
  }

  function draw() {
    resizeCanvas();
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#0a1014';
    ctx.fillRect(0, 0, W, H);

    const pad = { l: 54, r: 16, t: 18, b: 36 };
    const plotW = W - pad.l - pad.r;
    const plotH = H - pad.t - pad.b;

    let w = findWindow(cursor);
    if (!w) w = nearestWindow(cursor);
    if (!w) {
      ctx.fillStyle = '#8a9aaa';
      ctx.font = '14px Barlow, sans-serif';
      ctx.fillText('Atlas non chargé ou adresse hors zones.', pad.l, H / 2);
      setStatus('Hors atlas');
      return;
    }

    const winEnd = w.start + w.ori.length;
    const st = step();
    const maxSamples = Math.floor(w.ori.length / st);
    let nSamp = span > 0 ? span : maxSamples;
    nSamp = Math.max(8, Math.min(nSamp, maxSamples));

    // align viewStart
    viewStart = Math.max(w.start, Math.min(viewStart, winEnd - nSamp * st));
    viewStart = w.start + Math.floor((viewStart - w.start) / st) * st;
    if (cursor < w.start || cursor >= winEnd) cursor = viewStart;

    const keys = pairKeys();
    const labs = pairLabs();
    const left = sampleSeries(w, keys[0], viewStart, nSamp);
    const right = sampleSeries(w, keys[1], viewStart, nSamp);

    let minV = Infinity, maxV = -Infinity;
    for (let i = 0; i < nSamp; i++) {
      const a = left[i], b = right[i];
      if (!Number.isNaN(a)) { minV = Math.min(minV, a); maxV = Math.max(maxV, a); }
      if (!Number.isNaN(b)) { minV = Math.min(minV, b); maxV = Math.max(maxV, b); }
    }
    if (!Number.isFinite(minV)) { minV = 0; maxV = bitWidth === 8 ? 255 : 65535; }
    if (maxV <= minV) maxV = minV + 1;
    const yPad = (maxV - minV) * 0.06;
    minV -= yPad; maxV += yPad;

    // grid
    ctx.strokeStyle = '#1c2a32';
    ctx.lineWidth = 1;
    for (let g = 0; g <= 4; g++) {
      const y = pad.t + (plotH * g) / 4;
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + plotW, y); ctx.stroke();
      const val = maxV - ((maxV - minV) * g) / 4;
      ctx.fillStyle = '#6a7a86';
      ctx.font = '11px IBM Plex Mono, monospace';
      ctx.textAlign = 'right';
      ctx.fillText(String(Math.round(val)), pad.l - 8, y + 4);
    }

    function xAt(i) { return pad.l + (i / Math.max(1, nSamp - 1)) * plotW; }
    function yAt(v) { return pad.t + (1 - (v - minV) / (maxV - minV)) * plotH; }

    // diff bands
    for (let i = 0; i < nSamp; i++) {
      if (Number.isNaN(left[i]) || Number.isNaN(right[i])) continue;
      if (left[i] === right[i]) continue;
      const x0 = xAt(i) - (plotW / nSamp) * 0.45;
      const x1 = xAt(i) + (plotW / nSamp) * 0.45;
      ctx.fillStyle = 'rgba(245,215,110,0.18)';
      ctx.fillRect(x0, pad.t, Math.max(1, x1 - x0), plotH);
    }

    function strokeSeries(arr, color, width) {
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < nSamp; i++) {
        if (Number.isNaN(arr[i])) { started = false; continue; }
        const x = xAt(i), y = yAt(arr[i]);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    strokeSeries(left, '#d8e4ef', 1.6);
    strokeSeries(right, '#e23a1a', 1.8);

    // cursor
    const curOff = Math.floor((cursor - viewStart) / st);
    if (curOff >= 0 && curOff < nSamp) {
      const cx = xAt(curOff);
      ctx.strokeStyle = '#3ecf7a';
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 3]);
      ctx.beginPath(); ctx.moveTo(cx, pad.t); ctx.lineTo(cx, pad.t + plotH); ctx.stroke();
      ctx.setLineDash([]);
      const lv = left[curOff], rv = right[curOff];
      if (!Number.isNaN(lv)) {
        ctx.fillStyle = '#d8e4ef';
        ctx.beginPath(); ctx.arc(cx, yAt(lv), 4, 0, Math.PI * 2); ctx.fill();
      }
      if (!Number.isNaN(rv)) {
        ctx.fillStyle = '#e23a1a';
        ctx.beginPath(); ctx.arc(cx, yAt(rv), 4, 0, Math.PI * 2); ctx.fill();
      }
    }

    // x labels
    ctx.fillStyle = '#6a7a86';
    ctx.font = '11px IBM Plex Mono, monospace';
    ctx.textAlign = 'center';
    const ticks = 6;
    for (let t = 0; t <= ticks; t++) {
      const i = Math.round((t / ticks) * (nSamp - 1));
      const addr = viewStart + i * st;
      ctx.fillText(hx(addr), xAt(i), H - 12);
    }

    let diffN = 0;
    for (let i = 0; i < nSamp; i++) {
      if (!Number.isNaN(left[i]) && !Number.isNaN(right[i]) && left[i] !== right[i]) diffN++;
    }
    const curI = Math.floor((cursor - viewStart) / st);
    const lv = curI >= 0 && curI < nSamp ? left[curI] : NaN;
    const rv = curI >= 0 && curI < nSamp ? right[curI] : NaN;
    if (metaEl) {
      metaEl.innerHTML =
        'Zone <b>' + hx(w.start) + '</b>–<b>' + hx(winEnd - 1) + '</b> · vue <b>' + hx(viewStart) + '</b> · ' +
        nSamp + ' pts · ' + bitWidth + '-bit LoHi · diffs <b>' + diffN + '</b> · curseur <b>' + hx(cursor) + '</b>' +
        (Number.isNaN(lv) ? '' : (' · ' + labs[0] + ' <b>' + lv + '</b>')) +
        (Number.isNaN(rv) ? '' : (' · ' + labs[1] + ' <b>' + rv + '</b>'));
    }
    document.querySelectorAll('.d2-legend span').forEach((span, idx) => {
      if (idx === 0) span.innerHTML = '<i class="d2-l"></i> ' + labs[0];
      if (idx === 1) span.innerHTML = '<i class="d2-r"></i> ' + labs[1];
    });

    setStatus('OK · ' + labs[0] + ' / ' + labs[1]);
    addrInput.value = hx(cursor);
  }

  function gotoAddr(addr, opts) {
    opts = opts || {};
    if (addr == null || addr < 0) {
      if (!opts.silent) setStatus('Adresse invalide');
      return;
    }
    cursor = addr >>> 0;
    let w = findWindow(cursor);
    if (!w) {
      w = nearestWindow(cursor);
      if (w && (cursor < w.start || cursor >= w.start + w.ori.length)) {
        cursor = w.start;
      }
    }
    const st = step();
    const nSamp = span > 0 ? span : 256;
    if (w) {
      viewStart = cursor - Math.floor(nSamp / 2) * st;
      viewStart = Math.max(w.start, viewStart);
    } else {
      viewStart = cursor;
    }
    draw();
    if (opts.syncHex && typeof window.hexGoto === 'function') {
      window.hexGoto(cursor, { silent: true });
    }
  }

  function addrFromClientX(clientX) {
    const rect = canvas.getBoundingClientRect();
    const W = rect.width;
    const padL = 54, padR = 16;
    const plotW = W - padL - padR;
    let x = clientX - rect.left - padL;
    x = Math.max(0, Math.min(plotW, x));
    const w = findWindow(cursor) || nearestWindow(cursor);
    if (!w) return null;
    const st = step();
    const maxSamples = Math.floor(w.ori.length / st);
    let nSamp = span > 0 ? span : maxSamples;
    nSamp = Math.max(8, Math.min(nSamp, maxSamples));
    const i = Math.round((x / plotW) * (nSamp - 1));
    return viewStart + i * st;
  }

  document.getElementById('d2-go')?.addEventListener('click', () => {
    const a = parseAddr(addrInput.value);
    if (a == null) { setStatus('Adresse hex invalide'); return; }
    gotoAddr(a, { syncHex: true });
  });
  addrInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      document.getElementById('d2-go')?.click();
    }
  });
  document.getElementById('d2-prev')?.addEventListener('click', () => {
    const st = step();
    const n = span > 0 ? span : 128;
    gotoAddr(Math.max(0, cursor - Math.floor(n / 2) * st), { syncHex: true });
  });
  document.getElementById('d2-next')?.addEventListener('click', () => {
    const st = step();
    const n = span > 0 ? span : 128;
    gotoAddr(cursor + Math.floor(n / 2) * st, { syncHex: true });
  });
  document.querySelector('#dump2d .hex-modes')?.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-d2-width]');
    if (!btn) return;
    bitWidth = parseInt(btn.getAttribute('data-d2-width'), 10) || 16;
    document.querySelectorAll('#dump2d [data-d2-width]').forEach((b) => b.classList.toggle('on', b === btn));
    draw();
  });
  document.getElementById('d2-span')?.addEventListener('change', (e) => {
    span = parseInt(e.target.value, 10) || 0;
    gotoAddr(cursor);
  });
  document.getElementById('d2-to-hex')?.addEventListener('click', () => {
    if (typeof window.showPage === 'function') window.showPage('hexdump');
    if (typeof window.hexGoto === 'function') window.hexGoto(cursor, { scroll: true });
  });

  canvas.addEventListener('click', (e) => {
    const a = addrFromClientX(e.clientX);
    if (a == null) return;
    gotoAddr(a, { syncHex: true });
  });
  canvas.addEventListener('dblclick', () => gotoAddr(cursor));
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    const opts = [128, 256, 512, 1024, 0];
    let idx = opts.indexOf(span);
    if (idx < 0) idx = 1;
    idx = e.deltaY > 0 ? Math.min(opts.length - 1, idx + 1) : Math.max(0, idx - 1);
    span = opts[idx];
    const sel = document.getElementById('d2-span');
    if (sel) sel.value = String(span);
    gotoAddr(cursor);
  }, { passive: false });
  canvas.addEventListener('mousedown', (e) => {
    drag = { x: e.clientX, start: viewStart };
  });
  window.addEventListener('mousemove', (e) => {
    if (!drag) return;
    const st = step();
    const dx = e.clientX - drag.x;
    const nSamp = span > 0 ? span : 256;
    const shift = Math.round((-dx / Math.max(1, canvas.clientWidth - 70)) * nSamp) * st;
    viewStart = drag.start + shift;
    cursor = viewStart + Math.floor(nSamp / 2) * st;
    draw();
  });
  window.addEventListener('mouseup', () => { drag = null; });
  window.addEventListener('resize', () => draw());

  window.dump2dGoto = gotoAddr;
  window.dump2dRefreshPair = () => draw();

  // Prefer atlas already loaded by hex dump if available
  function ingest(data) {
    atlas = data;
    windows = (data.windows || []).map((w) => ({
      start: w.start,
      ori: typeof w.ori === 'string' ? b64ToBytes(w.ori) : w.ori,
      ace: typeof w.ace === 'string' ? b64ToBytes(w.ace) : w.ace,
      v1: typeof w.v1 === 'string' ? b64ToBytes(w.v1 || w.ace) : (w.v1 || w.ace),
      v2: typeof w.v2 === 'string' ? b64ToBytes(w.v2 || w.v1 || w.ace) : (w.v2 || w.v1 || w.ace),
    }));
    setStatus('Atlas OK · ' + data.windowCount + ' zones');
    const prio = (data.priority && data.priority[0] && data.priority[0].addr) || 0x1CF9C0;
    gotoAddr(prio);
  }

  if (window.__hexAtlasData) {
    ingest(window.__hexAtlasData);
  } else {
    setStatus('Chargement atlas…');
    fetch(ATLAS_URL)
      .then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(ingest)
      .catch((err) => {
        setStatus('Échec atlas');
        if (metaEl) metaEl.textContent = 'Impossible de charger data/hex-atlas.json — ' + (err.message || err);
      });
  }

  window.addEventListener('hex-atlas-ready', (e) => {
    if (e.detail) ingest(e.detail);
  });
})();
