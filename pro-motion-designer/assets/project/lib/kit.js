// Composition toolkit. Every helper here is a pure function of t (or sets styles from one), so a
// composition can be seeked to any time in any order — which is what the renderer does.
// Read references/toolkit.md for the patterns and the gotchas these helpers exist to avoid.
import { spring, LAND, MORPH, cameraMove } from './spring.js';
export { spring, LAND, MORPH };

// ---------- project + timeline ----------
export const P = { width: 1920, height: 1080, fps: 60, duration: 10, bpm: 120 };
export let BEAT = 0.5;
export const bt = (n) => n * BEAT;
export const EV = []; // every event: {t, beat, type, target, ...}; audio mix + self-check read this
export const ev = (t, type, target, extra = {}) => EV.push({ t: +t.toFixed(4), beat: +(t / BEAT).toFixed(3), type, target, ...extra });

// ---------- math ----------
export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, p) => a + (b - a) * p;
export const sp = (t, t0, p = MORPH) => spring(t - t0, p);
export const ease = (t, t0, d) => { const p = clamp((t - t0) / d); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
export const easeOut = (t, t0, d) => 1 - Math.pow(1 - clamp((t - t0) / d), 3);
export const easeIn = (t, t0, d) => Math.pow(clamp((t - t0) / d), 2);
// a value that springs through several targets: v0 + Σ Δ·spring (stays a pure function of t)
export function K(t, v0, keys) { let v = v0, prev = v0; for (const [t0, val, p] of keys) { v += (val - prev) * spring(t - t0, p || MORPH); prev = val; } return v; }
// when a spring first reaches its target (LAND ≈ 0.165 s, MORPH ≈ 0.226 s). Use it for LANDINGS (a dot
// hopping/dropping onto its spot). Reveals (text rising, words sweeping, pills growing) sound at their onset.
export const landTime = (p = LAND) => { for (let t = 0; t < 1; t += 0.001) if (spring(t, p) >= 1) return t; return 0.3; };
// critically damped step (no overshoot), used to glide layout changes
export const glide = (t, w = 32) => (t <= 0 ? 0 : 1 - (1 + w * t) * Math.exp(-w * t));
// parabolic hop from a to b, p = 0..1
export const hop = (a, b, p, height) => ({ x: lerp(a.x, b.x, p), y: lerp(a.y, b.y, p) - height * 4 * p * (1 - p) });

// ---------- DOM ----------
export function mk(parent, cls = '', style = {}, html = '') {
  const e = document.createElement('div'); e.className = ('abs ' + cls).trim(); Object.assign(e.style, style);
  if (html) e.innerHTML = html; parent.appendChild(e); return e;
}
// centre-based box
export function box(e, x, y, w, h, r) {
  e.style.left = (x - w / 2) + 'px'; e.style.top = (y - h / 2) + 'px';
  e.style.width = Math.max(0, w) + 'px'; e.style.height = Math.max(0, h) + 'px';
  if (r !== undefined) e.style.borderRadius = Math.max(0, r) + 'px';
}
export const dotBox = (e, x, y, w, h) => box(e, x, y, w, h, Math.min(w, h) / 2);
// 'inherit' (not 'visible') so a hidden container always hides its children
export const vis = (e, on) => { e.style.visibility = on ? 'inherit' : 'hidden'; };
export const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
// layout offset of el inside root (ignores CSS transforms — keep transforms off measured ancestors)
export function offsetIn(el, root) { let x = 0, y = 0, e = el; while (e && e !== root) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; } return { x, y }; }

// ---------- typed lines: the caret is a placeholder the dot follows ----------
export const LINES = [];
export class Line {
  // o: { x, y, w, h, align:'center'|'left'|'right', size, color, em, fam (css class), lh, ds (caret size), gap, name }
  constructor(parent, o) {
    this.o = Object.assign({ align: 'center', w: 1700, h: 200, size: 72, color: '#111', em: '#c50', fam: 'display', lh: 1.15, gap: 10, ds: 22 }, o);
    const { x, y, w, h, align } = this.o;
    const left = align === 'center' ? x - w / 2 : align === 'left' ? x : x - w;
    this.box = mk(parent, 'hid', { left: left + 'px', top: (y - h / 2) + 'px', width: w + 'px', height: h + 'px' });
    this.p = document.createElement('p');
    Object.assign(this.p.style, { margin: 0, position: 'absolute', textAlign: align, fontSize: this.o.size + 'px', lineHeight: this.o.lh, color: this.o.color, whiteSpace: 'pre' });
    this.p.className = this.o.fam; this.box.appendChild(this.p);
    this.chars = []; this.dels = []; this.n = -1; this.parent = parent; this.steps = null;
    LINES.push(this);
  }
  // type runs [[text, em?], ...] so the LAST keystroke lands on `end` (put `end` on a beat)
  type(end, runs, dur) {
    const list = []; for (const [s, em] of runs) for (const ch of [...s]) list.push({ ch, em: !!em });
    const n = list.length, d = dur ?? Math.min(0.42, 0.03 * n + 0.06), start = end - d;
    list.forEach((c, i) => { c.tIn = n === 1 ? end : start + d * (i / (n - 1)); this.chars.push(c); });
    ev(end, 'type', this.o.name || 'line', { chars: list.filter((c) => c.ch !== '\n').map((c) => +c.tIn.toFixed(4)) });
    return this;
  }
  // short deletes only (a few chars). Long lines should leave with lineOut(): fast deletes strobe.
  del(start, dur = 0.12) { this.dels.push({ start, dur }); return this; }
  count(t) {
    let n = 0; for (const c of this.chars) if (c.tIn <= t) n++;
    for (const d of this.dels) if (t >= d.start) {
      let present = 0; for (const c of this.chars) if (c.tIn <= d.start) present++;
      n = Math.min(n, Math.round(present * (1 - clamp((t - d.start) / d.dur))));
    }
    return n;
  }
  html(n) {
    let html = '', cur = null, buf = '';
    const flush = () => { if (!buf) return; html += cur ? `<span class="em" style="color:${this.o.em}">${esc(buf)}</span>` : esc(buf); buf = ''; };
    for (let i = 0; i < n; i++) { const c = this.chars[i]; if (c.em !== cur) { flush(); cur = c.em; } if (c.ch === '\n') { flush(); html += '\n'; } else buf += c.ch; }
    flush();
    return html + `<span class="ph" style="display:inline-block;width:${this.o.ds}px;height:${this.o.ds}px;margin-left:${n ? this.o.gap : 0}px"></span>`;
  }
  // every size the line takes and when (1 ms sampling), so re-centring glides instead of jumping
  buildSteps() {
    const ts = this.chars.map((c) => c.tIn).concat(this.dels.flatMap((d) => [d.start, d.start + d.dur]));
    if (!ts.length) { this.steps = [{ t: -1, w: 0, h: 0 }]; return; }
    const t0 = Math.min(...ts) - 0.01, t1 = Math.max(...ts) + 0.01, size = {};
    const get = (n) => { if (!size[n]) { this.p.innerHTML = this.html(n); size[n] = { w: this.p.offsetWidth, h: this.p.offsetHeight }; } return size[n]; };
    let prev = this.count(t0); this.steps = [{ t: -1, ...get(prev) }];
    for (let t = t0; t <= t1; t += 0.001) { const n = this.count(t); if (n !== prev) { this.steps.push({ t, ...get(n) }); prev = n; } }
    this.n = -1;
  }
  size(t) {
    let w = this.steps[0].w, h = this.steps[0].h;
    for (let i = 1; i < this.steps.length; i++) { const g = glide(t - this.steps[i].t); w += (this.steps[i].w - this.steps[i - 1].w) * g; h += (this.steps[i].h - this.steps[i - 1].h) * g; }
    return { w, h };
  }
  render(t) {
    const n = this.count(t);
    if (n !== this.n) { this.n = n; this.p.innerHTML = this.html(n); this.ph = this.p.lastChild; }
    if (!this.steps) return;
    const { w, h } = this.size(t), { w: W, h: Hh, align } = this.o;
    this.p.style.left = (align === 'center' ? W / 2 - w / 2 : align === 'left' ? 0 : W - w) + 'px';
    this.p.style.top = (Hh / 2 - h / 2) + 'px';
  }
  caret() { const o = offsetIn(this.ph, this.parent); return { x: o.x + this.ph.offsetWidth / 2, y: o.y + this.ph.offsetHeight / 2 }; }
  at(t) { this.render(t); return this.caret(); }  // render first: a caret read from a stale render jumps
  show(on) { vis(this.box, on); }
}
// the line rises through a mask edge fixed 60px above its box; gone after box height + 70 px
export const lineOut = (L, t, t0) => { const d = L.o.h + 70, k = sp(t, t0, MORPH); L.box.style.clipPath = `inset(${-60 + d * k}px -60px -60px -60px)`; L.box.style.transform = `translateY(${-d * k}px)`; };

// ---------- text that rises out of (and back into) a mask line ----------
export function riser(parent, style, html, cls = '') {
  const outer = mk(parent, 'mask hid', style); const inner = mk(outer, cls, { left: 0, top: 0, whiteSpace: 'nowrap' }, html);
  inner.style.position = 'relative'; return { outer, inner };
}
export function rise(r, t, tIn, tOut, p = LAND) {
  const h = r.outer.offsetHeight || 100, off = h * 1.1;
  const y = off - off * sp(t, tIn, p) - (tOut !== undefined ? off * sp(t, tOut, MORPH) : 0);
  r.inner.style.transform = `translateY(${y}px)`;
  vis(r.outer, t >= tIn - 0.02 && (tOut === undefined || t < tOut + 0.6));
}

// ---------- camera: one move at a time; `set` only while the frame is fully covered ----------
// entries: { at, set:{x,y,s} } | { start (beat), beats, to:{x?,y?,s?} }
export function makeCamera(entries) {
  for (const c of entries) if (!c.set) ev(bt(c.start), 'camera', 'camera', { end: bt(c.start + c.beats) });
  return (t) => {
    let s = { x: P.width / 2, y: P.height / 2, s: 1, ...(entries[0]?.set || {}) };
    for (const e of entries) {
      const t0 = e.set ? e.at : bt(e.start);
      if (t < t0) break;
      if (e.set) { s = { ...s, ...e.set }; continue; }
      const p = cameraMove(t, e.start, e.beats, BEAT), to = { ...s, ...e.to };
      s = { x: lerp(s.x, to.x, p), y: lerp(s.y, to.y, p), s: Math.exp(lerp(Math.log(s.s), Math.log(to.s), p)) };
    }
    return s;
  };
}
export const applyCamera = (el, c) => { el.style.transform = `translate(${P.width / 2 - c.x * c.s}px,${P.height / 2 - c.y * c.s}px) scale(${c.s})`; };
export const toScreen = (c, x, y) => ({ x: (x - c.x) * c.s + P.width / 2, y: (y - c.y) * c.s + P.height / 2 });

// ---------- flood: a shape grows past the frame's corners (~0.3 s) ----------
// from: {x,y,w,h,r} in screen coords. Overscale so no corner is left, and take ~0.3 s:
// faster and half the screen changes in one frame (the self-check flags it).
export function flood(el, t, t0, from, dur = 0.3) {
  const p = ease(t, t0, dur), W = P.width + 16, H = P.height + 16;
  box(el, lerp(from.x, P.width / 2, p), lerp(from.y, P.height / 2, p), lerp(from.w, W, p), lerp(from.h, H, p), lerp(from.r ?? 0, 0, p));
  return p;
}
export function circleFlood(el, t, t0, o, dur = 0.32) {
  const R = Math.hypot(P.width, P.height) + 40, r = lerp(0, R, ease(t, t0, dur));
  box(el, o.x, o.y, 2 * r, 2 * r, r);
}

// ---------- cursor ----------
// appearances: [{ a, b, pts: [[t, x, y], ...], press?, dark? }] — enter/exit from off-frame, never pop in
export function makeCursor(parent, appearances) {
  const el = mk(parent, 'hid', { width: '44px', height: '44px', zIndex: 100, transformOrigin: '6px 4px' });
  for (const c of appearances) if (c.press !== undefined) ev(c.press, 'click', c.target || 'cursor click');
  return (t) => {
    const c = appearances.find((c) => t >= c.a && t < c.b); vis(el, !!c); if (!c) return;
    let x = c.pts[0][1], y = c.pts[0][2], px = x, py = y;
    for (const [t0, X, Y] of c.pts.slice(1)) { const s = spring(t - t0, MORPH); x += (X - px) * s; y += (Y - py) * s; px = X; py = Y; }
    el.style.left = (x - 6) + 'px'; el.style.top = (y - 4) + 'px';
    const pr = c.press !== undefined ? 1 - 0.14 * (sp(t, c.press, LAND) - sp(t, c.press + 0.1, LAND)) : 1;
    el.style.transform = `scale(${pr})`;
    const k = String(!!c.dark);
    if (el.dataset.k !== k) { el.innerHTML = c.dark ? SVG.cursor('#FAFAFA', '#111') : SVG.cursor('#111', '#FAFAFA'); el.dataset.k = k; }
  };
}

export const SVG = {
  cursor: (fill, stroke) => `<svg viewBox="0 0 28 28" width="100%" height="100%"><path d="M5 3l17 9.6-7.3 1.9 4.4 7.6-3.2 1.8-4.4-7.6L6 21.6z" fill="${fill}" stroke="${stroke}" stroke-width="1.6" stroke-linejoin="round"/></svg>`,
  arrow: (c) => `<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="${c}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h15"/><path d="M13 6l6 6-6 6"/></svg>`,
  ext: (c) => `<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="${c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>`,
  search: (c) => `<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" stroke="${c}" stroke-width="2.2" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L20 20"/></svg>`,
  half: (c) => `<svg viewBox="0 0 24 24" width="100%" height="100%"><circle cx="12" cy="12" r="9" fill="none" stroke="${c}" stroke-width="2"/><path d="M12 3a9 9 0 0 1 0 18z" fill="${c}"/></svg>`,
};

// ---------- boot ----------
// Loads project.json (size, fps, duration, bpm) FIRST, then runs setup() — build the DOM, lines,
// camera and cursor there, not at module top level, so every bt(n) uses the project's real BPM.
// Then waits for images and fonts, runs measure(), builds every Line's layout table, registers
// sound events and exposes window.seek.
export async function boot({ setup = () => {}, measure = () => {}, render, events = () => {}, fonts = [] }) {
  try { Object.assign(P, await (await fetch('/project.json')).json()); } catch { /* keep defaults */ }
  BEAT = 60 / P.bpm;
  window.COMP = { width: P.width, height: P.height, fps: P.fps, duration: P.duration };
  window.TIMELINE = EV;
  document.documentElement.style.setProperty('--W', P.width + 'px'); document.documentElement.style.setProperty('--H', P.height + 'px');
  await setup();
  await Promise.all([...document.images].map((i) => (i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; }))));
  await Promise.all(fonts.map((f) => document.fonts.load(f, 'áéíóúñ¿AaBb')));
  await document.fonts.ready;
  for (const l of LINES) l.buildSteps(); // before measure(): carets read before this sit at the box edge
  await measure();
  for (const l of LINES) l.n = -1;
  await events();
  EV.sort((a, b) => a.t - b.t);
  window.seek = (t) => render(t);
  render(0);
  return true;
}
