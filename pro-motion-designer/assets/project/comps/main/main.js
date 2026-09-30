// Template composition: an 8 s (16-beat) demo of the house rules, meant to be copied and grown.
//   b0 dot pops · b1–b3 dot types the tagline · b4 (drop) a product card grows out of the dot ·
//   b5–b7 rows rise · b8 cursor enters · b9 click · b10 the button floods the frame ·
//   b11 flood contracts into the CTA pill · b12 pill shrinks back into the dot · b13 dot types the wordmark ·
//   b14 url rises · b15 the dot lands as the wordmark's period.
// Nothing fades, nothing cuts: every scene is made out of the previous one.
import {
  P, bt, ev, sp, ease, lerp, clamp, K, hop, mk, box, dotBox, vis, esc, Line, lineOut, riser, rise,
  makeCamera, applyCamera, toScreen, flood, makeCursor, LAND, MORPH, boot,
} from '../../lib/kit.js';
import { BRAND } from '../../brand/brand.js';
import * as D from './data.js';

const C = BRAND.light, DOT = BRAND.dot;
let W, H, CX, CY, bgEl, world, over, dot, L1, L2, card, cardC, rows, badge, btn, fl, pillTxt, url, cam, cursor;
const M = {};
const CARD = { w: 760, h: 460 };

function setup() {
  W = P.width; H = P.height; CX = W / 2; CY = H / 2;
  const css = document.createElement('style');
  css.textContent = `.display{font-family:${BRAND.fonts.display}} .ui{font-family:${BRAND.fonts.ui}} .mono{font-family:${BRAND.fonts.mono}}`;
  document.head.appendChild(css);
  bgEl = document.getElementById('bg'); world = document.getElementById('world'); over = document.getElementById('overlay');
  bgEl.style.background = C.bg;

  L1 = new Line(world, { x: CX, y: CY, w: W - 200, h: 180, size: 84, color: C.ink, em: C.accentText, fam: 'display', ds: DOT, name: 'tagline' });
  D.TAGLINE.forEach((run, i) => L1.type(bt(1 + i), [run]));

  // product card (build real UI from the product's screens; this is a stand-in)
  card = mk(world, 'hid clip', { background: C.raised, border: `2px solid ${C.border}`, zIndex: 5 });
  cardC = mk(card, '', { width: CARD.w + 'px', height: CARD.h + 'px' });
  mk(cardC, '', { left: 0, top: 0, width: '100%', height: '56px', borderBottom: `1px solid ${C.border}`, background: C.surface },
    `<span style="position:absolute;left:22px;top:21px;display:flex;gap:8px">${[0, 1, 2].map(() => `<i style="width:12px;height:12px;border-radius:50%;background:${C.border};display:inline-block"></i>`).join('')}</span>
     <span class="ui" style="position:absolute;left:96px;top:15px;font-size:20px;font-weight:600;color:${C.ink}">${esc(D.CARD.app)}</span>`);
  mk(cardC, 'display', { left: '40px', top: '84px', fontSize: '40px', color: C.ink }, esc(D.CARD.title));
  rows = D.CARD.rows.map(([k, v], i) => riser(cardC, { left: '40px', top: (164 + i * 64) + 'px', width: (CARD.w - 80) + 'px', height: '52px' },
    `<div class="ui" style="display:flex;justify-content:space-between;width:${CARD.w - 80}px;font-size:24px;line-height:52px;border-bottom:1px solid ${C.border}"><span style="color:${C.muted}">${esc(k)}</span><span class="mono" style="color:${C.ink}">${esc(v)}</span></div>`));
  badge = mk(cardC, 'ui', { left: (CARD.w - 120) + 'px', top: '92px', fontSize: '17px', fontWeight: 600, color: C.onAccent, background: C.accent, borderRadius: '999px', padding: '5px 14px' }, esc(D.CARD.badge));
  btn = mk(cardC, 'ui', { left: (CARD.w - 250) + 'px', top: (CARD.h - 80) + 'px', width: '210px', height: '56px', borderRadius: '12px', background: C.accent, color: C.onAccent,
    fontSize: '22px', fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center' }, esc(D.CARD.cta));
  M.btn = { x: CX - CARD.w / 2 + (CARD.w - 250) + 105, y: CY - CARD.h / 2 + (CARD.h - 80) + 28 };

  // flood → CTA pill (screen space)
  fl = mk(over, 'hid clip', { background: C.accent });
  pillTxt = riser(fl, { left: 0, top: 0, width: '100%', height: '100%' }, `<div class="ui" style="font-size:44px;font-weight:600;color:${C.onAccent};text-align:center;line-height:120px">${esc(D.CTA)}</div>`);
  pillTxt.inner.style.width = '100%';

  L2 = new Line(world, { x: CX, y: CY - 40, w: W - 200, h: 200, size: 150, color: C.ink, fam: 'display', ds: DOT * 1.25, gap: 8, name: 'wordmark' })
    .type(bt(13), [[BRAND.name]], 0.4);
  url = riser(world, { left: 0, top: (CY + 80) + 'px', width: W + 'px', height: '60px' }, `<div class="mono" style="width:${W}px;text-align:center;font-size:32px;line-height:60px;color:${C.muted}">${esc(BRAND.url)}</div>`);

  dot = mk(world, 'hid', { background: C.accent, zIndex: 50 });

  cam = makeCamera([{ at: 0, set: { x: CX, y: CY, s: 1 } }, { start: 4, beats: 4, to: { s: 1.06 } }, { at: bt(10) + 0.32, set: { x: CX, y: CY, s: 1 } }]);
  // the cursor starts just off-frame a moment before b8 so it is visibly crossing the frame ON the beat
  cursor = makeCursor(world, [{ a: bt(8) - 0.2, b: bt(10) + 0.33, pts: [[bt(8) - 0.2, W + 40, H * 0.9], [bt(8) - 0.15, M.btn.x + 10, M.btn.y + 8], [bt(10), W + 80, H + 80]], press: bt(9), target: 'CTA button' }]);
}

function measure() {
  M.L1c = L1.at(0); M.L1end = L1.at(bt(3) + 0.01);
  M.L2c = L2.at(0); M.L2end = L2.at(bt(13) + 0.01);
  L1.n = -1; L2.n = -1;
}

function render(t) {
  const c = cam(t); applyCamera(world, c);
  // tagline
  const on1 = t < bt(4) + 0.5; L1.show(on1); if (on1) { L1.render(t); lineOut(L1, t, bt(4)); }
  // card: grows out of the dot on the drop, stays until the flood has covered the frame
  const onCard = t >= bt(4) && t < bt(10) + 0.31; vis(card, onCard);
  if (onCard) {
    const g = sp(t, bt(4), MORPH), w = lerp(DOT, CARD.w, g), h = lerp(DOT, CARD.h, g);
    box(card, lerp(M.L1end.x, CX, g), lerp(M.L1end.y, CY, g), w, h, lerp(DOT / 2, 20, clamp(g)));
    cardC.style.left = (w / 2 - CARD.w / 2) + 'px'; cardC.style.top = (h / 2 - CARD.h / 2) + 'px';
    rows.forEach((r, i) => rise(r, t, bt(5 + i) - 0.06));
    badge.style.transform = `scale(${sp(t, bt(7), LAND)})`;
    btn.style.transform = `scale(${1 - 0.06 * (sp(t, bt(9), LAND) - sp(t, bt(9) + 0.1, LAND))})`;
  }
  // flood from the button, then contract into the CTA pill, then into the dot
  const onF = t >= bt(10) && t < bt(12) + 0.42; vis(fl, onF);
  if (onF) {
    const b = toScreen(cam(bt(10)), M.btn.x, M.btn.y);
    if (t < bt(11)) flood(fl, t, bt(10), { x: b.x, y: b.y, w: 210 * 1.06, h: 56 * 1.06, r: 12 });
    else {
      const k = sp(t, bt(11), MORPH), s = sp(t, bt(12), MORPH);
      const w = lerp(lerp(W + 16, 560, k), DOT, s), h = lerp(lerp(H + 16, 120, k), DOT, s);
      box(fl, lerp(CX, M.L2c.x, s), lerp(CY, M.L2c.y, s), w, h, Math.min(w, h) / 2 * clamp(k * 3));
      rise(pillTxt, t, bt(11) + 0.12, bt(12));
      pillTxt.inner.style.left = (w / 2 - 280) + 'px'; pillTxt.inner.style.width = '560px';
    }
  }
  // wordmark + url
  const on2 = t >= bt(12) + 0.4; L2.show(on2); if (on2) L2.render(t);
  rise(url, t, bt(14) - 0.06); // a riser is only visible ~0.06 s after it starts: lead it so the change lands on the beat
  // the dot
  let d = null;
  if (t < bt(4)) { const p = L1.at(t); d = { ...p, s: DOT * sp(t, 0, LAND) }; }
  else if (t >= bt(12) + 0.4) {
    const p = L2.at(t), land = t >= bt(15) ? K(t, 1, [[bt(15), 1.45, LAND], [bt(15) + 0.12, 1, LAND]]) : 1;
    d = { ...p, s: DOT * 1.25 * land };
  }
  vis(dot, !!d); if (d) dotBox(dot, d.x, d.y, d.s, d.s);
  cursor(t);
}

function events() {
  const pop = (t, target) => ev(t, 'pop', target);
  pop(0.08, 'dot appears');
  ev(bt(4), 'impact', 'card grows on the drop');
  [5, 6, 7].forEach((b) => pop(bt(b) + 0.08, 'row ' + b)); pop(bt(7) + 0.1, 'badge');
  ev(bt(10) + 0.12, 'whoosh', 'button floods the frame');
  ev(bt(11) + 0.1, 'whoosh', 'flood contracts into the pill', { gain: -4 });
  ev(bt(12) + 0.15, 'whoosh', 'pill into the dot', { gain: -8 });
  ev(bt(14) + 0.08, 'pop', 'url');
  ev(bt(15), 'chime', 'dot lands as the period');
}

window.ready = boot({ setup, measure, render, events });
