# Composition toolkit and gotchas (phase 7)

## Model
A composition is `comps/<name>/index.html` + `main.js` (+ `data.js` for product strings). `boot({ setup, measure, render, events, fonts })` from `lib/kit.js`:
1. loads `project.json` (size, fps, duration, bpm) — so build everything inside `setup()`, not at module top level (otherwise `bt(n)` uses the default BPM),
2. waits for images and fonts, runs `measure()` (read layout once: caret positions at hand-offs, text widths),
3. builds every `Line`'s layout table, runs `events()` (sound cues), exposes `window.seek(t)`.
`render(t)` must set every style from `t` alone: no CSS transitions, no timers, no state carried between frames. The renderer seeks subframes out of order across parallel workers.

## Pieces (lib/kit.js)
- `sp(t, t0, LAND|MORPH)`, `K(t, v0, [[t0, v, preset], …])` (value springing through several targets), `ease/easeOut/easeIn`, `glide`, `hop(a, b, p, height)`.
- `mk`, `box(e, cx, cy, w, h, r)` (centre-based), `dotBox`, `vis(e, on)`, `offsetIn(el, root)`.
- `Line(parent, {x, y, w, h, align, size, color, em, fam, ds, name}).type(endTime, [[text, em?], …])` — typed text whose caret placeholder the motif dot follows (`L.at(t)` renders then returns the caret position). Layout glides when a keystroke re-centres the line or adds a second line. `lineOut(L, t, t0)` exits it through a fixed mask edge.
- `riser(parent, style, html)` + `rise(r, t, tIn, tOut)` — text rising in/out of a mask line (spring in, morph out).
- `makeCamera([{at, set}, {start: beat, beats, to: {x, y, s}}])` → `cam(t)`; `applyCamera(world, c)`; `toScreen(c, x, y)`. Sets only while covered.
- `flood(el, t, t0, fromRect)` / `circleFlood(el, t, t0, origin)` — ~0.3 s, overscaled.
- `makeCursor(parent, [{a, b, pts: [[t, x, y], …], press, dark}])` — spring-driven cursor, registers `click` events.
- `ev(t, type, target, {gain})` — timeline events (`type`, `whoosh`, `click`, `pop`, `chime`, `impact`, `camera`).

## Layers
`#bg` (base colour, switched only while covered) → `#world` (camera-transformed; most content) → `#overlay` (screen-space floods). A trick that worked well: author an opening "macro" section inside a stage container that sits in world space scaled down at the spot a product UI element will later occupy; pulling the camera back then reveals the page around it with no cut.

## Gotchas (each one cost a render)
- **`visibility: visible` on a child shows through a hidden parent.** Use `vis()` (sets `inherit`) and the CSS rule `#world * { visibility: inherit }`. Symptom: ghost text from other scenes.
- **`offsetLeft/Top` ignore CSS transforms.** Measure through untransformed ancestors; convert stage→world yourself.
- **Measure the text span, not its mask wrapper** (a relative/block wrapper is as wide as its container).
- **Centred typing jitters** — each keystroke shifts the whole line by half a glyph, and a new line jumps the block up. `Line` glides its layout; keep using it rather than raw text.
- **Fast deletes strobe** (≥3 chars/frame looks like a double image with motion blur). Exit long lines with `lineOut`, delete only short words.
- **Mask exits must clip at a fixed edge** (the line rises *through* it). Clipping at the moving bottom leaves half the text visible.
- **Hand-offs**: when shape A becomes shape B, B's first frame must equal A's last (same rect, radius, colour). Compute hand-off positions in `measure()`; never read a caret from a stale render (`L.at(t)` renders first).
- **Floods**: overscale past the corners and take ~0.3 s, or half the frame changes in one frame (a cut, per the check).
- **Colour of a morphing shape**: swap colour only while it's tiny, or keep it constant.
- **Anything that disappears** must shrink to zero, rise out, or be covered — hiding a visible object pops.
- **Visible on the beat, not just started on it.** A riser is hidden by its mask for ~0.06 s after it starts, and a cursor entering from off-frame is invisible at first — start them slightly early (≈0.06 s for risers, ≈0.2 s for entrances) so the visible change lands on the beat. The self-check's every-beat test catches this.
- **Boxes, underlines and scan lines around text are sized from the measured text**, never a guessed width — and keep decorative lines out of wrapped text (a scan line following "the last line" crossed a 2-line report entry; a fixed-width box cut through a word).
- **Monospace ligatures change verbatim strings** (JetBrains Mono draws `>=` as `≥`): set `font-variant-ligatures: none` on terminal/report text.
- **Footage and images enter by shape too**: a video that switches on over other content is a single-frame pop (the check flags it). Rise it in from a mask edge or grow its window. Headless Chromium has no H.264: cut clips to VP9 WebM, all-intra (`-c:v libvpx-vp9 -g 1`), load as a blob, await `seeked`.
- **Cursor**: enters and exits off-frame; keep it until whatever covers the frame has covered it.
- **Fonts**: wait for `document.fonts.load()` before measuring; URL-encode commas in file names (`%2C`); subsetted webfonts from a site may lack glyphs (é, ñ, ¿) — use full families.
- **Footage**: re-encode all-intra (`ffmpeg -g 1`), load as a blob URL (the render server has no range requests), await `seeked` before drawing.
- **Windows**: ffmpeg has no glob input (use `studio/sheet.py`), set `PYTHONIOENCODING=utf8` when printing non-ASCII, and prefer writing Python patch scripts to files over long heredocs.

## Review loop
1. Stills at key times → `sheet.py` → look → fix. 2. Full render with `--subframes 4`. 3. Mix. 4. `check_film.py`; for any pop/cut, extract the frames around the timestamp and look before changing code. 5. 2 fps contact sheet of the final — look at all of it.
