# -*- coding: utf-8 -*-
"""Patch hex-dump-js for ORI/ACE/V1 pair compare."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "index.html"
t = p.read_text(encoding="utf-8")

old_mode = "  let mode = 'ace';"
new_mode = "  let mode = 'right';"
if old_mode not in t:
    raise SystemExit("mode marker missing")
t = t.replace(old_mode, new_mode, 1)

# Replace renderBytes + renderAscii + related helpers block
old_rb = '''  function renderBytes(w, off, which, selAddr) {
    let html = '';
    for (let i = 0; i < COLS; i++) {
      const abs = w.start + off + i;
      if (off + i >= w.ori.length) {
        html += '<span class="byte gap">··</span>';
        continue;
      }
      const o = w.ori[off + i];
      const a = w.ace[off + i];
      const v = which === 'ori' ? o : a;
      const cls = ['byte'];
      if (o !== a) cls.push('diff');
      if (abs === selAddr) cls.push('sel');
      html += '<span class="' + cls.join(' ') + '" title="' + hx(abs) + ' ORI=' + hx(o, 2) + ' ACE=' + hx(a, 2) + '">' + hx(v, 2) + '</span>';
    }
    return html;
  }
  function renderAscii(w, off, which) {
    let s = '';
    for (let i = 0; i < COLS; i++) {
      if (off + i >= w.ori.length) { s += ' '; continue; }
      const v = which === 'ori' ? w.ori[off + i] : w.ace[off + i];
      s += asciiChar(v);
    }
    return s;
  }'''

new_rb = '''  function sideBytes(w, key) {
    if (key === 'v1') return w.v1 || w.ace;
    return w[key];
  }
  function pairKeys() {
    if (window.COMPARE && window.COMPARE.sides) return window.COMPARE.sides();
    return ['ori', 'ace'];
  }
  function pairLabs() {
    const keys = pairKeys();
    const lab = (k) => (window.COMPARE && window.COMPARE.label) ? window.COMPARE.label(k) : k.toUpperCase();
    return [lab(keys[0]), lab(keys[1]), keys[0], keys[1]];
  }
  function renderBytes(w, off, which, selAddr) {
    const labs = pairLabs();
    const Lk = labs[2], Rk = labs[3];
    const Llab = labs[0], Rlab = labs[1];
    const left = sideBytes(w, Lk);
    const right = sideBytes(w, Rk);
    let html = '';
    for (let i = 0; i < COLS; i++) {
      const abs = w.start + off + i;
      if (off + i >= w.ori.length) {
        html += '<span class="byte gap">··</span>';
        continue;
      }
      const o = left[off + i];
      const a = right[off + i];
      const v = which === 'left' || which === 'ori' ? o : a;
      const cls = ['byte'];
      if (o !== a) cls.push('diff');
      if (abs === selAddr) cls.push('sel');
      html += '<span class="' + cls.join(' ') + '" title="' + hx(abs) + ' ' + Llab + '=' + hx(o, 2) + ' ' + Rlab + '=' + hx(a, 2) + '">' + hx(v, 2) + '</span>';
    }
    return html;
  }
  function renderAscii(w, off, which) {
    const keys = pairKeys();
    const arr = sideBytes(w, (which === 'left' || which === 'ori') ? keys[0] : keys[1]);
    let s = '';
    for (let i = 0; i < COLS; i++) {
      if (off + i >= w.ori.length) { s += ' '; continue; }
      s += asciiChar(arr[off + i]);
    }
    return s;
  }'''

if old_rb not in t:
    raise SystemExit("renderBytes block missing")
t = t.replace(old_rb, new_rb, 1)

# Patch changedInView and split render inside render()
old_chg = '''    const changedInView = (() => {
      let n = 0;
      for (let a = start; a < Math.min(start + lines * COLS, winEnd); a++) {
        const i = a - w.start;
        if (w.ori[i] !== w.ace[i]) n++;
      }
      return n;
    })();'''

new_chg = '''    const changedInView = (() => {
      const keys = pairKeys();
      const left = sideBytes(w, keys[0]);
      const right = sideBytes(w, keys[1]);
      let n = 0;
      for (let a = start; a < Math.min(start + lines * COLS, winEnd); a++) {
        const i = a - w.start;
        if (left[i] !== right[i]) n++;
      }
      return n;
    })();'''

if old_chg not in t:
    raise SystemExit("changedInView missing")
t = t.replace(old_chg, new_chg, 1)

old_split = '''    if (mode === 'split') {
      let left = '', right = '';
      for (let r = 0; r < lines; r++) {
        const abs = start + r * COLS;
        if (abs >= winEnd) break;
        const off = abs - w.start;
        left += '<div class="hex-line"><span class="addr-col">' + hx(abs) + '</span><span class="bytes">' +
          renderBytes(w, off, 'ori', cursor) + '</span><span class="ascii">' + renderAscii(w, off, 'ori') + '</span></div>';
        right += '<div class="hex-line"><span class="addr-col">' + hx(abs) + '</span><span class="bytes">' +
          renderBytes(w, off, 'ace', cursor) + '</span><span class="ascii">' + renderAscii(w, off, 'ace') + '</span></div>';
      }
      view.innerHTML = '<div class="hex-split-wrap cols">' +
        '<div><div class="hex-pane-lab">ORI</div>' + left + '</div>' +
        '<div><div class="hex-pane-lab">ACE</div>' + right + '</div></div>';
    } else {
      let html = '';
      const which = mode === 'ori' ? 'ori' : 'ace';
      for (let r = 0; r < lines; r++) {
        const abs = start + r * COLS;
        if (abs >= winEnd) break;
        const off = abs - w.start;
        html += '<div class="hex-line"><span class="addr-col">' + hx(abs) + '</span><span class="bytes">' +
          renderBytes(w, off, which, cursor) + '</span><span class="ascii">' + renderAscii(w, off, which) + '</span></div>';
      }
      view.innerHTML = html;
    }'''

new_split = '''    const labs = pairLabs();
    if (mode === 'split') {
      let leftH = '', rightH = '';
      for (let r = 0; r < lines; r++) {
        const abs = start + r * COLS;
        if (abs >= winEnd) break;
        const off = abs - w.start;
        leftH += '<div class="hex-line"><span class="addr-col">' + hx(abs) + '</span><span class="bytes">' +
          renderBytes(w, off, 'left', cursor) + '</span><span class="ascii">' + renderAscii(w, off, 'left') + '</span></div>';
        rightH += '<div class="hex-line"><span class="addr-col">' + hx(abs) + '</span><span class="bytes">' +
          renderBytes(w, off, 'right', cursor) + '</span><span class="ascii">' + renderAscii(w, off, 'right') + '</span></div>';
      }
      view.innerHTML = '<div class="hex-split-wrap cols">' +
        '<div><div class="hex-pane-lab">' + labs[0] + '</div>' + leftH + '</div>' +
        '<div><div class="hex-pane-lab">' + labs[1] + '</div>' + rightH + '</div></div>';
    } else {
      let html = '';
      const which = (mode === 'left' || mode === 'ori') ? 'left' : 'right';
      for (let r = 0; r < lines; r++) {
        const abs = start + r * COLS;
        if (abs >= winEnd) break;
        const off = abs - w.start;
        html += '<div class="hex-line"><span class="addr-col">' + hx(abs) + '</span><span class="bytes">' +
          renderBytes(w, off, which, cursor) + '</span><span class="ascii">' + renderAscii(w, off, which) + '</span></div>';
      }
      view.innerHTML = html;
    }'''

if old_split not in t:
    raise SystemExit("split render missing")
t = t.replace(old_split, new_split, 1)

# After windows are loaded (b64 decode), also decode v1
old_win = '''        ori: b64ToBytes(w.ori),
        ace: b64ToBytes(w.ace),'''
new_win = '''        ori: b64ToBytes(w.ori),
        ace: b64ToBytes(w.ace),
        v1: b64ToBytes(w.v1 || w.ace),'''
if old_win not in t:
    raise SystemExit("window decode missing")
t = t.replace(old_win, new_win, 1)

# Add hexRefreshPair before end of IIFE - find setStatus OK and add hook after atlas load
hook = '''
  window.hexRefreshPair = function () {
    if (!atlas) return;
    render();
  };
'''
marker = "  fetch(ATLAS_URL)"
if "hexRefreshPair" not in t:
    t = t.replace(marker, hook + "\n" + marker, 1)

p.write_text(t, encoding="utf-8")
print("hex dump patched OK")
